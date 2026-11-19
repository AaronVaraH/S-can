"""Hardware detection, capability profiling, and accelerator discovery for Raspberry Pi edge deployment."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil


@dataclass
class HardwareProfile:
    """Represents a validated edge hardware profile."""
    name: str
    cpu_architecture: str
    cores: int
    cpu_model: str
    typical_clock_ghz: float
    max_model_ram_mb: float
    recommended_threads: int
    supported_accelerators: List[str] = field(default_factory=list)
    target_inference_fps: float = 10.0
    max_acceptable_latency_ms: float = 100.0
    thermal_throttle_temp_c: float = 80.0


@dataclass
class HardwareInfo:
    """Runtime hardware snapshot detected on the edge device."""
    is_raspberry_pi: bool
    rpi_model: str
    rpi_revision: Optional[str]
    cpu_architecture: str
    cpu_cores: int
    cpu_freq_mhz: Optional[float]
    total_ram_mb: float
    available_ram_mb: float
    os_name: str
    os_release: str
    is_64bit: bool
    cuda_available: bool
    accelerators_found: List[str]
    arm_neon_supported: bool
    cpu_temperature_c: Optional[float]
    throttling_status: Dict[str, Any]
    detected_profile_name: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Revision code mapping for common Raspberry Pi boards
# Format based on Raspberry Pi Foundation documentation
RPI_REVISION_MAP = {
    "a02082": "Raspberry Pi 3 Model B (1GB)",
    "a22082": "Raspberry Pi 3 Model B (1GB)",
    "a020d3": "Raspberry Pi 3 Model B+ (1GB)",
    "902120": "Raspberry Pi Zero 2 W (512MB)",
    "a03111": "Raspberry Pi 4 Model B (1GB)",
    "b03111": "Raspberry Pi 4 Model B (2GB)",
    "b03112": "Raspberry Pi 4 Model B (2GB)",
    "b03114": "Raspberry Pi 4 Model B (2GB)",
    "b03115": "Raspberry Pi 4 Model B (2GB)",
    "c03111": "Raspberry Pi 4 Model B (4GB)",
    "c03112": "Raspberry Pi 4 Model B (4GB)",
    "c03114": "Raspberry Pi 4 Model B (4GB)",
    "c03115": "Raspberry Pi 4 Model B (4GB)",
    "d03114": "Raspberry Pi 4 Model B (8GB)",
    "d03115": "Raspberry Pi 4 Model B (8GB)",
    "a03140": "Raspberry Pi Compute Module 4 (1GB)",
    "b03140": "Raspberry Pi Compute Module 4 (2GB)",
    "c03140": "Raspberry Pi Compute Module 4 (4GB)",
    "d03140": "Raspberry Pi Compute Module 4 (8GB)",
    "c04170": "Raspberry Pi 5 (4GB)",
    "d04170": "Raspberry Pi 5 (8GB)",
    "d04171": "Raspberry Pi 5 (8GB)",
    "e04171": "Raspberry Pi 5 (16GB)",
}


def read_file_safe(path: str) -> Optional[str]:
    """Safely reads file content if it exists."""
    p = Path(path)
    if p.exists() and p.is_file():
        try:
            return p.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception:
            return None
    return None


def detect_raspberry_pi() -> Tuple[bool, str, Optional[str]]:
    """Detects if running on a Raspberry Pi and extracts model & revision."""
    model_str = ""
    revision = None
    is_rpi = False

    # Check /proc/device-tree/model first (canonical on Pi OS)
    dt_model = read_file_safe("/proc/device-tree/model")
    if dt_model and "Raspberry Pi" in dt_model:
        is_rpi = True
        model_str = dt_model.replace("\x00", "").strip()

    # Read /proc/cpuinfo for revision code
    cpuinfo = read_file_safe("/proc/cpuinfo")
    if cpuinfo:
        for line in cpuinfo.splitlines():
            line_clean = line.strip()
            if line_clean.startswith("Revision"):
                parts = line_clean.split(":")
                if len(parts) >= 2:
                    revision = parts[1].strip().lower()
                    if revision in RPI_REVISION_MAP:
                        is_rpi = True
                        if not model_str:
                            model_str = RPI_REVISION_MAP[revision]
            elif line_clean.startswith("Model") and not model_str:
                parts = line_clean.split(":")
                if len(parts) >= 2 and "Raspberry Pi" in parts[1]:
                    is_rpi = True
                    model_str = parts[1].strip()

    if not is_rpi:
        # Check fallback sys info or environment
        if "raspberrypi" in platform.uname().node.lower():
            is_rpi = True
            model_str = "Raspberry Pi (Generic)"
        else:
            model_str = "Standard Host / Non-Pi"

    return is_rpi, model_str, revision


def detect_accelerators() -> List[str]:
    """Detects available edge AI accelerators without raising exceptions."""
    accelerators: List[str] = []

    # 1. Raspberry Pi AI HAT+ (Hailo-8 / Hailo-8L)
    if Path("/dev/hailo0").exists():
        # Check Hailo model via sysfs or hailortcli if available
        accelerators.append("hailo8")
    else:
        # Check if hailort library is available
        try:
            import hailort  # type: ignore # noqa: F401
            accelerators.append("hailo_runtime_ready")
        except ImportError:
            pass

    # 2. Google Coral EdgeTPU (PCIe or USB)
    if Path("/dev/apex_0").exists():
        accelerators.append("coral_edgetpu_pcie")
    else:
        # Check for USB Coral
        try:
            from pycoral.utils import edgetpu  # type: ignore # noqa: F401
            accelerators.append("coral_edgetpu_runtime_ready")
        except ImportError:
            pass

    # 3. Intel Neural Compute Stick 2 (Myriad X)
    try:
        import openvino  # type: ignore # noqa: F401
        accelerators.append("openvino_ready")
    except ImportError:
        pass

    return accelerators


def check_arm_neon() -> bool:
    """Checks if CPU supports ARM NEON vector instructions for fast math."""
    arch = platform.machine().lower()
    if arch in ("aarch64", "arm64"):
        return True  # AArch64 mandates ASIMD / NEON
    if "arm" in arch:
        cpuinfo = read_file_safe("/proc/cpuinfo")
        if cpuinfo and ("neon" in cpuinfo.lower() or "asimd" in cpuinfo.lower()):
            return True
    return False


def get_cpu_temperature() -> Optional[float]:
    """Reads Raspberry Pi CPU temperature in Celsius."""
    # Method 1: vcgencmd (Raspberry Pi official utility)
    vcgencmd = shutil.which("vcgencmd")
    if vcgencmd:
        try:
            out = subprocess.check_output([vcgencmd, "measure_temp"], timeout=1.0).decode("utf-8")
            match = re.search(r"temp=([\d\.]+)'C", out)
            if match:
                return float(match.group(1))
        except Exception:
            pass

    # Method 2: sysfs thermal zone
    temp_str = read_file_safe("/sys/class/thermal/thermal_zone0/temp")
    if temp_str:
        try:
            # sysfs returns milliCelsius
            val = float(temp_str)
            if val > 1000:
                return round(val / 1000.0, 1)
            return round(val, 1)
        except ValueError:
            pass

    return None


def get_throttling_status() -> Dict[str, Any]:
    """Decodes Raspberry Pi throttling status flags from vcgencmd."""
    status = {
        "is_throttled": False,
        "undervoltage_detected": False,
        "arm_frequency_capped": False,
        "soft_temp_limit_reached": False,
        "raw_code": "0x0",
    }

    vcgencmd = shutil.which("vcgencmd")
    if not vcgencmd:
        return status

    try:
        out = subprocess.check_output([vcgencmd, "get_throttled"], timeout=1.0).decode("utf-8").strip()
        parts = out.split("=")
        if len(parts) == 2:
            raw_hex = parts[1].strip()
            status["raw_code"] = raw_hex
            val = int(raw_hex, 16)
            # Bitmask definitions from Raspberry Pi documentation
            status["undervoltage_detected"] = bool(val & 0x1)
            status["arm_frequency_capped"] = bool(val & 0x2)
            status["is_throttled"] = bool(val & 0x4)
            status["soft_temp_limit_reached"] = bool(val & 0x8)
    except Exception:
        pass

    return status


def detect_hardware(override_profile: Optional[str] = None) -> HardwareInfo:
    """Probes the physical machine and constructs a complete HardwareInfo snapshot.

    Never assumes CUDA is available on Raspberry Pi.
    """
    is_rpi, rpi_model, revision = detect_raspberry_pi()

    # Never assume CUDA on a Raspberry Pi
    cuda_available = False
    if not is_rpi:
        # Check safely without importing heavy frameworks
        try:
            import torch  # type: ignore
            cuda_available = bool(torch.cuda.is_available())
        except Exception:
            cuda_available = False

    mem = psutil.virtual_memory()
    total_ram_mb = round(mem.total / (1024 * 1024), 1)
    avail_ram_mb = round(mem.available / (1024 * 1024), 1)

    cpu_freq = psutil.cpu_freq()
    freq_mhz = cpu_freq.current if cpu_freq else None

    neon_supported = check_arm_neon()
    accelerators = detect_accelerators()
    temp_c = get_cpu_temperature()
    throttling = get_throttling_status()

    # Determine matched profile name
    profile_name = "generic_fallback"
    if override_profile:
        profile_name = override_profile
    elif is_rpi:
        rpi_lower = rpi_model.lower()
        if "pi 5" in rpi_lower:
            profile_name = "rpi_5"
        elif "compute module 4" in rpi_lower or "cm4" in rpi_lower:
            profile_name = "rpi_cm4"
        elif "pi 4" in rpi_lower:
            profile_name = "rpi_4b"
        elif "zero 2" in rpi_lower:
            profile_name = "rpi_zero_2w"
        elif "pi 3" in rpi_lower:
            profile_name = "rpi_3b_plus"

    return HardwareInfo(
        is_raspberry_pi=is_rpi,
        rpi_model=rpi_model,
        rpi_revision=revision,
        cpu_architecture=platform.machine(),
        cpu_cores=psutil.cpu_count(logical=True) or 4,
        cpu_freq_mhz=freq_mhz,
        total_ram_mb=total_ram_mb,
        available_ram_mb=avail_ram_mb,
        os_name=platform.system(),
        os_release=platform.release(),
        is_64bit=sys.maxsize > 2**32,
        cuda_available=cuda_available,
        accelerators_found=accelerators,
        arm_neon_supported=neon_supported,
        cpu_temperature_c=temp_c,
        throttling_status=throttling,
        detected_profile_name=profile_name,
    )


def estimate_hardware_capacity(
    hardware: HardwareInfo,
    model_ram_mb: float = 65.0,
    input_shape: Tuple[int, int, int] = (3, 320, 320),
    max_fps_required: float = 15.0,
) -> Dict[str, Any]:
    """Estimates memory headroom, inference feasibility, and system overhead before loading a model."""
    channels, height, width = input_shape
    raw_frame_mb = (height * width * channels * 4) / (1024 * 1024)  # Float32 buffer
    image_pipeline_buffers_mb = raw_frame_mb * 4  # Preprocessed, annotated, display, queue

    required_working_mem_mb = model_ram_mb + image_pipeline_buffers_mb + 120.0  # OS + service base

    headroom_mb = hardware.available_ram_mb - required_working_mem_mb
    is_memory_sufficient = headroom_mb > 50.0  # Safe 50MB reserve

    # Baseline latency estimate by architecture
    base_latency_ms = 85.0
    if hardware.detected_profile_name == "rpi_5":
        base_latency_ms = 35.0
    elif hardware.detected_profile_name == "rpi_4b":
        base_latency_ms = 95.0
    elif hardware.detected_profile_name == "rpi_3b_plus":
        base_latency_ms = 220.0
    elif hardware.detected_profile_name == "rpi_zero_2w":
        base_latency_ms = 350.0

    if "hailo8" in hardware.accelerators_found:
        base_latency_ms = min(base_latency_ms, 8.0)
    elif "coral_edgetpu" in hardware.accelerators_found:
        base_latency_ms = min(base_latency_ms, 12.0)

    estimated_fps = round(1000.0 / max(base_latency_ms, 1.0), 1)
    meets_fps_target = estimated_fps >= max_fps_required

    return {
        "hardware_profile": hardware.detected_profile_name,
        "available_ram_mb": hardware.available_ram_mb,
        "model_ram_mb": model_ram_mb,
        "pipeline_buffer_mb": round(image_pipeline_buffers_mb, 2),
        "estimated_working_ram_mb": round(required_working_mem_mb, 2),
        "ram_headroom_mb": round(headroom_mb, 2),
        "is_memory_sufficient": is_memory_sufficient,
        "estimated_latency_ms": base_latency_ms,
        "estimated_sustained_fps": estimated_fps,
        "target_fps": max_fps_required,
        "meets_target_throughput": meets_fps_target,
        "cpu_fallback_viable": True,
        "recommended_intra_threads": min(hardware.cpu_cores, 4),
    }


def verify_runtime_compatibility(runtime: str, hardware: HardwareInfo) -> Tuple[bool, str]:
    """Validates whether the chosen runtime is compatible with this physical device."""
    rt_lower = runtime.lower()

    if rt_lower in ("cuda", "tensorrt"):
        if hardware.is_raspberry_pi:
            return False, "CUDA/TensorRT is NOT available on Raspberry Pi hardware."
        if not hardware.cuda_available:
            return False, "CUDA runtime requested but no supported NVIDIA GPU was detected."

    if rt_lower == "onnx":
        try:
            import onnxruntime  # noqa: F401
            return True, f"ONNX Runtime available (v{onnxruntime.__version__}). CPUExecutionProvider supported."
        except ImportError:
            return False, "onnxruntime is not installed. Install via pip or wheels for your architecture."

    if rt_lower == "tflite":
        try:
            import tflite_runtime  # noqa: F401
            return True, "tflite_runtime available."
        except ImportError:
            try:
                import tensorflow.lite  # noqa: F401
                return True, "tensorflow.lite available."
            except ImportError:
                return False, "Neither tflite_runtime nor tensorflow is installed."

    if rt_lower == "hailo":
        if "hailo8" not in hardware.accelerators_found:
            return False, "Raspberry Pi AI HAT+ / Hailo device not found in /dev/hailo0."
        return True, "Hailo-8/8L hardware accelerator detected and ready."

    if rt_lower == "simulation":
        return True, "Simulation runtime is always supported."

    return True, f"Runtime '{runtime}' accepted."
