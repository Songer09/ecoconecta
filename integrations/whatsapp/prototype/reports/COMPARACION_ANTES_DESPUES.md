# Comparación antes y después

La suite anterior se reprodujo con 14 pruebas aprobadas. En el conjunto de 41 frases se reprodujeron 87,80 % de exactitud de intención y 92,68 % de pertinencia. La versión nueva pasó 29 pruebas de EcoConecta y obtuvo 41/41 en ese conjunto conocido. Las 18 pruebas de COMPOST AI corresponden a un informe independiente y quedan fuera de esta comparación.

## Batería de aceptación de UX

| Indicador | Antes | Después |
|---|---:|---:|
| Intención correcta en 56 frases | 49/56 · 87,50 % | 56/56 · 100 % |
| Pertinencia correcta | 52/56 · 92,86 % | 56/56 · 100 % |
| F1 macro de intención | 84,37 % | 100 % |
| Recall de materiales | 27/45 · 60,00 % | 45/45 · 100 % |
| Precisión de materiales | 27/28 · 96,43 % | 45/45 · 100 % |
| Coincidencia de todos los materiales por frase | 41/56 · 73,21 % | 56/56 · 100 % |
| Coincidencia en frases con varios materiales | 0/11 · 0 % | 11/11 · 100 % |
| Detección y flujo correcto sobre materiales con flujo esperado | 27/43 · 62,79 % | 43/43 · 100 % |
| Cantidad numérica correcta | 12/27 · 44,44 % | 27/27 · 100 % |
| Unidad indicada correctamente | 10/27 · 37,04 % | 27/27 · 100 % |
| Diálogos completados con los mensajes previstos | 2/12 · 16,67 % | 12/12 · 100 % |
| Preguntas redundantes sobre datos ya entregados | 10/27 · 37,04 % | 0/9 · 0 % |
| Diálogos con al menos una petición de repetir un dato | 4/12 · 33,33 % | 0/12 · 0 % |
| Aclaraciones medias por diálogo | 2,25 | 0,75 |

Con el guion fijo, la versión anterior no recibe turnos extra para completar los casos bloqueados. Un caso se cuenta como completo únicamente cuando se guardan todos los materiales en los colectivos esperados y con un aviso por flujo. En la versión anterior, C08 y C09 completaron el registro. Los otros diez casos se ilustran en `ux-antes.json`.

## Reto adicional de formulaciones indirectas

| Indicador en 12 frases | Antes | Después |
|---|---:|---:|
| Intención | 5/12 · 41,67 % | 8/12 · 66,67 % |
| Pertinencia | 10/12 · 83,33 % | 10/12 · 83,33 % |
| F1 macro de intención | 25,00 % | 36,36 % |
| Recall de materiales | 8/13 · 61,54 % | 13/13 · 100 % |
| Todos los materiales en frases múltiples | 0/4 | 4/4 |
| Material y flujo esperado | 8/12 | 11/12 |
| Cantidad numérica correcta | 1/5 | 5/5 |
| Unidad correcta | 2/5 | 5/5 |

Ambas baterías son sintéticas y se usaron para desarrollar y comprobar el alcance. El reto adicional expone casos que siguen fallando. La meta del 95 % de intención queda pendiente fuera de la batería de aceptación. Para la evidencia por clase y la matriz de confusión, consulta `ux-antes.json` y `ux-despues.json`. También contienen las respuestas de los doce diálogos y los resultados de las comprobaciones de seguridad.
