# Integración real de Gemini y WhatsApp

Actualizado: 2026-11-20. Rama objetivo: `feat/whatsapp-chatbot`.

## Estado verificado

| Tramo | Código | Credenciales/servicio | Resultado real |
|---|---|---|---|
| Panel → Gemini | Adaptador `generateContent`, salida JSON validada y respaldo local | El propietario rotó la clave de `Default Gemini Project`; está en el `.env` local ignorado por Git, con permisos `0600`. | El catálogo autenticó con HTTP 200 e incluyó `gemini-3.8-flash` con `generateContent`. Una llamada sintética del panel agotó el timeout de 12 s y respondió el respaldo local. Gemini aún no entrega una respuesta validada. |
| WhatsApp → procesamiento local | Webhook Meta, validación de firma y adaptador presentes | El propietario indica que existe un Business Portfolio y lo vinculará a esta cuenta. El asistente de Meta tiene seleccionado el caso WhatsApp, pero aún no muestra el portfolio; la app no se creó. | No se ha probado con Meta ni enviado ningún mensaje real. |
| WhatsApp → Gemini → panel | La aplicación puede combinar los adaptadores al configurarse | Depende de completar Gemini y Meta | Sin validar. |

El servicio de la rama usa únicamente datos sintéticos en su base aislada, con `APP_ENV=demo`, Gemini real y WhatsApp en mock; está publicado localmente en el puerto `55074`. No se modificó ni reinició ningún servicio de `main`. No se creó una app de Meta ni se aceptaron permisos de WhatsApp.

## Gemini

El propietario confirmó que rotó la clave en el proyecto existente `Default Gemini Project`. El valor no está en Git; el `.env` local está ignorado y tiene permisos `0600`. La contraseña local de PostgreSQL de esta instancia sintética también se rotó y no está versionada.

El catálogo del proveedor respondió HTTP 200 con la clave rotada; el modelo configurado aparece y anuncia `generateContent`. En el recorrido sintético del panel, Gemini agotó el límite de 12 segundos (`latency_ms≈12278`) y el asistente devolvió una respuesta local contextual. Una solicitud directa mínima de 30 segundos no produjo un resultado concluyente dentro de la ventana de ejecución. Por ello, Gemini real todavía no está validado.

El adaptador ahora solicita `thinkingLevel=low` y limita cada petición a 12 segundos (5 segundos para conexión), para que un proveedor lento no bloquee el flujo conversacional durante 45 segundos. El estado de respaldo conserva códigos de error seguros y no expone secretos.

Para activar el panel después de rotar la clave, configura localmente `integrations/whatsapp/prototype/.env` a partir de `.env.example`, con:

```dotenv
APP_ENV=demo
AI_PROVIDER=gemini
WHATSAPP_PROVIDER=mock
GEMINI_API_KEY=<clave-nueva-local>
GEMINI_MODEL=gemini-3.8-flash
```

Usa solo texto sintético y confirma que el panel informa `status=success` y `used=gemini`. `status=fallback` significa que respondió el procesador local, no Gemini.

## Meta y WhatsApp

La cuenta terminó el registro de Meta for Developers. En el asistente se ingresó el nombre “EcoConecta Chatbot” y se seleccionó el caso de uso de WhatsApp; el propietario autorizó el correo de contacto prellenado. El siguiente paso está bloqueado porque esta cuenta de desarrollador aún no muestra el Business Portfolio existente. La app no se ha creado. Después de vincularlo faltan credenciales, URL HTTPS del webhook y un destinatario de prueba autorizado.

El código actual verifica la firma del webhook y separa el entorno `pilot` del demo. La prueba con Meta debe comenzar con procesamiento local y un teléfono de prueba autorizado. Solo después de validar ese recorrido se debe habilitar Gemini para WhatsApp. No se enviaron mensajes a teléfonos reales.

## Verificación local de la rama

- `pytest -q -p no:cacheprovider`: 53 pruebas aprobadas; una advertencia de obsolescencia de AnyIO en Starlette TestClient.
- `ruff check --no-cache app migrations tests datasets`: sin hallazgos.
- Evaluación sintética de intención mock: 41 ejemplos; accuracy, scope accuracy y macro F1 de 1.0 en el conjunto existente.
- Benchmark UX sintético: 12 recorridos completos, cero preguntas redundantes, cero errores de ruta y cero solicitudes sin confirmación.
- Las pruebas automatizadas del proveedor usan respuestas HTTP sintéticas. No prueban disponibilidad de generación real ni el canal de Meta.

## Secuencia pendiente

1. Diagnosticar el tiempo de generación de Gemini y obtener una respuesta válida en el panel, manteniendo un límite que no bloquee el flujo.
2. Vincular el Business Portfolio existente a la cuenta de desarrollador y terminar la creación/configuración de la app Meta/WhatsApp.
3. Configurar webhook HTTPS y un destinatario de prueba autorizado.
4. Probar mensajes entrantes/salientes con procesamiento local; después conectar Gemini y comprobar cada tramo por separado.
5. Validar notas de voz con audio sintético o expresamente autorizado.

El criterio de integración completa sigue siendo un mensaje entrante desde un teléfono de prueba autorizado, respuesta contextual generada por Gemini y aviso visible en el panel. Aún no se ha alcanzado.
