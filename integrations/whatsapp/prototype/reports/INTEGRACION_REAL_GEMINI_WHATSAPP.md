# Integración real de Gemini y WhatsApp

Actualizado: 2026-11-20. Rama objetivo: `feat/whatsapp-chatbot`.

## Estado verificado

| Tramo | Código | Credenciales/servicio | Resultado real |
|---|---|---|---|
| Panel → Gemini | Adaptador `generateContent`, salida JSON validada y respaldo local | La clave se creó en `Default Gemini Project`; requiere rotación antes de volver a usarla. El checkout no contiene `.env`. | La autenticación contra el catálogo de modelos devolvió HTTP 200 y el catálogo incluyó `gemini-3.8-flash`. Las solicitudes de generación agotaron el tiempo de espera; no se obtuvo respuesta de Gemini. |
| WhatsApp → procesamiento local | Webhook Meta, validación de firma y adaptador presentes | La cuenta de desarrollador ya está registrada, pero Meta muestra **Aún no hay apps**. No hay token, número ni cuenta de WhatsApp Business configurados. | No se ha probado con Meta ni enviado ningún mensaje real. |
| WhatsApp → Gemini → panel | La aplicación puede combinar los adaptadores al configurarse | Depende de completar Gemini y Meta | Sin validar. |

El servicio de la rama usó únicamente datos sintéticos en su base aislada. No se modificó ni reinició ningún servicio de `main`. No se creó una app de Meta ni se aceptaron permisos de WhatsApp.

Tras las pruebas, retiré los contenedores aislados de esta rama para que no conservaran la credencial en su configuración. El volumen de datos no se borró. El servicio se debe recrear después de rotar la clave.

## Gemini

La clave se creó con autorización del propietario en el proyecto existente `Default Gemini Project`. Se verificó que el catálogo de Gemini responde y anuncia `generateContent` para el modelo configurado. Eso confirma que la clave autentica y que el modelo aparece disponible; no confirma que la generación esté funcionando.

Las solicitudes de generación probadas desde el chatbot agotaron el tiempo de espera; una solicitud directa mínima también superó 45 segundos. El chatbot devolvió el resultado local de respaldo. El adaptador ahora solicita razonamiento `low`, pero ese ajuste aún requiere una nueva llamada para verificar su efecto. Por ello, Gemini real todavía no está validado. Antes de otra llamada se debe rotar la clave desde AI Studio. El archivo `.env` no se versiona y debe permanecer fuera de Git.

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

La cuenta terminó el registro de Meta for Developers. La página de apps confirma que aún no existe una aplicación. Falta crear/configurar la app de Meta, agregar el caso de uso de WhatsApp, vincular una cuenta de WhatsApp Business, configurar credenciales y URL HTTPS del webhook, y autorizar un destinatario de prueba.

El código actual verifica la firma del webhook y separa el entorno `pilot` del demo. La prueba con Meta debe comenzar con procesamiento local y un teléfono de prueba autorizado. Solo después de validar ese recorrido se debe habilitar Gemini para WhatsApp. No se enviaron mensajes a teléfonos reales.

## Verificación local de la rama

- `pytest -q -p no:cacheprovider`: 53 pruebas aprobadas; una advertencia de obsolescencia de AnyIO en Starlette TestClient.
- `ruff check --no-cache app migrations tests datasets`: sin hallazgos.
- Evaluación sintética de intención mock: 41 ejemplos; accuracy, scope accuracy y macro F1 de 1.0 en el conjunto existente.
- Benchmark UX sintético: 12 recorridos completos, cero preguntas redundantes, cero errores de ruta y cero solicitudes sin confirmación.
- Las pruebas automatizadas del proveedor usan respuestas HTTP sintéticas. No prueban disponibilidad de generación real ni el canal de Meta.

## Secuencia pendiente

1. Rotar la clave Gemini en AI Studio y guardar la nueva clave localmente, sin incluirla en Git ni en el chat.
2. Repetir una solicitud sintética desde el panel y confirmar una respuesta real de Gemini.
3. Crear y configurar la app de Meta y WhatsApp Business Cloud API; asegurar webhook HTTPS y un destinatario de prueba autorizado.
4. Probar mensajes de texto entrantes/salientes con procesamiento local; después conectar Gemini y comprobar cada tramo por separado.
5. Validar notas de voz con audio sintético o expresamente autorizado.

El criterio de integración completa sigue siendo un mensaje entrante desde un teléfono de prueba autorizado, respuesta contextual generada por Gemini y aviso visible en el panel. Aún no se ha alcanzado.
