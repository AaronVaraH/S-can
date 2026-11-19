"""Production-line reject actuation interface with safety interlocks, timing gates, and hardware isolation."""

from __future__ import annotations

import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from edge_inspector.decision import DecisionResult, InspectionDecision

logger = logging.getLogger(__name__)


@dataclass
class ActuatorConfig:
    """Configurable reject valve and production interface parameters."""
    adapter: str = "simulation"  # "simulation", "gpio", "modbus_plc"
    gpio_pin: int = 17
    active_high: bool = True
    pulse_duration_ms: int = 45   # Solenoid blast pulse width
    conveyor_delay_ms: int = 180  # Conveyor transit delay between camera and reject nozzle
    deadline_tolerance_ms: int = 35 # Reject window tolerance window
    interlock_enabled: bool = True
    modbus_host: str = "192.168.1.100"
    modbus_port: int = 502
    modbus_coil_address: int = 1


class BaseRejectActuator(ABC):
    """Abstract reject actuator with safety interlock guards."""

    def __init__(self, config: ActuatorConfig) -> None:
        self.config = config
        self.interlock_active: bool = False
        self.total_actuations: int = 0
        self.total_blocked_interlock: int = 0
        self.total_timing_faults: int = 0
        self.last_actuation_time: float = 0.0

    def engage_safety_interlock(self, reason: str = "MANUAL_INTERLOCK") -> None:
        """Emergency hardware interlock: prevents all physical reject actuation."""
        self.interlock_active = True
        logger.warning(f"SAFETY INTERLOCK ENGAGED: {reason}")

    def release_safety_interlock(self) -> None:
        """Releases safety interlock after verification."""
        self.interlock_active = False
        logger.info("SAFETY INTERLOCK RELEASED")

    def validate_actuation_safety(
        self,
        decision: DecisionResult,
        frame_timestamp_ns: int,
    ) -> Tuple[bool, str]:
        """Strict interlock gate: Never fire solenoid unless all conditions pass."""
        if self.interlock_active:
            self.total_blocked_interlock += 1
            return False, "BLOCKED_BY_SAFETY_INTERLOCK"

        if not decision.actuate_reject or decision.decision != InspectionDecision.FAIL:
            return False, "DECISION_IS_NOT_CONFIRMED_FAIL"

        # Check conveyor timing synchronization
        now_ns = time.perf_counter_ns()
        elapsed_ms = (now_ns - frame_timestamp_ns) / 1_000_000.0

        # Max allowed processing time before the target can moves past the reject nozzle
        max_allowed_elapsed_ms = self.config.conveyor_delay_ms + self.config.deadline_tolerance_ms

        if elapsed_ms > max_allowed_elapsed_ms:
            self.total_timing_faults += 1
            return False, f"TIMING_FAULT: Processing took {elapsed_ms:.1f}ms > limit {max_allowed_elapsed_ms}ms. Solenoid aborted to prevent striking adjacent can."

        return True, "SAFETY_CHECKS_PASSED"

    @abstractmethod
    def trigger_reject(
        self,
        decision: DecisionResult,
        frame_timestamp_ns: int,
    ) -> Dict[str, Any]:
        """Fires reject solenoid after safety verification and delay compensation."""
        pass

    @abstractmethod
    def test_pulse(self) -> bool:
        """Manual maintenance test pulse."""
        pass

    def get_status(self) -> Dict[str, Any]:
        return {
            "adapter": self.__class__.__name__,
            "interlock_active": self.interlock_active,
            "total_actuations": self.total_actuations,
            "total_blocked_interlock": self.total_blocked_interlock,
            "total_timing_faults": self.total_timing_faults,
            "last_actuation_time": self.last_actuation_time,
            "config": asdict(self.config),
        }


class SimulationRejectActuator(BaseRejectActuator):
    """Safe software actuator for unit testing and offline development."""

    def trigger_reject(
        self,
        decision: DecisionResult,
        frame_timestamp_ns: int,
    ) -> Dict[str, Any]:
        safe, reason = self.validate_actuation_safety(decision, frame_timestamp_ns)
        if not safe:
            return {"actuated": False, "reason": reason}

        self.total_actuations += 1
        self.last_actuation_time = time.time()
        logger.info(f"[SIMULATION REJECT] Solenoid pulsed for {self.config.pulse_duration_ms}ms (Defects: {decision.critical_defects})")
        return {
            "actuated": True,
            "reason": "SIMULATED_REJECT_FIRED",
            "pulse_ms": self.config.pulse_duration_ms,
        }

    def test_pulse(self) -> bool:
        if self.interlock_active:
            return False
        self.total_actuations += 1
        return True


class GPIORejectActuator(BaseRejectActuator):
    """Raspberry Pi GPIO reject actuator driving pneumatic solenoid valve via optocoupled relay."""

    def __init__(self, config: ActuatorConfig) -> None:
        super().__init__(config)
        self.gpio_available = False
        self._setup_gpio()

    def _setup_gpio(self) -> None:
        # Try gpiod first (standard on Raspberry Pi OS Bookworm)
        try:
            import gpiod  # type: ignore
            chip = gpiod.Chip("gpiochip4") if gpiod.__version__.startswith("1.") else gpiod.Chip("/dev/gpiochip4")
            self.gpio_available = True
            logger.info(f"Initialized gpiod on pin {self.config.gpio_pin}")
        except Exception:
            # Try RPi.GPIO fallback
            try:
                import RPi.GPIO as GPIO  # type: ignore
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.config.gpio_pin, GPIO.OUT, initial=GPIO.LOW)
                self.gpio_available = True
                logger.info(f"Initialized RPi.GPIO on BCM pin {self.config.gpio_pin}")
            except Exception:
                self.gpio_available = False
                logger.warning("No native GPIO library available. Falling back to safe simulation mode.")

    def trigger_reject(
        self,
        decision: DecisionResult,
        frame_timestamp_ns: int,
    ) -> Dict[str, Any]:
        safe, reason = self.validate_actuation_safety(decision, frame_timestamp_ns)
        if not safe:
            return {"actuated": False, "reason": reason}

        # Calculate transit delay until can arrives at nozzle
        now_ns = time.perf_counter_ns()
        elapsed_ms = (now_ns - frame_timestamp_ns) / 1_000_000.0
        remaining_delay_ms = max(0.0, self.config.conveyor_delay_ms - elapsed_ms)

        # Dispatch async pulse thread to prevent blocking vision pipeline
        threading.Thread(
            target=self._execute_pulse_worker,
            args=(remaining_delay_ms / 1000.0, self.config.pulse_duration_ms / 1000.0),
            daemon=True,
        ).start()

        self.total_actuations += 1
        self.last_actuation_time = time.time()
        return {
            "actuated": True,
            "reason": "GPIO_REJECT_SCHEDULED",
            "remaining_delay_ms": round(remaining_delay_ms, 1),
            "pulse_ms": self.config.pulse_duration_ms,
        }

    def _execute_pulse_worker(self, delay_s: float, duration_s: float) -> None:
        """Waits for conveyor travel, then energizes pneumatic solenoid valve."""
        if delay_s > 0:
            time.sleep(delay_s)

        if self.interlock_active:
            logger.warning("Solenoid pulse aborted: Interlock engaged during conveyor transit.")
            return

        try:
            if self.gpio_available:
                import RPi.GPIO as GPIO  # type: ignore
                active_val = GPIO.HIGH if self.config.active_high else GPIO.LOW
                inactive_val = GPIO.LOW if self.config.active_high else GPIO.HIGH
                GPIO.output(self.config.gpio_pin, active_val)
                time.sleep(duration_s)
                GPIO.output(self.config.gpio_pin, inactive_val)
            else:
                time.sleep(duration_s)
        except Exception as e:
            logger.error(f"GPIO actuation failure: {str(e)}")

    def test_pulse(self) -> bool:
        if self.interlock_active:
            return False
        threading.Thread(
            target=self._execute_pulse_worker,
            args=(0.0, self.config.pulse_duration_ms / 1000.0),
            daemon=True,
        ).start()
        self.total_actuations += 1
        return True


def create_reject_actuator(config_dict: Dict[str, Any]) -> BaseRejectActuator:
    """Instantiates the appropriate reject actuator based on configuration."""
    cfg = ActuatorConfig(
        adapter=config_dict.get("adapter", "simulation"),
        gpio_pin=config_dict.get("gpio_pin", 17),
        active_high=config_dict.get("active_high", True),
        pulse_duration_ms=config_dict.get("pulse_duration_ms", 45),
        conveyor_delay_ms=config_dict.get("conveyor_delay_ms", 180),
        deadline_tolerance_ms=config_dict.get("deadline_tolerance_ms", 35),
        interlock_enabled=config_dict.get("interlock_enabled", True),
        modbus_host=config_dict.get("modbus_host", "192.168.1.100"),
        modbus_port=config_dict.get("modbus_port", 502),
        modbus_coil_address=config_dict.get("modbus_coil_address", 1),
    )

    if cfg.adapter == "gpio":
        return GPIORejectActuator(cfg)
    return SimulationRejectActuator(cfg)
