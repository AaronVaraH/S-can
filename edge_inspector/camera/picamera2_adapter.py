"""Raspberry Pi Camera Module adapter using Picamera2 / Libcamera."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple

import numpy as np

from edge_inspector.camera.base import (
    AcquisitionConfig,
    BaseCameraAdapter,
    CameraState,
    FrameMetadata,
)

# Optional Picamera2 import
_PICAMERA2_AVAILABLE = False
try:
    from picamera2 import Picamera2  # type: ignore
    _PICAMERA2_AVAILABLE = True
except ImportError:
    Picamera2 = None  # type: ignore


class PiCamera2Adapter(BaseCameraAdapter):
    """Adapter for official Raspberry Pi Camera Module 2/3 / Global Shutter Camera."""

    def __init__(self, config: AcquisitionConfig) -> None:
        super().__init__(config)
        self.picam2: Optional[Any] = None
        self._available = _PICAMERA2_AVAILABLE

    def connect(self) -> bool:
        if not self._available:
            self.state = CameraState.ERROR
            self.last_error_message = (
                "picamera2 library is not installed. This adapter requires Raspberry Pi OS with "
                "python3-picamera2 or picamera2 installed via apt."
            )
            return False

        try:
            self.state = CameraState.INITIALIZING
            self.picam2 = Picamera2(camera_num=self.config.device_index)

            # Build video configuration
            video_config = self.picam2.create_video_configuration(
                main={
                    "size": (self.config.width, self.config.height),
                    "format": "RGB888" if self.config.pixel_format == "RGB" else "BGR888",
                },
                controls={
                    "FrameRate": float(self.config.fps),
                }
            )

            # Industrial manual exposure settings to eliminate lighting fluctuations
            controls_dict = {}
            if not self.config.auto_exposure:
                controls_dict["AeEnable"] = False
                controls_dict["ExposureTime"] = self.config.exposure_time_us
                controls_dict["AnalogueGain"] = max(1.0, float(self.config.gain_db))

            if not self.config.auto_white_balance:
                controls_dict["AwbEnable"] = False

            if controls_dict:
                self.picam2.set_controls(controls_dict)

            self.picam2.configure(video_config)
            self.picam2.start()

            self.state = CameraState.CONNECTED
            self.last_error_message = None
            return True

        except Exception as e:
            self.state = CameraState.ERROR
            self.last_error_message = f"Failed to initialize Picamera2: {str(e)}"
            return False

    def disconnect(self) -> None:
        if self.picam2 is not None:
            try:
                self.picam2.stop()
                self.picam2.close()
            except Exception:
                pass
            self.picam2 = None
        self.state = CameraState.DISCONNECTED

    def capture_frame(self) -> Tuple[Optional[np.ndarray], Optional[FrameMetadata]]:
        if self.picam2 is None or self.state not in (CameraState.CONNECTED, CameraState.STREAMING):
            return None, None

        t0 = time.perf_counter_ns()
        try:
            # Capture numpy array directly from camera buffer
            frame = self.picam2.capture_array("main")
            if frame is None or frame.size == 0:
                self.state = CameraState.DISCONNECTED
                self.last_error_message = "Picamera2 returned empty buffer."
                return None, None

            t1 = time.perf_counter_ns()
            acq_ms = (t1 - t0) / 1_000_000.0

            self.frame_counter += 1
            self.last_capture_time_ns = t1
            self.state = CameraState.STREAMING

            h, w = frame.shape[:2]
            channels = 1 if len(frame.shape) == 2 else frame.shape[2]

            meta = FrameMetadata(
                frame_id=self.frame_counter,
                timestamp_ns=t1,
                acquisition_latency_ms=round(acq_ms, 2),
                width=w,
                height=h,
                channels=channels,
                adapter_name="PiCamera2Adapter",
                exposure_time_us=self.config.exposure_time_us,
                gain_db=self.config.gain_db,
                is_simulated=False,
            )
            return frame, meta

        except Exception as e:
            self.state = CameraState.ERROR
            self.last_error_message = f"Picamera2 capture error: {str(e)}"
            return None, None
