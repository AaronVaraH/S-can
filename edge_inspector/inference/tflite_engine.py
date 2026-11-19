"""TensorFlow Lite inference engine with CPU XNNPACK delegate support."""

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

_TFLITE_AVAILABLE = False
_INTERPRETER: Any = None

try:
    import tflite_runtime.interpreter as tflite  # type: ignore
    _INTERPRETER = tflite.Interpreter
    _TFLITE_AVAILABLE = True
except ImportError:
    try:
        import tensorflow.lite as tflite  # type: ignore
        _INTERPRETER = tflite.Interpreter
        _TFLITE_AVAILABLE = True
    except ImportError:
        pass


class TFLiteInferenceEngine(BaseInferenceEngine):
    """Production TFLite engine optimized for ARM Cortex CPUs."""

    def __init__(
        self,
        manifest: Optional[ModelManifest] = None,
        num_threads: int = 4,
    ) -> None:
        super().__init__(manifest)
        self.num_threads = num_threads
        self.interpreter: Optional[Any] = None
        self.input_details: Optional[List[Dict[str, Any]]] = None
        self.output_details: Optional[List[Dict[str, Any]]] = None

    def load_model(self, model_path: str, manifest: Optional[ModelManifest] = None) -> bool:
        if not _TFLITE_AVAILABLE or _INTERPRETER is None:
            raise RuntimeError("tflite_runtime or tensorflow is not installed.")

        p = Path(model_path)
        if not p.exists():
            raise FileNotFoundError(f"TFLite model not found: {model_path}")

        if manifest:
            self.manifest = manifest
            actual_hash = compute_file_sha256(str(p))
            if manifest.checksum_sha256 and actual_hash != manifest.checksum_sha256:
                raise ValueError("TFLite model SHA-256 verification failed.")

        self.interpreter = _INTERPRETER(model_path=str(p), num_threads=self.num_threads)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.model_path = str(p)
        self.is_loaded = True
        return True

    def infer(
        self,
        tensor: np.ndarray,
        transform_meta: Dict[str, Any],
    ) -> InferenceResult:
        if not self.is_loaded or self.interpreter is None or not self.input_details or not self.output_details:
            raise RuntimeError("TFLite engine called before model load.")

        # Match input tensor layout (NCHW vs NHWC)
        expected_shape = self.input_details[0]["shape"]
        if expected_shape[-1] == 3 and tensor.shape[1] == 3:
            # Transpose from NCHW to NHWC for TFLite standard layout
            feed_tensor = np.transpose(tensor, (0, 2, 3, 1))
        else:
            feed_tensor = tensor

        # Handle INT8 quantized input if needed
        input_dtype = self.input_details[0]["dtype"]
        if input_dtype == np.int8 or input_dtype == np.uint8:
            scale, zero_point = self.input_details[0].get("quantization", (1.0, 0))
            if scale > 0:
                feed_tensor = (feed_tensor / scale + zero_point).astype(input_dtype)

        t0 = time.perf_counter_ns()
        self.interpreter.set_tensor(self.input_details[0]["index"], feed_tensor)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]["index"])
        t1 = time.perf_counter_ns()
        latency_ms = (t1 - t0) / 1_000_000.0

        # Dequantize if output is INT8
        output_dtype = self.output_details[0]["dtype"]
        if output_dtype in (np.int8, np.uint8):
            out_scale, out_zero_point = self.output_details[0].get("quantization", (1.0, 0))
            if out_scale > 0:
                output_data = (output_data.astype(np.float32) - out_zero_point) * out_scale

        predictions: List[DefectPrediction] = []
        classes = self.manifest.classes if self.manifest else ["clean", "dent", "scratch", "seam_defect"]

        if len(output_data.shape) >= 2:
            scores = output_data[0]
            exp_scores = np.exp(scores - np.max(scores))
            probs = exp_scores / np.sum(exp_scores) if np.sum(exp_scores) > 0 else scores

            for idx, prob in enumerate(probs):
                score = float(prob)
                label = classes[idx] if idx < len(classes) else f"class_{idx}"
                if label.lower() == "clean" or score < 0.20:
                    continue

                orig_w = transform_meta.get("orig_width", 640)
                orig_h = transform_meta.get("orig_height", 480)
                dummy_box = (int(orig_w * 0.2), int(orig_h * 0.2), int(orig_w * 0.8), int(orig_h * 0.8))

                predictions.append(
                    DefectPrediction(
                        label=label,
                        confidence=round(score, 3),
                        bbox=dummy_box,
                        area_pixels=(dummy_box[2] - dummy_box[0]) * (dummy_box[3] - dummy_box[1]),
                        severity="CRITICAL" if label in ("pinhole", "seam_defect") else "MAJOR",
                    )
                )

        predictions.sort(key=lambda p: p.confidence, reverse=True)
        max_conf = predictions[0].confidence if predictions else 0.0

        return InferenceResult(
            predictions=predictions,
            inference_latency_ms=round(latency_ms, 2),
            model_id=self.manifest.model_id if self.manifest else "tflite_model",
            model_version=self.manifest.version if self.manifest else "1.0",
            backend="TFLite",
            is_defect_detected=len(predictions) > 0,
            max_defect_confidence=max_conf,
            primary_defect=predictions[0].label if predictions else None,
            raw_output_shape=list(output_data.shape),
        )

    def get_runtime_info(self) -> Dict[str, Any]:
        return {
            "backend": "TFLite",
            "is_loaded": self.is_loaded,
            "model_path": self.model_path,
            "num_threads": self.num_threads,
        }
