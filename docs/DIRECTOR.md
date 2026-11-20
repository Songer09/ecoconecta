# DIRECTOR.md — Mandato técnico de EcoConecta
**Versión:** 2.0 reconstruida · **Fecha:** 20-11-2026

> Este documento reconstruye el mandato a partir del resumen de decisiones previas y del reto oficial transcrito en esta conversación. No es una reproducción literal del DIRECTOR.md anterior. El reto oficial de Fundación Santo Domingo / Universidad Libre prevalece ante cualquier decisión técnica incompatible.

## 1. Propósito
Construir y desplegar un MVP accesible para hogares y unidades productivas de Villas de San Pablo que:
- Eduque sobre separación y aprovechamiento de residuos.
- Reciba solicitudes de recolección.
- Enrute orgánicos a huerteros y reciclables a recicladores.
- Permita revisar, asignar y programar la atención.
- Registre la recolección y los materiales recuperados.
- Reconozca la participación mediante puntos calculados con reglas configurables.
- Mantenga comunicación y notificaciones, incluyendo WhatsApp Business Cloud API.

La tecnología debe fortalecer el voz a voz y el liderazgo comunitario, no reemplazarlos.

## 2. Principios
1. Flujo completo antes que amplitud de funcionalidades.
2. Mobile-first; usable en móviles y tabletas.
3. Seguridad y privacidad por diseño.
4. Trazabilidad de solicitudes, asignaciones, programación, recolección y puntos.
5. Control humano de asignaciones finales, horarios y cierres.
6. Configurabilidad para parámetros aún no validados.
7. Código mantenible, modular y verificable.
8. No presentar datos simulados como operación real.

## 3. Arquitectura
- Monolito modular.
- Arquitectura hexagonal / puertos y adaptadores en el backend.
- Backend Python + FastAPI.
- Frontend React + TypeScript + Vite.
- PostgreSQL.
- SQLAlchemy + Psycopg; migraciones con Alembic.
- WhatsApp Business Cloud API oficial.
- Docker para ejecución local y despliegue reproducible.
- GitHub Actions para CI.

## 4. Ámbitos funcionales
- Identidad, autenticación y autorización por roles.
- Usuarios solicitantes y unidades productivas piloto.
- Colectivos: huerteros y recicladores.
- Zonas y cobertura territorial.
- Recolectores, asignaciones y calendarios.
- Solicitudes y flujo de estados.
- Programación día/hora/persona.
- Registro de recolección y materiales/cantidades.
- Motor parametrizable de puntos y libro de movimientos.
- Contenidos de educación ambiental.
- WhatsApp, plantillas, webhooks y registro de notificaciones.
- Paneles operativos y reportes básicos.
- Auditoría y configuración administrativa.

## 5. Tecnologías y restricciones
### Permitidas por el reto
- Lenguajes: Python, TypeScript, JavaScript, HTML, CSS.
- Base de datos: PostgreSQL.
- Backend: FastAPI, Flask o Django; SQLAlchemy, Psycopg, Pydantic, Pandas.
- Frontend: React, Next.js o Vue; Tailwind CSS o Bootstrap.
- Mensajería: WhatsApp Business Cloud API.
- IA: OpenAI API, Azure OpenAI API, Azure AI Foundry, Claude API.
- Infraestructura: Docker y Git.
- Agentes/modelos: LangChain, LangGraph y SDK oficiales indicados en el reto.

### Selección del equipo
- FastAPI + Pydantic + SQLAlchemy + Psycopg + Alembic.
- React + TypeScript + Vite + Tailwind.
- PostgreSQL.
- WhatsApp Business Cloud API directa.
- pytest + HTTPX, Vitest, Playwright.
- Docker + GitHub Actions.

### No incorporar
Twilio, Firebase, MongoDB, SQLite como BD de aplicación, Supabase, Redis, n8n, Make, Zapier, Power Automate u otros proveedores/servicios que sustituyan tecnologías autorizadas, salvo autorización expresa y verificable de la Fundación.

## 6. Decisiones que requieren validación
- Identidad visual oficial, variantes de logotipo, paleta, tipografías y usos.
- Catálogo real de zonas y asignación de los 15 recicladores.
- Horarios/días por reciclador y por zona.
- Operación exacta de los huerteros y su calendario.
- Reglas de cálculo de puntos, materiales, unidades, topes y vigencia.
- Datos y contactos de las unidades productivas piloto.
- Credenciales, número y configuración de WhatsApp Business.
- Proveedor cloud aprobado y disponibilidad de PostgreSQL administrado.
- Datos personales que la Fundación autoriza recopilar.
No inventar ninguno de estos valores.

## 7. Criterios de aceptación globales
- Solicitud orgánica y reciclable se enrutan al colectivo correcto.
- Coordinador asigna a un integrante.
- Una solicitud solo está programada si tiene fecha, hora y persona responsable.
- Usuario recibe confirmación y puede consultar estado.
- Recolector registra la recolección.
- Los materiales y cantidades quedan asociados a la recolección y al recolector.
- Los puntos solo se acreditan después del cierre validado y según regla activa.
- No se acreditan puntos dos veces por reintentos.
- Los roles solo acceden a datos necesarios.
- MVP desplegado, README, arquitectura, modelo de datos y demostración end-to-end.

## 8. Gestión de cambios
Toda modificación de arquitectura, tecnología permitida, alcance oficial o regla de negocio requiere:
- Motivo.
- Impacto.
- Riesgo.
- Alternativas.
- Aprobación humana.
Registrar decisiones en `docs/decisions/`.

> **ACTUALIZACIÓN v3:** Este documento proviene de la versión 2. Si contradice `AGENTS.md`, `docs/DECISION_LOG.md`, `docs/FOUNDATION_BRIEF.md` o `docs/DESIGN_GUIDE.md`, prevalece v3. En particular, Twilio está permitido para prototipo, la IA tiene libertad de elección bajo controles de privacidad/seguridad y la aplicación usa una única PostgreSQL compartida.

