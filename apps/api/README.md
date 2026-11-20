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

La sesión, los filtros de acceso y la recepción están implementados. La asignación, programación, cierre y cálculo de puntos corresponden a incrementos posteriores. Antes del cierre se debe acordar quién lo confirma y qué sucede cuando falta una regla de puntos aprobada.
