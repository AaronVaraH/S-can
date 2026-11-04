"""Unit tests for industrial decision rules and reject actuator interlocks."""

import time
import pytest
from edge_inspector.actuator import ActuatorConfig, SimulationRejectActuator
from edge_inspector.decision import (
    DecisionResult,
    DecisionRuleConfig,
    InspectionDecision,
    evaluate_inspection,
)
from edge_inspector.inference.base import DefectPrediction, InferenceResult
from edge_inspector.quality import QualityCheckResult


def test_clean_can_passes():
    quality = QualityCheckResult(is_valid=True, passed_quality_gate=True)
    inference = InferenceResult(
        predictions=[],
        inference_latency_ms=15.0,
        model_id="test_model",
        model_version="1.0",
        backend="ONNX",
    )
    decision = evaluate_inspection(quality, inference)
    assert decision.decision == InspectionDecision.PASS
    assert decision.actuate_reject is False
    assert decision.requires_human_review is False


def test_critical_seam_defect_fails():
    quality = QualityCheckResult(is_valid=True, passed_quality_gate=True)
    inference = InferenceResult(
        predictions=[DefectPrediction(label="seam_defect", confidence=0.75, severity="CRITICAL")],
        inference_latency_ms=15.0,
        model_id="test_model",
        model_version="1.0",
        backend="ONNX",
    )
    decision = evaluate_inspection(quality, inference)
    assert decision.decision == InspectionDecision.FAIL
    assert decision.actuate_reject is True
    assert "seam_defect" in decision.critical_defects


def test_uncertain_score_marks_review():
    quality = QualityCheckResult(is_valid=True, passed_quality_gate=True)
    # 0.50 is between pass threshold (0.35) and fail threshold (0.70)
    inference = InferenceResult(
        predictions=[DefectPrediction(label="scratch", confidence=0.50, severity="MINOR")],
        inference_latency_ms=15.0,
        model_id="test_model",
        model_version="1.0",
        backend="ONNX",
    )
    decision = evaluate_inspection(quality, inference)
    assert decision.decision == InspectionDecision.REVIEW
    assert decision.actuate_reject is False
    assert decision.requires_human_review is True


def test_blurry_image_marks_review():
    quality = QualityCheckResult(is_valid=True, passed_quality_gate=False, reasons=["BLURRY_IMAGE"])
    inference = InferenceResult(
        predictions=[],
        inference_latency_ms=15.0,
        model_id="test_model",
        model_version="1.0",
        backend="ONNX",
    )
    decision = evaluate_inspection(quality, inference)
    assert decision.decision == InspectionDecision.REVIEW
    assert decision.actuate_reject is False


def test_actuator_safety_interlock():
    actuator = SimulationRejectActuator(ActuatorConfig(conveyor_delay_ms=200, deadline_tolerance_ms=50))
    ts_ns = time.perf_counter_ns()

    fail_decision = DecisionResult(
        decision=InspectionDecision.FAIL,
        primary_reason="DEFECT",
        confidence_score=0.9,
        uncertainty_score=0.0,
        actuate_reject=True,
    )

    # Normal actuation succeeds
    res = actuator.trigger_reject(fail_decision, ts_ns)
    assert res["actuated"] is True

    # When interlock engaged, actuation is blocked
    actuator.engage_safety_interlock("EMERGENCY_BUTTON")
    res_blocked = actuator.trigger_reject(fail_decision, ts_ns)
    assert res_blocked["actuated"] is False
    assert "INTERLOCK" in res_blocked["reason"]

    actuator.release_safety_interlock()


def test_actuator_timing_deadline_fault():
    actuator = SimulationRejectActuator(ActuatorConfig(conveyor_delay_ms=100, deadline_tolerance_ms=20))
    # Frame timestamp from 300ms in the past (exceeds conveyor transit window)
    expired_ts_ns = time.perf_counter_ns() - int(300 * 1_000_000)

    fail_decision = DecisionResult(
        decision=InspectionDecision.FAIL,
        primary_reason="DEFECT",
        confidence_score=0.9,
        uncertainty_score=0.0,
        actuate_reject=True,
    )
    res = actuator.trigger_reject(fail_decision, expired_ts_ns)
    assert res["actuated"] is False
    assert "TIMING_FAULT" in res["reason"]
