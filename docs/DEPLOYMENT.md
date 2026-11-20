# Desarrollo local y despliegue

## Requisitos
- Git.
- Python versión fijada por el equipo en `.python-version` o `pyproject.toml`.
- Node LTS fijado por `.nvmrc` o `package.json`.
- Docker Desktop / Docker Engine.
- Acceso a PostgreSQL en Docker.
- Credenciales WhatsApp solo para pruebas de integración; no requeridas para ejecutar el resto del MVP.

## Principio
Docker Compose debe levantar API, frontend si aplica y PostgreSQL. PostgreSQL es la única base de datos de aplicación. No usar SQLite como fallback.

## Variables esperadas
DATABASE_URL
APP_ENV
APP_SECRET_KEY
CORS_ALLOWED_ORIGINS
WHATSAPP_ACCESS_TOKEN
WHATSAPP_PHONE_NUMBER_ID
WHATSAPP_BUSINESS_ACCOUNT_ID
WHATSAPP_WEBHOOK_VERIFY_TOKEN
WHATSAPP_APP_SECRET
WHATSAPP_API_VERSION

Variables de IA solo si se aprueba una funcionalidad concreta:
OPENAI_API_KEY / AZURE_OPENAI_* / ANTHROPIC_API_KEY según proveedor autorizado.

## Entorno cloud
Antes de elegir proveedor, verificar que la Fundación autorice el servicio y declarar:
- cómputo,
- PostgreSQL,
- almacenamiento si aplica,
- redes/TLS,
- gestión de secretos,
- logs/monitorización,
- backups.

No incluir valores de secretos en README. Documentar solo nombres y cómo configurarlos.

## Entrega
- URL pública accesible.
- README con ejecución local.
- Diagrama de arquitectura.
- Modelo de datos y migraciones.
- Pruebas de restauración/backups si el tiempo lo permite.

> **ACTUALIZACIÓN v3:** Este documento proviene de la versión 2. Si contradice `AGENTS.md`, `docs/DECISION_LOG.md`, `docs/FOUNDATION_BRIEF.md` o `docs/DESIGN_GUIDE.md`, prevalece v3. En particular, Twilio está permitido para prototipo, la IA tiene libertad de elección bajo controles de privacidad/seguridad y la aplicación usa una única PostgreSQL compartida.

