"""Dataset Train/Val Split Utility for S-can.

Splits processed JPG images from dataset/raw_jpg into data/dataset/train and data/dataset/val
with a configurable train/val ratio and stratified distribution.
"""

from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path

# Map raw folder names to standard training classes
CLASS_RENAME_MAP = {
    "no_defect": "clean",
    "fotos lata no dañada": "clean",
    "fotos lata no daada": "clean",
    "clean": "clean",
}


def split_dataset(
    source_dir: str = "dataset/raw_jpg",
    dest_dir: str = "data/dataset",
    val_ratio: float = 0.20,
    seed: int = 42,
) -> None:
    source = Path(source_dir).resolve()
    dest = Path(dest_dir).resolve()
    train_dest = dest / "train"
    val_dest = dest / "val"

    if not source.exists():
        raise FileNotFoundError(f"Source folder not found: {source}")

    random.seed(seed)
    categories = [d for d in source.iterdir() if d.is_dir()]

    if not categories:
        raise ValueError(f"No class folders found in {source}")

    total_train = 0
    total_val = 0

    print("=" * 65)
    print(" SPLITTING DATASET INTO TRAIN / VAL")
    print(f" Source: {source}")
    print(f" Dest:   {dest}")
    print(f" Ratio:  {int((1-val_ratio)*100)}% Train / {int(val_ratio*100)}% Val")
    print("=" * 65)

    for cat_dir in sorted(categories):
        raw_name = cat_dir.name
        class_name = CLASS_RENAME_MAP.get(raw_name, raw_name)

        images = [f for f in cat_dir.iterdir() if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png"}]
        if not images:
            continue

        random.shuffle(images)

        # Ensure at least 1 image goes to val if total >= 2
        val_count = max(1, int(round(len(images) * val_ratio))) if len(images) >= 2 else 0
        train_count = len(images) - val_count

        train_images = images[:train_count]
        val_images = images[train_count:]

        # Destination paths
        cat_train_dir = train_dest / class_name
        cat_val_dir = val_dest / class_name
        cat_train_dir.mkdir(parents=True, exist_ok=True)
        cat_val_dir.mkdir(parents=True, exist_ok=True)

        # Clear existing images in target class directories to avoid train/val leakage
        for f in cat_train_dir.iterdir():
            if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                f.unlink()
        for f in cat_val_dir.iterdir():
            if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                f.unlink()

        for img in train_images:
            shutil.copy2(img, cat_train_dir / img.name)
        for img in val_images:
            shutil.copy2(img, cat_val_dir / img.name)

        total_train += len(train_images)
        total_val += len(val_images)

        print(f"Class: {class_name:15s} | Train: {len(train_images):3d} | Val: {len(val_images):3d} | Total: {len(images):3d}")

    print("=" * 65)
    print(f"Grand Total: {total_train + total_val} photos ({total_train} train, {total_val} val)")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split dataset into train and val folders")
    parser.add_argument("--source", default="dataset/raw_jpg", help="Source folder with class subdirectories")
    parser.add_argument("--dest", default="data/dataset", help="Destination folder for train/ and val/")
    parser.add_argument("--val-ratio", type=float, default=0.20, help="Validation set split ratio (default: 0.20)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    split_dataset(args.source, args.dest, args.val_ratio, args.seed)
