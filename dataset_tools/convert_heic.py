"""HEIC to JPG Converter for S-can Dataset Tools.

Converts all Apple HEIC photos to high-quality JPEG images while preserving
folder structure, EXIF orientation, and RGB color channels.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from PIL import Image, ImageOps

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HAS_PILLOW_HEIF = True
except ImportError:
    HAS_PILLOW_HEIF = False
    try:
        import av
        HAS_AV = True
    except ImportError:
        HAS_AV = False

if not HAS_PILLOW_HEIF and not HAS_AV:
    print("Error: Neither 'pillow-heif' nor 'av' is installed. Please install one of them.")
    sys.exit(1)


# Optional mapping to standardize folder names with S-can defect classes
FOLDER_NAME_MAPPING = {
    "clean": "no_defect",
    "fotos lata no dañada": "no_defect",
    "fotos lata no daada": "no_defect",
    "dent": "dent",
    "scratch": "scratch",
    "contamination": "contamination",
    "rim dent": "rim_dent",
    "rim_dent": "rim_dent",
    "pin hole": "pinhole",
    "pinhole": "pinhole",
    "hole": "pinhole",
}


def load_image_frame(file_path: Path) -> Image.Image:
    """Loads an image from HEIC or video file as a PIL Image."""
    suffix = file_path.suffix.lower()
    if suffix in {".mov", ".mp4", ".avi"}:
        import cv2
        cap = cv2.VideoCapture(str(file_path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        mid = max(0, total_frames // 2)
        cap.set(cv2.CAP_PROP_POS_FRAMES, mid)
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            raise ValueError(f"Failed to read frame from video: {file_path}")
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)

    if HAS_PILLOW_HEIF:
        with Image.open(file_path) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode != "RGB":
                img = img.convert("RGB")
            return img.copy()

    if HAS_AV:
        import av
        container = av.open(str(file_path))
        frame = next(container.decode(video=0))
        img = frame.to_image()
        container.close()
        if img.mode != "RGB":
            img = img.convert("RGB")
        return img

    raise RuntimeError("No HEIC decoder available.")


def convert_heic_to_jpg(
    source_dir: Path | str,
    output_dir: Path | str,
    quality: int = 95,
    standardize_names: bool = False,
    include_videos: bool = True,
) -> tuple[int, int]:
    """Recursively converts all HEIC images in source_dir into JPG in output_dir.

    Args:
        source_dir: Directory containing HEIC files and subfolders.
        output_dir: Destination directory for converted JPG files.
        quality: JPEG compression quality (1-100).
        standardize_names: If True, maps folder names like 'rim dent' -> 'rim_dent'.
        include_videos: If True, extracts frames from standalone MOV/MP4 clips.

    Returns:
        (converted_count, skipped_or_failed_count)
    """
    source_dir = Path(source_dir).resolve()
    output_dir = Path(output_dir).resolve()

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_dir}")

    valid_exts = {".heic", ".heif"}
    if include_videos:
        valid_exts.update({".mov", ".mp4"})

    media_files = [
        p for p in source_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in valid_exts
    ]

    total = len(media_files)
    print(f"Found {total} media file(s) in: {source_dir}")
    if total == 0:
        return 0, 0

    converted = 0
    failed = 0

    for idx, file_path in enumerate(media_files, start=1):
        rel_path = file_path.relative_to(source_dir)
        
        # Determine target folder
        parts = list(rel_path.parent.parts)
        if standardize_names and parts:
            parts = [FOLDER_NAME_MAPPING.get(p.lower(), p) for p in parts]
        
        target_folder = output_dir.joinpath(*parts)
        target_folder.mkdir(parents=True, exist_ok=True)
        
        target_filename = file_path.stem + ".jpg"
        target_file = target_folder / target_filename

        try:
            img = load_image_frame(file_path)
            img.save(target_file, "JPEG", quality=quality, optimize=True)
            
            converted += 1
            print(f"[{idx}/{total}] Converted: {rel_path} -> {target_file.name}")
        except Exception as e:
            failed += 1
            print(f"[{idx}/{total}] FAILED: {rel_path} ({e})", file=sys.stderr)

    print("\n--- Conversion Complete ---")
    print(f"Total processed: {total}")
    print(f"Successfully converted: {converted}")
    print(f"Failed: {failed}")
    print(f"Output directory: {output_dir}")

    return converted, failed


def main():
    parser = argparse.ArgumentParser(description="Convert HEIC images to JPG for dataset processing.")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="dataset/raw_heic",
        help="Input folder containing HEIC images.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="dataset/raw_jpg",
        help="Output folder to save JPG images.",
    )
    parser.add_argument(
        "--quality",
        "-q",
        type=int,
        default=95,
        help="JPEG quality (1-100). Default is 95.",
    )
    parser.add_argument(
        "--standardize-names",
        action="store_true",
        help="Standardize folder names to match S-can defect classes (e.g. 'rim dent' -> 'rim_dent').",
    )

    args = parser.parse_args()
    convert_heic_to_jpg(
        source_dir=args.input,
        output_dir=args.output,
        quality=args.quality,
        standardize_names=args.standardize_names,
    )


if __name__ == "__main__":
    main()
