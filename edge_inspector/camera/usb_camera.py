"""USB camera adapter using OpenCV with robust reconnect logic for Raspberry Pi."""

from __future__ import annotations

import platform
import time
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

from edge_inspector.camera.base import (
    AcquisitionConfig,
    BaseCameraAdapter,
    CameraState,
    FrameMetadata,
)


class OpenCVUSBCameraAdapter(BaseCameraAdapter):
    """Production USB camera adapter for V4L2 (Linux) and DirectShow (Windows)."""

    def __init__(self, config: AcquisitionConfig) -> None:
        super().__init__(config)
        self.cap: Optional[cv2.VideoCapture] = None
        self.consecutive_failures: int = 0
        self.last_reconnect_attempt: float = 0.0

    def connect(self) -> bool:
        """Opens camera handle and configures acquisition parameters."""
        self.state = CameraState.INITIALIZING
        backend = cv2.CAP_V4L2 if platform.system() == "Linux" else cv2.CAP_ANY

        try:
            self.cap = cv2.VideoCapture(self.config.device_index, backend)
            if not self.cap.isOpened():
                self.state = CameraState.DISCONNECTED
                self.last_error_message = f"Cannot open USB camera device index {self.config.device_index}"
                return False

            # Configure resolution and FPS
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)

            # Configure manual exposure if requested (reduces motion blur on high-speed conveyor)
            if not self.config.auto_exposure:
                # In OpenCV V4L2, 1 = manual mode, 3 = auto mode
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
                # Shutter time mapping varies by driver; set if supported
                if self.config.exposure_time_us > 0:
                    self.cap.set(cv2.CAP_PROP_EXPOSURE, self.config.exposure_time_us / 1000.0)

            if self.config.gain_db > 0:
                self.cap.set(cv2.CAP_PROP_GAIN, self.config.gain_db)

            self.state = CameraState.CONNECTED
            self.consecutive_failures = 0
            self.last_error_message = None
            return True

        except Exception as e:
            self.state = CameraState.ERROR
            self.last_error_message = f"Exception opening camera: {str(e)}"
            return False

    def disconnect(self) -> None:
        """Releases video capture resource."""
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        self.state = CameraState.DISCONNECTED

    def _attempt_reconnect(self) -> bool:
        """Safely attempts camera reconnection with rate limiting."""
        now = time.time()
        if now - self.last_reconnect_attempt < self.config.reconnect_interval_sec:
            return False

        self.last_reconnect_attempt = now
        self.state = CameraState.RECONNECTING
        self.disconnect()
        success = self.connect()
        return success

    def capture_frame(self) -> Tuple[Optional[np.ndarray], Optional[FrameMetadata]]:
        """Grabs a frame with automatic recovery on disconnection."""
        if self.cap is None or not self.cap.isOpened():
            if not self._attempt_reconnect():
                return None, None

        t0 = time.perf_counter_ns()
        try:
            ret, frame = self.cap.read()
            if not ret or frame is None or frame.size == 0:
                self.consecutive_failures += 1
                if self.consecutive_failures >= 3:
                    self.state = CameraState.DISCONNECTED
                    self.last_error_message = "Camera read failed 3 consecutive times. Device likely disconnected."
                    self._attempt_reconnect()
                return None, None

            # Frame read succeeded
            self.consecutive_failures = 0
            self.state = CameraState.STREAMING
            t1 = time.perf_counter_ns()
            acq_latency_ms = (t1 - t0) / 1_000_000.0

            self.frame_counter += 1
            self.last_capture_time_ns = t1

            # Format conversion
            if self.config.pixel_format.upper() == "RGB":
                frame_out = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            elif self.config.pixel_format.upper() == "GRAY":
                frame_out = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                frame_out = frame

            h, w = frame_out.shape[:2]
            channels = 1 if len(frame_out.shape) == 2 else frame_out.shape[2]

            meta = FrameMetadata(
                frame_id=self.frame_counter,
                timestamp_ns=t1,
                acquisition_latency_ms=round(acq_latency_ms, 2),
                width=w,
                height=h,
                channels=channels,
                adapter_name="OpenCVUSBCameraAdapter",
                exposure_time_us=self.config.exposure_time_us,
                gain_db=self.config.gain_db,
                is_simulated=False,
            )
            return frame_out, meta

        except Exception as e:
            self.state = CameraState.ERROR
            self.last_error_message = f"Capture exception: {str(e)}"
            self.consecutive_failures += 1
            return None, None
