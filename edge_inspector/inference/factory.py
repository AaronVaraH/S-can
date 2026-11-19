"""Factory for creating and validating edge inference engines."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from edge_inspector.inference.base import BaseInferenceEngine, ModelManifest
from edge_inspector.inference.onnx_engine import ONNXInferenceEngine
from edge_inspector.inference.simulation_engine import SimulationInferenceEngine
from edge_inspector.inference.tflite_engine import TFLiteInferenceEngine


def create_inference_engine(
    backend: str,
    manifest: Optional[ModelManifest] = None,
    options: Optional[Dict[str, Any]] = None,
) -> BaseInferenceEngine:
    """Instantiates and configures the requested edge inference engine."""
    opts = options or {}
    b = backend.lower()

    if b == "onnx":
        return ONNXInferenceEngine(
            manifest=manifest,
            intra_threads=opts.get("intra_threads", 4),
            inter_threads=opts.get("inter_threads", 1),
            execution_provider=opts.get("execution_provider", "CPUExecutionProvider"),
        )
    elif b == "tflite":
        return TFLiteInferenceEngine(
            manifest=manifest,
            num_threads=opts.get("intra_threads", 4),
        )
    elif b in ("simulation", "sim"):
        return SimulationInferenceEngine(
            manifest=manifest,
            simulated_latency_ms=opts.get("simulated_latency_ms", 45.0),
        )
    else:
        # Default fallback to simulation
        return SimulationInferenceEngine(manifest=manifest)
