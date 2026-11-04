"""Integration tests for edge REST API endpoints."""

import io
from pathlib import Path
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from edge_inspector.actuator import SimulationRejectActuator
from edge_inspector.actuator import ActuatorConfig
from edge_inspector.api import create_app
from edge_inspector.camera.synthetic_camera import SyntheticCameraAdapter
from edge_inspector.camera.base import AcquisitionConfig
from edge_inspector.inference.simulation_engine import SimulationInferenceEngine
from edge_inspector.pipeline import InspectionPipeline
from edge_inspector.rag.assistant import InspectionDocumentationAssistant
from edge_inspector.storage import StorageManager
from edge_inspector.watchdog import EdgeWatchdog


@pytest.fixture
def client(tmp_path):
    cam = SyntheticCameraAdapter(AcquisitionConfig(width=320, height=240))
    cam.connect()
    engine = SimulationInferenceEngine(simulated_latency_ms=5.0)
    actuator = SimulationRejectActuator(ActuatorConfig())
    storage = StorageManager(
        db_path=str(tmp_path / "test.db"),
        image_dir=str(tmp_path / "images"),
        save_annotated_images=False,
    )
    pipeline = InspectionPipeline(
        camera=cam,
        inference_engine=engine,
        actuator=actuator,
        storage=storage,
    )
    watchdog = EdgeWatchdog()
    watchdog.register_callbacks(
        camera_cb=lambda: cam.is_connected(),
        model_cb=lambda: engine.is_loaded,
        storage_cb=lambda: storage.db_available,
    )
    rag = InspectionDocumentationAssistant()

    app = create_app(pipeline, watchdog, rag)
    return TestClient(app)


def test_api_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "state" in data
    assert "cpu_usage_percent" in data


def test_api_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "pipeline" in data
    assert "system" in data


def test_api_hardware_endpoint(client):
    response = client.get("/hardware")
    assert response.status_code == 200
    data = response.json()
    assert "hardware" in data
    assert "capacity_estimate" in data


def test_api_camera_capture_endpoint(client):
    response = client.post("/camera/capture")
    assert response.status_code == 200
    data = response.json()
    assert "decision" in data
    assert "inspection_id" in data
    assert "total_latency_ms" in data


def test_api_inspect_upload_image(client):
    # Create simple in-memory JPEG
    img = np.full((320, 320, 3), 180, dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)

    files = {"file": ("test_can.jpg", io.BytesIO(buf.tobytes()), "image/jpeg")}
    response = client.post("/inspect", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "decision" in data
    assert "primary_reason" in data


def test_api_rag_query(client):
    response = client.post("/rag/query", json={"question": "What is seam overlap?", "top_k": 2})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert len(data["passages"]) > 0


def test_api_actuator_interlock(client):
    response = client.post("/actuator/interlock", json={"action": "ENGAGE", "reason": "TEST"})
    assert response.status_code == 200
    assert response.json()["interlock_active"] is True

    response_rel = client.post("/actuator/interlock", json={"action": "RELEASE"})
    assert response_rel.status_code == 200
    assert response_rel.json()["interlock_active"] is False
