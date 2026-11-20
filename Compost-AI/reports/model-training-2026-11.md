# Informe de preparación y entrenamiento — COMPOST AI

Fecha: 2026-11-19. Modelo de investigación local, no validado para disposición operativa.

## Fuentes y permisos

- **Usado:** [Recyclable Waste Image Dataset, v1](https://data.mendeley.com/datasets/h5pxbsdz4m/1), João Alves (2026), DOI `10.17632/h5pxbsdz4m.1`, CC BY 4.0. La ficha indica que el release público contiene solo imágenes tomadas por el autor y excluye imágenes de terceros por restricciones de licencia. El ZIP también contiene esa declaración y CC BY 4.0.
- ZIP descargado: 1,6 GB; SHA-256 `fa5ce32115cc961b8f223b2b3a8de7cecafc33a66dec56ab76b4dc571e20f9ac`. La ficha dice 1.000 imágenes; el ZIP trae 989, una discrepancia documentada.
- **Excluido:** [RealWaste/UCI](https://archive.ics.uci.edu/dataset/908/realwaste). La ficha UCI indica CC BY 4.0, pero el README del ZIP descargado indica CC BY-NC-SA 4.0. Se mantuvo sin extraer y no se usó.
- **Alternativa no incorporada:** [Automatic waste management dataset, v2](https://data.mendeley.com/datasets/d4vsy9c9wk/2), CC BY 4.0 según su ficha, 1.973 imágenes y categoría orgánica. El ZIP anunciado por el endpoint de descarga pesa 3,97 GB; se canceló la descarga por transferencia inferior a 0,3 MB/s. No se utilizó el fragmento parcial descargado.
- **Auditado, no usado:** [WasteSegCluster, v4](https://data.mendeley.com/datasets/3wnf3n242s/4), ficha Mendeley y README interno indican CC BY 4.0. ZIP de 100.308.876 bytes, SHA-256 `732246989403a4b4b7d3569ed8809eab8fef7a91f54ddfcfca319acf5a43a896`. El ZIP contiene otro ZIP con 1.947 escenas de agua y máscaras COCO: train 1.795, validation 103, test 49. Conteos de instancias anotadas: Organic 681/39/11, Plastic 1.698/133/62, Paper 665/46/6, Composite_Rubber_Textile 515/31/13. Hay 121 fotos train sin anotaciones. El README declara aumentos de imagen y observé tres pares perceptuales cross-split (dHash ≤2). Las escenas suelen incluir varios objetos; la anotación de instancias no etiqueta toda la foto. Por ello se preservó como auditoría externa y no se mezcló en el clasificador de clase única.
- **Alternativas grandes:** [BDWaste v1](https://data.mendeley.com/datasets/96g5pgfnfw/1), CC BY 4.0 indicado en la ficha, declara 21 clases finas y discrepancia 2.624/2.625 imágenes; ZIP 7.144.426.327 bytes, no descargado. [Automatic v1](https://data.mendeley.com/datasets/d4vsy9c9wk/1) declara CC BY 4.0 y 909 fotos, pero su ZIP mide 2.123.210.640 bytes; no descargado. Antes de incorporarlos se requiere revisar las imágenes y condiciones de terceros en los archivos.
- Ningún dataset o artefacto de modelo se añadió a Git; `data/raw/`, `artifacts/` y `.cache/` están excluidos por `.gitignore`.

## Limpieza y etiquetas

Se validó cada imagen con Pillow, se calcularon SHA-256 y se redujeron **12 pares de duplicados exactos** a una copia. No aparecieron archivos dañados ni el mismo hash con etiquetas contradictorias. Un barrido de hash perceptual difference-hash con distancia de Hamming ≤2 no encontró candidatos duplicados adicionales dentro de cada clase. Una inspección visual aleatoria de cuatro fotos por clase encontró ejemplos mayormente compatibles con la etiqueta de carpeta; algunos empaques compuestos son ambiguos.

Las etiquetas son visuales/materiales. No son decisiones de compostabilidad.

| Clase visual | Únicas después de limpiar | Train | Validation | Test |
|---|---:|---:|---:|---:|
| cardboard | 429 | 299 | 65 | 65 |
| glass | 49 | 35 | 7 | 7 |
| metal | 90 | 63 | 13 | 14 |
| paper | 96 | 67 | 15 | 14 |
| plastic | 313 | 219 | 47 | 47 |
| **Total** | **977** | **683** | **147** | **147** |

Splits estratificados, semilla 42, 70/15/15 aprox. Los hashes idénticos se quitaron antes del split y el barrido perceptual no halló pares cercanos. Las dos agrupaciones de captura (`Calheta Waste Management Facility`, `Urban and Household Waste`) aparecen en los tres splits; por ello la evaluación no es independiente del contexto de fondo. La fuente no incluye suficientes IDs de sesión para crear tres particiones disjuntas por sitio sin perder cobertura de clases.

## Entrenamiento y artefactos

- Backbone: Meta DINOv2 ViT-B/14, repo `facebook/dinov2-base`, revisión `f9e44c814b77203eaa57a6bdbbd535f21ede1415`, Apache-2.0.
- Checkpoint safetensors: SHA-256 `d73036b56966966d07975d696bde331762f37297e2f095de8cea0040c3aa0841`.
- Cabeza: `StandardScaler` + `LogisticRegression(class_weight="balanced", max_iter=2000)`, semilla 42.
- Python 3.11.18, PyTorch 2.7.0, Transformers 4.51.3, scikit-learn 1.6.1. CPU; MPS no disponible.
- Preprocesamiento: RGB, `AutoImageProcessor` lento del mismo checkpoint, token CLS. El processor se serializó junto al backbone y se usa también en FastAPI.
- Artefactos locales en `artifacts/model/`: pesos DINOv2 y processor en `backbone/`, `classifier.joblib`, `metadata.json`, `labels.json`, `training_config.json`, `metrics.json`, `THIRD_PARTY.md`.

## Métricas de test

Test reservado, 147 imágenes; métricas calculadas por el script real de entrenamiento, sin valores de ejemplo.

- Accuracy: **0,9116**
- Macro precision: **0,8952**
- Macro recall: **0,8992**
- Macro F1: **0,8955**
- Latencia media: **177,3 ms/foto** para extracción DINOv2 + clasificador en CPU; no incluye transferencia HTTP completa.
- Cobertura selectiva: **0,9252** (136/147); accuracy de los aceptados: **0,9412** (128/136); rechazados: 11/147.

Matriz de confusión, orden de filas/columnas: cardboard, glass, metal, paper, plastic:

```text
[[61, 0, 0,  1,  3],
 [ 0, 7, 0,  0,  0],
 [ 0, 0,13,  0,  1],
 [ 4, 0, 0, 10,  0],
 [ 1, 1, 1,  1, 43]]
```

El soporte de vidrio es solo 7 en test; su recall 1,0 es demasiado inestable para generalizar. Durante `LogisticRegression.fit` se emitieron avisos temporales de overflow/división en pasos numéricos. El solver terminó convergido en 42 iteraciones; parámetros, probabilidades, escalas y resultados guardados son finitos. Conviene repetir el ajuste con solver/regularización conservadora y comparar antes de uso operativo.

Los umbrales se derivaron solo de validation: confianza mínima 0,6917, margen mínimo 0,4546 y distancia OOD máxima 50,2541. No hay un conjunto externo de OOD; por tanto no se midió precisión/recall de la detección de desconocidos.

## Pruebas e integración

La ejecución original tuvo 8 pruebas. Tras ampliar el contrato de respuesta con categoría, calibración, motivo, recomendación y revisión manual, la suite actualizada: `.venv/bin/pytest -q` dio **11 passed**. Incluye reglas, limpieza/partición, errores de entrada y prueba de integración con fotos holdout del split test.

Se enviaron por `POST /api/v1/recognize` cinco fotos reservadas, una por clase; cada request devolvió HTTP 200 y una predicción correcta. Las cinco tuvieron `out_of_distribution=false`; la confianza fue cardboard 0,9502, glass 0,8784, metal 0,9999, paper 0,8877 y plastic 0,9985. Es una prueba de contrato con fotos holdout del dataset, no una validación externa en teléfonos o residuos de otra instalación.

Como prueba exploratoria con fotografías externas se enviaron 41 escenas de validation/test de WasteSegCluster que tienen al menos una anotación `Organic`. Las 41 devolvieron HTTP 200; 36 quedaron `recognized` con candidata `plastic`, 3 `unknown`/OOD y 2 `review_required`. Todas recibieron decisión ambiental `REQUIRES_REVIEW`. Estas escenas contienen objetos mixtos y pueden tener plástico visible; no tienen etiqueta de clase global, así que no se calcula accuracy. El bajo rechazo OOD en un dominio de agua nuevo indica que el umbral OOD actual no es fiable y debe validarse y recalibrarse con conjuntos limpios, diversos y con etiquetas por imagen.

Las cinco respuestas ambientales fueron `REQUIRES_REVIEW`, que es el comportamiento correcto de la configuración actual: no se configuraron clases aceptadas por una instalación. No hay clase orgánica en el modelo, así que aún no puede reconocer residuos compostables.

## Límites y siguiente trabajo

1. Conseguir fotos de residuos orgánicos aislados con etiquetas de clase por foto, además de ampliar vidrio; reauditar las fuentes CC BY identificadas antes de incorporarlas.
2. Repetir evaluación con particiones por sesión/sitio, set externo limpio y fotos reales nuevas de múltiples dispositivos y condiciones.
3. Investigar los avisos numéricos del solver y recalibrar rechazo/OOD con ejemplos genuinos fuera de distribución.
4. Configurar reglas de compostaje por instalación y validar decisiones ambientales con operadores. El modelo visual no determina compostabilidad.
