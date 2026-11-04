"""ONNX Runtime edge inference engine with ARM CPU thread tuning."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from edge_inspector.inference.base import (
    BaseInferenceEngine,
    DefectPrediction,
    InferenceResult,
    ModelManifest,
    compute_file_sha256,
)
from edge_inspector.quality import unletterbox_bbox

# Optional import of onnxruntime
_ORT_AVAILABLE = False
try:
    import onnxruntime as ort  # type: ignore
    _ORT_AVAILABLE = True
except ImportError:
    ort = None  # type: ignore


class ONNXInferenceEngine(BaseInferenceEngine):
    """Production ONNX Runtime engine optimized for edge CPU inference."""

    def __init__(
        self,
        manifest: Optional[ModelManifest] = None,
        intra_threads: int = 4,
        inter_threads: int = 1,
        execution_provider: str = "CPUExecutionProvider",
    ) -> None:
        super().__init__(manifest)
        self.intra_threads = intra_threads
        self.inter_threads = inter_threads
        self.execution_provider = execution_provider
        self.session: Optional[Any] = None
        self.input_name: Optional[str] = None
        self.output_names: List[str] = []

    def load_model(self, model_path: str, manifest: Optional[ModelManifest] = None) -> bool:
        if not _ORT_AVAILABLE:
            raise RuntimeError("onnxruntime is not installed. CPU inference cannot proceed.")

        p = Path(model_path)
        if not p.exists():
            raise FileNotFoundError(f"Model file not found at: {model_path}")

        if manifest:
            self.manifest = manifest
            # Checksum verification for safety
            actual_hash = compute_file_sha256(str(p))
            if manifest.checksum_sha256 and actual_hash != manifest.checksum_sha256:
                raise ValueError(
                    f"Model checksum mismatch! Expected {manifest.checksum_sha256}, got {actual_hash}. "
                    "Refusing to execute unverified artifact."
                )

        opts = ort.SessionOptions()
        opts.intra_op_num_threads = max(1, self.intra_threads)
        opts.inter_op_num_threads = max(1, self.inter_threads)
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        # Verify available providers
        available_providers = ort.get_available_providers()
        selected_providers = []
        if self.execution_provider in available_providers:
            selected_providers.append(self.execution_provider)
        if "CPUExecutionProvider" not in selected_providers:
            selected_providers.append("CPUExecutionProvider")

        self.session = ort.InferenceSession(str(p), sess_options=opts, providers=selected_providers)
        self.model_path = str(p)

        inputs = self.session.get_inputs()
        outputs = self.session.get_outputs()
        self.input_name = inputs[0].name
        self.output_names = [o.name for o in outputs]
        self.is_loaded = True
        return True

    def infer(
        self,
        tensor: np.ndarray,
        transform_meta: Dict[str, Any],
    ) -> InferenceResult:
        if not self.is_loaded or self.session is None or self.input_name is None:
            raise RuntimeError("Inference called before model was successfully loaded.")

        t0 = time.perf_counter_ns()
        # Execute ONNX session
        raw_outputs = self.session.run(self.output_names, {self.input_name: tensor})
        t1 = time.perf_counter_ns()
        latency_ms = (t1 - t0) / 1_000_000.0

        predictions: List[DefectPrediction] = []
        primary_output = raw_outputs[0]

        classes = self.manifest.classes if self.manifest else [
            "dent", "scratch", "rim_dent", "pinhole", "contamination", "corrosion", "seam_defect", "ovalization"
        ]

        # Case 1: Detector output shaped (1, N, 6) -> (x1, y1, x2, y2, score, class_id)
        if len(primary_output.shape) == 3 and primary_output.shape[2] >= 6:
            boxes_data = primary_output[0]
            for det in boxes_data:
                score = float(det[4])
                if score < 0.20:
                    continue
                class_id = int(det[5])
                label = classes[class_id] if class_id < len(classes) else f"defect_{class_id}"

                box_letterbox = (float(det[0]), float(det[1]), float(det[2]), float(det[3]))
                orig_bbox = unletterbox_bbox(box_letterbox, transform_meta)
                area = (orig_bbox[2] - orig_bbox[0]) * (orig_bbox[3] - orig_bbox[1])

                severity = "CRITICAL" if label in ("pinhole", "seam_defect") else ("MAJOR" if score > 0.65 else "MINOR")

                predictions.append(
                    DefectPrediction(
                        label=label,
                        confidence=round(score, 3),
                        bbox=orig_bbox,
                        area_pixels=area,
                        severity=severity,
                    )
                )

        # Case 2: Multi-class logits or probabilities shaped (1, num_classes)
        elif len(primary_output.shape) == 2:
            scores = primary_output[0]
            # Softmax or sigmoid
            exp_scores = np.exp(scores - np.max(scores))
            probs = exp_scores / np.sum(exp_scores) if np.sum(exp_scores) > 0 else scores

            for idx, prob in enumerate(probs):
                score = float(prob)
                label = classes[idx] if idx < len(classes) else f"class_{idx}"
                if label.lower() == "clean" or score < 0.20:
                    continue

                severity = "CRITICAL" if label in ("pinhole", "seam_defect") else ("MAJOR" if score > 0.60 else "MINOR")
                # Default box in center of can if model is classifier rather than detector
                orig_w = transform_meta.get("orig_width", 640)
                orig_h = transform_meta.get("orig_height", 480)
                dummy_box = (int(orig_w * 0.25), int(orig_h * 0.25), int(orig_w * 0.75), int(orig_h * 0.75))

                predictions.append(
                    DefectPrediction(
                        label=label,
                        confidence=round(score, 3),
                        bbox=dummy_box,
                        area_pixels=(dummy_box[2] - dummy_box[0]) * (dummy_box[3] - dummy_box[1]),
                        severity=severity,
                    )
                )

        predictions.sort(key=lambda p: p.confidence, reverse=True)
        max_conf = predictions[0].confidence if predictions else 0.0
        primary_defect = predictions[0].label if predictions else None

        return InferenceResult(
            predictions=predictions,
            inference_latency_ms=round(latency_ms, 2),
            model_id=self.manifest.model_id if self.manifest else "onnx_model",
            model_version=self.manifest.version if self.manifest else "1.0",
            backend="ONNXRuntime",
            is_defect_detected=len(predictions) > 0,
            max_defect_confidence=max_conf,
            primary_defect=primary_defect,
            raw_output_shape=list(primary_output.shape),
        )

    def get_runtime_info(self) -> Dict[str, Any]:
        return {
            "backend": "ONNXRuntime",
            "version": getattr(ort, "__version__", "unknown") if _ORT_AVAILABLE else None,
            "is_loaded": self.is_loaded,
            "model_path": self.model_path,
            "intra_threads": self.intra_threads,
            "inter_threads": self.inter_threads,
            "execution_provider": self.execution_provider,
            "active_providers": self.session.get_providers() if self.session else [],
        }
