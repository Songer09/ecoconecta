# Diálogo contextual de EcoConecta

## Comportamiento verificado

El gestor conserva en PostgreSQL el borrador, la intención principal, el tema actual, la pregunta activa, una pregunta de datos en pausa y el último cambio reversible. Una pregunta informativa invalida el permiso pendiente de una acción. Retomar un borrador puede volver a mostrar el resumen, pero el siguiente «sí» solo ejecuta una operación si responde a esa confirmación y el contenido del aviso coincide con el resumen.

En el diálogo D01 se ejecutaron estos turnos contra FastAPI y PostgreSQL en modo local:

| Vecino | EcoConecta |
|---|---|
| «Hola, tengo dos bolsas de cartón» | Indica que puede avisar a recicladores y pide la dirección. |
| «Manzana 12, casa 8» | Conserva la dirección y muestra el resumen del cartón. |
| «¿Y las cáscaras de banano se pueden reciclar?» | Explica que sirven para compost y pregunta si también tiene cáscaras para entregar. |
| «Sí, como un balde» | Añade el balde aproximado a las dos bolsas de cartón y pregunta si comparte la dirección. |
| «Sí» | Acepta la dirección compartida y pregunta por una preferencia opcional de horario. La base sigue sin avisos. |
| «Mañana por la mañana» | Resume los materiales y pide la confirmación de envío. La base sigue sin avisos. |
| «Sí» | Registra dos avisos. Quedan recibidos y sin programación. |

En D02 el vecino preguntó por un taller y por la borra de café, dijo «¿En qué íbamos?» y corrigió «Perdón, son cuatro». Se registró un aviso de cuatro bolsas con la dirección original. En D03 rechazó añadir periódico con «No, solo quería saber» y siguió con el cartón. Los mensajes completos y los recuentos por turno están en `contexto-despues.json`.

## Comparación local

Se ejecutaron 10 guiones nuevos y 43 turnos por versión. Cada indicador comprueba los contenidos esperados y, cuando aplica, el número de solicitudes que cambió en ese turno. Las frases, eventos y cuentas de la demo son sintéticos.

| Indicador | Antes | Después |
|---|---:|---:|
| Respuesta a la pregunta principal | 9/10 | 10/10 |
| Recuperación de una tarea interrumpida | 0/4 | 4/4 |
| Regresar, corregir y cancelar | 3/7 | 7/7 |
| Cambios de tema atendidos | 3/5 | 5/5 |
| Necesidades atendidas en mensajes con varias intenciones | 3/6 | 6/6 |
| Mensajes con una necesidad ignorada | 3/3 | 0/3 |
| Referencias y datos contextuales correctos | 4/7 | 7/7 |
| Finalización de los guiones que debían registrar | 3/6 | 6/6 |
| Confirmaciones interpretadas correctamente | 6/11 | 11/11 |
| Avisos creados en un turno que no debía registrar | 2 | 0 |
| Preguntas sobre datos ya entregados | 0 | 0 |
| Eventos o programaciones inventados en las comprobaciones | 0 | 0 |
| Intervenciones hasta terminar, media / mediana | 5,67 / 5 | 5,33 / 5 |

La duración en intervenciones usa los turnos del guion hasta el envío final y grupos distintos de guiones completados. Es un recuento de la simulación, sin tiempos de espera de personas reales.

En la batería anterior se conservaron los **12/12** diálogos, las **56/56** intenciones de aceptación y los **11/11** casos de varios materiales. La exactitud en frases indirectas pasó de **8/12 a 11/12**. El F1 macro del reto indirecto pasó de **36,36 % a 80,95 %**, y en las 56 frases de aceptación fue **100 %** en ambas versiones. «¿Hay algún encuentro donde expliquen cómo armar una compostera?» sigue llegando a educación sobre compost en el clasificador local; debería consultar capacitaciones. Las pruebas conservan esa distinción sin generar actividades inexistentes.

La suite pasó **42 pruebas**. Incluye el webhook y los permisos existentes, diálogos de varios turnos, correcciones, reversión, dos direcciones, consentimiento de voz y confirmaciones por escrito. Se comprobó con HTTP simulado que Gemini recibe los nombres de los campos presentes y materiales de catálogo, con la dirección fuera del resumen. El piloto con Gemini y transcripción reales requiere credenciales. El modo oficial mantiene la condición de autorización escrita para Gemini.

## Validación de Docker

Docker Compose aplicó Alembic `003`. Se verificó el panel por HTTP y se repitió D01 por la API del contenedor con una cuenta sintética separada. Solo el último turno creó dos avisos recibidos con la preferencia indicada y sin programación. La demo se publicó en el puerto 8092 porque otro proyecto de integración fotográfica ocupa el 8091.

## Archivos y reproducción

- `app/dialogue.py` y la migración `003_dialogue_context.py` guardan la memoria y el alcance de cada confirmación.
- `app/conversation.py` gestiona pausas, reanudación, correcciones, cambios de tema y consultas múltiples.
- `app/language.py`, `app/entities.py` y `app/providers.py` interpretan intenciones, frases parciales, cantidades y referencias con un contrato tipado.
- `app/channel.py` conserva la confirmación por escrito. `app/operations.py` crea avisos agrupados por colectivo y dirección. `app/knowledge.py` aporta la orientación revisada sobre cáscaras.
- `tests/test_dialogue_context.py`, `datasets/contexto_dialogos.jsonl` y `datasets/contexto_benchmark.py` comprueban los recorridos. Los JSON de resultados preservan las salidas antes y después.

Con un PostgreSQL de pruebas en `TEST_DATABASE_URL`, desde la carpeta del servicio:

```sh
baseline="$(mktemp -d)"
tar -xzf reports/contexto-baseline.tar.gz -C "$baseline"
python -m datasets.contexto_benchmark --app-dir "$baseline" --output reports/contexto-antes.json
python -m datasets.contexto_benchmark --output reports/contexto-despues.json
python -m datasets.ux_benchmark --output reports/ux-contexto-despues.json
python -m pytest -q
ruff check app migrations tests datasets
```
