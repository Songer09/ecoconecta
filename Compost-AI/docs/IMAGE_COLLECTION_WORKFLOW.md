# Captura y etiquetado de COMPOST AI

Este paquete crea una primera colección local lista para integrar con el entrenamiento DINOv2. No es una aplicación móvil. La plantilla ya reserva las rutas, etiquetas, IDs de objeto, vistas y splits: el trabajo de captura consiste en guardar las fotos en las rutas indicadas y completar los metadatos.

## Lote piloto listo

`data/collection/capture_manifest.csv` contiene **640 espacios de foto**:

- **600 fotos etiquetadas**: 12 materiales × 25 objetos físicos × 2 vistas.
- **40 fotos de rechazo**: 20 objetos desconocidos/ambiguos × 2 vistas.

Las 12 clases incluyen las seis actuales —banano, papa, mango, caña, plástico y vidrio— además de las seis prioridades nuevas —posos de café, hojas secas, hojas verdes, restos vegetales, cáscara de huevo y metal—. Repetir las clases actuales con fotos locales mezcla la fuente propia con BDWaste y ayuda a evitar que el origen de la foto sea la única pista de la clase.

Por clase, el manifiesto reserva:

| Split | Objetos distintos | Fotos por objeto | Fotos |
|---|---:|---:|---:|
| Entrenamiento | 15 | 2 | 30 |
| Validación | 5 | 2 | 10 |
| Test bloqueado | 5 | 2 | 10 |

Cada objeto debe tener una foto `top` y una `oblique`. Las dos pertenecen al mismo `object_id`, `session_id` y split. Los objetos del test se capturan en una campaña separada, posterior a entrenamiento y validación. Este tamaño es un **piloto experimental**, no una garantía de rendimiento de producción.

El resumen por clase está en `data/collection/capture_plan_priority.csv`; el vocabulario y estado de las clases, en `config/material_taxonomy.yaml`. La taxonomía objetivo completa incluye materiales adicionales para otra tanda: césped, ramas pequeñas, naranja, limón, manzana, piña, zanahoria, tomate, lechuga, cebolla, té, pan, arroz, carne, huesos y lácteos. No están marcados como soportados por el modelo.

## Cómo tomar y guardar las imágenes

1. Usa el `capture_manifest.csv` ya preparado. Si necesitas una campaña en blanco aparte, genera una en una carpeta nueva con `.venv/bin/python scripts/init_collection_plan.py --output data/collection/round2/capture_manifest.csv`.
2. Abre `capture_manifest.csv` en Excel, Numbers o LibreOffice. Conserva los IDs, etiquetas, nombres de archivo, vistas, sesiones y splits que ya están asignados.
3. Toma una muestra física nueva por cada `object_id`; no reutilices el mismo residuo para varios IDs. Dos encuadres de la misma muestra forman el par `top`/`oblique`.
4. Guarda cada foto exactamente en el campo `image_path`. Usa JPEG, PNG o WEBP, enfocada y con el residuo principal ocupando aproximadamente 50–80 % del cuadro.
5. Completa `subtype` si se conoce (por ejemplo, zanahoria dentro de `vegetable_scraps` o lata dentro de `metal`). Completa `contaminated`, `condition`, `capture_date` (AAAA-MM-DD), `device`, `site_group`, `photographer` y `license_or_consent`.
6. Mantén cada campaña separada: `capture_train_01`, `capture_validation_01`, `capture_test_01` y `capture_ood_test_01`. La plantilla preasigna estos IDs; cámbialos solo si todas las fotos de una sesión siguen juntas en un mismo split.

No fotografíes fruta o verdura entera como si fuera cáscara/resto. Captura cáscaras separadas; posos después de preparar el café; cáscara de huevo vacía y sin huevo entero; hojas secas y verdes separadas; bagazo ya prensado; y residuos vegetales realmente descartados. Para `vegetable_scraps`, anota el subtipo y mezcla tipos entre objetos, no dentro de una foto. Para plástico, metal y vidrio, etiqueta el material visible, no si es reciclable. No fotografíes plásticos rotulados “compostables” como plástico convencional sin anotarlo en `notes`; no se permite que la imagen por sí sola autorice compostaje.

Varía de forma natural los fondos, recipientes, luz, dispositivos y sitios entre objetos. No asignes un fondo o una sesión exclusiva a cada clase. El test se mantiene bloqueado y se captura en una sesión independiente. Para vidrio, fotografía sin manipular fragmentos peligrosos.

En `license_or_consent`, registra `photographer_owned` para imágenes propias o una referencia concreta al permiso. No uses imágenes web sin derechos confirmados. Evita caras, direcciones y otros datos personales.

Para `unknown_or_ambiguous`, usa objetos fuera de alcance, mezclas, residuos con contaminación o materiales que no puedan identificarse. Explica el motivo en `notes`. Estas 40 fotos se reservan para rechazo/OOD; **no se añaden como una clase compostable**.

## Validar y producir el manifiesto de entrenamiento

Con las fotos en su sitio y el CSV completado, ejecuta:

```bash
.venv/bin/python scripts/prepare_collection.py
```

El validador comprueba que los archivos existen y se decodifican, que hay exactamente dos vistas distintas por objeto, que la etiqueta pertenece a la taxonomía, que los metadatos de derechos están completados, que no hay hashes duplicados y que `object_id`/`session_id` no cruzan splits. Escribe el detalle en `data/processed/collection-validation-report.json`.

Para admitir una clase nueva al entrenamiento, el validador exige como mínimo 10 objetos de entrenamiento, 3 de validación y 3 de test; las restantes quedan pendientes y no bloquean las clases que sí cumplen. Las seis clases del baseline BDWaste se conservan aunque la nueva captura local de alguna esté incompleta. El objetivo del piloto sigue siendo 15/5/5.

Si hay clases aptas, el script crea `data/processed/training-ready-expanded-manifest.csv`, que combina el subset BDWaste actual con fotos locales, y `data/processed/collection-ood-manifest.csv`, separado para medir rechazo. Para entrenar una nueva versión sin reemplazar el modelo actual:

```bash
.venv/bin/python scripts/train_bdwaste_individual.py \
  --manifest data/processed/training-ready-expanded-manifest.csv \
  --out artifacts/model_bdwaste_collection_expanded \
  --allow-new-classes \
  --cosine-threshold 0.995
```

El entrenamiento conserva los splits suministrados, vuelve a agrupar por IDs de objeto y similitud DINOv2, y aborta si un grupo aparece en más de una partición. El nuevo artefacto será `0.4.0-material-expansion-experimental`; la API solo debe apuntar a esa versión después de revisar el informe de métricas y configurar reglas ambientales explícitas para las etiquetas añadidas. Mientras una clase no esté configurada en reglas, la API la mantiene en revisión.

El script de inicialización no sobrescribe un manifiesto ni un plan de cuotas que ya existan. Para preparar una plantilla vacía aparte, usa una carpeta nueva; después ajusta `image_path` para que las nuevas imágenes queden bajo `data/collection/images/` antes de validarlas.

## Expansión posterior

La siguiente tanda reserva otras 16 clases de la taxonomía. Repite el mismo lote de 25 objetos y dos vistas por clase: **800 fotos** para césped, ramas pequeñas, naranja, limón, manzana, piña, zanahoria, tomate, lechuga, cebolla, té, pan, arroz, carne, huesos y lácteos. Carne, huesos y lácteos pueden entrenarse como reconocimiento visual, pero sus reglas ambientales deben permanecer en `REQUIRES_REVIEW` salvo que una instalación específica los autorice.
