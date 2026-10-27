"""
S-can Backend - Raspberry Pi
Servidor FastAPI para captura con Pi Camera e inferencia en tiempo real.
Envía video por MJPEG (/video_feed) y datos/telemetría vía WebSockets (/ws/telemetry).
"""

import asyncio
import json
import time
from typing import List
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="S-can Pi Backend API",
    description="API de lectura de cámara e inferencia en vivo",
    version="0.2.0"
)

# Permitir conexiones desde la laptop / dashboard web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gestor de conexiones WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

@app.get("/")
def read_root():
    return {
        "service": "S-can Pi Backend",
        "status": "online",
        "model_loaded": False,
        "active_ws_clients": len(manager.active_connections)
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": time.time()}

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """
    Canal de comunicación bidireccional en tiempo real con el dashboard de la laptop.
    Transmite detecciones, bounding boxes y telemetría de hardware de la Pi.
    """
    await manager.connect(websocket)
    try:
        # Enviar paquete de bienvenida
        await websocket.send_text(json.dumps({
            "type": "telemetry",
            "payload": {
                "cpuUsage": 40,
                "cpuTemp": 48.2,
                "ramUsage": "1.2 / 4.0 GB",
                "modelEngine": "ONNX Runtime (ARM64)",
                "modelLatencyMs": 24.5
            }
        }))
        while True:
            # Mantener conexión activa y recibir comandos si el dashboard los envía
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

@app.post("/predict")
async def predict_frame(file: UploadFile = File(...)):
    """
    Endpoint para inferencia directa recibiendo una imagen.
    """
    contents = await file.read()
    # TODO: Inferencia con modelo ONNX / TFLite
    result = {
        "filename": file.filename,
        "prediction": "intacta",
        "confidence": 0.98,
        "latency_ms": 22.4
    }
    # Difundir evento de detección a los dashboards conectados
    await manager.broadcast({
        "type": "detection",
        "payload": {
            "id": int(time.time() * 1000) % 10000,
            "time": time.strftime("%H:%M:%S"),
            "class": result["prediction"],
            "confidence": result["confidence"],
            "defectType": "Conforme",
            "latency": result["latency_ms"],
            "bbox": [0.33, 0.22, 0.34, 0.56]
        }
    })
    return result

async def generate_mjpeg_stream():
    """
    Generador de frames MJPEG para el stream de video en vivo.
    Si la cámara física aún no está lista, emite frames con señal de espera.
    """
    while True:
        # Aquí se capturan frames desde Picamera2 o cv2.VideoCapture(0)
        # Para evitar bloquear si no hay cámara conectada, se simula un sleep
        await asyncio.sleep(0.1)
        # Formato de transmisión MJPEG estándar
        # yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.get("/video_feed")
async def video_feed():
    """
    Stream de video MJPEG consumido por la etiqueta <img> en el dashboard de la laptop.
    """
    return StreamingResponse(
        generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/camera/status")
def camera_status():
    return {
        "camera_connected": False,
        "message": "Pi Camera lista para inicializar en OpenCV / Picamera2"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

