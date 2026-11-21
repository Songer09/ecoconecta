# Modelo de dominio y datos (borrador para revisión)

Este modelo es una propuesta de diseño, no una afirmación de que todos los datos operativos ya fueron entregados.

## Entidades principales
- User: identidad, nombre visible, contacto mínimo, estado.
- Role / UserRole: solicitante, coordinator_gardeners, gardener, coordinator_recyclers, recycler, admin.
- PilotEnrollment: habilitación de usuario/unidad productiva en el piloto.
- Collective: GARDENERS o RECYCLERS.
- Zone: zona territorial identificada por código/nombre y estado.
- CollectorProfile: usuario recolector, colectivo, identificador operativo y estado.
- CollectorZone: relación de cobertura entre recolector y zona, con vigencia.
- AvailabilitySlot: día de semana, hora inicial/final, zona y vigencia; no usar como autenticación.
- CollectionRequest: código público, solicitante, tipo de generador, flujo, dirección/ubicación protegida, observaciones, disponibilidad preferida y estado.
- RequestStatusHistory: estado anterior/nuevo, actor, fecha y motivo.
- Assignment: solicitud, coordinador, recolector, fecha de asignación.
- Schedule: solicitud, fecha/hora acordada, zona horaria, recolector responsable y quién confirmó.
- Collection: solicitud, recolector, fecha/hora de ejecución, estado de verificación y notas.
- Material: catálogo de materiales y unidades permitidas.
- CollectionItem: recolección, material, cantidad decimal, unidad, peso/unidad normalizada si aplica y evidencia opcional.
- PointRule: material, unidad base, puntos por unidad, vigencia, versión, estado, creado por.
- PointLedgerEntry: usuario, recolección, regla aplicada, cantidad base, puntos acreditados/debitados, idempotency key y fecha.
- EducationalContent: título, cuerpo, categoría, publicación y estado.
- Notification: destinatario, canal, plantilla, estado, proveedor message ID, timestamps sin guardar datos innecesarios.
- AuditEvent: actor, acción, entidad, ID, fecha, metadatos redactados.

## Invariantes
1. Request.flow determina el colectivo responsable: ORGANIC → GARDENERS; RECYCLABLE → RECYCLERS.
2. Una programación requiere fecha, hora y recolector asignado.
3. Un recolector solo opera solicitudes de su colectivo y ámbito autorizado.
4. Collection solo puede cerrar una solicitud en estado permitido.
5. Una recolección no puede acreditarse dos veces.
6. PointLedgerEntry debe referenciar la regla exacta aplicada; cambios futuros de regla no alteran puntos históricos.
7. No se permite saldo negativo por canjes si posteriormente se incorpora un módulo de recompensas.
8. Cantidades deben ser positivas y unidad compatible con material.
9. Las zonas son entidades territoriales; no modelarlas como etapas.
10. Contacto/dirección se muestran solo a usuarios que requieren atender la solicitud.

## Consideraciones PostgreSQL
- UUID para IDs internos.
- NUMERIC para cantidades/puntos, no FLOAT.
- CHECK constraints para cantidades positivas y enumeraciones.
- FK y UNIQUE para integridad e idempotencia.
- Índices por status, flow, zone_id, collector_id, created_at y scheduled_at.
- Transacciones para cierre y puntos.
- Fechas almacenadas en UTC con zona de visualización America/Bogota.

## Preguntas abiertas
- ¿Una solicitud puede contener más de un tipo de material?
- ¿La asignación es individual o por equipo?
- ¿Los recicladores atienden solo su zona asignada o pueden cubrir zonas vecinas?
- ¿Qué unidades oficiales se usan para pesar/contabilizar materiales?
- ¿Quién valida el peso/cantidad?
- ¿Se requiere evidencia fotográfica?
- ¿Cómo se corrigen errores de pesaje sin borrar trazabilidad?

> **ACTUALIZACIÓN v3:** Este documento proviene de la versión 2. Si contradice `docs/DECISION_LOG.md`, `docs/FOUNDATION_BRIEF.md` o `docs/DESIGN_GUIDE.md`, prevalece v3. En particular, Twilio está permitido para prototipo, la IA tiene libertad de elección bajo controles de privacidad/seguridad y la aplicación usa una única PostgreSQL compartida.

