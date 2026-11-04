"""Unit tests for camera adapters and acquisition recovery."""

import pytest
from edge_inspector.camera import AcquisitionConfig, create_camera_adapter
from edge_inspector.camera.synthetic_camera import SyntheticCameraAdapter


def test_synthetic_camera_capture():
    cfg = AcquisitionConfig(width=320, height=240, fps=30)
    cam = SyntheticCameraAdapter(cfg)
    assert cam.connect() is True
    assert cam.is_connected() is True

    frame, meta = cam.capture_frame()
    assert frame is not None
    assert frame.shape == (240, 320, 3)
    assert meta is not None
    assert meta.frame_id == 1
    assert meta.is_simulated is True
    assert meta.acquisition_latency_ms >= 0.0

    cam.disconnect()
    assert cam.is_connected() is False


def test_camera_factory():
    cam_sim = create_camera_adapter({"adapter": "synthetic", "width": 640, "height": 480})
    assert isinstance(cam_sim, SyntheticCameraAdapter)
