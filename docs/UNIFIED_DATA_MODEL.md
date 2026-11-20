# Modelo de datos unificado — fuente de verdad

## 1. Regla principal

EcoConecta tendrá **una sola base de datos PostgreSQL compartida por toda la aplicación**. Todos los módulos de negocio persisten en el mismo esquema lógico y coordinan sus cambios mediante migraciones Alembic.

No se permite que cada agente cree su propia BD, ni que el frontend o el módulo de visión mantengan una copia operacional separada. Los modelos ORM, DTOs y tipos de frontend deben derivarse de este contrato y mantenerse sincronizados.

Codex Backend es propietario técnico de esquema/migraciones. Cambios propuestos por otros agentes requieren revisión.

## 2. Esquemas

Para el MVP se recomienda un solo esquema `public` con nombres y módulos claramente delimitados. No introducir schemas PostgreSQL separados salvo que exista una razón concreta y aprobación humana.

## 3. Entidades conceptuales

El siguiente es un modelo lógico inicial, no un mandato para crear todas las tablas sin revisar el código actual.

### Identidad y acceso
- `users`: identidad de acceso, estado, timestamps.
- `roles`: catálogo de roles.
- `user_roles`: asignación de roles.
- `user_profiles`: datos de perfil estrictamente necesarios.
- `sessions` o tabla de refresh tokens revocables, solo si el patrón de autenticación elegido lo necesita.

### Geografía y operación
- `zones`: zonas comunitarias configuradas.
- `collector_profiles`: perfil de huertero/reciclador asociado a usuario.
- `collector_zone_coverage`: relación persona-zona, tipo de flujo y vigencia.
- `availability_slots`: día/franja horaria, recurrencia y vigencia.
- No convertir zona/día/hora en credenciales. Son atributos operativos.

### Solicitudes y programación
- `collection_requests`: creador, contacto, dirección/referencia, generador, flujo, observaciones, disponibilidad, estado y timestamps.
- `request_status_history`: estado anterior/nuevo, actor, fecha, motivo.
- `assignments`: coordinador, recolector, solicitud, estado y vigencia.
- `schedules`: fecha/hora acordada, zona horaria, responsable y estado.
- Restricción: solicitud programada debe tener schedule y responsable válidos.

### Recolección y materiales
- `collection_events`: solicitud, recolector, actor que confirma, fecha, observaciones y evidencia opcional.
- `materials`: catálogo de materiales, flujo, unidad base y estado.
- `collected_materials`: evento, material, cantidad decimal, unidad, notas.
- La cantidad debe ser mayor que cero; definir precisión y unidad permitida.
- Evitar almacenar el mismo material/cantidad en varios lugares como fuentes de verdad.

### Puntos
- `points_rules`: regla parametrizable, material/flujo, unidad, puntos por unidad, vigencia, versión, estado, creador/aprobador.
- `points_ledger`: movimiento inmutable (usuario, evento de recolección, regla/version, cantidad base, puntos, timestamp).
- Restricción única para impedir doble acreditación por el mismo evento/regla.
- Saldo = suma de movimientos; no mantener saldo mutable sin mecanismo de reconciliación.
- Ningún valor de puntos está definido todavía. No seedear valores inventados.

### Visión/IA
- `recognition_jobs` y `recognition_results` solo si hace falta trazabilidad persistente.
- Guardar versión de modelo, resultado, confianza, fecha y decisión humana.
- No guardar imagen original en PostgreSQL como blob por defecto.
- Si se necesita conservar imagen, definir almacenamiento, consentimiento/base legal, acceso y retención. La URI no debe ser pública.
- No persistir datos personales innecesarios en prompts o resultados.

### Integraciones y auditoría
- `notifications`: destinatario, canal, estado, referencia externa, timestamps.
- `webhook_events`: proveedor, ID externo único, estado de procesamiento, fecha y error sanitizado.
- `audit_events`: actor, acción, recurso, identificador, timestamp, metadatos permitidos y no sensibles.

## 4. Relaciones clave

- User 1—N UserRole.
- User 1—0..1 CollectorProfile.
- CollectorProfile N—M Zone mediante CollectorZoneCoverage.
- CollectorProfile 1—N AvailabilitySlot.
- User 1—N CollectionRequest (creador).
- CollectionRequest 1—N RequestStatusHistory.
- CollectionRequest 0..N Assignment (con una asignación activa según regla).
- CollectionRequest 0..N Schedule (reprogramaciones conservan historial).
- CollectionRequest 0..N CollectionEvent, según política del proceso.
- CollectionEvent 1—N CollectedMaterial.
- Material 1—N CollectedMaterial.
- CollectionEvent 0..N PointsLedgerEntry.
- PointsRule 1—N PointsLedgerEntry.

## 5. Integridad y concurrencia

- PK UUID (recomendado) o estrategia consistente definida por Codex Backend.
- FK para relaciones.
- `NOT NULL`, `CHECK`, `UNIQUE` donde correspondan.
- Índices por estado/fecha/zona, asignación/recolector, usuario e historial.
- Transacción al confirmar recolección y acreditar puntos.
- Bloqueo/consistencia ante doble clic, reintentos y solicitudes concurrentes.
- Idempotency key para operaciones de cierre y webhooks.
- No permitir estados imposibles por llamadas directas.
- Mantener historial en vez de sobrescribir información operativa crítica.

## 6. Migraciones y desarrollo

- Alembic es la única fuente de migraciones.
- PostgreSQL local en Docker para desarrollo e integración.
- No usar SQLite para tests de integración: sus diferencias pueden ocultar defectos.
- Fixtures de prueba aisladas y datos sintéticos.
- Los agentes no editan migraciones ya aplicadas/compartidas; crean migración nueva.
- No aplicar migraciones destructivas en producción sin backup, revisión y plan de rollback.

## 7. Decisiones pendientes

- Datos exactos de contacto y si se separan en tabla privada.
- Direcciones completas vs referencia de ubicación/coordenadas.
- Multiusuario por hogar/unidad productiva.
- Cobertura real de 15 recicladores y calendario de huerteros.
- Catálogo oficial de materiales y unidades.
- Política de recolecciones parciales/rechazadas.
- Retención de solicitudes, teléfonos, ubicaciones e imágenes.
- Si se requiere historial de saldo/puntos visible a usuarios.
