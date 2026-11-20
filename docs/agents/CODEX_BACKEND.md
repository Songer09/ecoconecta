# Instrucciones — Codex 1: Backend, PostgreSQL e integración

Leer primero `AGENTS.md`, `docs/00_START_HERE.md`, `docs/DESIGN_GUIDE.md`, `docs/UNIFIED_DATA_MODEL.md`, `docs/API_CONTRACTS.md` y `docs/SECURITY_2026_2027.md`.

Eres propietario técnico del backend y del modelo de datos unificado. Debes:
1. Inspeccionar el repositorio antes de crear o mover archivos.
2. Mantener una sola base PostgreSQL compartida.
3. Definir y versionar el esquema mediante Alembic.
4. Implementar FastAPI, Pydantic, SQLAlchemy y Psycopg.
5. Publicar OpenAPI y contratos consumibles por frontend.
6. Implementar autorización por rol y por objeto.
7. Hacer transaccionales el cierre de recolección y la acreditación de puntos.
8. Diseñar idempotencia para webhooks y acciones repetibles.
9. Integrar visión mediante contrato interno; nunca delegar autorización o reglas de puntos al modelo.
10. Integrar adaptadores de mensajería: Twilio para prototipo si se usa y WhatsApp Cloud API para definitivo.
11. Coordinar con OpenCode Frontend y QA mediante contratos y PRs.
12. Revisar seguridad, migraciones, logs, backups y despliegue.

No inventes cobertura, materiales, puntos ni datos de residentes. Si falta un dato, crea configuración pendiente y documenta el bloqueo. No implementes todas las entidades sugeridas si el alcance real no las necesita; evita sobreingeniería.
