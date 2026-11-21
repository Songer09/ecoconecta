# Integración Gemini y WhatsApp

Actualizado: 2026-11-20. Rama: `feat/whatsapp-chatbot`.

## Estado de integración

| Integración | Implementado | Configurado ahora | Probado con mock | Probado con API real | Estado |
|---|---:|---:|---:|---:|---|
| Gemini para el panel de demostración | Sí | No: falta `GEMINI_API_KEY` | Sí | No | Fase A lista para configurar; prueba real pendiente |
| WhatsApp Business Cloud API | Sí, adaptador/webhook existente | No | Sí | No | Fase B pendiente |
| Gemini + WhatsApp real | — | — | — | No | Fase C pendiente |

El contenedor activo observado está en `APP_ENV=demo`, `AI_PROVIDER=mock` y `WHATSAPP_PROVIDER=mock`. La clave Gemini no está configurada. No se hizo ninguna solicitud al proveedor externo. En el checkout de desarrollo tampoco existe un `.env` con credenciales.

En la revisión del 2026-11-20, el contenedor activo respondió `GET /health` con `ai=mock` y `channel=mock`. Su bundle `/panel/panel.js` todavía no incluye el diagnóstico por turno añadido en `4401fff`, por lo que el servicio activo no está ejecutando la imagen de la rama actual. No se reconstruyó ni reinició al faltar la clave Gemini.

## Fase A

El panel conserva el canal de mensajería simulado y permite usar el adaptador Gemini existente al configurar `AI_PROVIDER=gemini`. El panel muestra por turno si Gemini respondió correctamente, si el mensaje permaneció local por privacidad, o si el adaptador usó el respaldo local después de un error. Los fallos se reducen a códigos seguros como `timeout`, `authentication_rejected`, `model_not_found`, `quota_exceeded`, `service_unavailable` e `invalid_response`; no se guardan mensajes de error del proveedor ni secretos.

Para activar Gemini localmente, configura en `integrations/whatsapp/prototype/.env`:

```dotenv
APP_ENV=demo
AI_PROVIDER=gemini
WHATSAPP_PROVIDER=mock
GEMINI_API_KEY=<clave-local>
GEMINI_MODEL=gemini-3.6-flash
```

La clave debe permanecer en ese `.env` ignorado por Git. Reinicia solo el prototipo y conversa desde el panel como `hogar-demo`. Usa texto sintético. El backend continúa validando el esquema y conserva la responsabilidad de aceptación de materiales, confirmaciones y registros.

## Evidencia y límites

- El adaptador Gemini usa `generateContent`, instrucciones de sistema, JSON estructurado y validación Pydantic.
- La ficha oficial del modelo declara entrada de texto y audio y soporte de salidas estructuradas. La API aún permite `generateContent`; la documentación actual marca Interactions como interfaz recomendada para proyectos nuevos.
- **Configurado** no significa **conectado**. La conexión real se considerará probada solo después de una solicitud autorizada con una clave válida y una respuesta válida que el panel identifique como Gemini.
- El panel puede enrutar a Gemini solo cuando el mensaje no activa la regla local de privacidad/seguridad. Los campos privados, como direcciones, se mantienen localmente.
- Los indicadores y resultados de pruebas locales no demuestran recepción, procesamiento o entrega por WhatsApp.

### Verificación local (WhatsApp y proveedor IA simulados)

- `pytest -q`: 53 pruebas aprobadas.
- `ruff check app migrations tests datasets`: sin hallazgos.
- Evaluación de intención mock: 41/41 correctas; accuracy, scope accuracy y macro F1 de 1.0 en el conjunto existente.
- Benchmark UX: 12/12 recorridos completos, cero preguntas redundantes, cero errores de ruta y cero solicitudes sin confirmación.
- El contrato Gemini y los estados de éxito/respaldo se ejercitaron con respuestas HTTP sintéticas. Ninguna llamada real a Gemini ni WhatsApp se ejecutó.

## Siguientes fases

1. **Desbloqueo de Fase A:** el propietario configura `GEMINI_API_KEY` en el `.env` local; se ejecuta una prueba sintética autorizada y se conserva la evidencia de modelo, estado y latencia.
2. **Fase B:** configurar Meta en un entorno `pilot`, exponer el webhook por HTTPS y probar texto con procesamiento local, teléfono de prueba autorizado y destinatario autorizado.
3. **Fase C:** habilitar Gemini en ese entorno después de completar B y validar el recorrido entrante/saliente.
4. **Fases D–E:** verificar recolecciones por flujo y, tras verificar consentimiento y controles, audio real.

No se activó Meta, no se envió ningún mensaje externo y no se procesaron datos personales con Gemini.
