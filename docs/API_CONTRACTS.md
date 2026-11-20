# Contratos API — borrador inicial

FastAPI debe generar OpenAPI. Los paths son propuestas de diseño y deben revisarse antes de congelarlos.

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
- GET `/public/education`
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

