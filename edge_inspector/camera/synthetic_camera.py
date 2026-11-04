"""Synthetic camera adapter for development and simulation without physical camera hardware."""

from __future__ import annotations

import glob
import math
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from edge_inspector.camera.base import (
    AcquisitionConfig,
    BaseCameraAdapter,
    CameraState,
    FrameMetadata,
)


class SyntheticCameraAdapter(BaseCameraAdapter):
    """Simulates physical camera acquisition using stored images or generated can graphics."""

    def __init__(self, config: AcquisitionConfig) -> None:
        super().__init__(config)
        self.image_files: List[str] = []
        self.current_idx: int = 0
        self.simulate_drops: bool = False
        self.drop_rate: float = 0.0

    def connect(self) -> bool:
        self.state = CameraState.INITIALIZING
        self.image_files = []

        folder = self.config.synthetic_image_folder
        candidate_dirs = [folder] if folder else []
        candidate_dirs.extend(["data/sample_cans", ".", "sample_images"])

        for d in candidate_dirs:
            if d and Path(d).exists():
                for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp"):
                    self.image_files.extend(glob.glob(os.path.join(d, ext)))

        # Deduplicate and sort
        self.image_files = sorted(list(set(self.image_files)))
        self.state = CameraState.CONNECTED
        self.last_error_message = None
        return True

    def disconnect(self) -> None:
        self.state = CameraState.DISCONNECTED

    def _generate_synthetic_can_image(self) -> np.ndarray:
        """Synthesizes a realistic cylindrical can frame when no image files are found."""
        w, h = self.config.width, self.config.height
        # Dark industrial conveyor background
        img = np.full((h, w, 3), 45, dtype=np.uint8)

        # Draw cylindrical metal can body
        can_cx = w // 2 + random.randint(-15, 15)
        can_cy = h // 2 + random.randint(-10, 10)
        can_w = int(w * 0.45)
        can_h = int(h * 0.70)

        x1 = can_cx - can_w // 2
        x2 = can_cx + can_w // 2
        y1 = can_cy - can_h // 2
        y2 = can_cy + can_h // 2

        # Brushed aluminum gradient
        for x in range(max(0, x1), min(w, x2)):
            norm_x = (x - x1) / can_w
            # Cylindrical light reflection: brighter in center, darker at edges
            lum = int(140 + 85 * math.sin(norm_x * math.pi))
            img[max(0, y1):min(h, y2), x] = [lum - 10, lum, lum + 5]

        # Draw can rim / double seam
        rim_color = (210, 215, 220)
        cv2.ellipse(img, (can_cx, y1 + 10), (can_w // 2, 22), 0, 0, 360, rim_color, -1)
        cv2.ellipse(img, (can_cx, y1 + 10), (can_w // 2, 22), 0, 0, 360, (110, 115, 120), 2)

        # Bottom rim
        cv2.ellipse(img, (can_cx, y2 - 10), (can_w // 2, 22), 0, 0, 180, (100, 105, 110), 3)

        # Randomly inject defect (dent or scratch) on 50% of synthetic cans
        defect_type = random.choice(["none", "dent", "scratch", "corrosion", "clean"])
        if defect_type == "dent":
            dent_x = can_cx + random.randint(-30, 30)
            dent_y = can_cy + random.randint(-40, 40)
            cv2.ellipse(img, (dent_x, dent_y), (35, 20), random.randint(-30, 30), 0, 360, (70, 75, 80), -1)
            cv2.ellipse(img, (dent_x - 3, dent_y - 2), (28, 15), 0, 0, 360, (50, 52, 55), -1)
        elif defect_type == "scratch":
            sx1 = can_cx + random.randint(-40, 40)
            sy1 = can_cy + random.randint(-50, 50)
            sx2 = sx1 + random.randint(20, 60)
            sy2 = sy1 + random.randint(15, 45)
            cv2.line(img, (sx1, sy1), (sx2, sy2), (240, 240, 240), 2)
        elif defect_type == "corrosion":
            cx_cor = can_cx + random.randint(-25, 25)
            cy_cor = can_cy + random.randint(-30, 30)
            cv2.circle(img, (cx_cor, cy_cor), 18, (35, 55, 120), -1)  # Rust hue in BGR

        return img

    def capture_frame(self) -> Tuple[Optional[np.ndarray], Optional[FrameMetadata]]:
        if self.state not in (CameraState.CONNECTED, CameraState.STREAMING):
            return None, None

        # Simulate frame drop if configured
        if self.simulate_drops and random.random() < self.drop_rate:
            return None, None

        t0 = time.perf_counter_ns()

        # Simulate shutter & sensor exposure latency
        exposure_delay_s = (self.config.exposure_time_us / 1_000_000.0)
        jitter_s = random.uniform(0.0, self.config.synthetic_jitter_ms / 1000.0)
        time.sleep(min(exposure_delay_s + jitter_s, 0.05))

        if self.image_files:
            file_path = self.image_files[self.current_idx % len(self.image_files)]
            self.current_idx += 1
            raw_img = cv2.imread(file_path)
            if raw_img is not None:
                # Resize to target config dimensions
                frame = cv2.resize(raw_img, (self.config.width, self.config.height))
                if self.config.pixel_format.upper() == "RGB":
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                frame = self._generate_synthetic_can_image()
        else:
            frame = self._generate_synthetic_can_image()

        t1 = time.perf_counter_ns()
        acq_latency_ms = (t1 - t0) / 1_000_000.0

        self.frame_counter += 1
        self.last_capture_time_ns = t1
        self.state = CameraState.STREAMING

        h, w = frame.shape[:2]
        channels = 1 if len(frame.shape) == 2 else frame.shape[2]

        meta = FrameMetadata(
            frame_id=self.frame_counter,
            timestamp_ns=t1,
            acquisition_latency_ms=round(acq_latency_ms, 2),
            width=w,
            height=h,
            channels=channels,
            adapter_name="SyntheticCameraAdapter",
            exposure_time_us=self.config.exposure_time_us,
            gain_db=self.config.gain_db,
            is_simulated=True,
        )

        return frame, meta
