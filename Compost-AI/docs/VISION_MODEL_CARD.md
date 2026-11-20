# Ficha del modelo de visión — COMPOST AI

## Identificación y uso previsto

- **Versión:** `0.3.0-bdwaste-individual-experimental`.
- **Tarea:** clasificación visual de un material individual entre seis etiquetas.
- **Uso:** orientación experimental y solicitud de revisión cuando la entrada es incierta.
- **No usar para:** tomar decisiones finales de recolección, reciclaje o compostabilidad; inferir materiales fuera de las seis etiquetas.
- **Estado:** experimental, no listo para producción.

## Clases

`banana_peel`, `potato_peel`, `mango_peel`, `sugarcane_husk`, `plastic`, `glass`.

El clasificador identifica el material visual. La aptitud de compostaje se calcula aparte con reglas configurables por tipo de instalación.

## Datos y derechos

BDWaste v1, CC BY 4.0, DOI `10.17632/96g5pgfnfw.1`. Se curaron 686 imágenes después de excluir duplicados exactos, imágenes mal etiquetadas y cuadros ambiguos. Malta y limón no se usaron. Se dividió aproximadamente por grupos de similitud DINOv2 porque el dataset no proporciona identificadores fiables de objeto o sesión; esta agrupación no garantiza independencia física.

El conjunto completo no se incluye en este repositorio. La atribución y el detalle de la evaluación están en `reports/bdwaste-individual-training-2026-11.md`.

## Modelo y ejecución

- Extractor congelado: Meta DINOv2 ViT-B/14 (`facebook/dinov2-base`), licencia Apache-2.0.
- Clasificador: `StandardScaler` + `LogisticRegression` balanceada de scikit-learn.
- Preprocesamiento: imagen RGB y `AutoImageProcessor` del mismo checkpoint tanto en entrenamiento como en inferencia.
- Dependencias registradas: Python 3.11, PyTorch 2.7.0, Transformers 4.51.3 y scikit-learn 1.6.1.
- Los pesos, el clasificador serializado y el dataset no se versionan aquí. La API requiere obtener o generar esos artefactos localmente siguiendo `docs/TRAINING.md`.

## Evaluación interna reportada

En el test agrupado interno de BDWaste v1 (131 imágenes), el informe de entrenamiento reporta accuracy 1,000, macro-precision 1,000, macro-recall 1,000 y macro-F1 1,000. Cada clase tuvo precision/recall/F1 de 1,000 en ese split. Latencia medida en CPU: media 211,5 ms e intervalos p50 195,7 ms por imagen, sin transferencia HTTP.

Estos resultados no estiman generalización: todas las imágenes proceden de una sola fuente y el agrupamiento visual es aproximado. No hay test externo etiquetado comparable ni evaluación independiente del rechazo OOD. Las confianzas no están calibradas. La evidencia y la matriz de confusión están en el informe enlazado arriba.

## Riesgos y salvaguardas

Fondos, dispositivos y condiciones del dataset pueden correlacionarse con las etiquetas. Puede fallar con materiales mixtos, clases no soportadas, otras condiciones de captura o diferencias regionales. Las predicciones de baja confianza/desconocidas requieren revisión. `COMPOSTABLE`, `NO_COMPOSTABLE` y `REQUIRES_REVIEW` provienen del motor de reglas independiente, no de la etiqueta visual por sí sola.

## Integración

La interfaz HTTP estable es `POST /api/v1/recognize`, documentada por OpenAPI en `/docs`. La respuesta contiene clase, confianza, versión y evaluación ambiental. El modelo se carga una vez durante el ciclo de vida de FastAPI.

Próxima validación: completar las fotos del manifiesto `data/collection/capture_manifest.csv`, ejecutar `scripts/prepare_collection.py`, entrenar un artefacto nuevo y evaluar con el test bloqueado antes de habilitar clases adicionales.
