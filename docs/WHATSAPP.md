# Integración WhatsApp Business Cloud API

## Decisión
Usar la WhatsApp Business Cloud API oficial directamente. No usar Twilio para este reto salvo autorización formal explícita de la Fundación.

## Casos de uso MVP
- Confirmar recepción de solicitud.
- Comunicar fecha, hora y persona encargada cuando exista programación.
- Comunicar cambios/cancelación autorizados.
- Enviar recordatorios solo si se aprueban y hay consentimiento/base legal adecuada.

## Diseño
- Adaptador `WhatsAppCloudClient` en infraestructura.
- Casos de uso internos llaman un puerto `NotificationSender`.
- Token, Phone Number ID, WABA ID y Verify Token solo en secretos del entorno.
- Webhook con verificación de origen según documentación vigente de Meta.
- Deduplicar eventos entrantes por identificador del proveedor.
- Registrar estado de envío y errores sin registrar tokens ni contenido personal innecesario.
- Gestionar límites, reintentos con backoff y fallos permanentes.
- Plantillas aprobadas cuando el tipo de mensaje/ventana de conversación lo requiera.

## Seguridad y operación
- No exponer tokens en frontend.
- No aceptar comandos WhatsApp que asignen o cierren solicitudes automáticamente.
- El mensaje es canal de comunicación, no fuente de autorización.
- No enviar dirección completa a perfiles no autorizados.
- Usar números de prueba y datos ficticios durante desarrollo.
- La integración no se considera terminada hasta probar webhook, entrega, fallo, duplicado y consentimiento.

## Variables de entorno (nombres, nunca valores)
WHATSAPP_ACCESS_TOKEN
WHATSAPP_PHONE_NUMBER_ID
WHATSAPP_BUSINESS_ACCOUNT_ID
WHATSAPP_WEBHOOK_VERIFY_TOKEN
WHATSAPP_APP_SECRET
WHATSAPP_API_VERSION

> **ACTUALIZACIÓN v3:** Este documento proviene de la versión 2. Si contradice `AGENTS.md`, `docs/DECISION_LOG.md`, `docs/FOUNDATION_BRIEF.md` o `docs/DESIGN_GUIDE.md`, prevalece v3. En particular, Twilio está permitido para prototipo, la IA tiene libertad de elección bajo controles de privacidad/seguridad y la aplicación usa una única PostgreSQL compartida.


## Decisión vigente v3

Twilio puede utilizarse para prototipo/prueba según aclaración verbal del equipo. WhatsApp Business Cloud API oficial será la integración definitiva. La lógica de negocio debe depender de una interfaz de proveedor, no de un SDK concreto. Ver `docs/WHATSAPP_CHANNELS.md`.
