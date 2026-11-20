# Arquitectura

```text
Cliente futuro → POST /api/v1/recognize → validación de archivo
                                      → DINOv2 ViT-B/14 → clasificador sklearn
                                      → umbrales de confianza/OOD
                                      → motor de reglas por perfil
                                      → JSON estable
```

El reconocedor solo estima material/clase. El motor ambiental no recibe imagen ni embeddings y decide con reglas explícitas para `household`, `community` o `industrial`. Los valores iniciales de aceptación están vacíos, por lo que toda clase queda en `REQUIRES_REVIEW` hasta que una instalación local configure sus reglas. La configuración debe ser revisada por el operador de compostaje.

El proceso de API crea el extractor y el clasificador una vez en el ciclo de vida FastAPI. Se puede escalar con varias réplicas, cada una con su propia copia en memoria. La API no obliga a un cliente móvil ni depende de una tecnología de cliente.

## Contrato de inferencia

`POST /api/v1/recognize` usa `multipart/form-data`:

- `image`: JPEG, PNG o WEBP, hasta 10 MiB por defecto.
- `compost_profile`: `household`, `community` o `industrial`.

Respuesta JSON: incluye `request_id`, `status`, `material`, `predicted_class`, `waste_category`, `confidence`, `confidence_calibrated`, `confidence_margin`, `out_of_distribution`, `environmental`, `justification`, `handling_recommendation`, `manual_review_required`, `model_version`, `warnings` y `metadata`. `status` puede ser `recognized`, `review_required` o `unknown`. Si se rechaza una predicción, `predicted_class`, `material` y `waste_category` son `null`; `metadata.candidate_class` se conserva para revisión. La confianza actual no se calibró y el campo lo indica expresamente. Errores de archivo devuelven códigos HTTP 413/415; perfiles inválidos devuelven 422.

OpenAPI y Swagger UI están publicados en `/openapi.json` y `/docs`.

## Datos y particiones

El manifiesto guarda ruta, etiqueta, SHA-256 y split. Se eliminan duplicados byte a byte antes de la partición estratificada train/validation/test. Mantener imágenes de la misma escena/objeto en una sola partición es recomendable; para datasets que tengan identidad de escena se debe sustituir la partición aleatoria por un split agrupado para evitar fuga.

El código asume directorios por clase. Etiquetas específicas pueden usar `material__clase` (ej. `organico__cascara_banana`); adapte `materials` en `metadata.json` si se requiere otra taxonomía.

## Artefactos

- `classifier.joblib`: pipeline de escalado y regresión logística.
- `backbone/`: pesos DINOv2 ViT-B/14 y preprocesador serializados para inferencia local/offline.
- `metadata.json`: origen/revisión del backbone, etiquetas, mapeos, umbrales y centroides.
- `metrics.json`: resultado medido en el split de test.

No cargar artefactos `joblib` de fuentes no confiables. Para producción, almacenar artefactos con checksum, permisos restringidos y versión inmutable.
