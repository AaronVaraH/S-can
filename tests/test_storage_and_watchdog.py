"""Unit tests for SQLite storage manager and watchdog health evaluation."""

from pathlib import Path
import numpy as np
import pytest

from edge_inspector.decision import DecisionResult, InspectionDecision
from edge_inspector.quality import QualityCheckResult
from edge_inspector.storage import StorageManager
from edge_inspector.watchdog import EdgeWatchdog


def test_storage_manager_lifecycle(tmp_path):
    db_file = tmp_path / "test_insp.db"
    img_dir = tmp_path / "images"

    storage = StorageManager(
        db_path=str(db_file),
        image_dir=str(img_dir),
        save_annotated_images=True,
        save_fail_images=True,
    )
    assert storage.db_available is True

    raw_img = np.full((100, 100, 3), 150, dtype=np.uint8)
    q = QualityCheckResult(is_valid=True, passed_quality_gate=True)
    d = DecisionResult(
        decision=InspectionDecision.FAIL,
        primary_reason="DENT_DETECTED",
        confidence_score=0.85,
        uncertainty_score=0.0,
        actuate_reject=True,
    )

    record = storage.save_inspection(
        frame_id=1,
        raw_image=raw_img,
        quality=q,
        inference=None,
        decision=d,
        total_latency_ms=25.0,
    )

    assert record.inspection_id != ""
    assert record.decision == "FAIL"

    recent = storage.get_recent_inspections(limit=10)
    assert len(recent) == 1
    assert recent[0]["decision"] == "FAIL"


def test_watchdog_evaluate_health():
    # Set high threshold so local dev machine RAM usage doesn't trigger alerts during unit test
    wd = EdgeWatchdog(max_ram_percent=99.0)
    wd.register_callbacks(
        camera_cb=lambda: True,
        model_cb=lambda: True,
        storage_cb=lambda: True,
    )

    health = wd.evaluate_health()
    assert health.state == "OPERATIONAL"
    assert health.camera_connected is True
    assert health.model_loaded is True
    assert health.storage_healthy is True
