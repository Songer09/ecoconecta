# Preparación, entrenamiento y evaluación

## Datos

Organice imágenes ya autorizadas como `data/raw/<etiqueta>/*`. La etiqueta debe representar el objeto/material visual, no una decisión ambiental. Use `organico__cascara_banana` para material y clase o actualice el mapeo en los artefactos/configuración. No mezcle “compostable” como etiqueta visual universal: depende de instalaciones y condiciones.

## Reproducir

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m compost_ai.train --data data/raw --manifest data/processed/manifest.csv --out artifacts/model
```

El script verifica la decodificación de las imágenes, registra y excluye archivos dañados, deduplica por SHA-256 y excluye imágenes idénticas con etiquetas contradictorias. Genera splits estratificados con semilla, extrae el token CLS con `facebook/dinov2-base` (DINOv2 ViT-B/14) y entrena un pipeline scikit-learn de estandarización + regresión logística. El processor proviene del mismo checkpoint durante entrenamiento e inferencia. Primera ejecución requiere descargar checkpoint desde Hugging Face. Las imágenes fuente no se modifican ni eliminan.

## Métricas

`metrics.json` se crea solo tras ejecución real y contiene accuracy, macro precision/recall/F1, matriz de confusión por clase, resultados por clase, cobertura/accuracy selectiva y latencia medida en test incluyendo extracción DINOv2 y clasificador. La latencia depende de CPU/GPU y entorno. Evalúe también falsos aceptados con datos fuera de distribución representativos antes de uso operativo. La calibración actual deriva umbrales de confianza, margen y distancia de la partición validation; es un punto de partida, no una garantía de calibración probabilística.

Las métricas ambientales (acuerdo con reglas de cada instalación, contaminación/errores de disposición y coste de falsos positivos) requieren etiquetas y revisión por operadores locales. No se calculan desde etiquetas visuales y no se deben inferir como un valor del benchmark visual. Registre protocolo, versión de reglas, muestra y fecha con cada evaluación ambiental.

`tests/` contiene pruebas unitarias y de contrato; ejecutar con `pytest` cuando se quiera validar localmente.

## Ejecución registrada

El entrenamiento baseline anterior se ejecutó el 2026-11-19 con 977 imágenes únicas CC BY 4.0 de cinco clases reciclables; no incluyó orgánicos. Su accuracy fue 0,9116 y macro-F1 0,8955 (147 imágenes); la cobertura selectiva fue 0,9252 con accuracy 0,9412 entre las predicciones aceptadas. Se conserva en `artifacts/model/` como baseline.

La integración FastAPI carga ahora `artifacts/model_bdwaste_individual/` por defecto. El clasificador actual identifica seis materiales individuales. El clasificador anterior de escenas se conserva en `artifacts/model_organic_binary/` y no representa el objetivo actual.

## Entrenamiento orgánico inicial

Con el entorno del proyecto, regenerar datos y entrenar:

```bash
.venv/bin/python -m compost_ai.prepare_organic
.venv/bin/python -m compost_ai.train_organic \
  --manifest data/processed/organic-binary-manifest.csv \
  --out artifacts/model_organic_binary \
  --backbone-cache artifacts/model/backbone
```

El manifiesto separa grupos enteros por etiqueta y conserva SHA-256; los archivos originales no se modifican. El test final está reservado hasta completar selección en validation. El informe contiene métricas, condiciones de licencia, estrés externo y limitaciones: [entrenamiento orgánico 2026-11](../reports/organic-training-2026-11.md). Debido a que la clase y la fuente están confundidas, las métricas del split no prueban generalización a nuevas fuentes.

Para repetir API e integración: `.venv/bin/pytest -q`. Docker monta los artefactos locales y el `docker-compose.yml` apunta al modelo individual experimental.

## Experimento BDWaste v1: materiales individuales

Reproducir el experimento con el DINOv2 ViT-B/14 local. Las imágenes se agrupan por similitud DINO ≥0,995; esta aproximación no reemplaza IDs originales de objeto/sesión:

```bash
.venv/bin/python scripts/train_bdwaste_individual.py --cosine-threshold 0.995
```

El clasificador es `StandardScaler + LogisticRegression` sobre el token CLS congelado. Los manifiestos con splits, pares visualmente similares y métricas se escriben bajo `data/processed/`; el artefacto queda en `artifacts/model_bdwaste_individual/`. Una métrica perfecta de test en este dataset no demuestra generalización: todas las fotos vienen de una sola publicación/contexto y algunas etiquetas contienen composiciones repetidas. No hay test externo etiquetado disponible.

Para probar manualmente: ejecutar `uvicorn compost_ai.api:app --reload`, abrir `http://localhost:8000/docs`, usar `POST /api/v1/recognize`, adjuntar una imagen JPEG/PNG/WEBP y escoger `household`. El modelo y las reglas se cargan al inicio de la API; el backbone no se vuelve a cargar por petición.
