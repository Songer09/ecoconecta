# Seguridad y privacidad

## Amenazas principales
- Acceso indebido a teléfonos/direcciones.
- Recolector consultando solicitudes fuera de su zona o asignación.
- Coordinador modificando flujo del colectivo contrario.
- Acreditación duplicada de puntos.
- Manipulación de cantidades/pesos desde navegador.
- Webhooks falsos o repetidos.
- Exposición de tokens WhatsApp, credenciales DB o claves IA.
- Prompt injection en contenidos/mensajes si posteriormente se usa IA.

## Controles mínimos
- RBAC en backend y autorización por recurso/ámbito.
- Denegar por defecto.
- Validación Pydantic y restricciones DB.
- Contraseñas con hash robusto si se gestionan localmente; nunca texto plano.
- Cookies seguras HttpOnly/SameSite si se usa sesión web; revisar CSRF.
- Rate limiting donde sea necesario sin añadir servicios prohibidos.
- CORS restringido.
- TLS en despliegue.
- Secretos en variables/secret manager del proveedor aprobado.
- Logs estructurados con redacción de PII.
- Auditoría de asignación, programación, cierre, reglas de puntos y cambios de rol.
- Backups de PostgreSQL y prueba de restauración.
- Dependencias fijadas y escaneadas.
- Datos ficticios en demos.

## Acceso por rol
- Solicitante: sus propias solicitudes e historial/puntos.
- Coordinador huerteros: solicitudes orgánicas de su ámbito.
- Huertero: solicitudes asignadas.
- Coordinador recicladores: solicitudes reciclables de su ámbito.
- Reciclador: asignaciones propias y registro de su recolección.
- Administrador: configuración autorizada; acceso a PII sujeto a necesidad operativa y auditoría.

## Prohibiciones
- No compartir cuentas/tokens entre miembros.
- No copiar `auth.json` de Codex entre equipos.
- No subir `.env`, claves o datos reales a Git.
- No introducir datos personales en prompts de IA.
- No habilitar permisos amplios a agentes sin necesidad.

> **ACTUALIZACIÓN v3:** Este documento proviene de la versión 2. Si contradice `docs/DECISION_LOG.md`, `docs/FOUNDATION_BRIEF.md` o `docs/DESIGN_GUIDE.md`, prevalece v3. En particular, Twilio está permitido para prototipo, la IA tiene libertad de elección bajo controles de privacidad/seguridad y la aplicación usa una única PostgreSQL compartida.

