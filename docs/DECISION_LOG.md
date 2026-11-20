# Registro de decisiones — EcoConecta

| ID | Decisión | Estado | Procedencia / nota |
|---|---|---|---|
| D-001 | Arquitectura de monolito modular | Vigente | Decisión técnica recomendada para el MVP |
| D-002 | Backend FastAPI/Python | Vigente | Selección técnica del equipo dentro del stack |
| D-003 | Frontend React + TypeScript | Vigente | Selección técnica del equipo |
| D-004 | PostgreSQL única como BD de aplicación | Vigente | Requisito de persistencia y decisión explícita de unificación |
| D-005 | Twilio permitido para prototipo | Vigente con confirmación verbal | Aclaración comunicada por el equipo tras hablar con Daniel, director de TI |
| D-006 | WhatsApp Business Cloud API como integración definitiva | Vigente | Aclaración comunicada por el equipo |
| D-007 | IA permitida con libertad de elección | Vigente con límites de seguridad/privacidad | Aclaración comunicada por el equipo |
| D-008 | Reutilizar modelo de reconocimiento existente | Vigente | Trabajo reportado de Codex 2; métricas pendientes de auditoría |
| D-009 | Reconocimiento no toma decisiones críticas | Vigente | Salvaguarda de producto y seguridad |
| D-010 | Cuatro agentes: 2 Codex + 2 OpenCode | Vigente | Distribución comunicada por el equipo |
| D-011 | Zona/día/hora no son credenciales | Recomendación vigente | Usarlos como perfil/disponibilidad/filtros tras autenticación |
| D-012 | 15 recicladores por zonas/días/horarios | Pendiente de datos reales | Cantidad y organización reportadas por el equipo; cobertura exacta no entregada |

## Cambios respecto a v2

- Se elimina la prohibición absoluta de Twilio; queda permitido solo para prototipo según aclaración verbal.
- Se elimina la limitación rígida de proveedores de IA de la documentación anterior; la libertad comunicada no elimina obligaciones de privacidad, contratos, coste, seguridad y aprobación de datos.
- Se incorpora un segundo Codex dedicado a reconocimiento de imágenes.
- Se hace explícita la base de datos única y compartida por todos los módulos y equipos.
- La integración definitiva de mensajería queda establecida como WhatsApp Business Cloud API.

## Cómo cambiar una decisión

Crear propuesta con: contexto, alternativas, impacto técnico/seguridad/coste, migración, reversibilidad y responsable que aprueba. Actualizar este archivo y los documentos afectados en el mismo PR. No cambiar decisiones silenciosamente.
