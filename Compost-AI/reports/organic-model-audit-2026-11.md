# Auditoría inicial del modelo orgánico (histórico)

Fecha: 2026-11-19. Este documento conserva los resultados de la auditoría que precedió al nuevo entrenamiento. El estado actualizado, fuentes evaluadas y métricas del modelo orgánico están en el [informe de entrenamiento](organic-training-2026-11.md).

## Conclusión ejecutiva

El modelo actual **no reconoce residuos orgánicos**: fue entrenado solo con cartón, vidrio, metal, papel y plástico. Su 91,16 % de accuracy mide esas cinco clases en una partición aleatoria del mismo origen. No mide reconocimiento orgánico ni compostabilidad.

La prueba externa con WasteSegCluster encontró que 14 de 18 fotos anotadas únicamente como `Organic` fueron aceptadas por la API como `plastic`; su confianza media fue 0,9478. El rechazo OOD actual no previene esos errores. El motor ambiental, por su configuración conservadora, devolvió `REQUIRES_REVIEW` y no aprobó compostaje.

## 1. Auditoría de datos y etiquetas actuales

El manifiesto de entrenamiento contiene 977 imágenes únicas tras deduplicar 12 pares exactos de los 989 archivos del ZIP publicado. No había imágenes dañadas ni hashes idénticos con etiquetas incompatibles.

| Etiqueta actual | Train | Validación | Test | ¿Es material orgánico objetivo? |
|---|---:|---:|---:|---|
| cardboard | 299 | 65 | 65 | No |
| glass | 35 | 7 | 7 | No |
| metal | 63 | 13 | 14 | No |
| paper | 67 | 15 | 14 | No; está rotulado como papel, no como resto de papel compostable |
| plastic | 219 | 47 | 47 | No |

**Conteo orgánico etiquetado: cero.** No existen etiquetas verificadas para banano/cáscara, manzana, cítricos, mango, papaya, piña, papa/cáscara, verduras por especie, hojas, césped, poda, café, huevo, té, pan, arroz, carne, pescado, huesos, lácteos o restos con grasa. Tampoco hay una clase sanitaria o peligrosa. Vidrio (49 fotos totales) y papel (96) tienen poco soporte; el test de vidrio tiene solo siete ejemplos.

El conjunto proviene de dos grupos de captura. Ambos aparecen en train/valid/test: Calheta aporta 179/35/35 fotos; Urban and Household Waste, 504/112/112. No hay IDs de sesión, objetos físicos ni secuencias que permitan una separación independiente real. Por clase, Calheta no aporta vidrio y aporta solo cuatro fotos de papel en validación/train; por eso no es posible mantener todas las clases y a la vez separar sitio de forma íntegra con este dataset solamente.

## 2. Por qué las escenas orgánicas recibían la etiqueta plástico

La explicación más fuerte está comprobada por la configuración del sistema:

1. El clasificador es cerrado y tiene exactamente cinco etiquetas; no tiene una salida orgánica. Si decide aceptar, debe escoger una de esas cinco.
2. La cabeza se entrena en imágenes de materiales reciclables y la evaluación previa usa los mismos dos grupos de captura en los tres splits.
3. El endpoint procesa la foto completa. Las fotos externas son escenas acuáticas con varios objetos y fondos muy distintos. La anotación COCO describe instancias, no una clase global para la foto.
4. El rechazo mide distancia euclídea al centroide de la clase candidata en embeddings CLS sin escalado, con umbral 50,254 calibrado en el percentil 99 de validación **interna**. No se usó un conjunto OOD al escogerlo.

Resultados medidos en [la tabla por fotografía](wastesegcluster-api-stress.csv):

- Se probaron 41 fotos externas de validación/test con una instancia Organic; 21 también contienen una instancia Plastic y 18 tienen únicamente la categoría de instancia Organic.
- En las 41, la candidata fue `plastic` y la confianza media 0,9283. La API respondió HTTP 200 en todas: 36 `recognized`, 3 `unknown`/OOD y 2 `review_required`.
- En las 18 fotos con solo instancias Organic, 14 se aceptaron como `plastic` (confianza media 0,9478; rango 0,7481–0,9979), tres fueron rechazadas OOD y una requirió revisión. Es evidencia directa de fallo en este dominio.
- Distancia OOD de esas 41 fotos: 41,23–51,44. La mayoría cae dentro del umbral 50,25 pese al cambio de dominio. La distancia de las 147 fotos in-domain de test llegó a 49,12.

Se envió también el conjunto auditado completo de food waste (644 escenas): 644/644 dieron HTTP 200; 318 se marcaron `recognized`, 204 `unknown`/OOD y 122 `review_required`. Las candidatas fueron plastic 491, cardboard 67, paper 54, glass 24 y metal 8. En la carpeta “Vegetables waste”, 14/16 candidatas fueron plastic y 6/16 se aceptaron como plastic. Las carpetas son etiquetas de contexto, no de cada objeto; estos conteos no son accuracy, pero constituyen evidencia de sobreaceptación del dominio de platos/restos como clase reciclable. Los detalles por foto están en [food-waste-bangladesh-api-stress.csv](food-waste-bangladesh-api-stress.csv).

Como 21 escenas son mixtas, no se calculó accuracy sobre las 41. Las 18 fotos anotadas solo como Organic sí permiten medir el error de clase global bajo las categorías de instancia disponibles, aunque siguen siendo escenas de basura en canales y no el dominio típico de una cocina o cubo de compost.

## 3. Confusión y calibración disponibles

La matriz interna (clases en orden cardboard, glass, metal, paper, plastic) es:

```text
[[61, 0, 0,  1,  3],
 [ 0, 7, 0,  0,  0],
 [ 0, 0,13,  0,  1],
 [ 4, 0, 0, 10,  0],
 [ 1, 1, 1,  1, 43]]
```

No existe una matriz de confusión orgánica: no hay ninguna clase orgánica en el entrenamiento ni en el test interno.

Diagnóstico adicional de probabilidades, calculado sobre las 147 fotos de test internas sin ajustar umbrales: ECE de 10 bins **0,0584**, Brier multiclass **0,1478**, log loss **0,3433**. 126/147 fotos recibieron confianza máxima ≥0,90; en ese intervalo la accuracy observada fue 0,9524. Los bins pequeños y un solo origen no demuestran calibración transferible; la prueba externa muestra sobreconfianza fuera del dominio. La confianza es una probabilidad de la cabeza logística cerrada, no una probabilidad calibrada de “clase correcta” ante cualquier foto.

## 4. Avisos de LogisticRegression

El artefacto carga con `lbfgs`, `C=1.0`, `class_weight=balanced`, tolerancia 1e-4 y `n_iter_ = 42` de 2.000 máximas. Scaler, coeficientes e interceptos son finitos. El entrenamiento original emitió avisos temporales de overflow/división/operaciones inválidas dentro del optimizador, aunque terminó y produjo parámetros finitos. No se conservaron el log detallado del optimizador ni una caché de embeddings para reproducir exactamente esas operaciones; por eso no atribuyo el aviso a una causa única. Debe repetirse el ajuste con captura completa de warnings, revisar convergencia/gradiente y comparar regularización en validation antes de seleccionar otra cabeza.

## 5. Dataset orgánico localizado y auditado

[An image dataset for food waste in Bangladesh v1](https://data.mendeley.com/datasets/w68f9w6jmm/1) publica CC BY 4.0 en la ficha Mendeley; la descripción dice que los autores tomaron fotos en restaurantes, buffets y bodas. ZIP de 31.376.278 bytes, SHA-256 `1feeb673a658a376fbb93b21661ead7afce8901b0a5c18242106209551c442be`; ambas capas ZIP pasaron `unzip -t`. La ficha anuncia 645 imágenes; el archivo contiene **644**, todas decodificables y sin duplicados exactos. Se encontró un par perceptual cercano (IMG_4805/IMG_4806), fotos consecutivas de la misma escena.

| Carpeta de origen (no es una etiqueta de objeto) | Fotos auditadas |
|---|---:|
| Buffet Food waste | 91 |
| Food waste (General) | 145 |
| Restaurant food waste | 72 |
| Vegetables waste | 16 |
| Wedding Food waste | 320 |
| **Total** | **644** |

La inspección visual muestra restos servidos en platos, bandejas, utensilios y mesas, además de residuos vegetales. Las carpetas mayoritarias indican contexto de captura; no separan fruta, cáscara, ingrediente, carne, hueso, lácteo o grasa. “Vegetables waste” solo tiene 16 escenas sin subclases ni máscara por objeto. Se incorporó únicamente en una etiqueta experimental de **escena de desperdicio alimentario**; no permite asignar las categorías detalladas ni decidir compostabilidad.

### Otras fuentes investigadas

- [WasteSegCluster v4](https://data.mendeley.com/datasets/3wnf3n242s/4), CC BY 4.0, 1.947 imágenes y máscaras de instancias Organic/Paper/Plastic/Composite. Se auditó, pero son escenas acuáticas multiobjeto; hay 121 imágenes train sin anotaciones y tres pares perceptuales cercanos entre splits. Se usó solo para la prueba externa descrita, no para entrenar.
- [BDWaste v1](https://data.mendeley.com/datasets/96g5pgfnfw/1), ficha CC BY 4.0 y 21 clases descritas, entre ellas cáscaras de banano, papa, limón, mango, arroz y cáscara de huevo. ZIP de 7.144.426.327 bytes; no descargado. La descripción discrepa entre 2.624 y 2.625 imágenes y menciona augmentation; requiere auditar procedencia/duplicados y clases antes de incorporar.
- [Automatic waste management v1](https://data.mendeley.com/datasets/d4vsy9c9wk/1), ficha CC BY 4.0, 909 imágenes de cinco grupos incluyendo Organic, tamaño ZIP 2.123.210.640 bytes. La ficha describe capturas en cuatro localidades; etiquetas de orgánico son amplias. No descargado.
- [TU Wien Smart Trash Can](https://researchdata.tuwien.at/records/27k90-dvw73): 450 fotos domésticas, 119 orgánicas puras, 324 con contaminantes y masks; la sección Rights no especifica una licencia y el archivo pesa 5,1 GiB. **No se usa** hasta tener permiso/licencia explícita.
- [Kitchen Food Waste Segmentation](https://arxiv.org/abs/2401.15175) describe 2.912 fotos de restos domésticos y 19 categorías con anotaciones, pero no encontramos publicación abierta del dataset ni licencia que permita reutilizar las imágenes. Requiere autorización de titulares/autores.
- [Waste Classification Dataset](https://data.mendeley.com/datasets/n3gtgm9jxj/1) muestra CC BY 4.0 en Mendeley y clases binarias Organic/Recyclable, pero declara que deriva de un dataset de Kaggle. No se incorpora hasta verificar derechos sobre las fotos originales.

## 6. Plan de corrección basado en evidencia

1. **Congelar y etiquetar el baseline actual como no orgánico.** No reutilizar su 91,16 % como métrica de compostaje.
2. **Asegurar datos legales por objeto y fuente.** Prioridad inmediata: solicitar acceso/licencia al conjunto Kitchen Food Waste de 2.912 imágenes; evaluar BDWaste si se puede descargar y auditar de forma viable; usar Food Waste Bangladesh solo para una clase amplia `food_waste_scene`, nunca como especies inferidas por contexto.
3. **Completar la taxonomía con revisión humana.** Registrar clase por objeto, estado (fresco/seco/descompuesto), contaminación visible, grupo de captura/sesión, fuente y hash. No etiquetar por plausibilidad visual. Separar inicialmente frutas, vegetales/raíces, residuos vegetales, otros restos, orgánicos de condiciones especiales, no compostables y desconocidos; desglosar especies solo con cobertura suficiente.
4. **Separar por grupos antes del entrenamiento.** Mantener sesión/objeto/escenario/fuente íntegros en una sola partición. El test externo queda bloqueado; no se usa para seleccionar hiperparámetros ni calibrar. Con la fuente actual de reciclables esto no cubre cada clase, así que se necesita más de una fuente por material.
5. **Comparar A/B/C sobre el mismo cache de embeddings DINOv2:** LogisticRegression, SVM y MLP. Elegir por macro-F1/recall/precision orgánicos, falsas aceptaciones, matrices por clase y validación por grupo; no por accuracy global. Fine-tuning solo tras medir cobertura y recursos.
6. **Probar segmentación para fotos mixtas.** Un modelo de máscaras/objetos puede separar residuos; SAM 2 solo propone máscaras y requiere clasificador/validador de material posterior. Antes hacen falta máscaras y prueba independiente por objeto.
7. **Rehacer la calibración OOD.** Reservar positivos in-domain y fuentes OOD reales. Reportar AUROC/AUPR, FPR@95TPR y riesgo/coverage; probar umbrales por clase y calibración en validación separada. La confianza máxima sola no acepta una predicción.
8. **Mantener decisiones ambientales en revisión** hasta validar materiales, perfiles y reglas con operadores locales. Carne, pescado, huesos, lácteos, grasas, envases certificados y contaminantes no se aprueban solo por apariencia.

## 7. Estado actualizado

Se entrenó `0.2.0-organic-scene` usando escenas de desperdicio alimentario y un subconjunto conocido de reciclables. Las métricas holdout por contexto fueron perfectas, pero el origen de datos está confundido con la clase; estas cifras no prueban generalización a fuentes independientes. En el estrés externo, el rechazo a revisión funcionó por confianza/margen en las nueve escenas con instancias orgánicas, mientras que el umbral OOD no detectó el cambio de dominio. El motor conserva `REQUIRES_REVIEW` para ambas salidas y no aprueba compostaje. El detalle está en el [informe de entrenamiento orgánico](organic-training-2026-11.md).

La clasificación por objeto, clases orgánicas detalladas y test independiente por fuente siguen pendientes. No se requiere elegir ni desarrollar una aplicación móvil.
