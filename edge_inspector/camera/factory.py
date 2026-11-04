"""Camera factory supporting USB, Picamera2, and synthetic simulation cameras."""

from __future__ import annotations

from typing import Any, Dict

from edge_inspector.camera.base import AcquisitionConfig, BaseCameraAdapter
from edge_inspector.camera.picamera2_adapter import PiCamera2Adapter
from edge_inspector.camera.synthetic_camera import SyntheticCameraAdapter
from edge_inspector.camera.usb_camera import OpenCVUSBCameraAdapter


def create_camera_adapter(config_dict: Dict[str, Any]) -> BaseCameraAdapter:
    """Instantiates the appropriate camera adapter based on configuration."""
    adapter_type = config_dict.get("adapter", "synthetic").lower()

    acq_config = AcquisitionConfig(
        device_index=config_dict.get("device_index", 0),
        width=config_dict.get("width", 640),
        height=config_dict.get("height", 480),
        fps=config_dict.get("fps", 30),
        pixel_format=config_dict.get("pixel_format", "RGB"),
        auto_exposure=config_dict.get("auto_exposure", False),
        exposure_time_us=config_dict.get("exposure_time_us", 5000),
        gain_db=float(config_dict.get("gain_db", 6.0)),
        auto_white_balance=config_dict.get("auto_white_balance", False),
        reconnect_interval_sec=float(config_dict.get("reconnect_interval_sec", 2.0)),
        max_reconnect_attempts=int(config_dict.get("max_reconnect_attempts", 10)),
        synthetic_image_folder=config_dict.get("synthetic_image_folder"),
        synthetic_jitter_ms=float(config_dict.get("synthetic_jitter_ms", 5.0)),
    )

    if adapter_type == "usb":
        return OpenCVUSBCameraAdapter(acq_config)
    elif adapter_type in ("picamera2", "libcamera", "rpi_camera"):
        return PiCamera2Adapter(acq_config)
    elif adapter_type in ("synthetic", "simulation", "sim"):
        return SyntheticCameraAdapter(acq_config)
    else:
        # Default to synthetic if unrecognized
        return SyntheticCameraAdapter(acq_config)
