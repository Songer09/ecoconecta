# Protocolo de trabajo — 2 Codex + 2 OpenCode

## 1. Roles

Actualización de coordinación: Backend/Integración es el agente principal. Se añade
un responsable de WhatsApp/ChatBot en `feat/whatsapp-chatbot`, bajo su coordinación
técnica; ver `docs/agents/WHATSAPP_CHATBOT.md`. El desarrollo del backend continúa
solo tras la confirmación solicitada por el usuario; esta entrega prepara SQL,
PostgreSQL local y ramas para revisión.

### Codex 1 — Backend, base unificada e integración
Responsable de:
- FastAPI y casos de uso.
- esquema PostgreSQL unificado y Alembic.
- autenticación/autorización.
- reglas de negocio, estados, puntos y auditoría.
- contratos OpenAPI.
- integrar frontend, reconocimiento y mensajería.
- despliegue del backend.

No debe rehacer el modelo de visión sin coordinar con Codex 2.

### OpenCode 1 — Frontend
Responsable de:
- React + TypeScript + Vite + Tailwind.
- pantallas y componentes.
- navegación y experiencia por rol.
- validación de formularios a nivel UX (además de la validación backend).
- consumo de API real una vez disponible.
- pruebas de componentes y accesibilidad básica.

**Fase 1:** puede avanzar con mocks tipados acordados, pero debe aislarlos detrás de servicios/repositorios de frontend.  
**Fase 2:** reemplazar mocks por API real; no dejar datos falsos activos en la demo final.  
No crear persistencia propia ni reglas críticas en cliente.

### OpenCode 2 — QA
Responsable de:
- plan de pruebas y matriz requisito-prueba.
- pytest/HTTPX para pruebas backend en coordinación con Codex 1.
- Vitest y Playwright.
- pruebas de permisos, flujos, concurrencia, idempotencia, errores y regresión.
- reproducir defectos y verificar correcciones.

QA puede crear fixtures sintéticos, nunca inventar datos productivos.

### Codex 2 — Reconocimiento de imágenes / IA
Responsable de:
- auditar el modelo ya entrenado/desarrollado.
- asegurar reproducibilidad y documentar métricas.
- identificar limitaciones y clases soportadas.
- definir interfaz de inferencia estable.
- empaquetar el componente para ejecución local/contenedor/cloud.
- pruebas de rendimiento, robustez y seguridad de archivos.
- colaborar con Codex 1 para integrar; no conectar directamente a PostgreSQL ni gestionar estados/puntos.

## 2. Secuencia recomendada

**Paso 0 — Reconocimiento del repositorio (todos):** leer docs, `git status`, estructura, dependencias, código existente. No sobrescribir.

**Paso 1 — Acuerdos de integración (Codex 1 coordina):**
- entidades y relaciones;
- contratos API;
- autenticación y roles;
- formato de errores;
- interfaz de visión;
- proveedor de mensajería;
- variables de entorno;
- estrategia de ramas y PR.

**Paso 2 — Trabajo paralelo:**
- Backend: migraciones iniciales, auth, solicitudes, asignación, recolección, puntos.
- Frontend: pantallas con tipos/contratos acordados.
- Visión: evaluación, encapsulado y contrato.
- QA: matriz de pruebas y casos críticos desde requisitos.

**Paso 3 — Integración temprana:**
- frontend conecta primero autenticación y listado/creación de solicitudes;
- visión se invoca desde backend con una imagen sintética/de prueba;
- mensajería se prueba con sandbox/mock y después Twilio si aplica;
- PostgreSQL compartida usada por todos los flujos.

**Paso 4 — End-to-end:**
- orgánico;
- reciclable;
- programación;
- registro de materiales;
- puntos;
- notificación.

**Paso 5 — Hardening y demo:**
- ejecutar regresión;
- revisar seguridad y datos;
- verificar despliegue;
- ensayar demo completa;
- etiquetar lo simulado y lo real.

## 3. Ramas sugeridas

- `main`: protegida.
- `feat/backend-core`
- `feat/frontend`
- `feat/vision`
- `feat/whatsapp-chatbot`
- `test/qa`
- ramas cortas por tarea si es necesario.

No usar una rama permanente de documentación si causa conflictos: cambios de docs mediante PR pequeño. No force-push a ramas compartidas.

## 4. Reglas de coordinación

Antes de modificar una interfaz compartida, publicar propuesta:
- objetivo;
- archivo/contrato;
- compatibilidad;
- migración requerida;
- pruebas.

El propietario del módulo aprueba. Los cambios de esquema los aprueba Codex 1 y el responsable humano. Ningún agente integra su propio PR a `main`.

## 5. Integración frontend-backend

El frontend no debe esperar a que todo el backend esté terminado. Backend publica un OpenAPI inicial y ejemplos de payload. Frontend usa un API client tipado. Cuando endpoint cambie:
1. backend actualiza OpenAPI;
2. comunica breaking/non-breaking change;
3. actualiza tipos;
4. frontend adapta servicios/pantallas;
5. QA agrega regresión.

No hacer que el frontend consulte directamente el modelo de visión o la base de datos.

## 6. Entrega diaria/por tarea

Formato obligatorio:
- **Hecho**
- **Archivos modificados**
- **Contratos o migraciones**
- **Pruebas ejecutadas**
- **Resultado real**
- **Bloqueos/decisiones**
- **Siguiente paso**
