# EcoConecta — documentación técnica coordinada v3

**Propósito:** servir como fuente de verdad operativa para los cuatro agentes de desarrollo y para el equipo humano.

## Lectura obligatoria antes de modificar código

1. `AGENTS.md`
2. `docs/00_START_HERE.md`
3. `docs/FOUNDATION_BRIEF.md`
4. `docs/DESIGN_GUIDE.md`
5. `docs/TEAM_WORK_PROTOCOL.md`
6. `docs/UNIFIED_DATA_MODEL.md`
7. `docs/AI_VISION_INTEGRATION.md` (especialmente Codex de visión)
8. `docs/SECURITY_2026_2027.md`

Después, leer los documentos de dominio correspondientes al módulo que se vaya a modificar.

## Estado y procedencia

Esta versión incorpora las aclaraciones verbales del equipo sobre la reunión con Daniel, director de TI:
- Twilio puede utilizarse para la prueba/prototipo.
- La integración definitiva del canal será WhatsApp Business Cloud API.
- Se permite utilizar IA y el equipo tiene libertad para la solución de reconocimiento de imágenes.

Estas aclaraciones fueron comunicadas por el equipo; no son una transcripción firmada de la Fundación. Si aparece una instrucción escrita posterior que las contradiga, detenerse y pedir decisión humana.

La documentación también incorpora el reto oficial transcrito por el equipo y requisitos operativos compartidos en conversaciones. Los detalles aún no confirmados se marcan como **POR CONFIRMAR**. No inventar reglas, datos, credenciales, resultados de precisión ni compromisos de la Fundación.

## Distribución de agentes

| Agente | Responsabilidad principal | Propiedad |
|---|---|---|
| Codex 1 — Backend/Integración | API, dominio, seguridad, migraciones y base de datos unificada; integración de frontend y visión | `apps/api/**`, `db/**`, contratos |
| OpenCode 1 — Frontend | Interfaz React; luego integración contra API real | `apps/web/**` |
| OpenCode 2 — QA | Pruebas unitarias, integración, E2E, regresión y hallazgos | `tests/**`, `apps/**/tests/**`, `apps/web/e2e/**` |
| Codex 2 — Visión/IA | Auditar, documentar, probar y encapsular el modelo de reconocimiento existente | `services/vision/**` o módulo acordado; artefactos/modelos bajo control |
| Compañero — WhatsApp/ChatBot | Twilio y bot mediante contratos coordinados por Backend/Integración | `integrations/whatsapp/**`; rama `feat/whatsapp-chatbot` |

La asignación de carpetas es una propuesta de coordinación. Si el repositorio ya tiene una estructura distinta, los agentes deben inspeccionarla y proponer un ajuste antes de mover o renombrar código.

## Decisiones técnicas vigentes

- Arquitectura: monolito modular, con límites de dominio y adaptadores externos; no microservicios por defecto.
- Backend: Python + FastAPI + Pydantic + SQLAlchemy + Psycopg + Alembic.
- Frontend: React + TypeScript estricto + Vite + Tailwind CSS.
- **Una sola base de datos PostgreSQL compartida** por toda la aplicación y todos los módulos. No bases separadas por agente, microservicio o funcionalidad.
- Reconocimiento: reutilizar el modelo ya desarrollado, sujeto a revisión técnica y validación reproducible.
- Mensajería: Twilio permitido para prototipo/prueba si el equipo lo necesita; WhatsApp Business Cloud API oficial como integración definitiva.
- Infraestructura: Docker, Git y despliegue cloud. Proveedor cloud y recursos: POR CONFIRMAR con la Fundación/equipo.
- Pruebas: pytest + HTTPX para backend, Vitest para frontend, Playwright para flujos E2E.

## Conflictos con la versión 2

La versión 2 contenía restricciones conservadoras basadas en la transcripción inicial. En particular, prohibía Twilio y limitaba IA a un conjunto estrecho de proveedores. **Esas dos restricciones quedan sustituidas por las aclaraciones posteriores comunicadas por el equipo.** Revisar `docs/DECISION_LOG.md`.

No interpretar “libertad para usar IA” como permiso para enviar datos personales sin minimización, consentimiento/base legal, controles de seguridad o evaluación de impacto.

## Arranque

Revisión del SQL inicial y pendientes de integración: [`db/README.md`](db/README.md).
Configuración y alcance del compañero de Twilio/WhatsApp:
[`integrations/whatsapp/README.md`](integrations/whatsapp/README.md).

Abrir el repositorio desde su raíz. Confirmar estructura y estado Git. Leer las instrucciones. No crear código antes de revisar los archivos existentes y asignar claramente las tareas. Consultar `docs/INTEGRATION_PLAN.md` para la secuencia de trabajo.
