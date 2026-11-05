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
except ImportError:
    print("Error: 'pillow-heif' is required. Run 'pip install pillow-heif' first.")
    sys.exit(1)


# Optional mapping to standardize folder names with S-can defect classes
FOLDER_NAME_MAPPING = {
    "fotos lata no dañada": "no_defect",
    "fotos lata no daada": "no_defect",
    "rim dent": "rim_dent",
    "hole": "pinhole",
}


def convert_heic_to_jpg(
    source_dir: Path | str,
    output_dir: Path | str,
    quality: int = 95,
    standardize_names: bool = False,
) -> tuple[int, int]:
    """Recursively converts all HEIC images in source_dir into JPG in output_dir.

    Args:
        source_dir: Directory containing HEIC files and subfolders.
        output_dir: Destination directory for converted JPG files.
        quality: JPEG compression quality (1-100).
        standardize_names: If True, maps folder names like 'rim dent' -> 'rim_dent'.

    Returns:
        (converted_count, skipped_or_failed_count)
    """
    source_dir = Path(source_dir).resolve()
    output_dir = Path(output_dir).resolve()

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_dir}")

    heic_files = [
        p for p in source_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in {".heic", ".heif"}
    ]

    total = len(heic_files)
    print(f"Found {total} HEIC image(s) in: {source_dir}")
    if total == 0:
        return 0, 0

    converted = 0
    failed = 0

    for idx, file_path in enumerate(heic_files, start=1):
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
            with Image.open(file_path) as img:
                # Correct orientation from EXIF metadata
                img = ImageOps.exif_transpose(img)
                # Convert RGBA/P to RGB for JPEG compatibility
                if img.mode != "RGB":
                    img = img.convert("RGB")
                
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
        default=r"c:\Users\beti-\OneDrive\Documentos\Robert",
        help="Input folder containing HEIC images.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=r"c:\Users\beti-\OneDrive\Documentos\scan f\S-can\dataset\raw_jpg",
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
