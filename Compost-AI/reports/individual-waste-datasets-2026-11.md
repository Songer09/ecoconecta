# Fuentes de imágenes de residuos individuales — auditoría 2026-11

## Decisión ejecutiva

La fuente pública que mejor cumple el requisito es **BDWaste v1**. Su ficha Mendeley declara CC BY 4.0 y el artículo describe fotos primarias de residuos, cuatro zonas de Dhaka, cuatro teléfonos y consentimiento explícito. Descargamos diez carpetas de clase por separado y verificamos los tamaños y SHA-256 publicados. El subconjunto tiene 1.240 archivos válidos, 0 corruptos y 1.114 hashes únicos dentro de clase.

Esto permite preparar una semilla de entrenamiento para un prototipo pequeño, especialmente cáscara de banano, papa, mango y bagazo de caña, junto con plástico y vidrio como controles. **No basta para afirmar que el reconocedor funcionará en fotos nuevas de COMPOST AI ni para calcular una prueba independiente**: los archivos carecen de `object_id` y `session_id`, no incluyen fecha EXIF, algunos nombres de carpeta no corresponden a lo que aparece en la imagen, y la fuente es Dhaka con capturas relativamente controladas. Hace falta recolectar datos propios siguiendo [`docs/ORGANIC_IMAGE_COLLECTION.md`](../docs/ORGANIC_IMAGE_COLLECTION.md).

## Fuentes comprobadas

| Fuente | Derechos y procedencia | Calidad para residuo individual | Decisión |
|---|---|---|---|
| [BDWaste v1 / Mendeley](https://data.mendeley.com/datasets/96g5pgfnfw/1) | Ficha: CC BY 4.0. Artículo: recolección primaria en Dhaka y consentimiento explícito para imágenes de residuos. La ficha anuncia 2.625 imágenes; el artículo informa 2.497 originales y enumera 20 tipos. | Carpetas por etiqueta, nombres numéricos y varias fotos por categoría, pero sin IDs de objeto/sesión. La revisión local encontró etiquetas con contaminación semántica y repetición masiva en una carpeta. | Incorporar solo subconjuntos curados y con atribución. No crear un test aleatorio ni atribuir independencia por foto. |
| [TU Wien — Domestic Organic Waste](https://researchdata.tuwien.at/records/27k90-dvw73) | Ficha describe consentimiento escrito y permite descargar 5,1 GiB, pero el campo Rights/License está vacío. | 450 fotos domésticas de una familia: 119 orgánicas puras, 324 con contaminantes, 7 de fondo, máscaras. Principalmente etiquetas amplias de escena/segmentación, no taxonomía de restos individuales. | No descargar ni usar hasta obtener una licencia/permiso explícito; incluso con permiso, no sustituye la colección por material específico. |
| [RealWaste / UCI](https://archive.ics.uci.edu/dataset/908/realwaste) | La ficha UCI declara CC BY 4.0; el README del ZIP ya descargado declara CC BY-NC-SA 4.0. | Clasificación de materiales en entorno de vertedero; no se orienta a las clases orgánicas específicas del objetivo. | Excluido hasta resolver formalmente la contradicción de licencia. |
| [Waste Classification Dataset / Mendeley](https://data.mendeley.com/datasets/n3gtgm9jxj/1) | La ficha muestra CC BY 4.0, pero declara derivación desde Kaggle; no se pudo confirmar que ese permiso abarque cada imagen original. | Etiquetas binarias `Organic`/`Recyclable`, sin clases específicas de residuo individual. | Excluido por trazabilidad insuficiente y etiqueta demasiado amplia. |
| [UC-Food-Waste](https://github.com/CollaborativeRoboticsLab/UC-Food-Waste) | No se identificó una licencia de datos que otorgue claramente los derechos de reutilización de las imágenes. | Multicámara y laboratorio; “background organic” es contexto/placa, no clases como cáscara de banano o posos. | No incorporar sin autorización. |
| AI Services Berlin food-waste dataset | Tarjeta del dataset declara CC BY 4.0. | Platos después de comer, ingredientes/pesos y múltiples capturas de la misma comida; etiquetas de escena/receta, no objetos individuales. | No adecuado para entrenar etiquetas de material individual. |

El artículo de BDWaste está disponible en [PubMed Central](https://pmc.ncbi.nlm.nih.gov/articles/PMC10879810/). La diferencia entre ficha y artículo en número total de fotos/clases queda documentada; los conteos de abajo son los archivos realmente descargados, no el total anunciado.

## Auditoría local de BDWaste

Los ZIP individuales están en `data/raw/downloads/bdwaste-v1/`; su inventario de tamaño/hash está en `data/raw/downloads/bdwaste-v1/download-audit.json`. Los originales no se modificaron. La extracción auditada produjo `data/processed/bdwaste-individual-manifest.csv` y `data/processed/bdwaste-individual-audit.json`. El código está en `scripts/download_bdwaste_classes.py` y `scripts/audit_bdwaste_classes.py`.

| Etiqueta auditada | Archivos válidos | SHA únicos | Evaluación de uso |
|---|---:|---:|---|
| `banana_peel` | 123 | 122 | Semilla prometedora; la mayoría de la muestra muestra cáscara separada. |
| `potato_peel` | 130 | 126 | Semilla después de excluir imágenes con papas enteras y duplicados. |
| `mango_peel` | 121 | 121 | Semilla prometedora; EXIF concentrado en un teléfono. |
| `sugarcane_husk` | 125 | 117 | Semilla prometedora; auditar duplicados y dependencia de un teléfono. |
| `plastic` | 119 | 119 | Control de material; algunas fotos contienen varios envases/objetos. |
| `glass` | 120 | 120 | Control; incluye fragmentos y requiere manejo seguro al capturar datos nuevos. |
| `can_candidate` (carpeta `Cane`) | 120 | 120 | Muestra parece mostrar latas aplastadas; revisar la carpeta completa antes de renombrar/entrenar. |
| `eggshell` | 131 | 130 | Varias imágenes incluyen huevos enteros; curación manual pendiente. |
| `lemon_peel_candidate` | 125 | 125 | Muestra incluye limones enteros/cortados; no tratar como cáscara descartada. Excluir como clase de cáscara. |
| `malta_peel_candidate` | 126 | 14 | 112 rutas duplicadas por SHA; excluir. |

Otros límites: 1.078 imágenes tienen EXIF, 1.077 identifican dispositivo, ninguna registra fecha. Aparecen seis modelos de teléfono; las clases individuales no están balanceadas entre dispositivos. El `dHash` generó muchos pares de similitud por fondos claros repetidos, por lo que solo el SHA-256 se interpreta como duplicado exacto; la similitud perceptual requiere revisión visual. No hay identificadores de captura suficientes para agrupar con certeza imágenes del mismo residuo.

## Fotografías que COMPOST AI debe recopilar

Para un primer clasificador local que pueda evaluarse sin fuga por objeto, reunir **350 fotos por clase** de siete materiales: `banana_peel`, `potato_peel`, `mango_peel`, `sugarcane_husk`, `plastic`, `glass`, `metal_can`. Son **2.450 fotos de 1.225 objetos físicos distintos**, dos vistas por objeto:

| Split | Objetos distintos por clase | Fotos por objeto | Fotos por clase |
|---|---:|---:|---:|
| Entrenamiento | 100 | 2 | 200 |
| Validación | 25 | 2 | 50 |
| Test bloqueado | 50 | 2 | 100 |

Capturar `top` y `oblique` de cada objeto. Asignar `object_id` estable; conservar ambas vistas en un solo split. Hacer el test en una campaña/fecha posterior y no usarlo al elegir hiperparámetros o umbrales. El encuadre debe mostrar un residuo principal, no platos o escenas con varios residuos; usar fondos, recipientes, iluminación y dispositivos variados, sin un fondo exclusivo por etiqueta. Incluir variación realista de frescura y anotar contaminación. No incluir frutas enteras en las clases `*_peel`.

Si no se puede reunir la colección completa al principio, piloto de cuatro clases (`banana_peel`, `mango_peel`, `plastic`, `glass`): **1.400 fotos de 700 objetos** con los mismos tamaños de split. Añadir **100 fotos de rechazo** (dos vistas de 50 objetos desconocidos/ambiguos, por ejemplo cerámica, textiles, empaque multicapa, papel recubierto, batería, residuos contaminados y mezcla de objetos). Para evaluar bien OOD después, aumentar a 50 objetos por cada familia desconocida frecuente.

Para ampliar la clase orgánica detallada, reunir por cada material que hoy no esté soportado al menos el mismo lote de 175 objetos/350 fotos: cáscara de naranja, restos de verdura, hojas secas, césped, poda y posos de café. Huevo requiere un lote propio curado; no usar las fotos con huevo entero como ejemplos limpios de `eggshell`.

La plantilla de captura es [`data/collection/manifest_template.csv`](../data/collection/manifest_template.csv). Debe registrar etiquetas visibles, `object_id`, `session_id`, dispositivo, sitio, contaminación, consentimiento/licencia y hash. Para cada una de las siete clases, el nombre material describe lo que aparece en la foto; la compostabilidad se resuelve después con las reglas ambientales y el perfil configurado.

## Resultado de esta fase

- **Sí se consiguió** una fuente CC BY 4.0 de residuos individuales y diez clases ya están descargadas/verificadas localmente.
- **No se considera todavía suficiente** para una evaluación real de COMPOST AI ni para soportar todos los materiales solicitados.
- El siguiente bloqueo concreto es disponer de la colección propia con IDs de objeto/sesión, sobre todo de naranja, verduras, hojas, césped, poda, café y casos desconocidos. La guía especifica cómo capturarla y cuántas imágenes por split.
- No se entrenó ni se evaluó un nuevo modelo individual en este reporte. Los modelos existentes siguen siendo clasificadores de reciclables o escenas y no satisfacen este objetivo.
