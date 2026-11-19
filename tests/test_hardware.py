"""Unit tests for edge hardware detection and resource feasibility estimation."""

import pytest
from edge_inspector.hardware import (
    detect_hardware,
    estimate_hardware_capacity,
    verify_runtime_compatibility,
)


def test_detect_hardware_structure():
    hw = detect_hardware()
    assert hw.cpu_cores >= 1
    assert hw.total_ram_mb > 100
    assert hw.available_ram_mb > 0
    assert hw.os_name != ""
    assert isinstance(hw.accelerators_found, list)
    assert isinstance(hw.throttling_status, dict)
    # CUDA must never be assumed true on Raspberry Pi
    if hw.is_raspberry_pi:
        assert hw.cuda_available is False


def test_estimate_hardware_capacity():
    hw = detect_hardware()
    cap = estimate_hardware_capacity(hw, model_ram_mb=65.0, input_shape=(3, 320, 320), max_fps_required=10.0)
    assert "available_ram_mb" in cap
    assert "model_ram_mb" in cap
    assert "estimated_latency_ms" in cap
    assert "estimated_sustained_fps" in cap
    assert cap["recommended_intra_threads"] >= 1


def test_verify_runtime_compatibility():
    hw = detect_hardware()
    # Simulation is always compatible
    ok, msg = verify_runtime_compatibility("simulation", hw)
    assert ok is True

    # ONNX runtime compatibility
    ok_onnx, _ = verify_runtime_compatibility("onnx", hw)
    assert ok_onnx is True
