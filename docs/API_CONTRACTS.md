# Contratos API — borrador inicial

FastAPI debe generar OpenAPI. Los paths son propuestas de diseño y deben revisarse antes de congelarlos.

El contrato implementado de acceso, zonas y recepción de solicitudes está en
[`apps/api/openapi.json`](../apps/api/openapi.json). Consultar también la
[guía del backend](../apps/api/README.md) para permisos y ejemplos de uso.
Estos endpoints usan los valores de estado y flujo en español del esquema PostgreSQL.

## Convenciones
- Prefijo `/api/v1`.
- JSON UTF-8.
- UUID interno.
- Errores con código estable, mensaje seguro y correlation_id.
- Paginación por cursor o limit/offset con límites.
- Autenticación por sesión/token seguro; decidir mecanismo y almacenamiento antes de producción.
- No incluir dirección/teléfono en listados generales.

## Endpoints propuestos
### Auth
- POST `/auth/login`
- POST `/auth/logout`
- GET `/auth/me`

### Catálogo y educación
El catálogo público y el progreso del perfil están implementados. Cada contenido
publicado cuenta como un módulo. La finalización la declara el usuario al pulsar
«Marcar como completado». No otorga puntos de recolección.

- GET `/public/education` lista módulos publicados. GET `/public/education/{module_id}` devuelve el contenido.
- PUT `/users/me/learning-progress/{module_id}` requiere sesión y conserva la fecha de la primera finalización.
- GET `/users/me/learning-progress` devuelve `completed`, `total`, `percentage` y `completions` con identificadores y fechas. El porcentaje se redondea al entero más cercano y vale cero con un catálogo vacío.
- Catálogo e historial admiten `limit` (1–100, por defecto 50) y `offset` (por defecto 0). Los totales abarcan todo el catálogo publicado. Retirar un módulo lo excluye del cálculo y republicarlo recupera la marca anterior.

#### Edición de módulos

Se requiere una sesión de administrador. Los campos de contenido son `title`,
`body` (texto plano), `category` y `flow` (general si se envía `null`).

- `POST /admin/education` crea un borrador y devuelve el módulo con su `updated_at`.
- `GET /admin/education` lista borradores y publicaciones con `limit` y `offset`. `GET /admin/education/{module_id}` carga el texto para editarlo.
- `PUT /admin/education/{module_id}` recibe el contenido completo, `is_published` y `expected_updated_at`. Enviar exactamente el valor de `updated_at` recibido, conservando sus microsegundos. Ante un 409, volver a cargar el módulo y revisar las diferencias antes de guardar.
- Publicar muestra el módulo en el catálogo inmediatamente. Retirar y republicar conserva el progreso de quienes lo completaron.

Otros endpoints propuestos del catálogo:
- GET `/public/materials`
- GET `/public/collection-info`

### Solicitudes
- POST `/requests`
- GET `/requests/{request_id}` (acceso propietario o rol autorizado)
- GET `/coordinator/requests?flow=&status=&zone_id=`
- POST `/requests/{id}/assignments`
- POST `/requests/{id}/schedule`
- POST `/requests/{id}/cancel`

### Recolecciones
- POST `/requests/{id}/collection`
- POST `/collections/{id}/items`
- POST `/collections/{id}/confirm`
- GET `/collectors/{id}/collections`
- GET `/reports/collections`

### Zonas y disponibilidad
- GET `/zones`
- GET `/collectors/availability`
- Admin CRUD `/admin/zones`, `/admin/collectors`, `/admin/schedules`

### Puntos
- GET `/points/rules` (admin)
- POST `/admin/points/rules`
- GET `/users/me/points`
- GET `/users/{id}/points-ledger` (autorizado)

### WhatsApp
- GET `/integrations/whatsapp/webhook` (verificación)
- POST `/integrations/whatsapp/webhook` (eventos entrantes)
- POST `/admin/notifications/test` (solo entorno autorizado)

## Reglas de contrato
- No marcar request como SCHEDULED si falta assigned_collector_id, scheduled_at o confirmed_by.
- No aceptar cierre desde el frontend sin verificar rol y asignación en servidor.
- `POST /collections/{id}/confirm` debe ser idempotente.
- El servidor calcula puntos; nunca confiar en puntos enviados por el navegador.
- Cambios incompatibles requieren versión o migración coordinada.

## Estados propuestos
RECEIVED, UNDER_REVIEW, ASSIGNED, SCHEDULED, COLLECTED, CANCELLED.
Documentar transiciones permitidas y actor autorizado. No permitir saltos arbitrarios.

> **ACTUALIZACIÓN v3:** Este documento proviene de la versión 2. Si contradice `AGENTS.md`, `docs/DECISION_LOG.md`, `docs/FOUNDATION_BRIEF.md` o `docs/DESIGN_GUIDE.md`, prevalece v3. En particular, Twilio está permitido para prototipo, la IA tiene libertad de elección bajo controles de privacidad/seguridad y la aplicación usa una única PostgreSQL compartida.

## Agenda comunitaria

Todos los paths usan el prefijo `/api/v1`.

- `GET /public/events` devuelve eventos publicados próximos y en curso, en orden de inicio. Con `include_past=true` incluye también los finalizados. Admite `limit` (1–100) y `offset`.
- `GET /public/events/{id}` abre el detalle de cualquier evento publicado, incluso después de su fin. Un evento retirado o en borrador devuelve 404.
- `POST /admin/events` crea un borrador con `title`, `description`, `organizer`, `location`, `starts_at` y `ends_at`. Los textos se presentan como texto plano. Ambas fechas llevan zona horaria y el fin debe ser posterior al inicio. Frontend presenta las horas en `America/Bogota`.
- `GET /admin/events` y `GET /admin/events/{id}` permiten al administrador consultar publicaciones y borradores, incluida la versión `updated_at`.
- `PUT /admin/events/{id}` recibe todos los campos de contenido, `is_published` y `expected_updated_at`. Este último debe conservar exactamente la versión recibida. Un 409 requiere recargar el evento y revisar los cambios antes de guardar.
