"""Dataset preparation and directory structure initialization utility."""

from __future__ import annotations

import argparse
import logging
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_CLASSES = [
    "clean",
    "dent",
    "scratch",
    "rim_dent",
    "seam_defect",
    "pinhole",
    "contamination",
    "corrosion",
]


def setup_dataset_structure(root_dir: str = "data/dataset") -> None:
    """Creates the standard image classification dataset folders for training."""
    root = Path(root_dir)
    train_dir = root / "train"
    val_dir = root / "val"

    for split in [train_dir, val_dir]:
        for cls_name in DEFAULT_CLASSES:
            cls_path = split / cls_name
            cls_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Initialized dataset directories at: {root.resolve()}")
    print("\n" + "=" * 65)
    print(" DATASET FOLDER STRUCTURE READY")
    print("=" * 65)
    print(f"Root: {root.resolve()}")
    print("\nOrganize your can images into these folders:")
    for cls_name in DEFAULT_CLASSES:
        print(f"  |-- train/{cls_name}/  (80% of photos for '{cls_name}')")
        print(f"  \\-- val/{cls_name}/    (20% of photos for '{cls_name}')")

    print("\nRecommendations for Industrial Defect Data Collection:")
    print("  1. Aim for at least 30 to 100 images per defect class.")
    print("  2. Include variations in can rotation, lighting, and can sizes.")
    print("  3. Ensure images of 'clean' cans outnumber defect photos.")
    print("  4. Once photos are placed, run:")
    print("         python scripts/train_model.py --epochs 15")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare dataset directory structure")
    parser.add_argument("--dir", default="data/dataset", help="Dataset destination directory")
    args = parser.parse_args()

    setup_dataset_structure(args.dir)
