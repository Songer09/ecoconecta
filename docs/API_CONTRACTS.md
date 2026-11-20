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

## Comunidad y acceso al piloto

- `GET /public/community` entrega dos fichas públicas con nombre, descripción y enlace oficial. El contenido se versiona con la API.
- `GET /admin/users` lista identificador, nombre, rol y estado de cuenta y de piloto. Acepta `limit` (1–100) y `offset`.
- `POST /admin/users` registra un solicitante habilitado con `full_name`, teléfono E.164 en `phone` y `password` de 12 a 256 caracteres. Un teléfono duplicado devuelve 409.
- `PUT /admin/users/{user_id}/pilot-access` recibe `is_pilot` booleano. Retirar acceso revoca las sesiones. Reactivarlo requiere iniciar sesión de nuevo. Solo administración puede gestionar usuarios y las cuentas administrativas están protegidas.


## Operación del piloto

Los paths siguientes llevan el prefijo `/api/v1`. El [OpenAPI](../apps/api/openapi.json) contiene los esquemas y métodos.

- Administración configura colectivos, zonas, materiales y horarios públicos. Al crear personal asigna el colectivo, el rol y las zonas. Para recolectores configura vigencia de cobertura y franjas con horas locales de Bogotá. Una cuenta puede pertenecer a más de un colectivo. La disponibilidad se cambia por colectivo.
- El vecino puede actualizar su nombre y perfil de generación, ver sus solicitudes, consultar movimientos y canjear premios. En cada intento de canje, el frontend genera un UUID en `idempotency_key` y conserva ese UUID al reintentar la misma operación. Administración ajusta existencias enviando el stock esperado.
- El coordinador consulta solicitudes por ámbito, estado, zona y período. Los períodos de los reportes incluyen el inicio y excluyen el fin. Los pesos se agrupan por unidad. El valor de compra en COP usa las cantidades verificadas y la última tarifa oficial efectiva al recoger. Si falta un precio, el subtotal queda en `null` y se informa el número de partidas pendientes.
- Un solicitante propietario o un coordinador de su ámbito puede cancelar una solicitud recibida o en revisión con motivo. Si una parada programada falla antes de abrir el registro de campo, coordinación usa `POST /requests/{id}/missed` con motivo. La cita anterior queda en el historial y la solicitud vuelve a asignada. Programar una cita nueva vuelve a verificar cobertura y solapamientos.
- Huerta registra el faltante por zona, nombre y unidad. Una cantidad cero indica que quedó cubierto.

### Ruta y ubicación

La fecha de la ruta es local de Bogotá. `GET /coordinator/routes/{collector_id}` recibe `day` y `zone_id`. Al solicitar `suggest=true`, la primera parada con coordenadas es la cita más temprana. Con hasta ocho paradas geolocalizadas se minimiza la suma de distancias en línea recta desde esa primera parada. Para más paradas se elige sucesivamente la más cercana. Las paradas sin coordenadas quedan al final. La sugerencia desconoce vías, tráfico y tiempo de viaje. Coordinación revisa las horas de las citas y envía el orden completo de esa zona mediante PUT. El recolector consulta `GET /collector/route?day=…`, agrupado por zona.

El piloto técnico de posición se activa con `LIVE_TRACKING_ENABLED=1`. La web debe explicar el uso y solicitar permiso al recolector antes de enviar lecturas. Cada PUT en `/collector/location` reemplaza la última posición durante una parada programada para hoy. El frontend consulta `/coordinator/locations` periódicamente y presenta hora y precisión. Una comprobación visual se registra mediante `POST /coordinator/requests/{id}/verify-location`. El cierre mantiene su verificación de pesos independiente. Al dejar de compartir, la web debe enviar DELETE a `/collector/location`. La lectura caduca a los cinco minutos y un proceso de la API elimina lecturas caducadas cada quince segundos mientras el servicio está disponible. Validar el tratamiento con la Fundación antes de activar en el piloto real.

### Imagen y frontend

`POST /users/me/photo-preview` acepta el archivo como cuerpo binario autenticado JPEG o PNG (hasta 5 MiB y 12 megapíxeles). Devuelve JPEG normalizado, con dimensión máxima de 1600 píxeles, sin conservar el original. La respuesta permite previsualizar el material antes de la integración con visión. Si frontend y backend tienen orígenes diferentes, definir `FRONTEND_ORIGINS` como una lista de orígenes concretos separados por comas.

### Reconocimiento asistido

Configurar `COMPOST_AI_BASE_URL` con el origen interno del servicio. El vecino
envía JPEG o PNG en el cuerpo de `POST /api/v1/users/me/photo-recognition`.
El backend normaliza la foto y la envía en multipart a `/api/v1/recognize` con
el perfil doméstico. Devuelve la sugerencia, confianza, versión y necesidad de
revisión. Ante 503, la web conserva la selección manual. El usuario confirma el
flujo y material. El modelo requiere los artefactos indicados en su README.
