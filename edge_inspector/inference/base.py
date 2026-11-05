"""Inference base contracts, defect predictions, and model manifest specifications."""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class DefectPrediction:
    """Localized defect prediction with physical bounding box and severity."""
    label: str
    confidence: float
    bbox: Optional[Tuple[int, int, int, int]] = None  # (x1, y1, x2, y2) in original pixels
    area_pixels: int = 0
    severity: str = "MAJOR"  # "CRITICAL", "MAJOR", "MINOR", "NEGLIGIBLE"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InferenceResult:
    """Consolidated inference engine output."""
    predictions: List[DefectPrediction]
    inference_latency_ms: float
    model_id: str
    model_version: str
    backend: str
    is_defect_detected: bool = False
    max_defect_confidence: float = 0.0
    primary_defect: Optional[str] = None
    raw_output_shape: Optional[List[int]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "predictions": [p.to_dict() for p in self.predictions],
            "inference_latency_ms": self.inference_latency_ms,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "backend": self.backend,
            "is_defect_detected": self.is_defect_detected,
            "max_defect_confidence": self.max_defect_confidence,
            "primary_defect": self.primary_defect,
            "raw_output_shape": self.raw_output_shape,
        }


@dataclass
class ModelManifest:
    """Comprehensive manifest recording model provenance, shapes, labels, and parameters."""
    model_id: str
    version: str
    architecture: str
    runtime: str
    input_shape: List[int]  # e.g. [1, 3, 320, 320]
    classes: List[str]      # e.g. ["dent", "scratch", "seam_defect", ...]
    preprocessing: Dict[str, Any]
    thresholds: Dict[str, float]
    checksum_sha256: str
    quantization: str = "FP32"  # "FP32", "FP16", "INT8"
    target_hardware: str = "generic_edge"
    benchmarked_latency_ms: Optional[float] = None
    benchmarked_val_acc: Optional[float] = None
    created_at: str = "2026-10-21T00:00:00Z"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_file(cls, path: str) -> ModelManifest:
        p = Path(path)
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        import dataclasses
        valid_fields = {f.name for f in dataclasses.fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    def save(self, path: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)


def compute_file_sha256(path: str) -> str:
    """Computes SHA-256 checksum for model integrity verification."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class BaseInferenceEngine(ABC):
    """Abstract edge inference engine."""

    def __init__(self, manifest: Optional[ModelManifest] = None) -> None:
        self.manifest = manifest
        self.is_loaded: bool = False
        self.model_path: Optional[str] = None

    @abstractmethod
    def load_model(self, model_path: str, manifest: Optional[ModelManifest] = None) -> bool:
        """Loads and prepares the model for inference."""
        pass

    @abstractmethod
    def infer(
        self,
        tensor: np.ndarray,
        transform_meta: Dict[str, Any],
    ) -> InferenceResult:
        """Executes forward pass and returns localized predictions."""
        pass

    @abstractmethod
    def get_runtime_info(self) -> Dict[str, Any]:
        """Returns details on runtime provider, threads, and memory."""
        pass
