"""Industrial decision rules, uncertainty thresholds, and fail-safe policy enforcement."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from edge_inspector.inference.base import InferenceResult
from edge_inspector.quality import QualityCheckResult


class InspectionDecision(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"


@dataclass
class DefectRule:
    fail_threshold: float = 0.70
    critical: bool = False


@dataclass
class DecisionRuleConfig:
    """Configurable thresholds separating PASS, FAIL, and REVIEW zones."""
    default_pass_threshold: float = 0.35
    default_fail_threshold: float = 0.70
    defect_criticality: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: {
            "seam_defect": {"fail_threshold": 0.50, "critical": True},
            "pinhole": {"fail_threshold": 0.45, "critical": True},
            "dent": {"fail_threshold": 0.70, "critical": False},
            "rim_dent": {"fail_threshold": 0.65, "critical": True},
            "scratch": {"fail_threshold": 0.75, "critical": False},
            "contamination": {"fail_threshold": 0.65, "critical": False},
            "corrosion": {"fail_threshold": 0.60, "critical": True},
            "ovalization": {"fail_threshold": 0.65, "critical": True},
        }
    )


@dataclass
class DecisionResult:
    """Industrial decision record for manufacturing execution systems (MES) and line actuation."""
    decision: InspectionDecision
    primary_reason: str
    confidence_score: float
    uncertainty_score: float
    critical_defects: List[str] = field(default_factory=list)
    quality_gate_passed: bool = True
    requires_human_review: bool = False
    actuate_reject: bool = False  # True only for confirmed, verified FAIL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "primary_reason": self.primary_reason,
            "confidence_score": self.confidence_score,
            "uncertainty_score": self.uncertainty_score,
            "critical_defects": self.critical_defects,
            "quality_gate_passed": self.quality_gate_passed,
            "requires_human_review": self.requires_human_review,
            "actuate_reject": self.actuate_reject,
        }


def evaluate_inspection(
    quality: QualityCheckResult,
    inference: Optional[InferenceResult],
    config: Optional[DecisionRuleConfig] = None,
    deadline_exceeded: bool = False,
    memory_warning: bool = False,
) -> DecisionResult:
    """Applies strict fail-safe industrial decision logic.

    Rules:
    1. If deadline was exceeded -> REVIEW (timing fault, cannot guarantee conveyor synchronization).
    2. If image corrupted or quality gate failed (blurry, glare) -> REVIEW (never falsely pass unverified cans).
    3. If inference engine failed or timed out -> REVIEW.
    4. If defect detected with confidence >= threshold -> FAIL (Actuate Reject).
    5. If defect detected with confidence in ambiguous zone (between pass & fail thresholds) -> REVIEW.
    6. If no defects or all defect scores < pass threshold -> PASS.
    """
    cfg = config or DecisionRuleConfig()

    # Fail-safe Check 1: Processing deadline exceeded
    if deadline_exceeded:
        return DecisionResult(
            decision=InspectionDecision.REVIEW,
            primary_reason="INFERENCE_DEADLINE_EXCEEDED (conveyor travel timing expired)",
            confidence_score=0.0,
            uncertainty_score=1.0,
            quality_gate_passed=quality.passed_quality_gate,
            requires_human_review=True,
            actuate_reject=False,
        )

    # Fail-safe Check 2: Quality gate failure
    if not quality.is_valid:
        return DecisionResult(
            decision=InspectionDecision.REVIEW,
            primary_reason=f"IMAGE_INVALID: {', '.join(quality.reasons)}",
            confidence_score=0.0,
            uncertainty_score=1.0,
            quality_gate_passed=False,
            requires_human_review=True,
            actuate_reject=False,
        )

    if not quality.passed_quality_gate:
        return DecisionResult(
            decision=InspectionDecision.REVIEW,
            primary_reason=f"IMAGE_QUALITY_FAIL: {', '.join(quality.reasons)}",
            confidence_score=0.0,
            uncertainty_score=1.0,
            quality_gate_passed=False,
            requires_human_review=True,
            actuate_reject=False,
        )

    # Fail-safe Check 3: Missing inference result
    if inference is None:
        return DecisionResult(
            decision=InspectionDecision.REVIEW,
            primary_reason="MODEL_INFERENCE_UNAVAILABLE",
            confidence_score=0.0,
            uncertainty_score=1.0,
            quality_gate_passed=True,
            requires_human_review=True,
            actuate_reject=False,
        )

    # Clean can evaluation
    if not inference.predictions:
        return DecisionResult(
            decision=InspectionDecision.PASS,
            primary_reason="CAN_SURFACE_CLEAN (no anomalies above detection threshold)",
            confidence_score=1.0,
            uncertainty_score=0.0,
            quality_gate_passed=True,
            requires_human_review=False,
            actuate_reject=False,
        )

    # Defect evaluation against per-defect criticality rules
    critical_defects_found: List[str] = []
    fail_detected = False
    review_detected = False
    highest_conf = 0.0
    highest_defect = ""

    for pred in inference.predictions:
        rule = cfg.defect_criticality.get(pred.label, {
            "fail_threshold": cfg.default_fail_threshold,
            "critical": False,
        })
        threshold = float(rule.get("fail_threshold", cfg.default_fail_threshold))
        is_critical = bool(rule.get("critical", False))

        if pred.confidence > highest_conf:
            highest_conf = pred.confidence
            highest_defect = pred.label

        if is_critical and pred.confidence >= threshold:
            critical_defects_found.append(pred.label)

        if pred.confidence >= threshold:
            fail_detected = True
        elif pred.confidence >= cfg.default_pass_threshold:
            # Uncertain / ambiguous zone
            review_detected = True

    # Compute uncertainty: distance from decisive boundaries
    # Maximum uncertainty (1.0) occurs midway between pass and fail thresholds
    midpoint = (cfg.default_pass_threshold + cfg.default_fail_threshold) / 2.0
    half_range = (cfg.default_fail_threshold - cfg.default_pass_threshold) / 2.0
    uncertainty = max(0.0, 1.0 - (abs(highest_conf - midpoint) / half_range)) if half_range > 0 else 0.0

    if fail_detected:
        reasons = [f"CRITICAL_{highest_defect.upper()}" if highest_defect in critical_defects_found else highest_defect.upper()]
        return DecisionResult(
            decision=InspectionDecision.FAIL,
            primary_reason=f"DEFECT_DETECTED: {highest_defect} (confidence={highest_conf:.2f})",
            confidence_score=highest_conf,
            uncertainty_score=round(uncertainty, 3),
            critical_defects=critical_defects_found,
            quality_gate_passed=True,
            requires_human_review=False,
            actuate_reject=True,
        )

    if review_detected:
        return DecisionResult(
            decision=InspectionDecision.REVIEW,
            primary_reason=f"UNCERTAIN_PREDICTION: {highest_defect} in review zone (conf={highest_conf:.2f})",
            confidence_score=highest_conf,
            uncertainty_score=round(uncertainty, 3),
            critical_defects=critical_defects_found,
            quality_gate_passed=True,
            requires_human_review=True,
            actuate_reject=False,  # Never actuate pneumatic reject without validated certainty
        )

    return DecisionResult(
        decision=InspectionDecision.PASS,
        primary_reason="ALL_SCORES_BELOW_PASS_THRESHOLD",
        confidence_score=round(1.0 - highest_conf, 3),
        uncertainty_score=round(uncertainty, 3),
        quality_gate_passed=True,
        requires_human_review=False,
        actuate_reject=False,
    )
