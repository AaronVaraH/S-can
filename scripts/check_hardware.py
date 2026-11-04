"""Hardware detection and edge compatibility verification utility."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from edge_inspector.hardware import (
    detect_hardware,
    estimate_hardware_capacity,
    verify_runtime_compatibility,
)


def print_banner(text: str) -> None:
    print("\n" + "=" * 65)
    print(f" {text}")
    print("=" * 65)


def run_checks() -> None:
    print_banner("RASPBERRY PI EDGE HARDWARE DETECTION & COMPATIBILITY CHECK")

    hw = detect_hardware()
    print(f"  Target Device       : {hw.rpi_model}")
    print(f"  Is Raspberry Pi     : {hw.is_raspberry_pi}")
    if hw.rpi_revision:
        print(f"  Board Revision Code : {hw.rpi_revision}")
    print(f"  CPU Architecture    : {hw.cpu_architecture} ({'64-bit' if hw.is_64bit else '32-bit'})")
    print(f"  Logical CPU Cores   : {hw.cpu_cores}")
    if hw.cpu_freq_mhz:
        print(f"  Current CPU Freq    : {hw.cpu_freq_mhz:.1f} MHz")
    print(f"  ARM NEON Supported  : {'YES (Vectorized math enabled)' if hw.arm_neon_supported else 'NO'}")
    print(f"  Total System RAM    : {hw.total_ram_mb} MB")
    print(f"  Available RAM       : {hw.available_ram_mb} MB")
    print(f"  Operating System    : {hw.os_name} {hw.os_release}")

    # CUDA Verification
    print(f"\n  CUDA Available      : {'YES' if hw.cuda_available else 'NO (Standard edge CPU execution)'}")
    if hw.is_raspberry_pi and hw.cuda_available:
        print("  [WARNING] CUDA flagged on Raspberry Pi. Verifying non-CUDA fallback.")

    # AI Accelerators
    print_banner("AI ACCELERATORS & HAT+ DISCOVERY")
    if hw.accelerators_found:
        for acc in hw.accelerators_found:
            print(f"  [FOUND] Accelerator device: {acc}")
    else:
        print("  [INFO] No discrete hardware accelerator detected. Using optimized ARM CPU NEON fallback.")

    # Thermal & Throttling
    print_banner("THERMAL & VOLTAGE STATUS")
    temp_display = f"{hw.cpu_temperature_c} °C" if hw.cpu_temperature_c is not None else "Not available on current OS"
    print(f"  CPU Temperature     : {temp_display}")
    print(f"  Throttling Active   : {hw.throttling_status.get('is_throttled', False)}")
    print(f"  Undervoltage Flag   : {hw.throttling_status.get('undervoltage_detected', False)}")
    print(f"  Frequency Capped    : {hw.throttling_status.get('arm_frequency_capped', False)}")

    # Runtime Compatibility
    print_banner("INFERENCE RUNTIME COMPATIBILITY")
    for rt in ["onnx", "tflite", "hailo", "simulation", "cuda"]:
        compatible, msg = verify_runtime_compatibility(rt, hw)
        status_tag = "[COMPATIBLE]  " if compatible else "[UNSUPPORTED] "
        print(f"  {status_tag} {rt.upper():10s} : {msg}")

    # Capacity Estimation
    print_banner("RESOURCE ALLOCATION & LATENCY ESTIMATION")
    cap = estimate_hardware_capacity(hw, model_ram_mb=65.0, input_shape=(3, 320, 320), max_fps_required=15.0)
    print(f"  Hardware Profile       : {cap['hardware_profile']}")
    print(f"  Model Memory Estimate  : {cap['model_ram_mb']} MB")
    print(f"  Buffer Pipeline Memory : {cap['pipeline_buffer_mb']} MB")
    print(f"  Est. Total Working RAM : {cap['estimated_working_ram_mb']} MB")
    print(f"  RAM Headroom           : {cap['ram_headroom_mb']} MB")
    print(f"  Memory Feasible        : {'YES' if cap['is_memory_sufficient'] else 'NO - RISK OF OOM'}")
    print(f"  Est. Inference Latency : ~{cap['estimated_latency_ms']} ms")
    print(f"  Est. Sustained FPS     : ~{cap['estimated_sustained_fps']} FPS (Target: {cap['target_fps']} FPS)")
    print(f"  Recommended Threads    : {cap['recommended_intra_threads']} intra-op threads")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_checks()
