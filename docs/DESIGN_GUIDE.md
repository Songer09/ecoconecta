# Guía de Diseño del Software — EcoConecta

## 1. Principios

1. **Una sola fuente de verdad:** PostgreSQL compartido por todos los módulos.
2. **Modularidad antes que microservicios:** monolito modular para el MVP.
3. **Contratos primero:** frontend, backend, QA y visión acuerdan esquemas antes de integrar.
4. **Seguridad desde el diseño:** autorización server-side, mínimo privilegio y minimización de datos.
5. **Humano en el circuito:** decisiones operativas sensibles permanecen en manos de coordinadores/recolectores.
6. **Integración incremental:** flujo completo funcional antes de agregar funciones accesorias.
7. **Trazabilidad:** cambios de estado, asignaciones y puntos quedan auditados.
8. **Reutilizar lo que ya existe:** inspeccionar frontend y modelo de visión antes de reescribir.

## 2. Arquitectura objetivo

Monolito modular:

- `apps/api`: FastAPI, casos de uso, dominio, repositorios, adaptadores.
- `apps/web`: React + TypeScript.
- `packages/contracts` (si el repositorio lo justifica): OpenAPI generado/tipos compartidos; no duplicar contratos manualmente.
- `services/vision` o `apps/api/.../vision`: servicio/componente de inferencia, según el estado real del modelo.
- `db`: migraciones Alembic, seeds sintéticos y documentación del esquema.
- `tests`: integración y E2E.

No imponer esta estructura a ciegas. Primero inspeccionar repositorio y proponer mapeo si ya hay estructura creada.

### Backend por capas

- **API/presentation:** rutas, dependencias, serialización y validación HTTP.
- **Application:** casos de uso y coordinación transaccional.
- **Domain:** entidades, invariantes y reglas sin dependencia de FastAPI/ORM.
- **Infrastructure:** SQLAlchemy, Psycopg, proveedores de mensajería, almacenamiento e inferencia.

Los controladores no deben contener reglas de negocio extensas. Los modelos ORM no deben convertirse en la única definición del dominio.

### Módulos de dominio

- Identity & Access
- Community/Profiles
- Geography & Coverage
- Collection Requests
- Scheduling & Assignment
- Collection Execution
- Materials & Quantities
- Points & Ledger
- Education Content
- Notifications/Messaging
- Image Recognition
- Reporting & Audit

## 3. Base de datos unificada

**Obligatorio:** una instancia/cluster PostgreSQL y una base lógica de aplicación compartida. Todos los módulos escriben y leen el mismo modelo mediante backend/repositorios.

No crear:
- una BD para frontend;
- una BD distinta para IA;
- una BD para cada equipo;
- tablas duplicadas con nombres alternativos;
- SQLite local como sustituto de PostgreSQL para desarrollo funcional.

El modelo ML puede tener artefactos de archivos (pesos, configuración, etiquetas) y usar almacenamiento de objetos aprobado para imágenes si se autoriza; esos artefactos no son una base de datos transaccional paralela.

Reglas:
- Codex Backend es el propietario técnico del esquema y migraciones.
- Los demás proponen cambios mediante PR/issue y describen campos, relaciones, restricciones e impacto.
- Alembic es la fuente versionada de cambios.
- Una migración por cambio lógico; no editar migraciones ya aplicadas en ramas compartidas.
- Usar claves foráneas, constraints, índices y transacciones.
- Evitar borrado físico de registros operativos; definir soft-delete/retención cuando proceda.
- No almacenar secretos ni datos sensibles en seeds.
- Separar configuración de puntos de movimientos de puntos: reglas versionadas y ledger inmutable.

## 4. Modelo conceptual mínimo

Consultar `UNIFIED_DATA_MODEL.md`. Entidades sugeridas:
- User, Role, UserRole, ContactProfile
- Zone, CollectorProfile, CollectorZoneCoverage, AvailabilitySlot
- CollectionRequest, RequestStatusHistory
- Assignment, Schedule
- CollectionEvent, CollectedMaterial, Material
- PointsRule, PointsLedgerEntry
- RecognitionJob/RecognitionResult (si se persiste la inferencia)
- Notification, WebhookEvent, AuditEvent
- EducationalContent

No crear entidades adicionales sin explicar su responsabilidad y cardinalidad.

## 5. Autenticación y autorización

- Autenticar identidad mediante mecanismo seguro (sesión o tokens correctamente implementados); decidir e implementar un único patrón coherente.
- No solicitar zona/día/hora como “contraseña”. Son atributos operativos y se configuran después de autenticar.
- RBAC por rol y autorización por objeto/ámbito (zona, solicitud asignada, organización).
- Verificar permisos en cada endpoint, incluyendo exportaciones y descargas.
- Admin con MFA si el proveedor/infraestructura lo permite; nunca cuentas compartidas.
- Evitar enumeración de IDs y acceso horizontal entre usuarios.
- Reautenticación para operaciones administrativas críticas cuando aplique.

## 6. Contratos entre frontend y backend

- Backend publica OpenAPI.
- Tipos TypeScript se generan desde OpenAPI o se mantienen sincronizados mediante validación CI.
- Fechas ISO 8601 con offset; persistir UTC; zona de negocio `America/Bogota`.
- Respuestas de error consistentes: código, mensaje seguro, detalles de validación sin filtrar stack traces.
- Paginación, orden y filtros explícitos.
- No enviar al frontend campos internos ni datos personales que el rol no necesita.

El frontend de OpenCode debe usar API client centralizado, variables de entorno para URL base, manejo de expiración/autenticación, loading/error/empty states y no duplicar lógica de negocio.

## 7. Integración de visión

Codex Visión entrega una interfaz interna estable. El backend invoca el módulo por función/servicio interno o endpoint privado, no directamente desde el navegador.

Respuesta recomendada:
- `model_name`, `model_version`
- `predictions[]`: `class_id`, `label`, `confidence`
- `top_k` opcional
- `input_quality`/`warnings`
- `inference_id`
- `needs_human_review`
- `created_at`

El backend valida clases, tamaño/tipo de imagen, autorización y resultado. El usuario confirma/corrige. La clasificación no dispara acciones críticas automáticamente.

## 8. Integración de mensajería

Crear puerto `MessagingProvider` o equivalente con operaciones de envío y estado. Implementaciones separadas:
- `TwilioMessagingAdapter` para prototipo.
- `WhatsAppCloudAdapter` para integración definitiva.

No mezclar lógica de solicitudes con lógica específica de Twilio/Meta. Guardar identificador externo, estado y errores sanitizados. El sistema funciona aunque el proveedor de mensajes esté temporalmente caído.

## 9. Tecnología

- Python, FastAPI, Pydantic, SQLAlchemy, Psycopg, Alembic.
- PostgreSQL.
- React, TypeScript estricto, Vite, Tailwind.
- Docker, Git, GitHub Actions.
- pytest/HTTPX, Vitest, Playwright.
- Modelo de visión existente; framework y librerías se determinan tras inspección.

No agregar frameworks por moda. Cualquier dependencia debe justificar necesidad, mantenimiento, licencia, vulnerabilidades, peso y coste operativo.

## 10. Calidad de datos y reglas de negocio

- Solicitud orgánica y reciclable siguen enrutamiento separado.
- No marcar programada sin fecha, hora y recolector responsable.
- No cerrar recolección sin actor autorizado y registro de materiales/cantidades cuando el flujo lo requiera.
- Puntos solo tras recolección válida; cálculo reproducible y con regla vigente registrada.
- Idempotencia para evitar doble cierre y doble acreditación.
- Cambios de reglas de puntos no recalculan silenciosamente el historial.
- Zona y disponibilidad deben tener vigencia y procedencia; no asumir disponibilidad permanente.

## 11. Criterio de terminado

Una función no está terminada solo porque la pantalla se vea bien. Debe tener:
- contrato;
- validación;
- autorización;
- persistencia;
- estados de carga/error/vacío;
- pruebas positivas y negativas;
- registro de auditoría cuando corresponda;
- documentación de configuración;
- integración demostrable.
