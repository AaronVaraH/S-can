"""Local edge storage manager: SQLite inspection history, image annotation, and disk quota pruning."""

from __future__ import annotations

import json
import logging
import os
import shutil
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from edge_inspector.decision import DecisionResult, InspectionDecision
from edge_inspector.inference.base import InferenceResult
from edge_inspector.quality import QualityCheckResult

logger = logging.getLogger(__name__)


@dataclass
class InspectionRecord:
    inspection_id: str
    timestamp: str
    frame_id: int
    decision: str
    primary_defect: Optional[str]
    confidence: float
    uncertainty: float
    quality_gate_passed: bool
    total_latency_ms: float
    image_path: Optional[str]
    metadata_json: str


class StorageManager:
    """Manages SQLite database for inspection records and automated image retention policies."""

    def __init__(
        self,
        db_path: str = "data/inspection.db",
        image_dir: str = "data/inspections",
        save_annotated_images: bool = True,
        save_pass_images: bool = False,
        save_fail_images: bool = True,
        save_review_images: bool = True,
        max_disk_usage_percent: float = 85.0,
    ) -> None:
        self.db_path = Path(db_path)
        self.image_dir = Path(image_dir)
        self.save_annotated_images = save_annotated_images
        self.save_pass_images = save_pass_images
        self.save_fail_images = save_fail_images
        self.save_review_images = save_review_images
        self.max_disk_usage_percent = max_disk_usage_percent

        self.db_available = False
        self._init_storage()

    def _init_storage(self) -> None:
        """Initializes database schema and inspection directories."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.image_dir.mkdir(parents=True, exist_ok=True)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS inspections (
                        inspection_id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        frame_id INTEGER NOT NULL,
                        decision TEXT NOT NULL,
                        primary_defect TEXT,
                        confidence REAL NOT NULL,
                        uncertainty REAL NOT NULL,
                        quality_gate_passed INTEGER NOT NULL,
                        total_latency_ms REAL NOT NULL,
                        image_path TEXT,
                        metadata_json TEXT
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON inspections(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_decision ON inspections(decision)")
                conn.commit()

            self.db_available = True
        except Exception as e:
            logger.error(f"Failed to initialize SQLite storage at {self.db_path}: {str(e)}")
            self.db_available = False

    def check_disk_space(self) -> Tuple[bool, float]:
        """Checks partition disk usage percentage."""
        try:
            total, used, free = shutil.disk_usage(self.image_dir)
            percent_used = (used / total) * 100.0
            return percent_used < self.max_disk_usage_percent, round(percent_used, 1)
        except Exception:
            return True, 50.0

    def prune_old_images_if_needed(self) -> int:
        """Prunes oldest images to prevent filling the Raspberry Pi SD card / eMMC."""
        healthy, percent_used = self.check_disk_space()
        if healthy:
            return 0

        logger.warning(f"Disk usage ({percent_used}%) exceeds threshold ({self.max_disk_usage_percent}%). Pruning oldest images...")
        pruned_count = 0

        try:
            # Query oldest images from PASS first, then REVIEW, keeping FAIL images longest
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT inspection_id, image_path FROM inspections
                    WHERE image_path IS NOT NULL AND decision = 'PASS'
                    ORDER BY timestamp ASC LIMIT 50
                """)
                rows = cursor.fetchall()

                # If no PASS images to delete, prune oldest REVIEW images
                if not rows:
                    cursor.execute("""
                        SELECT inspection_id, image_path FROM inspections
                        WHERE image_path IS NOT NULL AND decision = 'REVIEW'
                        ORDER BY timestamp ASC LIMIT 25
                    """)
                    rows = cursor.fetchall()

                for insp_id, img_path in rows:
                    p = Path(img_path)
                    if p.exists():
                        try:
                            p.unlink()
                            pruned_count += 1
                        except Exception:
                            pass
                    cursor.execute("UPDATE inspections SET image_path = NULL WHERE inspection_id = ?", (insp_id,))

                conn.commit()

        except Exception as e:
            logger.error(f"Image pruning failed: {str(e)}")

        return pruned_count

    def render_annotated_image(
        self,
        raw_image: np.ndarray,
        quality: QualityCheckResult,
        inference: Optional[InferenceResult],
        decision: DecisionResult,
    ) -> np.ndarray:
        """Overlays bounding boxes, labels, and industrial status banners on inspection frame."""
        annotated = raw_image.copy()
        if len(annotated.shape) == 2:
            annotated = cv2.cvtColor(annotated, cv2.COLOR_GRAY2BGR)
        elif annotated.shape[2] == 4:
            annotated = cv2.cvtColor(annotated, cv2.COLOR_RGBA2BGR)

        h, w = annotated.shape[:2]

        # Draw defect bounding boxes if any
        if inference and inference.predictions:
            for pred in inference.predictions:
                if pred.bbox:
                    x1, y1, x2, y2 = pred.bbox
                    color = (0, 0, 255) if pred.severity == "CRITICAL" else (0, 165, 255)
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                    label_text = f"{pred.label.upper()} {pred.confidence:.2f}"
                    cv2.putText(
                        annotated,
                        label_text,
                        (x1, max(20, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        color,
                        2,
                        cv2.LINE_AA,
                    )

        # Header status banner
        banner_h = 40
        banner_color = (0, 180, 0)  # Green for PASS
        if decision.decision == InspectionDecision.FAIL:
            banner_color = (0, 0, 220)  # Red for FAIL
        elif decision.decision == InspectionDecision.REVIEW:
            banner_color = (0, 200, 220)  # Yellow/Amber for REVIEW

        overlay = annotated.copy()
        cv2.rectangle(overlay, (0, 0), (w, banner_h), banner_color, -1)
        cv2.addWeighted(overlay, 0.85, annotated, 0.15, 0, annotated)

        status_text = f"[{decision.decision.value}] {decision.primary_reason}"
        cv2.putText(
            annotated,
            status_text[:65],
            (10, 26),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        return annotated

    def save_inspection(
        self,
        frame_id: int,
        raw_image: np.ndarray,
        quality: QualityCheckResult,
        inference: Optional[InferenceResult],
        decision: DecisionResult,
        total_latency_ms: float,
    ) -> InspectionRecord:
        """Stores inspection metadata to SQLite and conditionally saves annotated images."""
        inspection_id = str(uuid.uuid4())
        timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

        # Determine whether to save image
        should_save = False
        if self.save_annotated_images:
            if decision.decision == InspectionDecision.FAIL and self.save_fail_images:
                should_save = True
            elif decision.decision == InspectionDecision.REVIEW and self.save_review_images:
                should_save = True
            elif decision.decision == InspectionDecision.PASS and self.save_pass_images:
                should_save = True

        image_path_str = None
        if should_save:
            try:
                self.prune_old_images_if_needed()
                annotated = self.render_annotated_image(raw_image, quality, inference, decision)
                fname = f"{decision.decision.value}_{frame_id}_{inspection_id[:8]}.jpg"
                out_path = self.image_dir / fname
                cv2.imwrite(str(out_path), annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
                image_path_str = str(out_path)
            except Exception as e:
                logger.error(f"Failed to write inspection image: {str(e)}")

        meta_dict = {
            "quality": quality.to_dict(),
            "inference": inference.to_dict() if inference else None,
            "decision": decision.to_dict(),
        }
        meta_json = json.dumps(meta_dict)

        record = InspectionRecord(
            inspection_id=inspection_id,
            timestamp=timestamp_iso,
            frame_id=frame_id,
            decision=decision.decision.value,
            primary_defect=inference.primary_defect if inference else None,
            confidence=decision.confidence_score,
            uncertainty=decision.uncertainty_score,
            quality_gate_passed=quality.passed_quality_gate,
            total_latency_ms=round(total_latency_ms, 2),
            image_path=image_path_str,
            metadata_json=meta_json,
        )

        if self.db_available:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO inspections (
                            inspection_id, timestamp, frame_id, decision,
                            primary_defect, confidence, uncertainty,
                            quality_gate_passed, total_latency_ms, image_path, metadata_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record.inspection_id,
                        record.timestamp,
                        record.frame_id,
                        record.decision,
                        record.primary_defect,
                        record.confidence,
                        record.uncertainty,
                        1 if record.quality_gate_passed else 0,
                        record.total_latency_ms,
                        record.image_path,
                        record.metadata_json,
                    ))
                    conn.commit()
            except Exception as e:
                logger.error(f"Failed to insert record into SQLite: {str(e)}")

        return record

    def get_recent_inspections(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Queries recent inspection records for UI or MES."""
        if not self.db_available:
            return []

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT inspection_id, timestamp, frame_id, decision,
                           primary_defect, confidence, uncertainty,
                           quality_gate_passed, total_latency_ms, image_path
                    FROM inspections
                    ORDER BY timestamp DESC LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []
