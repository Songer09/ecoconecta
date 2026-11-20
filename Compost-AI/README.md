# COMPOST AI

Sistema de IA independiente del cliente para reconocimiento visual de residuos, evaluación de incertidumbre y decisión ambiental configurable. Esta fase no implementa aplicaciones móviles.

## Estado

Se entrenó un primer modelo **experimental de materiales individuales** con BDWaste v1: cáscara de banano, papa, mango, bagazo de caña, plástico y vidrio. Usa DINOv2 ViT-B/14 congelado y un clasificador supervisado scikit-learn; el modelo anterior de escenas se conserva por separado y no se usa como modelo objetivo. La evaluación agrupada interna dio macro-F1 de 1,0, pero todas las imágenes vienen de una sola fuente y los grupos visuales aproximan los IDs originales ausentes: no es una estimación de generalización ni está listo para producción. El perfil doméstico aplica reglas independientes y devuelve revisión si la inferencia no supera los umbrales. Consulte el [informe del experimento individual](reports/bdwaste-individual-training-2026-11.md), la [auditoría de fuentes](reports/individual-waste-datasets-2026-11.md) y el [informe histórico de escenas](reports/organic-training-2026-11.md). Los artefactos se guardan en `artifacts/model_bdwaste_individual/` y se excluyen de Git.

## Inicio local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
# Para reproducir el modelo individual experimental:
.venv/bin/python scripts/train_bdwaste_individual.py --cosine-threshold 0.995
uvicorn compost_ai.api:app --reload
```

Visite `http://localhost:8000/docs`. Reconocer una imagen:

```bash
curl -X POST http://localhost:8000/api/v1/recognize \
  -F 'image=@residuo.jpg' \
  -F 'compost_profile=household'
```

## Docker

El entrenamiento genera `artifacts/model_bdwaste_individual/`; luego:

```bash
docker compose up --build
```

La imagen de Docker no incluye pesos ni dataset. Para GPU, configure una base/runtime CUDA y una build de PyTorch apropiados al host; la configuración incluida es CPU.

## Componentes

- DINOv2 ViT-B/14 congelado para embeddings visuales.
- Clasificador scikit-learn sobre embeddings; umbrales de confianza/margen y distancia para rechazar dudas/OOD.
- Reglas ambientales YAML independientes, con perfiles doméstico, comunitario e industrial.
- FastAPI REST con contrato OpenAPI y pruebas.

## Documentación

- [Arquitectura](docs/ARCHITECTURE.md)
- [Datasets y licencias](docs/DATASETS.md)
- [Captura, etiquetado y preparación de fotos faltantes](docs/IMAGE_COLLECTION_WORKFLOW.md)
- [Entrenamiento y métricas](docs/TRAINING.md)
- [Contrato API](docs/API.md)
- [Informe real de preparación, entrenamiento, métricas y pruebas](reports/model-training-2026-11.md)

Ejecute pruebas con `pytest`. Dependencias Python fijadas en `pyproject.toml`; runtime Python 3.11. El backbone de Meta se identifica como `facebook/dinov2-base`.
