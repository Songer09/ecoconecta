# Entrenamiento experimental por material — BDWaste v1

## Resultado

Se entrenó `0.3.0-bdwaste-individual-experimental` con DINOv2 ViT-B/14 congelado como extractor CLS y un clasificador `StandardScaler + LogisticRegression(class_weight="balanced")`. El artefacto está en `artifacts/model_bdwaste_individual/`. FastAPI carga este modelo por defecto en `POST /api/v1/recognize`.

Clases incluidas: `banana_peel`, `potato_peel`, `mango_peel`, `sugarcane_husk`, `plastic` y `glass`. Se excluyeron Malta y limón. No se añadieron `can_candidate` ni `eggshell`: las latas aún no tienen revisión completa y el conjunto de huevo mezcla cáscara con huevos enteros.

## Curación y particiones

Se revisaron las hojas de contacto completas de las clases seleccionadas. Se quitaron 13 imágenes duplicadas exactas dentro de la selección y 39 imágenes mal etiquetadas o ambiguas: ocho con tubérculos de papa enteros, una con un racimo de bananos intacto y 30 que incluyen un mango verde entero junto con fragmentos de cáscara. Las decisiones y rutas están en `data/processed/bdwaste-individual-curation-exclusions.csv`; los archivos originales no se alteraron.

Quedaron 686 imágenes. Las características DINOv2 se compararon dentro de cada clase; pares con coseno ≥0,995 se conectaron en un mismo grupo visual y cada grupo completo se mantuvo en una partición. Es una aproximación a objeto/sesión: BDWaste no proporciona esos IDs y dos vistas del mismo objeto pueden no superar el umbral, mientras imágenes distintas pueden ser muy similares. No se presenta este split como garantía de independencia física.

| Clase | Incluidas | Grupos visuales aprox. | Entrenamiento | Validación | Test agrupado |
|---|---:|---:|---:|---:|---:|
| `banana_peel` | 121 | 121 | 76 | 20 | 25 |
| `potato_peel` | 118 | 118 | 75 | 19 | 24 |
| `mango_peel` | 91 | 59 | 64 | 15 | 12 |
| `sugarcane_husk` | 117 | 109 | 74 | 21 | 22 |
| `plastic` | 119 | 119 | 76 | 19 | 24 |
| `glass` | 120 | 120 | 76 | 20 | 24 |
| **Total** | **686** | **646** | **441** | **114** | **131** |

Manifiesto split: `data/processed/bdwaste-individual-train-manifest.csv`. Pares visualmente similares: `data/processed/bdwaste-visual-similar-pairs.csv`. Features congeladas para reproducibilidad: `data/processed/bdwaste-individual-dinov2-features.npz`.

## Métricas internas reales

Test agrupado dentro de BDWaste v1, seleccionado una sola vez tras fijar el protocolo:

- Accuracy: **1,000** (131/131)
- Macro precision: **1,000**
- Macro recall: **1,000**
- Macro-F1: **1,000**
- Errores de clase en este split: **0**
- Precisión/recall/F1 por cada una de las seis clases: **1,000**

Matriz de confusión, filas = verdad; columnas = predicción, orden `banana_peel`, `potato_peel`, `mango_peel`, `sugarcane_husk`, `plastic`, `glass`:

```text
[[25, 0,  0,  0,  0,  0],
 [ 0,24,  0,  0,  0,  0],
 [ 0, 0, 12,  0,  0,  0],
 [ 0, 0,  0, 22,  0,  0],
 [ 0, 0,  0,  0, 24,  0],
 [ 0, 0,  0,  0,  0, 24]]
```

Latencia medida de imagen completa (DINOv2 CPU + clasificador), sobre 30 fotos de test, cinco por clase: **media 211,5 ms; p50 195,7 ms** en este equipo. Depende del hardware y no incluye lectura HTTP.

Estos resultados **no indican generalización**. Todas las imágenes proceden de un único dataset, Dhaka y las condiciones/dispositivos que lo acompañan; fondos y protocolos visuales pueden correlacionarse con las etiquetas. El agrupamiento también es aproximado. No existe un test externo con etiquetas verificadas para estos mismos materiales y no se calculó accuracy externa. No se ajustó el modelo con el test; los umbrales se calcularon usando validation. La confianza no está calibrada y no se evaluó el rechazo con una colección independiente de objetos desconocidos.

## Prueba de API con fotografías reales del test

Se enviaron fotos retenidas al endpoint FastAPI con `TestClient`; la respuesta incluyó clase candidata, confianza, versión y decisión ambiental. Resultado observado en una imagen por clase:

| Verdad de la foto | Predicción observada | Decisión observada |
|---|---|---|
| Banano | `banana_peel` (0,999680) | `COMPOSTABLE` |
| Papa | `potato_peel` (0,999952) | `COMPOSTABLE` |
| Mango | `mango_peel` (0,999990) | `COMPOSTABLE` |
| Caña | `sugarcane_husk` (0,999976) | `COMPOSTABLE` |
| Vidrio | `glass` (0,999598) | `NO_COMPOSTABLE` |
| Plástico | `plastic` (0,999232) | `NO_COMPOSTABLE` |

El motor ambiental opera sobre la clase aceptada, no sobre píxeles: para `household` permite explícitamente las cuatro cáscaras/fibras vegetales y excluye plástico y vidrio; cualquier predicción rechazada conserva `REQUIRES_REVIEW`. Los perfiles comunitario e industrial mantienen los orgánicos en revisión hasta configurar feedstocks del operador. Las reglas están en `config/environmental_rules.yaml`.

## Artefactos, dependencias y reproducción

- Clasificador, backbone DINOv2, processor, etiquetas, thresholds y versiones: `artifacts/model_bdwaste_individual/`.
- Código reproducible: `scripts/train_bdwaste_individual.py`.
- Dependencias registradas en el artefacto: PyTorch 2.7.0, Transformers 4.51.3, Scikit-learn 1.6.1; Python 3.11. DINOv2 `facebook/dinov2-base` / ViT-B/14, licencia Apache-2.0; BDWaste v1, CC BY 4.0. Atribuciones en `artifacts/model_bdwaste_individual/THIRD_PARTY.md`.
- Reentrenamiento: `.venv/bin/python scripts/train_bdwaste_individual.py --cosine-threshold 0.995`.
- Swagger: iniciar con `uvicorn compost_ai.api:app --reload` y abrir `http://localhost:8000/docs`; probar `POST /api/v1/recognize`, subir JPEG/PNG/WEBP y seleccionar `household`.
- Verificación automatizada de reglas, contrato e inferencia con fotos retenidas: `.venv/bin/pytest -q`.

Es una versión experimental funcional para esas seis etiquetas y este dominio de imágenes. No identifica otros residuos y no está lista para producción.
