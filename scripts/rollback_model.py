"""Atomic rollback script to safely revert to a previously validated edge model."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from edge_inspector.inference.base import ModelManifest, compute_file_sha256

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def rollback_model(base_dir: str = "models", target_archive: str = None) -> bool:
    """Restores the most recent (or specified) archive model version."""
    base = Path(base_dir)
    active_dir = base / "active"
    archive_dir = base / "archive"
    registry_file = base / "registry.json"

    if not archive_dir.exists():
        logger.error("No archive directory found. Cannot perform rollback.")
        return False

    arch_versions = sorted([p for p in archive_dir.iterdir() if p.is_dir()], key=lambda p: p.name)
    if not arch_versions:
        logger.error("No archived model versions found. Rollback impossible.")
        return False

    selected_archive = None
    if target_archive:
        cand = archive_dir / target_archive
        if cand.exists() and cand.is_dir():
            selected_archive = cand
        else:
            logger.error(f"Target archive '{target_archive}' does not exist.")
            return False
    else:
        # Default to the most recent archive
        selected_archive = arch_versions[-1]

    restored_model = selected_archive / "can_detector.onnx"
    restored_manifest = selected_archive / "manifest.json"

    if not restored_model.exists() or not restored_manifest.exists():
        logger.error(f"Archive {selected_archive.name} is missing model or manifest.")
        return False

    try:
        manifest = ModelManifest.from_file(str(restored_manifest))
        actual_hash = compute_file_sha256(str(restored_model))
        if manifest.checksum_sha256 and actual_hash != manifest.checksum_sha256:
            logger.error("Archived artifact checksum failure! Corrupted backup.")
            return False
    except Exception as e:
        logger.error(f"Failed to validate archived model: {str(e)}")
        return False

    # Overwrite active with archived version
    active_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(restored_model, active_dir / "can_detector.onnx")
    shutil.copy2(restored_manifest, active_dir / "manifest.json")
    logger.info(f"Restored model version v{manifest.version} from {selected_archive.name}")

    # Update registry
    registry: Dict[str, Any] = {"history": []}
    if registry_file.exists():
        try:
            with open(registry_file, "r", encoding="utf-8") as f:
                registry = json.load(f)
        except Exception:
            pass

    record = {
        "action": "ROLLBACK",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_id": manifest.model_id,
        "version": manifest.version,
        "restored_from": selected_archive.name,
        "status": "ACTIVE_RESTORED",
    }
    registry["active_version"] = manifest.version
    registry["history"].append(record)

    with open(registry_file, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)

    logger.info(f"Rollback complete. System active version is now v{manifest.version}.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Edge Model Rollback Utility")
    parser.add_argument("--base-dir", default="models", help="Base models directory")
    parser.add_argument("--target", default=None, help="Specific archive folder name")
    args = parser.parse_args()

    success = rollback_model(args.base_dir, args.target)
    sys.exit(0 if success else 1)
