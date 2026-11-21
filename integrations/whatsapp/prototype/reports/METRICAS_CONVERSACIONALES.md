# Métricas conversacionales

## Conversaciones sintéticas

Se enviaron los mismos 12 guiones al endpoint de demostración de FastAPI con PostgreSQL 18 y un esquema vacío por ejecución. Cada guion contiene entre uno y cuatro mensajes de contexto y termina con una confirmación escrita. La identificación de preguntas redundantes compara los campos que el bot pide con los que el guion ya había entregado. Una aclaración sobre la seguridad de un material se cuenta aparte de volver a pedir su nombre.

| Indicador | Antes | Después |
|---|---:|---:|
| Promedio de respuestas por guion ejecutado | 3,00 | 3,00 |
| Promedio y mediana de respuestas en guiones completados | 3,50 / 3,50 | 3,00 / 3,00 |
| Aclaraciones en total | 27 | 9 |
| Aclaraciones por guion | 2,25 | 0,75 |
| Casos que abrieron una revisión manual | 1/12 | 0/12 |
| Errores de enrutamiento en los avisos generados | 0 | 0 |
| Tiempo técnico medio y mediano para registros completados | 9,99 / 9,99 ms | 16,90 / 16,83 ms |

La duración corresponde al guion procesado en un cliente local, con mediciones auxiliares intercaladas. Excluye la espera real entre mensajes. Los tiempos de las dos versiones abarcan grupos distintos de guiones completados. Los avisos que llegaron a coordinación requieren asignación, programación y cierre humano. La fila de revisión manual solo cuenta escalamientos adicionales de materiales. El guion C11 pidió al vecino decidir sobre las pilas y este confirmó seguir solo con el cartón.

## Seguridad y operación

| Indicador comprobado | Antes | Después |
|---|---:|---:|
| Solicitudes antes de la confirmación | 0 | 0 |
| Recolecciones cerradas automáticamente | 0 | 0 |
| Programaciones inventadas | 0 | 0 |
| Puntos antes del cierre | 0 | 0 |
| Eventos inventados | 0 | 0 |
| Preguntas que exigieron kilogramos | 0 | 0 |
| Registros duplicados al reenviar el mismo webhook firmado | 0 | 0 |
| Errores en las entregas válidas de prueba al webhook | 0/2 | 0/2 |

La prueba de webhook rechazó la firma ausente. La suite de 29 pruebas incluye voz simulada y consentimiento, intento de alterar las instrucciones, aislamiento por propietario y colectivo, evento sin publicar y cierre idempotente. Con el proveedor HTTP simulado se comprobó que la salida libre no puede publicar una cita ni crear un aviso.

## Telemetría

`GET /api/v1/admin/metrics` agrega por separado simulaciones y piloto. `chat_analytics` almacena un identificador aleatorio por borrador activo, tipo de evento, fecha y atributos acotados. Registra inicio de conversación, intención y pertinencia, recuento de materiales, borrador iniciado, campos solicitados, confirmación, creación de avisos, derivación a coordinación, descarte explícito, envío, errores de IA, fallo de entrega y resultados del webhook. Los eventos no contienen teléfonos, direcciones, audios ni mensajes. El reporte calcula promedio y mediana de respuestas y duración por intento completado, junto con errores y latencia p50/p95 del proveedor cuando existe tráfico externo.

El abandono se etiqueta al rechazar un resumen o cancelar el borrador explícitamente. Los intentos sin confirmación ni rechazo quedan abiertos. No hay muestra de usuarios reales para estimar abandono, tiempo efectivo ni satisfacción. Tampoco hay muestras reales de latencia Gemini ni de errores de la API externa. Las pruebas del adaptador usaron respuestas simuladas.

## Reproducción

Se guardó una copia de los módulos Python y la migración inicial usados en la línea base en `baseline-ux.zip`. El evaluador crea y elimina un esquema de trabajo aleatorio. Ejecuta desde la carpeta del servicio con las dependencias de desarrollo y configura `TEST_DATABASE_URL` con un PostgreSQL de pruebas.

```sh
baseline="$(mktemp -d)"
unzip -q reports/baseline-ux.zip -d "$baseline"
python -m datasets.ux_benchmark --app-dir "$baseline" --output reports/ux-antes.json
python -m datasets.ux_benchmark --output reports/ux-despues.json
python -m datasets.evaluation --output reports/intenciones-mock.json
python -m pytest -q
ruff check app migrations tests datasets
```

`intenciones-antes-ux.json` contiene la reproducción de las 41 frases originales. `ux-antes.json` y `ux-despues.json` conservan respuestas sintéticas, recuentos exactos y matrices de confusión. Las tablas por clase de la batería de 56 frases aparecen al final.

## Precisión, recall y F1 por intención en 56 frases

| Intención | Casos | Precisión antes | Recall antes | F1 antes | Precisión después | Recall después | F1 después |
|---|---:|---:|---:|---:|---:|---:|---:|
| ambiguous | 2 | 40,0 % | 100,0 % | 57,1 % | 100,0 % | 100,0 % | 100,0 % |
| bye | 1 | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % |
| cancel | 2 | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % |
| collection | 26 | 100,0 % | 80,8 % | 89,4 % | 100,0 % | 100,0 % | 100,0 % |
| compost | 3 | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % |
| event | 2 | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % |
| hello | 1 | 0,0 % | 0,0 % | 0,0 % | 100,0 % | 100,0 % | 100,0 % |
| human | 1 | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % |
| material | 3 | 50,0 % | 100,0 % | 66,7 % | 100,0 % | 100,0 % | 100,0 % |
| modify | 2 | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % |
| offtopic | 3 | 75,0 % | 100,0 % | 85,7 % | 100,0 % | 100,0 % | 100,0 % |
| points | 2 | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % |
| recycling | 3 | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % |
| track | 2 | 100,0 % | 50,0 % | 66,7 % | 100,0 % | 100,0 % | 100,0 % |
| training | 3 | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % | 100,0 % |
