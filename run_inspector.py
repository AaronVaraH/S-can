"""Production entrypoint daemon for Raspberry Pi Edge-AI Can-Defect Inspection System."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict

import uvicorn
import yaml

from edge_inspector.actuator import create_reject_actuator
from edge_inspector.api import create_app
from edge_inspector.camera import create_camera_adapter
from edge_inspector.decision import DecisionRuleConfig
from edge_inspector.hardware import detect_hardware, estimate_hardware_capacity
from edge_inspector.inference import (
    ModelManifest,
    create_inference_engine,
)
from edge_inspector.pipeline import InspectionPipeline
from edge_inspector.quality import QualityGateConfig
from edge_inspector.rag import (
    BM25Retriever,
    InspectionDocumentationAssistant,
)
from edge_inspector.storage import StorageManager
from edge_inspector.watchdog import EdgeWatchdog

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s",
)
logger = logging.getLogger("can_inspector")


def load_yaml_config(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        logger.warning(f"Config file {path} not found. Using defaults.")
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Raspberry Pi Edge-AI Can-Defect Inspector Daemon")
    parser.add_argument("--config", default="config/config.default.yaml", help="Path to configuration file")
    parser.add_argument("--host", default=None, help="Server host override")
    parser.add_argument("--port", type=int, default=None, help="Server port override")
    args = parser.parse_args()

    cfg = load_yaml_config(args.config)

    logger.info("==================================================================")
    logger.info(" Starting Raspberry Pi Edge Can-Defect Inspection Service         ")
    logger.info("==================================================================")

    # 1. Hardware Detection & Capacity Estimate
    hw_override = cfg.get("system", {}).get("hardware_override")
    hw = detect_hardware(override_profile=hw_override)
    cap = estimate_hardware_capacity(hw)
    logger.info(f"Target Device Profile: {hw.rpi_model} ({hw.cpu_architecture})")
    logger.info(f"Available RAM: {hw.available_ram_mb} MB | Memory Feasible: {cap['is_memory_sufficient']}")

    # 2. Camera Adapter Initialization
    cam_cfg = cfg.get("camera", {})
    camera = create_camera_adapter(cam_cfg)
    cam_connected = camera.connect()
    if cam_connected:
        logger.info(f"Camera adapter '{cam_cfg.get('adapter')}' connected successfully.")
    else:
        logger.warning(f"Camera adapter failed initial connection: {camera.last_error_message}. Watchdog will attempt recovery.")

    # 3. Model Manifest & Inference Engine
    inf_cfg = cfg.get("inference", {})
    manifest_path = inf_cfg.get("manifest_path", "models/active/manifest.json")
    model_path = inf_cfg.get("active_model_path", "models/active/can_detector.onnx")

    manifest = None
    if Path(manifest_path).exists():
        manifest = ModelManifest.from_file(manifest_path)
        logger.info(f"Loaded active model manifest: v{manifest.version} ({manifest.architecture})")

    backend = inf_cfg.get("backend", "onnx")
    engine = create_inference_engine(backend=backend, manifest=manifest, options=inf_cfg)
    try:
        engine.load_model(model_path, manifest=manifest)
        logger.info(f"Inference engine ({backend}) loaded model successfully from: {model_path}")
    except Exception as e:
        logger.error(f"Failed to load primary inference model: {str(e)}. Falling back to simulation engine.")
        engine = create_inference_engine(backend="simulation", manifest=manifest)

    # 4. Reject Actuator
    act_cfg = cfg.get("actuator", {})
    actuator = create_reject_actuator(act_cfg)
    logger.info(f"Reject actuator initialized: {act_cfg.get('adapter')} (Delay: {act_cfg.get('conveyor_delay_ms')}ms)")

    # 5. Storage Manager
    stor_cfg = cfg.get("storage", {})
    storage = StorageManager(
        db_path=stor_cfg.get("db_path", "data/inspection.db"),
        image_dir=stor_cfg.get("image_dir", "data/inspections"),
        save_annotated_images=stor_cfg.get("save_annotated_images", True),
        save_pass_images=stor_cfg.get("save_pass_images", False),
        save_fail_images=stor_cfg.get("save_fail_images", True),
        save_review_images=stor_cfg.get("save_review_images", True),
        max_disk_usage_percent=stor_cfg.get("max_disk_usage_percent", 85.0),
    )

    # 6. Quality Gate & Decision Configs
    q_cfg_dict = cfg.get("quality_gate", {})
    quality_config = QualityGateConfig(
        enabled=q_cfg_dict.get("enabled", True),
        min_width=q_cfg_dict.get("min_width", 320),
        min_height=q_cfg_dict.get("min_height", 320),
        blur_laplacian_threshold=q_cfg_dict.get("blur_laplacian_threshold", 65.0),
        min_mean_brightness=q_cfg_dict.get("min_mean_brightness", 35.0),
        max_mean_brightness=q_cfg_dict.get("max_mean_brightness", 235.0),
        max_glare_pixel_ratio=q_cfg_dict.get("max_glare_pixel_ratio", 0.12),
        can_presence_threshold=q_cfg_dict.get("can_presence_threshold", 0.12),
    )

    dec_cfg_dict = cfg.get("decision", {})
    decision_config = DecisionRuleConfig(
        default_pass_threshold=dec_cfg_dict.get("default_pass_threshold", 0.35),
        default_fail_threshold=dec_cfg_dict.get("default_fail_threshold", 0.70),
        defect_criticality=dec_cfg_dict.get("defect_criticality", {}),
    )

    # 7. Pipeline Coordinator
    pipe_cfg = cfg.get("pipeline", {})
    pipeline = InspectionPipeline(
        camera=camera,
        inference_engine=engine,
        actuator=actuator,
        storage=storage,
        quality_config=quality_config,
        decision_config=decision_config,
        queue_max_size=pipe_cfg.get("queue_max_size", 10),
        overload_policy=pipe_cfg.get("overload_policy", "DROP_OLDEST"),
        memory_guard_limit_mb=pipe_cfg.get("memory_guard_limit_mb", 450.0),
        inference_timeout_ms=inf_cfg.get("timeout_ms", 120.0),
    )
    pipeline.start()

    # 8. Watchdog & Monitoring
    wd_cfg = cfg.get("watchdog", {})
    watchdog = EdgeWatchdog(
        thermal_warning_c=wd_cfg.get("thermal_warning_temp_c", 78.0),
        thermal_critical_c=wd_cfg.get("thermal_critical_temp_c", 84.0),
        max_ram_percent=wd_cfg.get("max_memory_percent", 85.0),
        heartbeat_interval_sec=wd_cfg.get("heartbeat_interval_sec", 1.0),
    )
    watchdog.register_callbacks(
        camera_cb=lambda: camera.is_connected(),
        model_cb=lambda: engine.is_loaded,
        storage_cb=lambda: storage.db_available,
    )
    watchdog.start()

    # 9. Local RAG Documentation Assistant
    rag_cfg = cfg.get("rag", {})
    rag_assistant = None
    if rag_cfg.get("enabled", True):
        retriever = BM25Retriever(
            index_path=rag_cfg.get("index_path", "data/rag_index.json"),
            documents_dir=rag_cfg.get("documents_dir", "edge_inspector/rag/documents"),
        )
        rag_assistant = InspectionDocumentationAssistant(
            retriever=retriever,
        )
        logger.info("Local RAG Documentation Assistant initialized (100% offline mode).")

    # 10. FastAPI REST Application
    app = create_app(pipeline=pipeline, watchdog=watchdog, rag_assistant=rag_assistant)

    # Signal handlers for clean shutdown
    def handle_signal(sig, frame):
        logger.info("Shutdown signal received. Releasing resources...")
        pipeline.stop()
        watchdog.stop()
        camera.disconnect()
        logger.info("Edge Inspector shutdown cleanly.")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Server configuration
    srv_cfg = cfg.get("server", {})
    host = args.host or srv_cfg.get("host", "0.0.0.0")
    port = args.port or srv_cfg.get("port", 8080)

    logger.info(f"REST API service listening at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
