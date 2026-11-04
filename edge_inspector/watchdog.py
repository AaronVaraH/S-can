"""System watchdog, thermal health monitor, and fail-safe recovery for edge deployment."""

from __future__ import annotations

import logging
import os
import shutil
import socket
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import psutil

from edge_inspector.hardware import get_cpu_temperature, get_throttling_status

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    is_healthy: bool
    state: str  # "OPERATIONAL", "DEGRADED", "EMERGENCY_FAILSAFE"
    cpu_usage_percent: float
    ram_usage_percent: float
    cpu_temperature_c: Optional[float]
    throttled: bool
    camera_connected: bool
    model_loaded: bool
    storage_healthy: bool
    disk_usage_percent: float
    active_alerts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EdgeWatchdog:
    """Monitors system vitals, thermals, storage, and interfaces with systemd watchdog."""

    def __init__(
        self,
        thermal_warning_c: float = 78.0,
        thermal_critical_c: float = 84.0,
        max_ram_percent: float = 85.0,
        heartbeat_interval_sec: float = 1.0,
    ) -> None:
        self.thermal_warning_c = thermal_warning_c
        self.thermal_critical_c = thermal_critical_c
        self.max_ram_percent = max_ram_percent
        self.heartbeat_interval_sec = heartbeat_interval_sec

        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.last_heartbeat_time = time.time()
        self.active_alerts: List[str] = []
        self.emergency_state = False

        # Component health callbacks
        self.camera_check_cb = lambda: True
        self.model_check_cb = lambda: True
        self.storage_check_cb = lambda: True

    def register_callbacks(self, camera_cb, model_cb, storage_cb) -> None:
        self.camera_check_cb = camera_cb
        self.model_check_cb = model_cb
        self.storage_check_cb = storage_cb

    def notify_systemd_watchdog(self) -> None:
        """Pings systemd watchdog socket if configured via NOTIFY_SOCKET."""
        notify_socket = os.environ.get("NOTIFY_SOCKET")
        if not notify_socket:
            return

        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            if notify_socket.startswith("@"):
                notify_socket = "\0" + notify_socket[1:]
            sock.sendto(b"WATCHDOG=1", notify_socket)
            sock.close()
        except Exception:
            pass

    def evaluate_health(self) -> HealthStatus:
        """Evaluates live health vitals of the edge device."""
        alerts: List[str] = []
        cpu_pct = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        ram_pct = ram.percent

        temp_c = get_cpu_temperature()
        throttling = get_throttling_status()

        if temp_c is not None:
            if temp_c >= self.thermal_critical_c:
                alerts.append(f"CRITICAL_CPU_TEMPERATURE ({temp_c}°C >= {self.thermal_critical_c}°C)")
            elif temp_c >= self.thermal_warning_c:
                alerts.append(f"HIGH_CPU_TEMPERATURE ({temp_c}°C >= {self.thermal_warning_c}°C)")

        if throttling.get("is_throttled", False):
            alerts.append("CPU_THROTTLED (frequency reduced due to heat or power)")
        if throttling.get("undervoltage_detected", False):
            alerts.append("UNDERVOLTAGE_DETECTED (insufficient power supply on Raspberry Pi)")

        if ram_pct >= self.max_ram_percent:
            alerts.append(f"RAM_USAGE_HIGH ({ram_pct}% >= {self.max_ram_percent}%)")

        # Check disk space on data partition
        disk_usage_pct = 50.0
        try:
            total, used, free = shutil.disk_usage(".")
            disk_usage_pct = round((used / total) * 100.0, 1)
            if disk_usage_pct >= 90.0:
                alerts.append(f"DISK_SPACE_CRITICAL ({disk_usage_pct}%)")
        except Exception:
            pass

        cam_ok = bool(self.camera_check_cb())
        if not cam_ok:
            alerts.append("CAMERA_DISCONNECTED")

        model_ok = bool(self.model_check_cb())
        if not model_ok:
            alerts.append("MODEL_UNAVAILABLE")

        storage_ok = bool(self.storage_check_cb())
        if not storage_ok:
            alerts.append("STORAGE_UNAVAILABLE")

        is_healthy = len(alerts) == 0
        state = "OPERATIONAL" if is_healthy else ("EMERGENCY_FAILSAFE" if not cam_ok or not model_ok else "DEGRADED")

        return HealthStatus(
            is_healthy=is_healthy,
            state=state,
            cpu_usage_percent=cpu_pct,
            ram_usage_percent=ram_pct,
            cpu_temperature_c=temp_c,
            throttled=throttling.get("is_throttled", False),
            camera_connected=cam_ok,
            model_loaded=model_ok,
            storage_healthy=storage_ok,
            disk_usage_percent=disk_usage_pct,
            active_alerts=alerts,
        )

    def start(self) -> None:
        """Starts watchdog background thread."""
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self.thread.start()
        logger.info("Watchdog monitor started.")

    def stop(self) -> None:
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

    def _watchdog_loop(self) -> None:
        while self.is_running:
            try:
                status = self.evaluate_health()
                self.active_alerts = status.active_alerts

                if status.state == "OPERATIONAL" or status.state == "DEGRADED":
                    self.notify_systemd_watchdog()

                self.last_heartbeat_time = time.time()
            except Exception as e:
                logger.error(f"Watchdog evaluation error: {str(e)}")

            time.sleep(self.heartbeat_interval_sec)
