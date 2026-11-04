"""Unit tests for inference engines, checksums, and manifests."""

from pathlib import Path
import numpy as np
import pytest

from edge_inspector.inference.base import ModelManifest, compute_file_sha256
from edge_inspector.inference.onnx_engine import ONNXInferenceEngine
from edge_inspector.inference.simulation_engine import SimulationInferenceEngine


def test_simulation_engine_inference():
    engine = SimulationInferenceEngine(simulated_latency_ms=10.0)
    dummy_tensor = np.zeros((1, 3, 320, 320), dtype=np.float32)
    meta = {"orig_width": 640, "orig_height": 480}

    res = engine.infer(dummy_tensor, meta)
    assert res.backend == "SimulationEngine"
    assert res.inference_latency_ms > 0.0
    assert isinstance(res.predictions, list)


def test_onnx_engine_with_active_model():
    model_path = Path("models/active/can_detector.onnx")
    manifest_path = Path("models/active/manifest.json")

    if not model_path.exists() or not manifest_path.exists():
        pytest.skip("Active ONNX model not generated.")

    manifest = ModelManifest.from_file(str(manifest_path))
    engine = ONNXInferenceEngine(manifest=manifest, intra_threads=2)
    loaded = engine.load_model(str(model_path), manifest=manifest)
    assert loaded is True
    assert engine.is_loaded is True

    dummy_tensor = np.zeros((1, 3, 320, 320), dtype=np.float32)
    meta = {"orig_width": 640, "orig_height": 480}
    res = engine.infer(dummy_tensor, meta)

    assert res.backend == "ONNXRuntime"
    assert res.inference_latency_ms > 0.0
    assert res.raw_output_shape is not None


def test_checksum_mismatch_fails_safely():
    model_path = Path("models/active/can_detector.onnx")
    manifest_path = Path("models/active/manifest.json")

    if not model_path.exists() or not manifest_path.exists():
        pytest.skip("Active ONNX model not generated.")

    manifest = ModelManifest.from_file(str(manifest_path))
    # Deliberately tamper with manifest checksum
    manifest.checksum_sha256 = "0000000000000000000000000000000000000000000000000000000000000000"

    engine = ONNXInferenceEngine(manifest=manifest)
    with pytest.raises(ValueError, match="Model checksum mismatch"):
        engine.load_model(str(model_path), manifest=manifest)
