# Entrenamiento orgánico inicial — COMPOST AI

Fecha: 2026-11-19
Modelo: `0.2.0-organic-scene`

## Qué identifica este modelo

Clasifica **escenas de desperdicio alimentario** frente a **escenas del subconjunto conocido de materiales reciclables**. La etiqueta positiva procede de carpetas contextuales de fotos de restos de alimentos. La negativa incluye fotos etiquetadas como cartón, vidrio, metal, papel y plástico. El nombre de la salida negativa no significa que el modelo cubra todo residuo no orgánico.

El modelo no detecta con precisión cada objeto presente en una foto ni determina compostabilidad. “Desconocido/ambiguo” se maneja rechazando a revisión según confianza, margen y distancia de embeddings; no hay una clase desconocida supervisada. Las reglas ambientales no aprobaron ningún compostaje.

## Fuentes y derechos

| Fuente | Licencia/procedencia evaluada | Decisión |
|---|---|---|
| [An image dataset for food waste in Bangladesh v1](https://data.mendeley.com/datasets/w68f9w6jmm/1), DOI `10.17632/w68f9w6jmm.1` | La ficha declara CC BY 4.0 y describe fotos tomadas por el equipo en restaurantes, buffets y bodas. Declara 645 fotos. | **Usado** como etiquetas amplias de escena. No identifica el material de cada objeto. |
| [Recyclable Waste Image Dataset v1](https://data.mendeley.com/datasets/h5pxbsdz4m/1), DOI `10.17632/h5pxbsdz4m.1` | CC BY 4.0. La ficha y el README del release dicen que solo incluye la subcolección de imágenes recogidas por el autor; excluye imágenes de terceros que estaban en la colección original. | **Usado** solo como negativo de reciclables conocidos. Atribución en `artifacts/model_organic_binary/THIRD_PARTY.md`. |
| [Waste Classification Dataset](https://data.mendeley.com/datasets/n3gtgm9jxj/1) | Mendeley declara CC BY 4.0 y señala que el conjunto deriva del repositorio de Kaggle de otro autor. No hay licencia verificable de cada imagen de la fuente antecedente. | **No usado**: la licencia publicada no resuelve por sí misma los derechos de las imágenes originales. |
| [RealWaste, UCI #908](https://archive.ics.uci.edu/dataset/908/realwaste) | La ficha oficial de UCI indica CC BY 4.0. El README del archivo descargado indica CC BY-NC-SA 4.0, una condición incompatible. | **No usado** hasta aclaración escrita del responsable de derechos. |
| [TU Wien Domestic Organic Waste](https://researchdata.tuwien.at/records/27k90-dvw73) | La ficha describe 450 fotos domésticas (119 puras orgánicas, 324 con contaminantes, 7 de fondo) y máscaras, pero el campo `Rights / License` está vacío; un hogar y una familia. | **No descargado ni usado**: falta permiso/licencia explícita. |

La licencia CC BY 4.0 de las dos fuentes usadas permite reutilización con atribución, pero no cambia el alcance de sus etiquetas ni convierte las clases en decisiones ambientales.

## Curación y particiones

Las imágenes originales se preservaron. Se verificó que los archivos abrieran, se calcularon SHA-256 y se excluyeron duplicados exactos y el par perceptualmente cercano `IMG_4805.JPG`/`IMG_4806.JPG` de la fuente alimentaria; no se borraron ni sobrescribieron.

| Etiqueta del modelo | Train | Validación | Test | Grupo de test |
|---|---:|---:|---:|---|
| `organic_food_waste_scene` | 235 | 88 | 320 | `Wedding Food waste` |
| `recyclable_material_scene` | 582 | 146 | 249 | `Calheta Waste Management Facility` |
| **Total** | **817** | **234** | **569** | |

La prueba no comparte grupos de captura con el entrenamiento dentro de cada etiqueta. El split de validación de reciclables sí comparte el contexto `Urban and Household Waste` con su entrenamiento, y se usa solo para seleccionar clasificador/calibrar rechazo. La elección de modelos y thresholds no consultó el test.

**Limitación crítica:** la clase orgánica procede únicamente de la fuente de food waste Bangladesh y la clase negativa únicamente de la fuente de reciclables Mendeley. Por ello, la fuente/dominio está perfectamente asociada a la etiqueta. Aunque se reservaron contextos/eventos completos, estos resultados no aíslan generalización a una fuente independiente. No hay hoy test con ambas etiquetas y derechos verificados procedentes de nuevas fuentes. La exactitud del test no debe usarse como estimación de desempeño en fotografías nuevas del público.

Auditoría reproducible: `src/compost_ai/prepare_organic.py`; manifiesto excluido de Git: `data/processed/organic-binary-manifest.csv`; resumen de conteos, exclusiones y hashes: `data/processed/organic-binary-manifest.audit.json`.

## Entrenamiento y artefactos

- Extractor visual congelado: DINOv2 ViT-B/14 (`facebook/dinov2-base`, Apache-2.0), token CLS y processor del checkpoint.
- Cabezas comparadas con validación: StandardScaler + LogisticRegression, SVM lineal calibrado, y SVM RBF. Se seleccionó LogisticRegression por mayor macro-F1 de validación (0,9862); el RBF obtuvo 0,9485 y SVM lineal 0,9240.
- El entrenamiento es reproducible con `.venv/bin/python -m compost_ai.prepare_organic` y `.venv/bin/python -m compost_ai.train_organic`.
- Artefactos: `artifacts/model_organic_binary/` (clasificador joblib, DINOv2, processor, clases, metadata, configuración y métricas). Pesos y datos están excluidos de Git. El baseline anterior sigue preservado en `artifacts/model/`.
- El ajuste registró avisos numéricos transitorios `divide by zero/overflow/invalid value encountered in matmul` en el optimizador logístico y SVM lineal. El clasificador seleccionado terminó en 20 iteraciones; su scaler y coeficientes son finitos. Se deben investigar estos avisos antes de uso operativo.

## Métricas holdout por contexto

Se evaluaron 569 fotos una vez, tras elegir la cabeza y thresholds solo en validación:

| Métrica | Resultado |
|---|---:|
| Accuracy | 1,0000 |
| Macro precision | 1,0000 |
| Macro recall | 1,0000 |
| Macro-F1 | 1,0000 |
| Confusión (filas real, columnas predichas; orden orgánico, reciclable) | `[[320, 0], [0, 249]]` |
| Cobertura con rechazo activo | 0,9736 (554/569) |
| Accuracy en predicciones no rechazadas | 1,0000 (554/554) |
| Latencia media completa DINOv2 + cabeza | 182,1 ms/foto |
| Latencia p50 | 121,7 ms/foto |

Los umbrales se calcularon solo con validation: confianza mínima 0,9918, margen mínimo 0,9836, distancia OOD máxima 50,6021. `confidence_calibrated=false`: son cortes operativos, no una calibración probabilística validada. El 100 % es específico de este conjunto con origen de datos confundido con la etiqueta.

## Prueba externa de dominio y rechazo

El conjunto test de WasteSegCluster (49 imágenes, escenas de canales con máscaras de instancias, no etiquetas globales de imagen) se pasó por la API como estrés externo sin ajustar el modelo:

- 49/49 HTTP 200; 46 `review_required`, 3 `recognized`.
- 31 candidatas `organic_food_waste_scene`, 18 candidatas `recyclable_material_scene`.
- 9 imágenes tenían instancias anotadas `Organic`; las 9 acabaron en revisión (5 candidatas orgánicas y 4 reciclables, todas rechazadas por confianza/margen).
- 0/49 activaron el umbral `out_of_distribution`; la detección OOD por distancia **no** reconoció este cambio de dominio.
- 0/49 decisiones ambientales fueron `COMPOSTABLE`; esto se debe a que el motor de reglas deja ambas etiquetas en `REQUIRES_REVIEW`, no demuestra seguridad de compostabilidad.

No se calcula accuracy en este dataset: las máscaras enumeran varios objetos por escena y no proporcionan una etiqueta binaria única de escena.
CSV por foto: `reports/organic-model-wasteseg-test-stress.csv`.

La integración real `POST /api/v1/recognize` se ejecutó sobre dos fotos del test, con el modelo nuevo cargado en FastAPI: `IMG_20241227_150642.jpg` dio `organic_food_waste_scene` (confianza 1,0000) y `CWMF_Cardboard (17).jpg` dio `recyclable_material_scene` (0,9990). Ambas respuestas fueron `recognized` visualmente y `REQUIRES_REVIEW` ambientalmente. También se verificaron `/docs` y `/openapi.json` (HTTP 200, ruta incluida).

## Fase detallada y límites pendientes

No se entrenaron restos de frutas, restos de verduras, residuos vegetales, otros alimentos ni orgánicos de tratamiento especial. La fuente alimentaria solo clasifica escenas por evento/contexto; la carpeta `Vegetables waste` tiene 16 fotos y no contiene etiquetas por objeto o especie. La fuente TU Wien tiene máscaras útiles pero no licencia explícita. No se debe inferir fruta/especie ni compostabilidad desde estas etiquetas.

La siguiente validación necesaria es conseguir una fuente independiente con licencia clara y etiquetas por imagen/objeto para ambas clases (incluidos materiales no compostables no reciclables), y probar fotos reales recogidas con consentimiento/localización de captura independientes. Hasta entonces, COMPOST AI debe tratar la clasificación como una señal preliminar y mantener revisión manual.
