"""Camera acquisition and hardware abstraction package."""

from edge_inspector.camera.base import (
    AcquisitionConfig,
    BaseCameraAdapter,
    CameraState,
    FrameMetadata,
)
from edge_inspector.camera.factory import create_camera_adapter

__all__ = [
    "AcquisitionConfig",
    "BaseCameraAdapter",
    "CameraState",
    "FrameMetadata",
    "create_camera_adapter",
]
