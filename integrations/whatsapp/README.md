# WhatsApp / Twilio — espacio de integración

Responsable: compañero encargado de mensajería. Esta carpeta contiene configuración
y acuerdos del adaptador; la aplicación sigue siendo un monolito FastAPI con una
única PostgreSQL. No crear aquí un backend, base de datos o sistema de usuarios paralelo.
No hay conexión implementada ni credenciales configuradas todavía.

Rama propia: `feat/whatsapp-chatbot`. El agente principal coordina contratos y revisa
integración; no editar en paralelo archivos de backend/esquema sin acuerdo.

## Alcance

Twilio es el proveedor elegido para la integración actual del prototipo.
La documentación v3 mantiene WhatsApp Business Cloud API como destino definitivo;
si Twilio también será definitivo, registrar esa decisión humana antes de cambiarla.
El adaptador ejecutable se integrará bajo `apps/api` cuando exista el backend.

El compañero prepara ChatBot, sandbox, configuración, validación de firma, normalización
de eventos y pruebas del proveedor. Backend conserva autorización, persistencia,
transacciones, reintentos y reglas de negocio. Coordinar antes de editar `db/schema.sql`,
`db/**`, contratos o archivos compartidos de `apps/api`.

## Configuración de prueba

1. Usar una cuenta y destinatarios de prueba autorizados. Activar el Sandbox y unir
   el teléfono de prueba con el código que muestra Twilio; no publicar ese código.
2. Copiar `.env.example` a un archivo local `.env` y completar los valores fuera de Git.
   No poner secretos en frontend, capturas, documentación ni logs.
3. Cuando backend implemente las rutas acordadas, configurar la URL HTTPS pública de
   recepción y el callback de estados. La URL externa debe coincidir con la usada
   para validar la firma, incluso si existe proxy.
4. Validar `X-Twilio-Signature` mediante el SDK oficial y todos los parámetros recibidos.
   No deshabilitar validación en el endpoint público ni aceptar parámetros añadidos
   por el cliente como identidad autenticada de EcoConecta.
5. Probar recepción, envío, firma inválida, duplicados, callback de entrega/fallo,
   eventos fuera de orden y caída del proveedor con datos sintéticos.

Referencias oficiales: [inicio y sandbox](https://www.twilio.com/docs/whatsapp/quickstart),
[seguridad y validación de firmas](https://www.twilio.com/docs/usage/security).

## Contrato propuesto para acordar con backend

Rutas futuras, todavía no implementadas:

- `POST /api/v1/integrations/whatsapp/twilio/inbound`: webhook entrante.
- `POST /api/v1/integrations/whatsapp/twilio/status`: callback de estado.
- Las rutas GET de verificación de Meta no se reutilizan como verificación de Twilio.

El adaptador traduce los campos del proveedor a:
`provider`, `provider_message_id`, `event_key`, `event_kind`, `delivery_status`
y contexto mínimo validado. El identificador de usuario lo resuelve backend;
el webhook no elige arbitrariamente el `user_id` de la aplicación.

`event_key` se deriva de forma determinista: para mensajes entrantes, del ID del
mensaje y tipo de evento; para callbacks, también del estado y del identificador
de evento si está disponible. No deduplicar todos los estados solo por MessageSid:
un mismo mensaje puede producir varios callbacks legítimos. Acordar normalización
y orden de estados antes de implementar. Deduplicación en `webhook_events` mediante
`UNIQUE(provider, event_key)`, con reintento de eventos fallidos y sin repetir efectos
de eventos procesados.

Puerto saliente sugerido: `send_notification(notification_id, recipient, template,
parameters) -> provider_message_id`. Los datos de destinatario viven solo dentro
del backend autorizado; `notification_id` sirve de referencia para reintentos.
Un timeout de envío no prueba que Twilio no aceptó el mensaje: acordar reconciliación
antes de reenviar automáticamente. Fallar el proveedor no revierte una recolección.

La firma prueba el origen de un webhook, no concede permisos de coordinador ni
autoriza cerrar solicitudes. No guardar payloads completos por defecto.

## Entrega del compañero

Entregar versión/dependencias del SDK, rutas, configuración de proxy, ejemplos
sintéticos, pruebas y resultados, errores normalizados y política de reintentos.
No modificar migraciones ni estados/puntos desde el adaptador. Retención de cuerpos,
consentimiento y plantillas se acuerdan con el responsable humano.
