# API de EcoConecta

Este primer incremento cubre el acceso al piloto, las zonas activas y la recepción de solicitudes. Usa Python 3.12, FastAPI, Pydantic, SQLAlchemy y Psycopg sobre la base PostgreSQL compartida.

## Desarrollo local

Desde `apps/api`, instalar el entorno con `uv sync --locked --extra dev`. El archivo `uv.lock` fija las dependencias. Con PostgreSQL local en funcionamiento, ejecutar en PowerShell:

```powershell
. ..\..\infra\use-local-db.ps1 -Role Owner
uv run alembic upgrade head
. ..\..\infra\use-local-db.ps1
uv run uvicorn ecoconecta.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Una base vacía se inicializa desde la revisión `0001_schema`. Una base que ya tenga el SQL de `34ad455` y carezca de revisión Alembic requiere comparar antes su catálogo con `db/schema.sql`. Solo si son equivalentes corresponde `alembic stamp 0001_schema`, seguido de `upgrade head`. El equipo debe conservar ese snapshot inicial y añadir nuevos cambios mediante revisiones. La cuenta de la API usa los permisos de ejecución de `ecoconecta_app`.

## Contrato para frontend y QA

Swagger UI está en `/docs` y el contrato generado por FastAPI en `/openapi.json`. Los endpoints comparten el prefijo `/api/v1`. Los valores de flujo y estado se serializan en español, igual que en PostgreSQL.

- `POST /auth/login` recibe `phone` con prefijo internacional y `password`. Requiere un usuario activo del piloto con contraseña Argon2id. Devuelve un bearer opaco válido por una hora. Mantener el token en memoria en la web, enviarlo en `Authorization: Bearer …` y usar HTTPS al desplegar. El límite inicial es de 20 intentos por minuto por IP de conexión. Acordar los proxies de confianza antes de desplegar.
- `GET /auth/me` devuelve identidad y rol. `POST /auth/logout` revoca la sesión.
- `GET /zones` lista las zonas activas para el formulario.
- `POST /requests` recibe `generator`, `flow`, `zone_id`, `contact_phone`, `address`, `preferred_time` y opcionalmente `observations`. El servidor deriva el solicitante de la sesión, enruta al colectivo correspondiente y registra el primer cambio de estado en la misma transacción. Devuelve 201 con ID, código, zona, flujo, fecha y estado `recibida`.
- `GET /requests/{request_id}` incluye datos operativos e historial para el propietario, coordinador autorizado o recolector con asignación activa.
- `GET /coordinator/requests` admite filtros `flow`, `status`, `zone_id`, `limit` y `offset`. Devuelve resúmenes sin teléfono ni dirección. El coordinador debe pertenecer al colectivo de su rol y tener asignada la zona mediante `coordinator_zones`.

Para usar el flujo con el piloto, el responsable debe configurar usuarios habilitados, zonas y colectivos. Para probarlo inmediatamente con datos sintéticos, configurar `TEST_DATABASE_URL` con la URL de propietario de una base PostgreSQL de pruebas cuyo nombre termine en `_test`, y ejecutar `uv run pytest -q` desde esta carpeta. Cada ejecución crea y retira su propio esquema aislado.

## Revisión, asignación y programación

Con el token del coordinador, ejecutar las operaciones bajo `/api/v1` en este orden.

1. `POST /requests/{id}/review` inicia la revisión de una solicitud recibida.
2. `GET /collectors/availability?request_id={id}` devuelve las franjas configuradas
   de los recolectores activos del colectivo que cubren la zona. Una persona puede
   aparecer en varias franjas. El día ISO va de 1 (lunes) a 7 (domingo). Las horas
   corresponden a la zona horaria de la franja y las fechas de vigencia son inclusivas.
3. `POST /requests/{id}/assignments` con `{"collector_id":"<uuid>"}` pasa la solicitud
   en revisión a asignada. El ID corresponde al usuario recolector.
4. `POST /requests/{id}/schedule` recibe `scheduled_start` y `scheduled_end` en ISO 8601
   con offset. La ventana debe ser futura, caber en una misma franja y estar libre.
   La lista de disponibilidad describe el horario habitual. La reserva comprueba
   ocupación en ese momento. Ante `409 schedule_overlap`, permitir elegir otra hora.
5. `GET /requests/{id}` incluye responsable, inicio, fin e historial. Los cuatro
   comandos de consulta y escritura respetan los permisos del colectivo y de la zona.

## Registro de materiales por el recolector

Las siguientes rutas se encuentran bajo `/api/v1`. El catálogo es público y las
operaciones de campo requieren la sesión del recolector con asignación vigente.

1. `GET /collector/requests` lista las solicitudes asignadas al usuario y admite
   `limit` y `offset`. En una solicitud programada, abrir el detalle habitual.
2. `GET /public/materials?flow=organico` (o `reciclable`) devuelve materiales
   activos con su unidad oficial. Una lista vacía significa que falta configurar el catálogo.
3. `POST /requests/{id}/collection` abre el registro de la recolección. Devuelve el
   mismo ID al reintentar. La hora de recolección corresponde a la apertura del registro.
4. `POST /collections/{id}/items` recibe `waste_type_id` y `quantity` decimal
   positiva, con hasta cuatro decimales. Mostrar la unidad devuelta por el catálogo.
   Una repetición idéntica devuelve 200 y el registro original. Si ya se guardó el
   mismo material con otra cantidad, se devuelve `409 material_already_recorded`.
5. `GET /requests/{id}/collection` recupera el registro y sus materiales al regresar
   a la pantalla. Un 404 para el recolector asignado puede indicar que aún no abrió el registro.

La solicitud sigue programada hasta confirmar el cierre. Falta acordar quién lo
confirma y cómo proceder si no hay una regla de puntos aprobada.
