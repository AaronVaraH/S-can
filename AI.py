"""100% Local Edge-AI Can-Defect Inspector (Zero API keys, Zero Cloud Calls).

This script executes artificial neurons directly on the local Raspberry Pi / PC CPU
using the local compiled ONNX neural network weights. No internet or API calls required.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

# Path to the local neural network weights
MODEL_PATH = Path("models/active/can_detector.onnx")
SAMPLE_IMAGE = "Metal-Can.jpg"

DEFECT_CLASSES = [
    "dent",
    "scratch",
    "rim_dent",
    "pinhole",
    "contamination",
    "corrosion",
    "seam_defect",
    "ovalization",
]


def load_local_neurons(model_path: Path) -> ort.InferenceSession:
    """Loads the artificial neural network graph and weight tensors into local memory."""
    if not model_path.exists():
        raise FileNotFoundError(
            f"Local model weights not found at '{model_path}'. "
            "Run 'python scripts/export_model.py' to generate the local weights."
        )

    # Configure local CPU execution with thread tuning for Raspberry Pi / local cores
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = min(4, os.cpu_count() or 2)
    opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    session = ort.InferenceSession(str(model_path), sess_options=opts, providers=["CPUExecutionProvider"])
    return session


def preprocess_image_local(image_path: str, target_size: tuple[int, int] = (320, 320)) -> np.ndarray:
    """Loads and letterbox-preprocesses the image into a normalized float32 tensor."""
    if not Path(image_path).exists():
        raise FileNotFoundError(f"Image file '{image_path}' not found.")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to read image file '{image_path}'.")

    # Resize while preserving aspect ratio
    h, w = img.shape[:2]
    tw, th = target_size
    scale = min(tw / w, th / h)
    nw, nh = int(round(w * scale)), int(round(h * scale))

    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    padded = np.full((th, tw, 3), 114, dtype=np.uint8)

    top = (th - nh) // 2
    left = (tw - nw) // 2
    padded[top:top + nh, left:left + nw] = resized

    # Convert BGR to RGB and normalize (ImageNet mean & std)
    rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    normalized = (rgb - mean) / std

    # Transpose to NCHW layout: (1, 3, 320, 320)
    tensor = np.transpose(normalized, (2, 0, 1))
    tensor = np.expand_dims(tensor, axis=0)
    return tensor


def run_local_inspection(image_path: str = SAMPLE_IMAGE) -> None:
    print("=" * 65)
    print(" 100% LOCAL EDGE AI CAN INSPECTION (NO APIS, AIR-GAPPED)")
    print("=" * 65)
    print(f"Loading local neurons from: {MODEL_PATH}")

    t0 = time.perf_counter()
    session = load_local_neurons(MODEL_PATH)
    t_load = (time.perf_counter() - t0) * 1000

    input_name = session.get_inputs()[0].name
    print(f"Neurons loaded in {t_load:.2f} ms onto local CPU.")
    print(f"Reading local image: {image_path}")

    tensor = preprocess_image_local(image_path)

    # Forward pass: executing the neurons locally
    t_inf_0 = time.perf_counter()
    outputs = session.run(None, {input_name: tensor})
    t_inf_1 = time.perf_counter()
    latency_ms = (t_inf_1 - t_inf_0) * 1000

    logits = outputs[0][0]  # Array of 8 class activations
    # Sigmoid activation on output neurons
    probabilities = 1.0 / (1.0 + np.exp(-logits))

    print(f"Inference completed locally in: {latency_ms:.2f} ms")
    print("\n" + "-" * 65)
    print("id,defect_type,confidence,status")
    print("-" * 65)

    has_defect = False
    for i, (defect_name, score) in enumerate(zip(DEFECT_CLASSES, probabilities), start=1):
        status = "FAIL" if score >= 0.70 else ("REVIEW" if score >= 0.35 else "PASS")
        if status in ("FAIL", "REVIEW"):
            has_defect = True
        print(f"{i},{defect_name},{score:.4f},{status}")

    print("-" * 65)
    overall = "FAIL (REJECT CAN)" if has_defect else "PASS (ACCEPT CAN)"
    print(f"OVERALL INSPECTION DECISION: {overall}")
    print("=" * 65)


if __name__ == "__main__":
    target_img = sys.argv[1] if len(sys.argv) > 1 else SAMPLE_IMAGE
    run_local_inspection(target_img)
