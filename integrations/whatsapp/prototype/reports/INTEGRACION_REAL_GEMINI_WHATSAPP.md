# Integración real de Gemini y WhatsApp

Actualizado: 2026-11-20. Rama objetivo: `feat/whatsapp-chatbot`.

## Estado verificado

| Tramo | Código | Credenciales/servicio | Resultado real |
|---|---|---|---|
| Panel → Gemini | Adaptador `generateContent`, salida JSON validada y respaldo local | El propietario rotó la clave de `Default Gemini Project`; está en el `.env` local ignorado por Git, con permisos `0600`. | El catálogo autenticó con HTTP 200 e incluyó `gemini-3.8-flash` con `generateContent`. Una llamada sintética del panel agotó el timeout de 12 s y respondió el respaldo local. Gemini aún no entrega una respuesta validada. |
| WhatsApp → procesamiento local | Webhook Meta, validación de firma y adaptador presentes | App “EcoConecta Chatbot” vinculada al portfolio existente; caso de uso WhatsApp, número/WABA de prueba y permisos `whatsapp_business_management` + `whatsapp_business_messaging`. Token de prueba, secreto de app y verify token guardados solo en `.env` local ignorado por Git, modo `0600`. | Meta confirmó la conexión de una cuenta de WhatsApp. No se ha completado un envío: falta un destinatario de prueba autorizado y el portal de pruebas quedó en blanco tras la autorización. Una consulta GET de solo lectura a Graph API desde el entorno local terminó con `URLError`, sin respuesta HTTP. |
| WhatsApp → Gemini → panel | La aplicación puede combinar los adaptadores al configurarse | El entorno local aún usa el token temporal de prueba de Meta; no hay webhook HTTPS público configurado | Sin validar. |

El servicio de la rama usa únicamente datos sintéticos en su base aislada, con `APP_ENV=demo`, Gemini real y WhatsApp en mock; está publicado localmente en el puerto `55074`. El `.env` conserva esa selección para que el demo siga usando Gemini con WhatsApp simulado. No se modificó ni reinició ningún servicio de `main`.

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

La app “EcoConecta Chatbot” quedó creada y vinculada al Business Portfolio existente. La app sigue en modo de desarrollo y sin publicar. Meta autorizó una sola cuenta actual de WhatsApp; no se habilitaron permisos generales de empresa, correo, eventos ni administración de otras apps. El número de prueba, WABA, token de acceso temporal, secreto de app, verify token y versión de Graph quedaron configurados solo en `integrations/whatsapp/prototype/.env`, ignorado por Git y con permisos `0600`. No se guardaron esos valores en este reporte ni se añadieron a Git.

El `.env` continúa con `APP_ENV=demo`, `AI_PROVIDER=gemini` y `WHATSAPP_PROVIDER=mock`. No cambié el canal a Meta porque la API local está publicada solo en loopback y Meta requiere un callback HTTPS accesible públicamente para entregar mensajes entrantes. Tampoco envié mensajes: Meta no tiene un destinatario de prueba seleccionado. No se enviaron mensajes a teléfonos reales.

La prueba de lectura del número con Graph API no obtuvo respuesta HTTP desde este entorno (`URLError`). Después de completar la autorización, el panel de pruebas de Meta quedó en blanco y no permitió comprobar el envío desde su UI. Por tanto, la presencia de credenciales y el estado de conexión de Meta no equivalen a una prueba funcional de WhatsApp.

## Verificación local de la rama

- `pytest -q -p no:cacheprovider`: 53 pruebas aprobadas; una advertencia de obsolescencia de AnyIO en Starlette TestClient.
- `ruff check --no-cache app migrations tests datasets`: sin hallazgos.
- Evaluación sintética de intención mock: 41 ejemplos; accuracy, scope accuracy y macro F1 de 1.0 en el conjunto existente.
- Benchmark UX sintético: 12 recorridos completos, cero preguntas redundantes, cero errores de ruta y cero solicitudes sin confirmación.
- Las pruebas automatizadas del proveedor usan respuestas HTTP sintéticas. No prueban disponibilidad de generación real ni el canal de Meta.

## Secuencia pendiente

1. Diagnosticar el tiempo de generación de Gemini y obtener una respuesta válida en el panel, manteniendo un límite que no bloquee el flujo.
2. El propietario debe añadir un destinatario de prueba autorizado en Meta; esto comparte su número con Meta. Confirmar ese destinatario antes de enviar el mensaje de prueba.
3. Definir y autorizar un endpoint HTTPS público para staging, suscribir el webhook a `messages` y verificar la ruta sin usar direcciones reales.
4. Renovar un token de prueba si caduca; validar primero el envío y la recepción Meta con procesamiento local. El token temporal actual no es una credencial de despliegue.
5. Solo después de aislar y validar Meta, cambiar la instancia de piloto a `WHATSAPP_PROVIDER=meta` y conectar Gemini. La publicación, verificación empresarial, número productivo, token de sistema y plantillas aprobadas siguen pendientes.
6. Validar notas de voz con audio sintético o expresamente autorizado.

El criterio de integración completa sigue siendo un mensaje entrante desde un teléfono de prueba autorizado, respuesta contextual generada por Gemini y aviso visible en el panel. Aún no se ha alcanzado.
