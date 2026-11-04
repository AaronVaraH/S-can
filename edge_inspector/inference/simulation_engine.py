"""High-fidelity simulation inference engine for testing, development, and fallback."""

from __future__ import annotations

import random
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from edge_inspector.inference.base import (
    BaseInferenceEngine,
    DefectPrediction,
    InferenceResult,
    ModelManifest,
)


class SimulationInferenceEngine(BaseInferenceEngine):
    """Simulates edge vision inference with realistic latency and heuristic feature inspection."""

    def __init__(
        self,
        manifest: Optional[ModelManifest] = None,
        simulated_latency_ms: float = 45.0,
    ) -> None:
        super().__init__(manifest)
        self.simulated_latency_ms = simulated_latency_ms
        self.is_loaded = True
        self.model_path = "simulated_model.onnx"

    def load_model(self, model_path: str, manifest: Optional[ModelManifest] = None) -> bool:
        if manifest:
            self.manifest = manifest
        self.model_path = model_path
        self.is_loaded = True
        return True

    def infer(
        self,
        tensor: np.ndarray,
        transform_meta: Dict[str, Any],
    ) -> InferenceResult:
        t0 = time.perf_counter_ns()

        # Simulate edge execution delay with realistic jitter
        jitter_s = random.uniform(0.002, 0.008)
        time.sleep((self.simulated_latency_ms / 1000.0) + jitter_s)

        t1 = time.perf_counter_ns()
        latency_ms = (t1 - t0) / 1_000_000.0

        orig_w = transform_meta.get("orig_width", 640)
        orig_h = transform_meta.get("orig_height", 480)

        # Inspect tensor gradients to determine if image contains anomalous dark/dented regions
        # Tensor is (1, 3, H, W)
        std_val = float(np.std(tensor))
        min_val = float(np.min(tensor))

        predictions: List[DefectPrediction] = []

        # Heuristic: High variance or sharp contrast indicates a defect on the can surface
        if std_val > 1.2 or min_val < -1.8:
            # Detect simulated dent or seam defect
            x1 = int(orig_w * 0.35)
            y1 = int(orig_h * 0.30)
            x2 = int(orig_w * 0.65)
            y2 = int(orig_h * 0.55)
            area = (x2 - x1) * (y2 - y1)

            predictions.append(
                DefectPrediction(
                    label="dent",
                    confidence=0.88,
                    bbox=(x1, y1, x2, y2),
                    area_pixels=area,
                    severity="MAJOR",
                )
            )
        elif std_val > 0.85:
            # Minor surface scratch
            x1 = int(orig_w * 0.40)
            y1 = int(orig_h * 0.20)
            x2 = int(orig_w * 0.55)
            y2 = int(orig_h * 0.35)
            predictions.append(
                DefectPrediction(
                    label="scratch",
                    confidence=0.62,
                    bbox=(x1, y1, x2, y2),
                    area_pixels=(x2 - x1) * (y2 - y1),
                    severity="MINOR",
                )
            )

        predictions.sort(key=lambda p: p.confidence, reverse=True)
        max_conf = predictions[0].confidence if predictions else 0.0
        primary_defect = predictions[0].label if predictions else None

        return InferenceResult(
            predictions=predictions,
            inference_latency_ms=round(latency_ms, 2),
            model_id=self.manifest.model_id if self.manifest else "simulated_can_detector",
            model_version=self.manifest.version if self.manifest else "1.0.0",
            backend="SimulationEngine",
            is_defect_detected=len(predictions) > 0,
            max_defect_confidence=max_conf,
            primary_defect=primary_defect,
            raw_output_shape=[1, 8],
        )

    def get_runtime_info(self) -> Dict[str, Any]:
        return {
            "backend": "SimulationEngine",
            "is_loaded": True,
            "simulated_latency_ms": self.simulated_latency_ms,
        }
