# S-can

Sistema inteligente de escaneo y clasificación en tiempo real usando Raspberry Pi y visión computacional.

---

## Estructura del Repositorio

```text
S-can/
├── dataset_tools/          # (Data Lead) Scripts para tomar fotos, recortar y separar por día
├── ml_training/            # (Model Lead) Notebooks/scripts de entrenamiento, curvas de loss y pesos (.onnx / .tflite)
├── pi_backend/             # (Pi & Tools Lead) Servidor FastAPI, lectura de Pi Camera e inferencia en vivo
│   ├── main.py
│   └── requirements.txt
├── web_dashboard/          # (Pi & Tools Lead) Frontend en React/Vue + Tailwind para la laptop
│   ├── src/
│   └── package.json
├── evaluation_and_docs/    # (Evaluation Lead) Scripts del test set fijo, matriz de confusión y el reporte de 2 páginas
└── README.md               # Instrucciones de ejecución y bitácora semanal del equipo (contribution log)
```

---

## Instrucciones de Ejecución

### 1. Dashboard API (Raspberry Pi / Servidor Local)
```bash
cd pi_backend
python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En Linux / Raspberry Pi OS:
# source venv/bin/activate

pip install -r requirements.txt
python main.py
```
El servidor de dashboard escucha en `0.0.0.0:8000`; abre `http://localhost:8000` desde la laptop.

### 2. Inspector Edge-AI
Desde la raíz del repositorio, instala las dependencias y ejecuta el servicio de inspección:
```bash
python -m venv .venv
# En Windows:
.\.venv\Scripts\activate
# En Linux / Raspberry Pi OS:
# source .venv/bin/activate

pip install -r requirements-edge.txt
python run_inspector.py
```
La API del inspector escucha en `0.0.0.0:8080`; abre `http://localhost:8080/docs` desde la laptop.
El modelo ONNX no se incluye en esta combinación de carpetas; mientras no se instale
un modelo en `models/active/can_detector.onnx`, el inspector usa su motor de simulación.

### 3. Dashboard Web (Laptop)
```bash
cd web_dashboard
npm install
npm run dev
```

### Pruebas del Inspector
Desde la raíz del repositorio y con el entorno virtual activado:
```bash
pytest
```

---

## Roles del Equipo

- **Data Lead**: Módulo `dataset_tools/` (captura, preprocesamiento y estructuración de datos).
- **Model Lead**: Módulo `ml_training/` (entrenamiento, exportación a `.onnx`/`.tflite` y métricas de convergencia).
- **Pi & Tools Lead**: Módulos `pi_backend/` y `web_dashboard/` (despliegue en Raspberry Pi, API REST/WebSockets y visualización).
- **Evaluation Lead**: Módulo `evaluation_and_docs/` (benchmarking en test set fijo, matriz de confusión y reporte final).

---

## Bitácora Semanal (Contribution Log)

| Semana | Fecha | Integrante | Rol | Actividades Realizadas | Evidencias / Commits |
|---|---|---|---|---|---|
| Sem. 1 | 21–27/10/2026 | Aaron | Pi & Tools Lead | Inicialización del repositorio, arquitectura base del backend y dashboard, y primera versión visual de la interfaz. | `e7ef533`, `5003276`, `3bef05b` |
| Sem. 2 | 28/10–03/11/2026 | Aaron; Ana| Pi & Tools Lead | Incorporación de imágenes, logo, favicons y ajustes de navegación y presentación del dashboard. | `5f12509` |
| Sem. 3 | 04–10/11/2026 | Max; Aaron | Model Lead; Pi & Tools Lead | Integración de módulos de datos, entrenamiento y despliegue del modelo edge v1.1.0 con exportación ONNX; mejoras de paleta y sidebar. | `73d9efa`, `0e2f3a6`, `6116e57`, `cc40b71` |
| Sem. 4 | 11–18/11/2026 | Max; karimeli; Aaron | Model Lead; Pi & Tools Lead | Integración de inferencia ONNX y detección de defectos en backend/dashboard; autodetección de cámara y corrección del stream MJPEG; normalización de URLs, configuración de pruebas, correcciones de estabilización y limpieza de controles demo. | `e16f195`, `249dfb6`, `228aab5`, `aa72009`, `453e164`, `bfe697e`, `879e594`, `fb4a01e`, `585597b` |
