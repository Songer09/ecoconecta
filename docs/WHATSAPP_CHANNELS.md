# Canales de WhatsApp — prototipo y definitivo

## Decisión

- **Prototipo/prueba:** Twilio está permitido según aclaración verbal comunicada por el equipo tras hablar con Daniel, director de TI.
- **Definitivo:** WhatsApp Business Cloud API oficial.

La implementación debe desacoplar el dominio del proveedor. La aplicación no debe depender de Twilio para gestionar solicitudes, asignaciones o recolecciones.

## Diseño

Definir una interfaz de proveedor de mensajería con operaciones necesarias, por ejemplo:
- enviar mensaje de plantilla/texto según capacidades y políticas del proveedor;
- consultar/recibir estado de entrega;
- normalizar mensajes entrantes;
- gestionar errores y reintentos.

Implementaciones separadas:
- `TwilioAdapter` para prototipo.
- `WhatsAppCloudAdapter` para producción.

## Seguridad y fiabilidad

- Verificar autenticidad de webhooks según el mecanismo oficial del proveedor.
- Rechazar firmas inválidas.
- Idempotencia por ID de mensaje/evento externo.
- Guardar eventos recibidos y estado de procesamiento.
- Manejar reintentos y eventos fuera de orden.
- No ejecutar lógica de negocio crítica dos veces por duplicado.
- No incluir teléfonos completos, tokens o cuerpos sensibles en logs.
- Guardar secretos en variables seguras/secret manager.
- Aplicar límites de tasa y validación de payload.
- Respetar consentimiento, opt-in, ventanas y plantillas aplicables a WhatsApp.
- No usar mensajes como fuente de verdad: PostgreSQL mantiene el estado real.

## Configuración

Documentar solo nombres de variables, nunca valores:
- `MESSAGING_PROVIDER=twilio|whatsapp_cloud`
- variables de credenciales específicas del adaptador
- `WEBHOOK_PUBLIC_BASE_URL`
- identificadores de cuenta/número/phone-number-id cuando aplique.

No versionar `.env`, tokens, claves o secretos.

## Transición

1. Mantener contratos internos estables.
2. Desarrollar y probar Twilio en sandbox si es útil.
3. Implementar WhatsApp Cloud Adapter usando documentación oficial vigente.
4. Probar webhook, mensajes entrantes/salientes, errores y reintentos.
5. Cambiar configuración por entorno; no cambiar lógica de dominio.
6. Desactivar Twilio cuando se apruebe el definitivo, salvo que exista una razón documentada para mantenerlo como fallback.
