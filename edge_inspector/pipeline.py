"""Real-time inspection pipeline coordinator with bounded queue, memory guard, and overload handling."""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import psutil

from edge_inspector.actuator import BaseRejectActuator
from edge_inspector.camera.base import BaseCameraAdapter, FrameMetadata
from edge_inspector.decision import (
    DecisionResult,
    DecisionRuleConfig,
    InspectionDecision,
    evaluate_inspection,
)
from edge_inspector.inference.base import BaseInferenceEngine, InferenceResult
from edge_inspector.quality import (
    QualityCheckResult,
    QualityGateConfig,
    letterbox_preprocess,
    validate_image_quality,
)
from edge_inspector.storage import InspectionRecord, StorageManager

logger = logging.getLogger(__name__)


@dataclass
class QueuedInspectionItem:
    frame_id: int
    timestamp_ns: int
    image: np.ndarray
    source: str
    metadata: Optional[FrameMetadata] = None


class InspectionPipeline:
    """Coordinates the 8-step industrial inspection pipeline with strict memory and deadline bounds."""

    def __init__(
        self,
        camera: BaseCameraAdapter,
        inference_engine: BaseInferenceEngine,
        actuator: BaseRejectActuator,
        storage: StorageManager,
        quality_config: Optional[QualityGateConfig] = None,
        decision_config: Optional[DecisionRuleConfig] = None,
        queue_max_size: int = 10,
        overload_policy: str = "DROP_OLDEST",
        memory_guard_limit_mb: float = 450.0,
        inference_timeout_ms: float = 120.0,
    ) -> None:
        self.camera = camera
        self.inference_engine = inference_engine
        self.actuator = actuator
        self.storage = storage
        self.quality_config = quality_config or QualityGateConfig()
        self.decision_config = decision_config or DecisionRuleConfig()
        self.queue_max_size = queue_max_size
        self.overload_policy = overload_policy.upper()
        self.memory_guard_limit_mb = memory_guard_limit_mb
        self.inference_timeout_ms = inference_timeout_ms

        self.processing_queue: queue.Queue[QueuedInspectionItem] = queue.Queue(maxsize=queue_max_size)
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.camera_loop_thread: Optional[threading.Thread] = None

        # Statistics
        self.total_processed: int = 0
        self.pass_count: int = 0
        self.fail_count: int = 0
        self.review_count: int = 0
        self.dropped_count: int = 0
        self.last_latency_ms: float = 0.0
        self.latency_samples: List[float] = []

    def check_memory_guard(self) -> Tuple[bool, float]:
        """Ensures process RSS memory does not exceed edge memory limits."""
        process = psutil.Process()
        rss_mb = process.memory_info().rss / (1024 * 1024)
        is_safe = rss_mb < self.memory_guard_limit_mb
        return is_safe, round(rss_mb, 1)

    def enqueue_image(
        self,
        image: np.ndarray,
        source: str = "upload",
        frame_id: Optional[int] = None,
        timestamp_ns: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """Thread-safe enqueueing with memory guard and graceful overload handling."""
        is_mem_safe, current_rss_mb = self.check_memory_guard()
        if not is_mem_safe:
            self.dropped_count += 1
            logger.warning(f"Memory guard active ({current_rss_mb} MB > {self.memory_guard_limit_mb} MB). Dropping frame to prevent OOM.")
            return False, f"DROPPED_MEMORY_GUARD_LIMIT ({current_rss_mb} MB)"

        f_id = frame_id if frame_id is not None else self.total_processed + self.processing_queue.qsize() + 1
        ts = timestamp_ns if timestamp_ns is not None else time.perf_counter_ns()
        item = QueuedInspectionItem(frame_id=f_id, timestamp_ns=ts, image=image, source=source)

        try:
            self.processing_queue.put_nowait(item)
            return True, "ENQUEUED"
        except queue.Full:
            if self.overload_policy == "DROP_OLDEST":
                try:
                    # Drop oldest uninspected frame to preserve real-time recency
                    _ = self.processing_queue.get_nowait()
                    self.dropped_count += 1
                    self.processing_queue.put_nowait(item)
                    return True, "ENQUEUED_AFTER_DROP_OLDEST"
                except queue.Empty:
                    return False, "QUEUE_OVERLOAD"
            else:
                self.dropped_count += 1
                return False, "REJECTED_QUEUE_OVERFLOW"

    def process_frame(self, item: QueuedInspectionItem) -> Dict[str, Any]:
        """Executes the full 8-step industrial inspection pipeline synchronously on a frame."""
        t_start = time.perf_counter_ns()

        # Step 1: Image Quality Assessment & Validation Gate
        quality_res = validate_image_quality(item.image, self.quality_config)

        inference_res: Optional[InferenceResult] = None
        deadline_exceeded = False

        if quality_res.is_valid and quality_res.passed_quality_gate:
            # Step 2: Defect-preserving preprocessing
            tensor, meta = letterbox_preprocess(item.image, (320, 320))

            # Step 3: Forward inference
            t_inf_start = time.perf_counter_ns()
            try:
                inference_res = self.inference_engine.infer(tensor, meta)
            except Exception as e:
                logger.error(f"Inference execution failure on frame {item.frame_id}: {str(e)}")
                inference_res = None

            t_inf_end = time.perf_counter_ns()
            inf_duration_ms = (t_inf_end - t_inf_start) / 1_000_000.0
            if inf_duration_ms > self.inference_timeout_ms:
                deadline_exceeded = True
                logger.warning(f"Inference deadline exceeded on frame {item.frame_id}: {inf_duration_ms:.1f}ms > {self.inference_timeout_ms}ms")

        # Step 4: Apply Configurable Industrial PASS / FAIL / REVIEW rules
        decision_res = evaluate_inspection(
            quality=quality_res,
            inference=inference_res,
            config=self.decision_config,
            deadline_exceeded=deadline_exceeded,
        )

        # Step 5: Actuation Interface with Hardware Interlock & Timing Check
        actuator_res = self.actuator.trigger_reject(decision_res, item.timestamp_ns)

        t_end = time.perf_counter_ns()
        total_latency_ms = (t_end - item.timestamp_ns) / 1_000_000.0

        # Step 6: Local SQLite Storage & Annotated Image Retention
        record = self.storage.save_inspection(
            frame_id=item.frame_id,
            raw_image=item.image,
            quality=quality_res,
            inference=inference_res,
            decision=decision_res,
            total_latency_ms=total_latency_ms,
        )

        # Update Metrics
        self.total_processed += 1
        self.last_latency_ms = round(total_latency_ms, 2)
        if len(self.latency_samples) >= 500:
            self.latency_samples.pop(0)
        self.latency_samples.append(self.last_latency_ms)

        if decision_res.decision == InspectionDecision.PASS:
            self.pass_count += 1
        elif decision_res.decision == InspectionDecision.FAIL:
            self.fail_count += 1
        else:
            self.review_count += 1

        return {
            "inspection_id": record.inspection_id,
            "frame_id": item.frame_id,
            "decision": decision_res.decision.value,
            "primary_reason": decision_res.primary_reason,
            "confidence": decision_res.confidence_score,
            "uncertainty": decision_res.uncertainty_score,
            "quality": quality_res.to_dict(),
            "inference": inference_res.to_dict() if inference_res else None,
            "actuator": actuator_res,
            "image_path": record.image_path,
            "total_latency_ms": round(total_latency_ms, 2),
            "inference_latency_ms": inference_res.inference_latency_ms if inference_res else 0.0,
        }

    def start(self) -> None:
        """Starts worker thread for queue processing without blocking caller."""
        if self.is_running:
            return
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Inspection pipeline worker started.")

    def stop(self) -> None:
        """Stops pipeline cleanly."""
        self.is_running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2.0)
        logger.info("Inspection pipeline stopped.")

    def _worker_loop(self) -> None:
        """Continuous worker taking frames from the bounded queue."""
        while self.is_running:
            try:
                item = self.processing_queue.get(timeout=0.1)
                self.process_frame(item)
                self.processing_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in pipeline worker: {str(e)}")

    def get_metrics(self) -> Dict[str, Any]:
        """Provides real-time telemetry on latency, throughput, and error rates."""
        median_lat = float(np.median(self.latency_samples)) if self.latency_samples else 0.0
        p95_lat = float(np.percentile(self.latency_samples, 95)) if len(self.latency_samples) >= 10 else median_lat

        return {
            "total_processed": self.total_processed,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "review_count": self.review_count,
            "dropped_count": self.dropped_count,
            "queue_depth": self.processing_queue.qsize(),
            "last_latency_ms": self.last_latency_ms,
            "median_latency_ms": round(median_lat, 2),
            "p95_latency_ms": round(p95_lat, 2),
            "estimated_fps": round(1000.0 / median_lat, 1) if median_lat > 0 else 0.0,
        }
