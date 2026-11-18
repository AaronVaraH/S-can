"""Camera testing, calibration, and acquisition verification utility."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from edge_inspector.camera import create_camera_adapter
from edge_inspector.quality import validate_image_quality


def run_camera_test(
    adapter: str = "synthetic",
    device_index: int = 0,
    width: int = 640,
    height: int = 480,
    fps: int = 30,
    frames_to_test: int = 20,
    save_sample: bool = True,
) -> None:
    print("\n" + "=" * 65)
    print(f" CAMERA STREAM VERIFICATION & CALIBRATION (Adapter: {adapter})")
    print("=" * 65)

    config = {
        "adapter": adapter,
        "device_index": device_index,
        "width": width,
        "height": height,
        "fps": fps,
        "pixel_format": "RGB",
        "auto_exposure": False,
        "exposure_time_us": 5000,
        "gain_db": 6.0,
    }

    cam = create_camera_adapter(config)
    print(f"Connecting to camera adapter: {adapter} (device index: {device_index})...")

    connected = cam.connect()
    if not connected:
        print(f"ERROR: Could not connect to camera: {cam.last_error_message}")
        sys.exit(1)

    print(f"Camera connected. Capturing {frames_to_test} test frames...")

    latencies = []
    blur_scores = []
    brightness_scores = []
    last_frame = None

    for i in range(frames_to_test):
        frame, meta = cam.capture_frame()
        if frame is None or meta is None:
            print(f"  Frame {i+1}: FAILED to grab buffer!")
            continue

        latencies.append(meta.acquisition_latency_ms)
        last_frame = frame

        # Run quality check on sample
        q = validate_image_quality(frame)
        blur_scores.append(q.blur_score)
        brightness_scores.append(q.mean_brightness)

        if (i + 1) % 5 == 0 or i == frames_to_test - 1:
            print(f"  Frame {i+1:2d}/{frames_to_test}: Latency={meta.acquisition_latency_ms:5.1f}ms | Sharpness={q.blur_score:6.1f} | Brightness={q.mean_brightness:5.1f} | Gate={'PASS' if q.passed_quality_gate else 'FAIL'}")

    cam.disconnect()

    if not latencies:
        print("ERROR: No valid frames captured.")
        sys.exit(1)

    avg_lat = np.mean(latencies)
    p95_lat = np.percentile(latencies, 95)
    avg_sharp = np.mean(blur_scores)
    avg_bright = np.mean(brightness_scores)

    print("\n" + "-" * 65)
    print(" CAMERA TEST SUMMARY")
    print("-" * 65)
    print(f"  Frames Captured     : {len(latencies)} / {frames_to_test}")
    print(f"  Average Acquisition : {avg_lat:.2f} ms")
    print(f"  P95 Acquisition     : {p95_lat:.2f} ms")
    print(f"  Effective Frame Rate: {1000.0 / avg_lat:.1f} FPS")
    print(f"  Mean Image Sharpness: {avg_sharp:.1f} (Threshold: 65.0)")
    print(f"  Mean Brightness     : {avg_bright:.1f} (Target range: 35 - 235)")

    if save_sample and last_frame is not None:
        out_dir = Path("data")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "camera_test_sample.jpg"
        # Convert RGB to BGR for cv2 imwrite
        bgr = cv2.cvtColor(last_frame, cv2.COLOR_RGB2BGR) if len(last_frame.shape) == 3 else last_frame
        cv2.imwrite(str(out_path), bgr)
        print(f"  Saved Sample Frame  : {out_path.resolve()}")

    print("=" * 65 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Camera Testing and Calibration Utility")
    parser.add_argument("--adapter", default="synthetic", choices=["synthetic", "usb", "picamera2"], help="Camera adapter type")
    parser.add_argument("--device", type=int, default=0, help="Device index")
    parser.add_argument("--width", type=int, default=640, help="Frame width")
    parser.add_argument("--height", type=int, default=480, help="Frame height")
    parser.add_argument("--fps", type=int, default=30, help="Target FPS")
    parser.add_argument("--frames", type=int, default=15, help="Number of test frames")
    args = parser.parse_args()

    run_camera_test(
        adapter=args.adapter,
        device_index=args.device,
        width=args.width,
        height=args.height,
        fps=args.fps,
        frames_to_test=args.frames,
    )
