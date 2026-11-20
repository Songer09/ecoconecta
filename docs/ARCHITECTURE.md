# Arquitectura propuesta

## 1. Estilo
Monolito modular con arquitectura hexagonal. Para el MVP, evitar microservicios: aumentan complejidad operativa y despliegue sin necesidad demostrada.

## 2. Componentes
- Web React: interfaz pública, paneles de coordinadores, recolectores y administración.
- API FastAPI: autenticación, reglas de negocio, autorización, consultas y comandos.
- PostgreSQL: única persistencia transaccional.
- WhatsApp Cloud API: notificaciones salientes y recepción de webhooks.
- Almacenamiento de archivos: solo si se necesita evidencia; seleccionar un servicio compatible con las condiciones de la Fundación y documentarlo antes de implementarlo.
- CI/CD: GitHub Actions y Docker.

## 3. Módulos backend
auth, users, organizations/collectives, zones, schedules, requests, assignments, collections, materials, points, education, notifications, audit.

## 4. Capas por módulo
- domain: entidades, value objects, invariantes y eventos de dominio.
- application: casos de uso y puertos.
- infrastructure: SQLAlchemy, WhatsApp adapter, repositorios.
- presentation: routers FastAPI, schemas Pydantic y dependencias.

Las reglas de negocio no deben depender de FastAPI ni SQLAlchemy.

## 5. Flujos
### Solicitud
Web → API → validación → creación de request → clasificación de flujo → asignación de bandeja al colectivo correcto → notificación de recepción.

### Asignación y programación
Coordinador → API → validar ámbito y disponibilidad → registrar asignación y programación → historial → notificación al usuario.

### Cierre y puntos
Recolector → registra materiales y cantidades → coordinador/responsable confirma según política → transacción única: cerrar recolección + registrar movimientos de puntos + historial. Usar clave idempotente para impedir duplicados.

### WhatsApp entrante
Meta webhook → validar firma/token según mecanismo oficial → registrar evento → deduplicar por message/event ID → procesar de forma segura → no permitir que un mensaje ejecute cierre o asignación crítica automáticamente.

## 6. Frontend
React + TypeScript + Vite + Tailwind. Separar features por dominio. React Router para navegación, TanStack Query para estado servidor si se mantiene la decisión previa. Leaflet solo si el mapa aporta al MVP y se valida el uso; no es requisito mínimo del reto.

## 7. Contratos
OpenAPI generado por FastAPI como contrato inicial. Versionar cambios. Frontend consume tipos generados o tipos revisados contra OpenAPI. No inventar endpoints de forma independiente.

## 8. Despliegue
Contenedor web, contenedor API y PostgreSQL. Para producción, declarar proveedor cloud y servicios concretos aprobados. No desplegar con SQLite ni sustituir PostgreSQL. Secretos solo como variables protegidas del entorno.

> **ACTUALIZACIÓN v3:** Este documento proviene de la versión 2. Si contradice `AGENTS.md`, `docs/DECISION_LOG.md`, `docs/FOUNDATION_BRIEF.md` o `docs/DESIGN_GUIDE.md`, prevalece v3. En particular, Twilio está permitido para prototipo, la IA tiene libertad de elección bajo controles de privacidad/seguridad y la aplicación usa una única PostgreSQL compartida.

