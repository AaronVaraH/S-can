# Dataset Tools (Data Lead)

Este directorio contiene herramientas y utilidades para:
- Capturar imágenes de muestras con la cámara.
- Convertir imágenes HEIC (iPhone) a formato JPG optimizado para entrenamiento.
- Recortar y normalizar imágenes para el dataset de entrenamiento y prueba.
- Organizar y separar automáticamente los datos por día/sesión.

### Contenido:
- `convert_heic.py`: Convierte lotes de fotos HEIC a JPG preservando orientación EXIF y estructura de carpetas.
- `capture_samples.py`: Script para captura automática/interactiva de imágenes.
- `crop_and_preprocess.py`: Recorte y filtrado de muestras.
- `organize_by_day.py`: Separación por lotes de fecha.
