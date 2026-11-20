# 00 — Inicio obligatorio para los agentes

## Qué estamos construyendo

EcoConecta es un MVP para conectar hogares/unidades productivas con huerteros y recicladores de oficio para gestionar solicitudes de recolección, programarlas, registrar lo recolectado y reconocer la participación mediante puntos.

El producto debe apoyar la organización comunitaria existente, no reemplazar el liderazgo ni asumir que todos los residentes usan la plataforma.

## Antes de escribir código

1. Ejecuta `git status`, identifica rama y revisa estructura real.
2. Lee `AGENTS.md` y los documentos de esta carpeta.
3. Inspecciona el código ya existente; no presupongas que una carpeta está vacía.
4. Identifica qué agente es dueño de cada módulo.
5. Revisa `docs/UNIFIED_DATA_MODEL.md` y `docs/API_CONTRACTS.md`.
6. Reporta conflictos, riesgos o decisiones faltantes antes de hacer cambios destructivos.

## Cuatro agentes, cuatro responsabilidades

- **Codex 1 — Backend/Integración:** núcleo transaccional, API, PostgreSQL unificada, autenticación/autorización, integración de frontend, visión y mensajería.
- **OpenCode 1 — Frontend:** interfaz React. Debe diseñar con contratos acordados y posteriormente conectar sus pantallas a la API real.
- **OpenCode 2 — QA:** estrategia, automatización, pruebas funcionales, seguridad y regresión.
- **Codex 2 — Visión/IA:** modelo existente de reconocimiento de residuos; reproducibilidad, evaluación, API interna del módulo e integración con backend.

La persona responsable del proyecto conserva la autoridad para resolver conflictos y aprobar decisiones de producto.

## Objetivo de integración

No basta con que cada módulo funcione por separado. El entregable es un flujo completo:

1. Usuario registra solicitud.
2. Backend la enruta según flujo de residuo.
3. Coordinador revisa y asigna recolector.
4. Se registra programación completa.
5. Recolector registra cantidades/materiales y confirma recolección.
6. Backend actualiza estado e historial y calcula puntos en una transacción.
7. Usuario puede consultar el resultado y recibir notificación.

## Qué no asumir

- No asumir que las 15 personas recicladoras cubren todas las zonas o todos los horarios; cargar cobertura real confirmada.
- No asumir que huerteros tienen el mismo modelo de cobertura que recicladores.
- No asumir que el modelo de visión clasifica orgánicos con la misma calidad que no orgánicos.
- No inventar precisión, matriz de confusión, umbrales ni catálogo de materiales.
- No inventar reglas de puntos.
- No dar por conectada WhatsApp Cloud API si solo funciona Twilio o un mock.
- No presentar una demo con datos reales de residentes sin autorización.

## Entrega de cada agente

Cada agente debe entregar:
- alcance implementado;
- contratos/interfaces;
- archivos tocados;
- pruebas ejecutadas y resultados;
- limitaciones conocidas;
- instrucciones de integración;
- variables de entorno requeridas (nombres, nunca valores secretos).
