# API REST v1

## `POST /api/v1/recognize`

Content type: `multipart/form-data`.

| Campo | Tipo | Requerido | Valores |
|---|---|---:|---|
| `image` | archivo | sí | JPEG, PNG, WEBP; máximo por defecto 10 MiB |
| `compost_profile` | texto | no | `household` (predeterminado), `community`, `industrial` |

Respuesta (200):

```json
{
  "request_id": "<uuid generado por el servidor>",
  "status": "recognized | review_required | unknown",
  "material": "<material o null>",
  "predicted_class": "<clase o null>",
  "waste_category": "organic | inorganic | null",
  "confidence": "<valor medido o null>",
  "confidence_calibrated": false,
  "confidence_margin": "<valor medido o null>",
  "out_of_distribution": "<booleano calculado>",
  "environmental": {
    "decision": "COMPOSTABLE",
    "profile": "household",
    "reason": "The predicted material is explicitly allowed by the household rules."
  },
  "justification": "<motivo de la regla ambiental>",
  "handling_recommendation": "<recomendación segura o revisión manual>",
  "manual_review_required": true,
  "model_version": "<versión del artefacto>",
  "warnings": [],
  "metadata": {"candidate_class": "<clase candidata>", "ood_distance": "<distancia calculada>"}
}
```

`confidence` es la probabilidad máxima sin calibración posterior mientras `confidence_calibrated` sea `false`; no debe interpretarse como garantía de corrección. `waste_category` solo se devuelve para clases mapeadas explícitamente por las reglas ambientales. Las clases desconocidas, las clases no calibradas o cualquier decisión `REQUIRES_REVIEW` marcan `manual_review_required: true`.

El artefacto predeterminado `0.3.0-bdwaste-individual-experimental` identifica seis clases visuales individuales de BDWaste v1: cáscara de banano, papa, mango, bagazo de caña, plástico y vidrio. Sus umbrales de aceptación provienen de validación interna y las confianzas no están calibradas. Con el perfil doméstico, las cuatro clases vegetales permitidas por `config/environmental_rules.yaml` pueden ser `COMPOSTABLE`; plástico/vidrio confiablemente identificados son `NO_COMPOSTABLE`; incertidumbre u OOD devuelve `REQUIRES_REVIEW`. El modelo no está validado para producción ni para materiales no incluidos. El modelo anterior de escenas se conserva como artefacto histórico. El contrato HTTP no depende del cliente móvil.

`environmental.decision` se limita a `COMPOSTABLE`, `NO_COMPOSTABLE`, `REQUIRES_REVIEW`. Errores: 413 tamaño excedido, 415 imagen inválida/formato no permitido, 422 perfil desconocido. Los errores siguen el formato JSON estándar de FastAPI.

Contrato OpenAPI: `/openapi.json`; interfaz: `/docs`. Mantener v1 compatible y versionar cambios incompatibles bajo otra ruta.
