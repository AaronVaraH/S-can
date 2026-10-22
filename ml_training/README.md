# ML Training (Model Lead)

Este directorio contiene:
- Notebooks y scripts para el entrenamiento del modelo.
- Visualización de curvas de pérdida (*loss*) y precisión (*accuracy*).
- Exportación y optimización de pesos en formatos ligeros para borde (`.onnx` / `.tflite`).

### Subdirectorios sugeridos:
- `notebooks/`: Jupyter Notebooks para exploración y experimentación inicial.
- `models/`: Archivos de pesos exportados (`model.onnx`, `model.tflite`).
- `train.py`: Script principal de entrenamiento reproducible.
- `export.py`: Conversión de checkpoints a `.onnx` o `.tflite`.
