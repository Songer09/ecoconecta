# EcoConecta — instrucciones obligatorias para agentes

## 1. Fuente de verdad y precedencia

Leer `docs/00_START_HERE.md` y los documentos de v3 antes de actuar.

Orden de autoridad:
1. Decisiones humanas explícitas más recientes y requisitos escritos de la Fundación.
2. `docs/FOUNDATION_BRIEF.md` (separa requisitos transcritos, aclaraciones verbales y pendientes).
3. `docs/DECISION_LOG.md` (decisiones vigentes).
4. `docs/DESIGN_GUIDE.md`, `docs/UNIFIED_DATA_MODEL.md`, `docs/API_CONTRACTS.md`, `docs/SECURITY_2026_2027.md`.
5. Documentación anterior v2, solo donde no contradiga v3.

Si hay contradicción, no resolverla silenciosamente: documentar el conflicto y pedir decisión humana.

## 2. Restricciones y decisiones actuales

- Una única base de datos PostgreSQL para toda la aplicación. Una sola fuente de verdad.
- Backend FastAPI/Python; frontend React/TypeScript; respetar el stack existente si ya está correctamente iniciado.
- Twilio está permitido para prototipo/prueba según aclaración verbal comunicada por el equipo.
- WhatsApp Business Cloud API oficial será el canal definitivo.
- IA y reconocimiento de imágenes están permitidos; reutilizar primero el modelo existente. No rehacerlo sin evidencia técnica.
- No introducir otra base de datos como almacenamiento operacional, ni Redis/MongoDB/Firebase/Supabase/SQLite para persistencia de la aplicación. Un modelo de ML puede usar archivos/artefactos versionados o almacenamiento de objetos aprobado; eso no crea una segunda base de datos transaccional.
- No usar automatizadores no-code como n8n, Make, Zapier o Power Automate.
- No añadir proveedores externos, servicios cloud o servicios de pago sin aprobación humana cuando impliquen coste, datos personales o dependencia operativa.
- No inventar reglas de puntos, tarifas, horarios, cobertura, datos de recicladores ni porcentajes de precisión.

## 3. Reglas de trabajo multiagente

- Cuatro agentes: Codex Backend/Integración, Codex Visión/IA, OpenCode Frontend y OpenCode QA.
- Se incorpora un compañero de WhatsApp/ChatBot en `feat/whatsapp-chatbot`, con ámbito
  `integrations/whatsapp/**` y `docs/agents/WHATSAPP_CHATBOT.md`. Backend/Integración
  es el agente principal y coordina decisiones técnicas e interfaces compartidas.
  Las decisiones de negocio, privacidad y aprobación de producción siguen siendo humanas.
- Cada agente debe trabajar en su ámbito y rama; coordinar cambios compartidos antes de tocar archivos ajenos.
- No editar simultáneamente el mismo archivo sin acuerdo explícito.
- No crear tablas, endpoints o tipos duplicados. Consultar el modelo unificado y contratos antes de implementar.
- El agente de frontend consume contratos acordados; no debe inventar respuestas de API para “hacer que funcione”.
- El agente de visión expone una interfaz estable; no debe conectarse directamente a PostgreSQL ni escribir puntos/estados.
- El backend es dueño de reglas de negocio, persistencia, autorización y transacciones.
- QA diseña pruebas independientes y reporta defectos reproducibles; no modifica lógica de producción sin coordinar.
- Integración a `main` solo mediante PR revisado y aprobación humana.

## 4. Calidad mínima

- Validación server-side de todas las entradas.
- Autorización en backend por rol y por objeto; nunca confiar en el frontend.
- Migraciones versionadas y revisables.
- Transacciones para operaciones críticas; idempotencia en webhooks y cierre de recolecciones.
- Auditoría de cambios de estado, asignación y puntos.
- UTC en persistencia; presentación `America/Bogota`.
- Secretos solo en variables/secret manager; nunca en Git, capturas, logs, prompts o documentación.
- Datos sintéticos en desarrollo. No utilizar datos reales de residentes sin autorización.
- No registrar teléfonos, direcciones, tokens, imágenes originales ni payloads sensibles completos en logs.
- Pruebas de permisos negativos, validación, duplicados, concurrencia y errores de integración.

## 5. Honestidad de entrega

Al cerrar una tarea indicar: archivos cambiados, decisiones, pruebas ejecutadas y resultados reales, riesgos, pendientes y cómo reproducir. Diferenciar claramente implementado, simulado, probado, no probado y bloqueado. Nunca afirmar que un test o integración funciona si no se ejecutó.
