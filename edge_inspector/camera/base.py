"""Abstract camera adapter interface, frame metadata, and acquisition configurations."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Tuple

import numpy as np


class CameraState(str, Enum):
    INITIALIZING = "INITIALIZING"
    CONNECTED = "CONNECTED"
    STREAMING = "STREAMING"
    DISCONNECTED = "DISCONNECTED"
    RECONNECTING = "RECONNECTING"
    ERROR = "ERROR"


@dataclass
class AcquisitionConfig:
    """Configurable settings for camera hardware."""
    device_index: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30
    pixel_format: str = "RGB"  # "RGB", "BGR", "GRAY"
    auto_exposure: bool = False
    exposure_time_us: int = 5000  # 5000 microseconds (5 ms)
    gain_db: float = 6.0
    auto_white_balance: bool = False
    reconnect_interval_sec: float = 2.0
    max_reconnect_attempts: int = 10
    synthetic_image_folder: Optional[str] = None
    synthetic_jitter_ms: float = 5.0


@dataclass
class FrameMetadata:
    """Industrial metadata stamped on each captured frame."""
    frame_id: int
    timestamp_ns: int
    acquisition_latency_ms: float
    width: int
    height: int
    channels: int
    adapter_name: str
    exposure_time_us: Optional[int] = None
    gain_db: Optional[float] = None
    is_simulated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseCameraAdapter(ABC):
    """Abstract base class for industrial camera adapters."""

    def __init__(self, config: AcquisitionConfig) -> None:
        self.config = config
        self.state: CameraState = CameraState.INITIALIZING
        self.frame_counter: int = 0
        self.last_capture_time_ns: int = 0
        self.last_error_message: Optional[str] = None

    @abstractmethod
    def connect(self) -> bool:
        """Establishes connection to physical or virtual camera device."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Closes camera connection and releases hardware resources."""
        pass

    @abstractmethod
    def capture_frame(self) -> Tuple[Optional[np.ndarray], Optional[FrameMetadata]]:
        """Captures a single frame synchronously.

        Returns:
            (frame_array, metadata) or (None, None) on capture failure.
        """
        pass

    def is_connected(self) -> bool:
        return self.state in (CameraState.CONNECTED, CameraState.STREAMING)

    def trigger_software(self) -> bool:
        """Software trigger signal for snapshot mode."""
        return True

    def get_status(self) -> Dict[str, Any]:
        """Returns health and operational metrics."""
        return {
            "adapter": self.__class__.__name__,
            "state": self.state.value,
            "connected": self.is_connected(),
            "frame_counter": self.frame_counter,
            "last_error": self.last_error_message,
            "config": asdict(self.config),
        }
