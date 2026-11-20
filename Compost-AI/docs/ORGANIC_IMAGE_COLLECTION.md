# Especificación de fotografías individuales — COMPOST AI

## Fuente pública que sí contiene residuos individuales

**BDWaste v1** es la fuente pública más útil encontrada para una semilla de reconocimiento por material. Mendeley declara **CC BY 4.0**. El artículo describe una colección primaria de residuos seleccionados, con consentimiento de propietarios, fotografiados en cuatro zonas de Dhaka con cuatro modelos de teléfono. La ficha informa 2.625 imágenes; el artículo describe 2.497 crudas, una diferencia no explicada por los autores. Se descargaron diez carpetas de clase y se verificaron sus hashes; el detalle está más abajo.

El artículo también indica que las fotos fueron tomadas desde distintos ángulos y que los nombres se sustituyeron por números. No publica `object_id`, sesión, localidad, dispositivo ni partición por imagen. Hasta completar la inspección visual y agrupar duplicados/ráfagas, **no contar cada foto como un objeto físico independiente ni usar una partición aleatoria como test final**.

Se descargaron por separado diez ZIP de clase y se verificó su SHA-256 con la API pública de Mendeley. Los 1.240 archivos de imagen abren correctamente; 1.114 tienen SHA-256 único dentro de sus respectivas clases. El hash único no garantiza que sean objetos físicos distintos: no hay identificadores de objeto/sesión y algunas fotos casi idénticas requieren revisión. El muestreo visual indica que el conteo bruto no equivale al número de ejemplos etiquetados limpios:

| Etiqueta del archivo | Archivos | Hashes únicos | Hallazgo de calidad |
|---|---:|---:|---|
| `Banana peel` | 123 | 122 | Muestra: cáscara separada en la mayoría; candidata inicial. |
| `Potato Peel` | 130 | 126 | Algunas fotos muestran papas enteras; requiere retirar positivos falsos al curar. |
| `Mango Peel` | 121 | 121 | Muestra: piezas de cáscara; candidata inicial, aunque el EXIF apunta a un solo teléfono. |
| `Sugarcane husk` | 125 | 117 | Muestra: fibra/cáscara de caña; candidata inicial, pero duplicados y un solo teléfono. |
| `Plastic` | 119 | 119 | Control de material; varias fotos agrupan objetos y envases. |
| `Glass` | 120 | 120 | Control; incluye fragmentos. Solo manipular con protección. |
| `Cane` (nombre del archivo) | 120 | 120 | La muestra son latas aplastadas con residuos de etiqueta; candidata a `metal_can`, sujeta a revisar las 120. |
| `Egg shell` | 131 | 130 | Varias fotos incluyen huevos enteros; no usar como clase limpia hasta curarlas. |
| `Lemon Peel` | 125 | 125 | La muestra contiene limones enteros y cortados, no solo cáscaras descartadas; excluir como `lemon_peel`. |
| `Shell of Malta` | 126 | 14 | 112 rutas son duplicados exactos, la mayoría de una misma foto; excluir. |

No aparecen fechas de captura en EXIF ni `object_id`/`session_id` por imagen. La cámara puede leerse en 1.077 imágenes, pero algunas clases están asociadas a un solo modelo. Se conserva el manifiesto sin splits; no se presenta una partición aleatoria como test independiente. Los originales permanecen intactos. Código: `scripts/audit_bdwaste_classes.py`; manifiesto y conteos bajo `data/processed/bdwaste-individual-*`.

**Decisión de suficiencia:** BDWaste sí aporta ejemplos con licencia clara para una semilla estrecha de clasificación de materiales individuales. No es suficiente para demostrar que el sistema funcionará en fotografías reales locales: no proporciona grupos de objeto/sesión, concentra dispositivos y condiciones de captura, y parte de las etiquetas no corresponde limpiamente al nombre de la carpeta. Se puede entrenar un prototipo con el subconjunto curado, pero no se debe publicar una métrica de test independiente hasta recolectar imágenes propias por objeto y reservar una campaña bloqueada.

## Primer alcance recomendado del modelo individual

Semilla de entrenamiento candidata (una etiqueta visual por imagen), después de curación manual de todo el subconjunto que se use:

1. `banana_peel`
2. `potato_peel` (después de excluir papas enteras)
3. `mango_peel`
4. `sugarcane_husk`
5. Controles de material no compostable: `plastic`, `glass`; `metal_can` solo después de confirmar la carpeta `Cane` completa
6. `unknown_or_ambiguous`: ejemplos de prueba de rechazo, no una clase positiva que permita compostar.

No usar `lemon_peel` ni `malta_citrus_peel` de estos ZIP; la primera carpeta tiene fruta entera/cortada y la segunda duplicados masivos. `eggshell` queda pendiente de curación manual por las fotos de huevos enteros. Tampoco usar `paper`, `coffee cup` ni `fish ash` como compostables por la etiqueta “digestible” del dataset. “Papel” no informa recubrimientos, “coffee cup” parece etiquetar el recipiente y `fish ash` requiere interpretación; mantenerlos fuera de clases automáticas hasta anotación independiente.

## Fotografías propias necesarias

Las fotos propias son necesarias para adaptar las clases a residuos locales y medir generalización en una fuente no vista. Para el primer modelo material, recopilar siete clases: cuatro orgánicas (cáscara de banano, cáscara de papa, cáscara de mango y bagazo/cáscara de caña) y tres controles no compostables (plástico, vidrio y lata de metal). La lata sigue pendiente de confirmar en BDWaste, pero es un negativo útil que COMPOST AI debe aprender a reconocer. Por **cada clase**, el lote recomendado es:

| Partición | Objetos físicos únicos por clase | Fotos por objeto | Fotos por clase |
|---|---:|---:|---:|
| Entrenamiento local | 100 | 2 | 200 |
| Validación | 25 | 2 | 50 |
| Test bloqueado | 50 | 2 | 100 |
| **Total por clase** | **175** | | **350** |

Esto da **2.450 fotos propias** para siete clases, de **1.225 objetos físicos distintos**. Mantener todas las vistas de un objeto en un solo split. Capturar test en una sesión/campaña posterior, sin reutilizar esos objetos en entrenamiento o validación. Si no se pueden recopilar todas, piloto reducido de cuatro clases (banano, mango, plástico y vidrio): **1.400 fotos** de **700 objetos físicos distintos**, con el mismo reparto por clase. Estas cantidades son una meta inicial para entrenar/evaluar; no garantizan por sí solas una precisión de producción.

Además, reunir **100 fotos de rechazo**: dos vistas de 50 objetos no soportados o ambiguos (por ejemplo: cerámica, textil, empaque multicapa, papel recubierto, cuero, batería, residuo contaminado o mezcla de varios objetos). Registrar estos ejemplos como `unknown_or_ambiguous`; se usan para evaluar rechazo y nunca se convierten en clase compostable. Para una estimación de rechazo menos frágil, ampliar luego a 50 objetos por cada familia desconocida relevante.

El conjunto público BDWaste puede aportar ejemplos de entrenamiento adicionales para clases que sobrevivan la auditoría. No sustituye las 50 piezas de test independientes por clase y no permite una evaluación por sesión mientras falten sus IDs de objeto.

## Cómo tomar cada foto

- Un residuo u objeto principal por foto; no platos completos, bolsas cerradas, mesas con muchos objetos ni escenas de restaurante.
- Fotografiar residuos después de desecharlos: cáscara separada, resto cortado, hoja seca, posos usados. Una fruta/verdura entera no es una cáscara ni un residuo.
- Tomar dos encuadres del **mismo objeto**: vista superior y oblicua. Las dos fotos conservan el mismo `object_id` y siempre quedan en la misma partición.
- El residuo ocupa aproximadamente 50–80 % del cuadro. Mantener el objeto completo y enfocado; no recortar partes que cambien la identificación.
- Variar de forma realista el fondo, la luz y el recipiente entre objetos. No usar un color de fondo distinto por clase.
- Para cada clase, incluir estados realistas separados (fresco, seco/marchito, parcialmente deteriorado) y anotarlos; no mezclar un estado con una etiqueta ambiental diferente.
- Incluir tomas limpias y contaminadas solo como etiquetas distintas. Plástico adherido, etiquetas, tierra, grasa, vidrio u otros contaminantes visibles deben marcar `contaminated=true` y pasar a revisión.
- No incluir personas, caras, direcciones ni información privada. Guardar permiso/autoría para las fotos propias y no copiar fotos web sin licencia explícita.

## Metadatos obligatorios

Por archivo: `image_id`, `object_id`, `session_id`, `label_material`, `label_category`, `contaminated`, `condition`, `view` (`top`/`oblique`), `capture_date`, `device`, `site_group`, `split`, `photographer`, `license_or_consent`, `sha256`, `notes`.

La anotación debe describir lo visible. La **decisión ambiental** se calcula después con reglas del perfil, no se usa como etiqueta visual. Mantener todos los archivos del mismo `object_id` y `session_id` en una sola partición. Reservar el test antes de comparar modelos y no ajustar thresholds con él.

## Aún sin fuente pública individual suficiente

BDWaste no establece cobertura suficiente para cáscara de naranja/limón (la carpeta de limón muestreada contiene fruta entera y cortada), restos de manzana, restos de verduras mixtas, hojas secas, césped, poda ni posos de café. Para cada clase específica nueva, recopilar 175 objetos únicos y dos fotos por objeto (350 fotos), con el mismo reparto 100/25/50 objetos para train/validación/test. Para `eggshell`, curar y etiquetar únicamente cáscara visible, excluyendo huevo entero; la colección propia también debe aportar 175 objetos. Hasta contar con esos datos, devolver categoría general o revisión, sin inventar una clase detallada.
