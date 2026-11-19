"""Deployment and verification script for new edge model artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from edge_inspector.inference.base import ModelManifest, compute_file_sha256
from edge_inspector.inference.onnx_engine import ONNXInferenceEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def deploy_model(
    staged_model_path: str,
    staged_manifest_path: str,
    base_dir: str = "models",
) -> bool:
    """Safely validates, stages, registers, and activates a new edge model artifact."""
    base = Path(base_dir)
    active_dir = base / "active"
    archive_dir = base / "archive"
    registry_file = base / "registry.json"

    model_src = Path(staged_model_path)
    manifest_src = Path(staged_manifest_path)

    if not model_src.exists():
        logger.error(f"Staged model not found: {model_src}")
        return False
    if not manifest_src.exists():
        logger.error(f"Staged manifest not found: {manifest_src}")
        return False

    # 1. Parse manifest
    try:
        manifest = ModelManifest.from_file(str(manifest_src))
        logger.info(f"Parsed manifest: Model ID '{manifest.model_id}', Version '{manifest.version}'")
    except Exception as e:
        logger.error(f"Corrupted or invalid manifest: {str(e)}")
        return False

    # 2. Checksum validation
    actual_hash = compute_file_sha256(str(model_src))
    if manifest.checksum_sha256 and actual_hash != manifest.checksum_sha256:
        logger.error(
            f"CHECKSUM VERIFICATION FAILED! Manifest: {manifest.checksum_sha256}, Actual: {actual_hash}. "
            "Aborting deployment to preserve line safety."
        )
        return False
    logger.info("SHA-256 checksum verified.")

    # 3. Smoke Test on device
    try:
        logger.info("Executing device smoke test...")
        engine = ONNXInferenceEngine(manifest=manifest)
        engine.load_model(str(model_src), manifest=manifest)
        dummy_tensor = np.zeros(tuple(manifest.input_shape), dtype=np.float32)
        res = engine.infer(dummy_tensor, {"orig_width": 640, "orig_height": 480})
        logger.info(f"Smoke test passed successfully. Latency: {res.inference_latency_ms} ms")
    except Exception as e:
        logger.error(f"Device verification failed: {str(e)}. Aborting deployment.")
        return False

    # 4. Archive current active model
    archive_dir.mkdir(parents=True, exist_ok=True)
    active_model = active_dir / "can_detector.onnx"
    active_manifest = active_dir / "manifest.json"

    if active_model.exists() and active_manifest.exists():
        try:
            curr_manifest = ModelManifest.from_file(str(active_manifest))
            curr_ver = curr_manifest.version
        except Exception:
            curr_ver = "unknown"

        ts = time.strftime("%Y%m%d_%H%M%S")
        arch_sub = archive_dir / f"{ts}_v{curr_ver}"
        arch_sub.mkdir(parents=True, exist_ok=True)

        shutil.copy2(active_model, arch_sub / "can_detector.onnx")
        active_model_data = active_dir / f"{active_model.name}.data"
        if active_model_data.exists():
            shutil.copy2(active_model_data, arch_sub / active_model_data.name)
        shutil.copy2(active_manifest, arch_sub / "manifest.json")
        logger.info(f"Archived previous version v{curr_ver} to: {arch_sub}")

    # 5. Copy new artifact to active
    active_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(model_src, active_dir / "can_detector.onnx")
    model_src_data = model_src.parent / f"{model_src.name}.data"
    if model_src_data.exists():
        shutil.copy2(model_src_data, active_dir / model_src_data.name)
    shutil.copy2(manifest_src, active_dir / "manifest.json")
    logger.info("Promoted new model to active production directory.")

    # 6. Update deployment registry
    registry: Dict[str, Any] = {"history": []}
    if registry_file.exists():
        try:
            with open(registry_file, "r", encoding="utf-8") as f:
                registry = json.load(f)
        except Exception:
            pass

    record = {
        "action": "DEPLOY",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_id": manifest.model_id,
        "version": manifest.version,
        "checksum_sha256": actual_hash,
        "status": "ACTIVE",
    }
    registry["active_version"] = manifest.version
    registry["history"].append(record)

    with open(registry_file, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)

    logger.info(f"Successfully registered active model version {manifest.version}.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Edge Model Deployment Utility")
    parser.add_argument("--model", required=True, help="Path to staged model artifact (.onnx)")
    parser.add_argument("--manifest", required=True, help="Path to staged model manifest (.json)")
    parser.add_argument("--base-dir", default="models", help="Base models directory")
    args = parser.parse_args()

    success = deploy_model(args.model, args.manifest, args.base_dir)
    sys.exit(0 if success else 1)
