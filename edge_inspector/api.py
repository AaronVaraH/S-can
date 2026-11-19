"""Local REST API endpoints for Raspberry Pi edge inspection and industrial integration."""

from __future__ import annotations

import base64
import io
import time
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from edge_inspector.hardware import detect_hardware, estimate_hardware_capacity
from edge_inspector.pipeline import InspectionPipeline, QueuedInspectionItem
from edge_inspector.rag.assistant import InspectionDocumentationAssistant
from edge_inspector.watchdog import EdgeWatchdog


class RagQueryRequest(BaseModel):
    question: str
    top_k: int = 3


class InterlockRequest(BaseModel):
    action: str  # "ENGAGE" or "RELEASE"
    reason: str = "MANUAL_API_REQUEST"


def create_app(
    pipeline: InspectionPipeline,
    watchdog: EdgeWatchdog,
    rag_assistant: Optional[InspectionDocumentationAssistant] = None,
) -> FastAPI:
    """Creates configured FastAPI application for edge device."""
    app = FastAPI(
        title="Edge-AI Industrial Can Inspector",
        description="Raspberry Pi Edge Computing Service for High-Speed Can-Defect Inspection",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["Monitoring"])
    def get_health() -> Dict[str, Any]:
        """Local health endpoint reporting system vitals, thermals, and alerts."""
        health = watchdog.evaluate_health()
        status_code = status.HTTP_200_OK if health.is_healthy else (
            status.HTTP_503_SERVICE_UNAVAILABLE if health.state == "EMERGENCY_FAILSAFE" else status.HTTP_200_OK
        )
        return JSONResponse(status_code=status_code, content=health.to_dict())

    @app.get("/metrics", tags=["Monitoring"])
    def get_metrics() -> Dict[str, Any]:
        """Provides real-time production metrics, latency percentiles, and throughput."""
        pipeline_metrics = pipeline.get_metrics()
        health = watchdog.evaluate_health()

        return {
            "timestamp": time.time(),
            "pipeline": pipeline_metrics,
            "system": {
                "cpu_usage_pct": health.cpu_usage_percent,
                "ram_usage_pct": health.ram_usage_percent,
                "cpu_temp_c": health.cpu_temperature_c,
                "throttled": health.throttled,
                "disk_usage_pct": health.disk_usage_percent,
            },
        }

    @app.get("/hardware", tags=["Hardware"])
    def get_hardware_info() -> Dict[str, Any]:
        """Returns physical Raspberry Pi hardware specifications and capacity estimates."""
        hw = detect_hardware()
        cap = estimate_hardware_capacity(hw)
        return {
            "hardware": hw.to_dict(),
            "capacity_estimate": cap,
        }

    @app.get("/camera/status", tags=["Camera"])
    def get_camera_status() -> Dict[str, Any]:
        """Queries camera adapter health, connection state, and settings."""
        return pipeline.camera.get_status()

    @app.post("/camera/capture", tags=["Inspection"])
    def capture_and_inspect() -> Dict[str, Any]:
        """Acquires frame from configured camera and executes full inspection pipeline."""
        if not pipeline.camera.is_connected():
            raise HTTPException(status_code=503, detail="Camera is disconnected or unavailable.")

        frame, meta = pipeline.camera.capture_frame()
        if frame is None or meta is None:
            raise HTTPException(status_code=500, detail="Failed to capture frame from camera.")

        item = QueuedInspectionItem(
            frame_id=meta.frame_id,
            timestamp_ns=meta.timestamp_ns,
            image=frame,
            source="camera",
            metadata=meta,
        )
        result = pipeline.process_frame(item)
        return result

    @app.post("/inspect", tags=["Inspection"])
    async def inspect_uploaded_image(
        file: UploadFile = File(...),
        return_annotated_base64: bool = Query(False, description="Include base64 annotated image in response"),
    ) -> Dict[str, Any]:
        """Inspects an uploaded image file (JPEG, PNG, WebP) with defect localization and decision rules."""
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file or unsupported format.")

        ts_ns = time.perf_counter_ns()
        item = QueuedInspectionItem(
            frame_id=pipeline.total_processed + 1,
            timestamp_ns=ts_ns,
            image=img,
            source="upload",
        )

        result = pipeline.process_frame(item)

        if return_annotated_base64 and result.get("image_path"):
            try:
                with open(result["image_path"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                result["annotated_image_base64"] = f"data:image/jpeg;base64,{b64}"
            except Exception:
                pass

        return result

    @app.get("/decision/history", tags=["History"])
    def get_inspection_history(limit: int = Query(20, ge=1, le=100)) -> List[Dict[str, Any]]:
        """Queries recent inspection records from local SQLite database."""
        return pipeline.storage.get_recent_inspections(limit=limit)

    @app.post("/rag/query", tags=["Documentation RAG"])
    def query_rag_assistant(req: RagQueryRequest) -> Dict[str, Any]:
        """Queries local offline inspection documentation and defect standards."""
        if not rag_assistant:
            raise HTTPException(status_code=503, detail="Local RAG assistant is not enabled.")

        res = rag_assistant.query(question=req.question, top_k=req.top_k)
        return res.to_dict()

    @app.post("/actuator/interlock", tags=["Actuator"])
    def toggle_interlock(req: InterlockRequest) -> Dict[str, Any]:
        """Engages or releases emergency reject actuator interlock."""
        if req.action.upper() == "ENGAGE":
            pipeline.actuator.engage_safety_interlock(reason=req.reason)
        elif req.action.upper() == "RELEASE":
            pipeline.actuator.release_safety_interlock()
        else:
            raise HTTPException(status_code=400, detail="Action must be ENGAGE or RELEASE.")

        return pipeline.actuator.get_status()

    return app
