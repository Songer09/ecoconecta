# Plan de integración end-to-end

Ver el [backlog del backend por pantallas](BACKEND_SCREEN_BACKLOG.md) para los
acuerdos sobre cierre, reglas administrativas de puntos y las tareas agregadas.
La ubicación de recolectores queda programada para después del flujo principal.

## Prioridad 0 — inspección y acuerdos
- Confirmar repositorio, ramas y código existente.
- Confirmar que los cuatro agentes tienen acceso a la misma carpeta/repositorio, pero no comparten credenciales personales.
- Acordar modelo unificado, OpenAPI, roles y autenticación.
- Codex Backend publica migraciones iniciales y contrato.
- Codex Visión entrega Model Card y contrato de inferencia.
- QA convierte requisitos en casos de prueba.

## Prioridad 1 — núcleo funcional sin dependencias externas
1. Login y autorización por rol.
2. Alta y consulta de solicitudes.
3. Enrutamiento orgánico/reciclable.
4. Bandejas de coordinadores.
5. Asignación y programación.
6. Historial de estados.
7. Registro de recolección y materiales/cantidades.
8. Puntos con reglas configurables y ledger.
9. Reporte básico.

## Prioridad 2 — integración frontend
- OpenCode Frontend conecta login, dashboard, solicitudes, agenda, registro de recolección e historial con API real.
- Eliminar mocks del camino de demo.
- Verificar permisos por rol en backend, no solo en rutas UI.
- QA prueba en viewport móvil y escritorio.

## Prioridad 3 — reconocimiento de imágenes
- Codex Visión entrega evaluación reproducible.
- Backend integra llamada interna.
- UI presenta sugerencia y permite confirmar/corregir.
- Probar baja confianza, clase desconocida y fallo del modelo.
- No bloquear flujo manual si el modelo no responde.

## Prioridad 4 — mensajería
- Twilio sandbox/prototipo si aporta valor a la demo.
- Adaptador definitivo de WhatsApp Business Cloud API.
- Webhooks verificados, idempotencia, reintentos y consentimiento.
- La demo debe etiquetar claramente qué proveedor está conectado.

## Prioridad 5 — seguridad y despliegue
- CI real sin pruebas opcionales silenciosas.
- Escaneo de dependencias/secretos.
- Configuración cloud autorizada.
- HTTPS, backups, logs y health checks.
- Ensayo de restauración y rollback cuando sea viable.
- Ensayo de demo con datos sintéticos.

## Criterio de éxito

La demo debe mostrar una solicitud orgánica y una reciclable recorriendo los estados correctos; asignación real; programación completa; registro de materiales/cantidades; puntos calculados con regla explícita; trazabilidad y notificación identificada como real o simulada.

No priorizar funciones accesorias (chatbot complejo, gamificación avanzada, analítica sofisticada) sobre el flujo transaccional completo.
