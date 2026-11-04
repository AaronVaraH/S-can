"""Comprehensive Raspberry Pi edge benchmark and industrial acceptance testing utility."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import psutil

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from edge_inspector.actuator import SimulationRejectActuator
from edge_inspector.camera.synthetic_camera import SyntheticCameraAdapter
from edge_inspector.decision import evaluate_inspection
from edge_inspector.hardware import (
    detect_hardware,
    get_cpu_temperature,
    get_throttling_status,
)
from edge_inspector.inference.base import ModelManifest
from edge_inspector.inference.onnx_engine import ONNXInferenceEngine
from edge_inspector.quality import letterbox_preprocess, validate_image_quality
from edge_inspector.storage import StorageManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def count_onnx_parameters(model_path: Path) -> int:
    """Calculates total trainable/weight parameters in an ONNX model."""
    try:
        import onnx
        from onnx import numpy_helper
        model = onnx.load(str(model_path))
        total_params = 0
        for initializer in model.graph.initializer:
            w_arr = numpy_helper.to_array(initializer)
            total_params += int(w_arr.size)
        return total_params
    except Exception:
        return 0


def run_edge_benchmark(
    model_path: str = "models/active/can_detector.onnx",
    manifest_path: str = "models/active/manifest.json",
    iterations: int = 50,
    target_fps: float = 15.0,
    target_latency_ms: float = 75.0,
    output_json: Optional[str] = "data/benchmark_results.json",
) -> Dict[str, Any]:
    print("\n" + "=" * 70)
    print(" RASPBERRY PI EDGE-AI BENCHMARK & HARDWARE ACCEPTANCE TEST")
    print("=" * 70)

    # 1. Hardware and Environment Inspection
    hw = detect_hardware()
    initial_temp = get_cpu_temperature()
    initial_throttling = get_throttling_status()

    print(f"  Target Hardware     : {hw.rpi_model} ({hw.cpu_architecture})")
    print(f"  CPU Cores / Clock   : {hw.cpu_cores} cores @ {hw.cpu_freq_mhz or 'N/A'} MHz")
    print(f"  ARM NEON Supported  : {hw.arm_neon_supported}")
    print(f"  Available Memory    : {hw.available_ram_mb:.1f} MB (Total: {hw.total_ram_mb:.1f} MB)")
    print(f"  OS / Kernel         : {hw.os_name} {hw.os_release} ({'64-bit' if hw.is_64bit else '32-bit'})")
    print(f"  Initial Temperature : {initial_temp or 'N/A'} °C")
    print(f"  Initial Throttling  : {initial_throttling.get('is_throttled', False)}")

    # 2. Model Architecture and Manifest
    m_path = Path(model_path)
    if not m_path.exists():
        print(f"ERROR: Model file not found at {m_path}")
        sys.exit(1)

    file_size_mb = m_path.stat().st_size / (1024 * 1024)
    param_count = count_onnx_parameters(m_path)

    manifest = None
    if Path(manifest_path).exists():
        manifest = ModelManifest.from_file(manifest_path)
        arch_name = manifest.architecture
        input_shape = manifest.input_shape
        classes = manifest.classes
    else:
        arch_name = "Generic-ONNX-Model"
        input_shape = [1, 3, 320, 320]
        classes = ["dent", "scratch", "pinhole", "seam_defect"]

    print("\n" + "-" * 70)
    print(" MODEL SPECIFICATIONS")
    print("-" * 70)
    print(f"  Model File          : {m_path.name} ({file_size_mb:.2f} MB)")
    print(f"  Architecture        : {arch_name}")
    print(f"  Total Parameters    : {param_count:,}")
    print(f"  Input Dimensions    : {input_shape}")
    print(f"  Classes ({len(classes)})       : {', '.join(classes[:5])}...")

    # 3. Initialize Components
    from edge_inspector.camera.base import AcquisitionConfig
    cam = SyntheticCameraAdapter(AcquisitionConfig(width=640, height=480))
    cam.connect()

    engine = ONNXInferenceEngine(manifest=manifest, intra_threads=min(hw.cpu_cores, 4))

    # 4. Cold-Start Latency
    print("\n" + "-" * 70)
    print(" EXECUTING BENCHMARK RUNS")
    print("-" * 70)

    process = psutil.Process()
    ram_before_mb = process.memory_info().rss / (1024 * 1024)

    t_cold_load_0 = time.perf_counter_ns()
    engine.load_model(str(m_path), manifest=manifest)
    t_cold_load_1 = time.perf_counter_ns()
    model_load_latency_ms = (t_cold_load_1 - t_cold_load_0) / 1_000_000.0

    dummy_tensor = np.zeros(tuple(input_shape), dtype=np.float32)
    meta = {"orig_width": 640, "orig_height": 480}

    t_cold_inf_0 = time.perf_counter_ns()
    _ = engine.infer(dummy_tensor, meta)
    t_cold_inf_1 = time.perf_counter_ns()
    cold_inference_latency_ms = (t_cold_inf_1 - t_cold_inf_0) / 1_000_000.0

    print(f"  Model Load Latency  : {model_load_latency_ms:.2f} ms")
    print(f"  Cold-Start Inference: {cold_inference_latency_ms:.2f} ms")

    # 5. Warm-up Iterations
    for _ in range(5):
        _ = engine.infer(dummy_tensor, meta)

    # 6. Sustained Inference & End-to-End Pipeline Latency
    inference_latencies: List[float] = []
    end_to_end_latencies: List[float] = []
    cpu_percent_samples: List[float] = []

    # Storage and Actuator for pipeline test
    storage = StorageManager(save_annotated_images=False)
    actuator = SimulationRejectActuator(ActuatorConfig())

    print(f"  Running {iterations} warm iterations...")
    benchmark_start_time = time.perf_counter()

    for i in range(iterations):
        # Capture frame
        frame, frame_meta = cam.capture_frame()

        t_e2e_0 = time.perf_counter_ns()

        # Step 1: Quality Gate
        q_res = validate_image_quality(frame)

        # Step 2: Preprocess
        tensor, t_meta = letterbox_preprocess(frame, (input_shape[2], input_shape[3]))

        # Step 3: Forward Inference
        t_inf_0 = time.perf_counter_ns()
        inf_res = engine.infer(tensor, t_meta)
        t_inf_1 = time.perf_counter_ns()
        inf_ms = (t_inf_1 - t_inf_0) / 1_000_000.0
        inference_latencies.append(inf_ms)

        # Step 4: Decision
        dec_res = evaluate_inspection(q_res, inf_res)

        # Step 5: Actuator
        _ = actuator.trigger_reject(dec_res, frame_meta.timestamp_ns if frame_meta else t_e2e_0)

        t_e2e_1 = time.perf_counter_ns()
        e2e_ms = (t_e2e_1 - t_e2e_0) / 1_000_000.0
        end_to_end_latencies.append(e2e_ms)

        if (i + 1) % 10 == 0:
            cpu_percent_samples.append(psutil.cpu_percent(interval=None))

    benchmark_duration_s = time.perf_counter() - benchmark_start_time
    cam.disconnect()

    ram_after_mb = process.memory_info().rss / (1024 * 1024)
    peak_rss_mb = ram_after_mb
    final_temp = get_cpu_temperature()
    final_throttling = get_throttling_status()

    # 7. Statistics Computation
    inf_median = float(np.median(inference_latencies))
    inf_mean = float(np.mean(inference_latencies))
    inf_min = float(np.min(inference_latencies))
    inf_p95 = float(np.percentile(inference_latencies, 95))
    inf_p99 = float(np.percentile(inference_latencies, 99))

    e2e_median = float(np.median(end_to_end_latencies))
    e2e_p95 = float(np.percentile(end_to_end_latencies, 95))

    sustained_fps = round(iterations / benchmark_duration_s, 1)
    avg_cpu_util = float(np.mean(cpu_percent_samples)) if cpu_percent_samples else psutil.cpu_percent()

    meets_fps_slo = sustained_fps >= target_fps
    meets_latency_slo = inf_p95 <= target_latency_ms

    print("\n" + "=" * 70)
    print(" BENCHMARK ACCEPTANCE TEST RESULTS")
    print("=" * 70)
    print(f"  Warm Inferences     : {iterations} iterations")
    print(f"  Inference Min / Mean: {inf_min:.2f} ms / {inf_mean:.2f} ms")
    print(f"  Inference Median    : {inf_median:.2f} ms")
    print(f"  Inference P95 / P99 : {inf_p95:.2f} ms / {inf_p99:.2f} ms")
    print(f"  Total Pipeline (E2E): Median = {e2e_median:.2f} ms | P95 = {e2e_p95:.2f} ms")
    print(f"  Sustained Throughput: {sustained_fps} FPS (Target SLO: {target_fps} FPS) -> {'PASS' if meets_fps_slo else 'WARNING'}")
    print(f"  Peak RAM (RSS)      : {peak_rss_mb:.1f} MB (Delta: +{peak_rss_mb - ram_before_mb:.1f} MB)")
    print(f"  Mean CPU Utilization: {avg_cpu_util:.1f} %")
    if final_temp is not None:
        delta_temp = round(final_temp - (initial_temp or final_temp), 1)
        print(f"  Final Temperature   : {final_temp} °C (Delta: {'+' if delta_temp >= 0 else ''}{delta_temp} °C)")
    print(f"  Final Throttling    : {final_throttling.get('is_throttled', False)}")
    print(f"  SLO Target Latency  : {target_latency_ms} ms -> {'PASS' if meets_latency_slo else 'WARNING'}")
    print("=" * 70 + "\n")

    results_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hardware": hw.to_dict(),
        "model": {
            "name": m_path.name,
            "architecture": arch_name,
            "parameters": param_count,
            "size_mb": round(file_size_mb, 2),
            "input_shape": input_shape,
        },
        "latencies": {
            "model_load_ms": round(model_load_latency_ms, 2),
            "cold_start_ms": round(cold_inference_latency_ms, 2),
            "inference_min_ms": round(inf_min, 2),
            "inference_mean_ms": round(inf_mean, 2),
            "inference_median_ms": round(inf_median, 2),
            "inference_p95_ms": round(inf_p95, 2),
            "inference_p99_ms": round(inf_p99, 2),
            "camera_to_decision_median_ms": round(e2e_median, 2),
            "camera_to_decision_p95_ms": round(e2e_p95, 2),
        },
        "throughput": {
            "sustained_fps": sustained_fps,
            "target_fps": target_fps,
            "meets_slo": meets_fps_slo,
        },
        "resources": {
            "peak_rss_mb": round(peak_rss_mb, 1),
            "cpu_utilization_pct": round(avg_cpu_util, 1),
            "initial_temp_c": initial_temp,
            "final_temp_c": final_temp,
            "throttling": final_throttling,
        },
    }

    if output_json:
        p_out = Path(output_json)
        p_out.parent.mkdir(parents=True, exist_ok=True)
        with open(p_out, "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2)
        print(f"Benchmark artifact saved to: {p_out.resolve()}")

    return results_data


if __name__ == "__main__":
    from edge_inspector.actuator import ActuatorConfig

    parser = argparse.ArgumentParser(description="Edge AI Benchmark and SLO Acceptance Test")
    parser.add_argument("--model", default="models/active/can_detector.onnx", help="Path to ONNX model")
    parser.add_argument("--manifest", default="models/active/manifest.json", help="Path to manifest")
    parser.add_argument("--iterations", type=int, default=50, help="Number of benchmark iterations")
    parser.add_argument("--target-fps", type=float, default=15.0, help="Target FPS SLO")
    parser.add_argument("--target-latency-ms", type=float, default=75.0, help="Target P95 latency SLO")
    parser.add_argument("--output", default="data/benchmark_results.json", help="Output JSON path")
    args = parser.parse_args()

    run_edge_benchmark(
        model_path=args.model,
        manifest_path=args.manifest,
        iterations=args.iterations,
        target_fps=args.target_fps,
        target_latency_ms=args.target_latency_ms,
        output_json=args.output,
    )
