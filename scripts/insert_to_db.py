"""Utility to insert images and inspection records directly into SQLite database."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import uuid
from pathlib import Path

import cv2

# Project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from edge_inspector.decision import evaluate_inspection
from edge_inspector.inference.onnx_engine import ONNXInferenceEngine
from edge_inspector.quality import letterbox_preprocess, validate_image_quality
from edge_inspector.storage import StorageManager


def insert_image_into_db(
    image_path: str,
    db_path: str = "data/inspection.db",
    store_blob: bool = False,
    run_ai_inspection: bool = True,
    manual_decision: str = "PASS",
    manual_defect: str = None,
) -> str:
    """Inserts an image into the SQLite database."""
    img_p = Path(image_path)
    if not img_p.exists():
        raise FileNotFoundError(f"Image '{image_path}' not found.")

    img = cv2.imread(str(img_p))
    if img is None:
        raise ValueError(f"Failed to decode image '{image_path}'.")

    db_p = Path(db_path)
    db_p.parent.mkdir(parents=True, exist_ok=True)

    # 1. Initialize DB and add image_blob column if BLOB storage requested
    with sqlite3.connect(db_p) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inspections (
                inspection_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                frame_id INTEGER NOT NULL,
                decision TEXT NOT NULL,
                primary_defect TEXT,
                confidence REAL NOT NULL,
                uncertainty REAL NOT NULL,
                quality_gate_passed INTEGER NOT NULL,
                total_latency_ms REAL NOT NULL,
                image_path TEXT,
                metadata_json TEXT
            )
        """)
        # Ensure image_blob column exists if store_blob is enabled
        cursor.execute("PRAGMA table_info(inspections)")
        columns = [row[1] for row in cursor.fetchall()]
        if "image_blob" not in columns:
            cursor.execute("ALTER TABLE inspections ADD COLUMN image_blob BLOB")
        conn.commit()

    inspection_id = str(uuid.uuid4())
    timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    saved_image_path = None

    if run_ai_inspection:
        # Run local AI models to get real detection and decision
        from edge_inspector.inference.base import ModelManifest
        manifest_p = Path("models/active/manifest.json")
        manifest = ModelManifest.from_file(str(manifest_p)) if manifest_p.exists() else None
        engine = ONNXInferenceEngine(manifest=manifest)
        engine.load_model("models/active/can_detector.onnx", manifest=manifest)

        q_res = validate_image_quality(img)
        tensor, t_meta = letterbox_preprocess(img, (320, 320))
        t0 = time.perf_counter()
        inf_res = engine.infer(tensor, t_meta)
        latency_ms = (time.perf_counter() - t0) * 1000

        dec_res = evaluate_inspection(q_res, inf_res)
        decision_str = dec_res.decision.value
        defect_str = inf_res.primary_defect
        conf_val = dec_res.confidence_score
        unc_val = dec_res.uncertainty_score
        q_pass = 1 if q_res.passed_quality_gate else 0

        # Save annotated image and record
        storage = StorageManager(db_path=str(db_p), save_annotated_images=True, save_review_images=True, save_fail_images=True, save_pass_images=True)
        rec = storage.save_inspection(
            frame_id=1,
            raw_image=img,
            quality=q_res,
            inference=inf_res,
            decision=dec_res,
            total_latency_ms=latency_ms,
        )
        inspection_id = rec.inspection_id
        saved_image_path = rec.image_path
        timestamp_iso = rec.timestamp

        # If storing raw bytes directly inside DB as BLOB, update this row
        if store_blob:
            with open(img_p, "rb") as f:
                raw_blob_bytes = f.read()
            with sqlite3.connect(db_p) as conn:
                conn.execute(
                    "UPDATE inspections SET image_blob = ? WHERE inspection_id = ?",
                    (raw_blob_bytes, inspection_id),
                )
                conn.commit()
    else:
        # Manual entry
        decision_str = manual_decision.upper()
        defect_str = manual_defect
        conf_val = 1.0
        unc_val = 0.0
        q_pass = 1
        latency_ms = 0.0
        saved_image_path = str(img_p.resolve())
        meta_json = json.dumps({"source": "manual_upload"})

        raw_blob_bytes = None
        if store_blob:
            with open(img_p, "rb") as f:
                raw_blob_bytes = f.read()

        with sqlite3.connect(db_p) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO inspections (
                    inspection_id, timestamp, frame_id, decision,
                    primary_defect, confidence, uncertainty,
                    quality_gate_passed, total_latency_ms, image_path,
                    metadata_json, image_blob
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inspection_id,
                timestamp_iso,
                1,
                decision_str,
                defect_str,
                conf_val,
                unc_val,
                q_pass,
                round(latency_ms, 2),
                saved_image_path,
                meta_json,
                raw_blob_bytes,
            ))
            conn.commit()

    print("\n" + "=" * 65)
    print(" IMAGE INSERTED INTO DATABASE SUCCESSFULLY")
    print("=" * 65)
    print(f"  Database File     : {db_p.resolve()}")
    print(f"  Inspection ID     : {inspection_id}")
    print(f"  Timestamp         : {timestamp_iso}")
    print(f"  Decision          : {decision_str}")
    print(f"  Primary Defect    : {defect_str or 'None (Clean Can)'}")
    print(f"  Confidence        : {conf_val:.2f}")
    print(f"  Image File Path   : {saved_image_path}")
    print(f"  Stored as BLOB    : {'YES (bytes in .db file)' if store_blob else 'NO (linked via image_path)'}")
    print("=" * 65 + "\n")

    return inspection_id


def extract_image_from_db(inspection_id: str, output_path: str, db_path: str = "data/inspection.db") -> None:
    """Extracts image bytes stored as a BLOB from SQLite and saves to an image file."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT image_blob, image_path FROM inspections WHERE inspection_id = ?", (inspection_id,))
        row = cursor.fetchone()
        if not row:
            print(f"No record found with ID: {inspection_id}")
            return

        blob_data, file_path = row
        if blob_data:
            with open(output_path, "wb") as f:
                f.write(blob_data)
            print(f"Extracted image from database BLOB to: {output_path}")
        elif file_path and Path(file_path).exists():
            import shutil
            shutil.copy2(file_path, output_path)
            print(f"Copied referenced image from disk to: {output_path}")
        else:
            print("No image data or file reference found for this record.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Insert images into SQLite database")
    parser.add_argument("image", help="Path to image file (JPEG, PNG, WebP)")
    parser.add_argument("--db", default="data/inspection.db", help="Path to SQLite database")
    parser.add_argument("--blob", action="store_true", help="Store raw JPEG bytes directly inside the .db file (BLOB)")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI inspection and insert manually")
    parser.add_argument("--decision", default="PASS", choices=["PASS", "FAIL", "REVIEW"], help="Manual decision")
    parser.add_argument("--defect", default=None, help="Manual defect label")
    args = parser.parse_args()

    insert_image_into_db(
        image_path=args.image,
        db_path=args.db,
        store_blob=args.blob,
        run_ai_inspection=not args.no_ai,
        manual_decision=args.decision,
        manual_defect=args.defect,
    )
