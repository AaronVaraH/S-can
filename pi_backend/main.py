"""
S-can Backend - Raspberry Pi
Servidor FastAPI para captura con Pi Camera e inferencia en tiempo real.
"""

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="S-can Pi Backend API",
    description="API de lectura de cámara e inferencia en vivo",
    version="0.1.0"
)

# Permitir conexiones desde la laptop / dashboard web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "service": "S-can Pi Backend",
        "status": "online",
        "model_loaded": False
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/predict")
async def predict_frame(file: UploadFile = File(...)):
    """
    Endpoint para inferencia directa recibiendo una imagen.
    """
    contents = await file.read()
    # TODO: Cargar imagen con OpenCV/PIL y pasarla al modelo ONNX / TFLite
    return {
        "filename": file.filename,
        "prediction": "dummy_class",
        "confidence": 0.95
    }

@app.get("/camera/status")
def camera_status():
    """
    Verifica el estado de conexión de la cámara (PiCamera o USB webcam).
    """
    return {
        "camera_connected": False,
        "message": "Pi Camera pendiente de inicializar"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
