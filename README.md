# S-can

Sistema inteligente de escaneo y clasificación en tiempo real usando Raspberry Pi y visión computacional.

---

## 📁 Estructura del Repositorio

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

## 🚀 Instrucciones de Ejecución

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

## 👥 Roles del Equipo

- **Data Lead**: Módulo `dataset_tools/` (captura, preprocesamiento y estructuración de datos).
- **Model Lead**: Módulo `ml_training/` (entrenamiento, exportación a `.onnx`/`.tflite` y métricas de convergencia).
- **Pi & Tools Lead**: Módulos `pi_backend/` y `web_dashboard/` (despliegue en Raspberry Pi, API REST/WebSockets y visualización).
- **Evaluation Lead**: Módulo `evaluation_and_docs/` (benchmarking en test set fijo, matriz de confusión y reporte final).

---

## 📝 Bitácora Semanal (Contribution Log)

| Semana | Fecha | Integrante | Rol | Actividades Realizadas | Evidencias / Commits |
|---|---|---|---|---|---|
| Sem. 1 | DD/MM/AAAA | - | - | Configuración inicial del repositorio y arquitectura base | - |
| Sem. 2 | DD/MM/AAAA | - | - | - | - |
| Sem. 3 | DD/MM/AAAA | - | - | - | - |
| Sem. 4 | DD/MM/AAAA | - | - | - | - |
