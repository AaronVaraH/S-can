"""Model training and fine-tuning pipeline for can defect inspection (Run on PC / GPU workstation)."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def check_torch_installed() -> bool:
    try:
        import torch  # type: ignore # noqa: F401
        import torchvision  # type: ignore # noqa: F401
        return True
    except ImportError:
        return False


def train_edge_model(
    data_dir: str = "data/dataset",
    output_dir: str = "models/staging",
    epochs: int = 15,
    batch_size: int = 16,
    learning_rate: float = 0.001,
    image_size: int = 320,
    model_version: str = "1.1.0",
) -> None:
    """Trains a lightweight MobileNetV3-Small classifier and exports to ONNX for the Raspberry Pi."""
    if not check_torch_installed():
        logger.error(
            "PyTorch and Torchvision are required for training. Install them on your development PC:\n"
            "    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118 (for GPU)\n"
            "    or: pip install torch torchvision (for CPU)\n"
            "Note: Model training should be performed on a workstation, not the Raspberry Pi."
        )
        sys.exit(1)

    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader
    from torchvision import datasets, models, transforms

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training on device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Host CPU'})")

    data_path = Path(data_dir)
    train_path = data_path / "train"
    val_path = data_path / "val"

    if not train_path.exists() or not val_path.exists():
        logger.error(
            f"Dataset directories not found. Expected:\n  {train_path}\n  {val_path}\n"
            "Each folder should contain subdirectories for each defect class:\n"
            "  clean/, dent/, scratch/, seam_defect/, pinhole/, etc.\n"
            "Run 'python scripts/prepare_dataset.py' to generate a sample structure."
        )
        sys.exit(1)

    # 1. Industrial Data Augmentation
    # Simulates factory vibration, conveyor jitter, and illumination fluctuations
    train_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=10),
        transforms.ColorJitter(brightness=0.15, contrast=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    train_dataset = datasets.ImageFolder(str(train_path), transform=train_transform)
    val_dataset = datasets.ImageFolder(str(val_path), transform=val_transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    classes = train_dataset.classes
    num_classes = len(classes)
    logger.info(f"Loaded dataset: {len(train_dataset)} training samples, {len(val_dataset)} validation samples.")
    logger.info(f"Classes ({num_classes}): {classes}")

    # 2. Lightweight Edge Backbone (MobileNetV3-Small)
    # Designed specifically for ARM Cortex-A72 / A76 CPUs (Raspberry Pi 4 / 5)
    model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
    in_features = model.classifier[3].in_features
    # Replace final linear layer with custom defect classes
    model.classifier[3] = nn.Linear(in_features, num_classes)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    # 3. Training Loop
    best_acc = 0.0
    best_weights = None

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

        scheduler.step()
        train_loss = running_loss / total
        train_acc = correct / total

        # Validation
        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, preds = torch.max(outputs, 1)
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)

        val_acc = val_correct / val_total
        logger.info(f"Epoch [{epoch:02d}/{epochs:02d}] Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2%} | Val Acc: {val_acc:.2%}")

        if val_acc >= best_acc:
            best_acc = val_acc
            best_weights = model.state_dict().copy()

    # Load best validated model
    if best_weights:
        model.load_state_dict(best_weights)
    logger.info(f"Training complete. Peak Validation Accuracy: {best_acc:.2%}")

    # 4. Export Directly to Optimized ONNX Format
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = out_dir / "can_detector.onnx"
    manifest_path = out_dir / "manifest.json"

    model.eval()
    model = model.to("cpu")
    dummy_input = torch.randn(1, 3, image_size, image_size, requires_grad=False)

    logger.info(f"Exporting trained model to ONNX: {onnx_path}")
    torch.onnx.export(
        model,
        dummy_input,
        str(onnx_path),
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=["input_tensor"],
        output_names=["output_logits"],
        dynamic_axes={"input_tensor": {0: "batch_size"}, "output_logits": {0: "batch_size"}},
    )

    # 5. Calculate SHA-256 Checksum and Generate Manifest
    h = hashlib.sha256()
    with open(onnx_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    checksum = h.hexdigest()

    manifest_data = {
        "model_id": f"can_defect_mobilenet_{model_version}",
        "version": model_version,
        "architecture": "MobileNetV3-Small-FineTuned",
        "runtime": "ONNXRuntime",
        "input_shape": [1, 3, image_size, image_size],
        "classes": classes,
        "preprocessing": {
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225],
            "target_size": [image_size, image_size],
            "preserve_aspect_ratio": True,
        },
        "thresholds": {
            c: 0.70 if c != "pinhole" and c != "seam_defect" else 0.50
            for c in classes
        },
        "checksum_sha256": checksum,
        "quantization": "FP32",
        "target_hardware": "Raspberry Pi 4 / Pi 5 / Generic Edge",
        "benchmarked_val_acc": round(best_acc, 4),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    logger.info(f"Model manifest saved to: {manifest_path}")
    logger.info(f"SHA-256 Checksum: {checksum}")
    logger.info(
        "\n=================================================================="
        "\nNEXT STEP: Deploy this model to the Raspberry Pi:"
        f"\n    python scripts/deploy_model.py --model {onnx_path} --manifest {manifest_path}"
        "\n=================================================================="
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train / Fine-tune Can Defect Model (Workstation/PC)")
    parser.add_argument("--data-dir", default="data/dataset", help="Dataset root directory containing train/ and val/")
    parser.add_argument("--output-dir", default="models/staging", help="Output directory for ONNX model and manifest")
    parser.add_argument("--epochs", type=int, default=15, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--size", type=int, default=320, help="Input image dimension (default: 320)")
    parser.add_argument("--version", default="1.1.0", help="Model semantic version string")
    args = parser.parse_args()

    train_edge_model(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        image_size=args.size,
        model_version=args.version,
    )
