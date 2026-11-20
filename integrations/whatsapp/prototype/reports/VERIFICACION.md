# Verificación de EcoConecta

## Ejecución local

- Docker Compose construyó el panel React, inició PostgreSQL 18 y aplicó la migración Alembic. La API y el worker quedaron activos.
- La API local devolvió HTTP 200 para salud, Swagger, panel y paquete JavaScript.
- Por HTTP se simuló una nota de voz orgánica con consentimiento, confirmación escrita, alerta a huerteros, asignación, programación y cierre. El saldo quedó en cero porque la demo no tiene regla de puntos cargada.
- Un residente distinto registró cartón. El aviso llegó a la coordinación de recicladores. Se comprobó el taller sintético publicado, la respuesta documentada sobre pañales y el límite frente a una pregunta sobre el Mundial.

## Pruebas automatizadas

| Área | Evidencia |
|---|---|
| Conversación | Avisos orgánico, reciclable y mixto, memoria de dirección, interrupciones, corrección, cancelación y revisión de especiales |
| Operación | Permisos por flujo y solicitud, rechazo de programación incompleta, cierre concurrente, una acreditación con la regla sintética |
| Canal | Verificación GET, firma HMAC, deduplicación persistente, consentimiento y revocación de voz, descarga HTTP simulada y control de host, política de envío y plantillas |
| IA y conocimiento | Contrato JSON de Gemini con HTTP simulado, recuperación PostgreSQL, filtrado de artículos borrador, descarte de instrucciones incrustadas y respuesta sin información inventada si falla el proveedor |
| Regresión | Suite existente del clasificador visual |

Resultado de `python -m pytest -q` con PostgreSQL 18 y un esquema aislado. **14 pruebas pasaron**. Hubo una advertencia de deprecación de AnyIO en TestClient. `ruff check app migrations tests datasets` pasó. `docker compose config --quiet` validó el archivo. La suite visual pasó sus **18 pruebas** con una advertencia de urllib3 sobre LibreSSL.

## Evaluación del clasificador local

Resultados de `python -m datasets.evaluation --output reports/intenciones-mock.json` sobre 41 frases sintéticas separadas de los ejemplos del prompt.

| Métrica | Resultado |
|---|---:|
| Exactitud de intención | 87,80 % |
| Exactitud de pertinencia | 92,68 % |
| F1 macro por intención | 88,54 % |
| Consultas educativas clasificadas como recolección | 0 de 9 |
| Latencia p50/p95 del clasificador local | 0,012 ms / 0,168 ms |

El JSON incluye precisión, recall, F1 y soporte por clase, además de la matriz de confusión. Varios ejemplos por clase y un conjunto sintético pequeño sirven como punto de partida para detectar confusiones. La latencia mide solo el clasificador en el equipo local. Faltan métricas de Gemini, calidad de transcripción real, latencia de proveedores, costo y entrega por WhatsApp.

## Validación externa pendiente

Las aplicaciones de Meta y de IA requieren credenciales y una cuenta con datos autorizados. Quedan por validar el webhook HTTPS público, las plantillas, las descargas reales de Ogg/Opus y la precisión de los modelos externos para el lenguaje de la comunidad. Gemini sigue sujeto a autorización escrita para la evaluación oficial. El catálogo, la agenda y las reglas de puntos del piloto dependen de los responsables del programa.
