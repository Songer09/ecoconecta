# EcoConecta · Punto de retoma del 21 de noviembre de 2026

Continúa en `feat/fullstack-integration`. El código desplegado corresponde al commit `0b0f86a`. La rama predeterminada de GitHub todavía apunta a una versión anterior. [Abrir EcoConecta](https://ecoconectadk.netlify.app).

**Estado de la web.** Netlify sirve el frontend y dirige las llamadas de la aplicación al backend de Railway, que usa PostgreSQL en Supabase. Tras el despliegue se comprobó que el catálogo respondió HTTP 200 desde el dominio público y que el perfil sin sesión respondió HTTP 401.

## Pendientes, en orden

1. **Probar la web con cuentas piloto.** Registrar un vecino de prueba, crear una solicitud con materiales y foto, revisar la sugerencia de Compost-AI y confirmar el material. Desde coordinación, asignar y programar la recogida. Desde la cuenta recolectora, registrar el peso. Volver a coordinación para confirmar y comprobar el estado y el saldo del vecino. Para este recorrido hacen falta una zona con cobertura, un recolector disponible y una regla de puntos aprobada.
2. **Elegir el número emisor del piloto.** Jeremy recibió el mensaje enviado por el número de prueba de Meta. El equipo aún debe elegir un número de negocio bajo su control y verificarlo en Meta, en **Conectar en WhatsApp → Configuración básica → Paso 2: Configuración de producción**.
3. **Conectar ese emisor a Railway.** En la API y el worker del piloto de WhatsApp, configurar `META_PHONE_NUMBER_ID` con el identificador del emisor que entrega Meta. Confirmar que `META_WABA_ID` y `META_ACCESS_TOKEN` corresponden a esa cuenta y tienen acceso al número. Los valores privados se guardan como secretos en Railway.
4. **Probar WhatsApp de extremo a extremo.** El equipo comunicó que Meta aceptó la configuración. Confirmar la suscripción del webhook al evento `messages` para la cuenta elegida. Desde otro teléfono, escribir al número piloto, comprobar la respuesta del bot y confirmar que una solicitud completada aparece una sola vez en EcoConecta. El envío de prueba a Jeremy solo comprobó la salida de mensajes.

El directorio operativo y los informes administrativos siguen teniendo alcance limitado. El piloto de WhatsApp se preparó con `AI_PROVIDER=mock`; la prueba con Gemini sigue pendiente si el equipo decide habilitarlo.
