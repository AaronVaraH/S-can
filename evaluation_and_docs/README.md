# Evaluation and Docs (Evaluation Lead)

Este directorio está destinado a:
- Scripts de validación y benchmarking sobre el **test set fijo**.
- Generación y exportación de la **matriz de confusión**, curvas ROC/PR y métricas (F1-score, precision, recall).
- El **reporte técnico final de 2 páginas** (formato PDF o LaTeX / Markdown compilado).

### Contenido previsto:
- `evaluate_fixed_testset.py`: Script para correr inferencia por lotes en el test set fijo.
- `plot_confusion_matrix.py`: Generador de matrices de confusión y métricas por clase.
- `report/`: Documento del reporte de 2 páginas y figuras generadas.
