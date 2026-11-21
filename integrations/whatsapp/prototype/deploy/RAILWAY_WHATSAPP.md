# Despliegue de WhatsApp en Railway

Traspaso para Jeremy y su Codex. Gerson y su Codex harán el despliegue en el
proyecto Railway de Gerson. Jeremy trabaja desde GitHub y, si tiene acceso,
desde Meta. El objetivo es que la API, el panel y el worker funcionen en la
nube con los computadores de ambos apagados.

## Entrega que necesitamos de Jeremy

1. Confirma qué commit debe desplegarse y abre una PR con los cambios
   posteriores a la #14. Indica si `0842ed2` es la versión de entrega o si
   hay correcciones adicionales. Incluye los comandos de API, worker y
   migraciones y las variables requeridas, con valores de ejemplo únicamente.
2. Confirma si su app de Meta tiene una WABA y un número emisor **de prueba**
   que podamos usar. Identifica al administrador que puede agregar un
   destinatario autorizado, configurar el webhook y suscribir `messages`.
   Cuando Gerson entregue la URL HTTPS, ese administrador puede configurar
   Meta o dar acceso al responsable de EcoConecta.
3. Si se autoriza usar esa app, acuerda cómo entregar a Gerson sus
   identificadores y cargar en privado un token vigente y el secreto de la
   app. Las claves del panel son opcionales para el traspaso, porque Gerson
   puede generar otras. Adjunta el guion de prueba y los resultados
   disponibles, con datos sensibles redactados.

Gerson y su Codex ejecutan todas las tareas de Railway y PostgreSQL descritas
abajo. El administrador de Meta configura el canal y un participante
autorizado envía el mensaje de prueba desde su teléfono.

## Demo ya alojada

En el proyecto Railway de EcoConecta están en línea `whatsapp-web`,
`whatsapp-worker` y `whatsapp-postgres`. La base de demo tiene un volumen
persistente y se accede a ella por la red privada. Se verificaron el panel y
sus recursos por HTTPS, los accesos de vecino y administrador y una respuesta
simulada con el procesador local. Los tokens nuevos del panel se generaron
para este despliegue y están configurados como secretos de Railway.

Para Jeremy queda confirmar los recursos de prueba de Meta y quién puede
administrarlos. Gerson compartirá la URL del webhook del entorno piloto cuando
se configure ese entorno con sus credenciales y su base aislada. El panel
alojado actualmente sigue en modo demo.

[Panel de demostración](https://whatsapp-web-production-c49ad447.up.railway.app/panel) · [Estado de la API](https://whatsapp-web-production-c49ad447.up.railway.app/health)

## Punto de partida

La PR #14 fusionó las mejoras anteriores. El commit `0842ed2` en
`feat/whatsapp-chatbot` añadió el arranque sin Docker y el aprovisionamiento
de accesos del panel. El proyecto EcoConecta ya tiene FastAPI y Compost-AI
en Railway, con Supabase para la API principal. El bot todavía usa su propio
modelo de datos. Para estas pruebas, prepara una PostgreSQL alojada y aislada
para el prototipo. Sus migraciones incluyen tablas propias como `users` y
`collection_requests`. Mantén sus migraciones fuera de la base principal.

## 1. Publicar el panel con mensajería simulada

Este paso funciona sin cuenta Meta ni clave de Gemini.

1. En Railway usa el proyecto EcoConecta y crea los servicios de prueba
   `whatsapp-web` y `whatsapp-worker`. Usa el mismo commit en ambos y el
   directorio raíz `integrations/whatsapp/prototype`. Usa el Dockerfile ya
   disponible o Python 3.12 y Node 24 con `sh deploy/build.sh`.
2. Configura en ambos servicios el mismo `DATABASE_URL` de la base **del
   prototipo**, `APP_ENV=demo`, `AI_PROVIDER=mock` y
   `WHATSAPP_PROVIDER=mock`. Para la instalación nativa, usa
   `sh deploy/start-web.sh` en la API y `python -m app.worker` en el worker.
   Con Docker, la API puede usar el comando del Dockerfile y el worker debe
   sobrescribirlo con `python -m app.worker`. El Procfile documenta procesos
   separados para plataformas que lo soporten.
3. Ejecuta una sola vez `python -m alembic upgrade head` como tarea de
   inicialización antes de arrancar ambos servicios. En el servicio web usa
   `HOST=0.0.0.0` y `PORT=8000`, genera el dominio HTTPS para ese puerto y usa
   `/health` como comprobación. El worker funciona sin dominio público.
4. En la base de demo, ejecuta `python -m app.seed demo` en una sesión privada
   si necesitas las cuentas y el catálogo sintéticos. El comando muestra los
   tokens iniciales una vez. Usa `python -m app.access` con
   `PANEL_RESIDENT_TOKEN` y `PANEL_ADMIN_TOKEN` si necesitas provisionar
   accesos determinados. Genera tokens distintos para el despliegue o impórtalos
   por un canal privado con autorización del titular. Las variables del panel
   se usan para aprovisionar las cuentas. La aplicación consulta sus hashes en
   PostgreSQL.
5. Comprueba por HTTPS que `/health` devuelve `channel=mock`, que `/panel`
   carga y que un vecino de demo recibe una respuesta desde el panel. Reinicia
   la API y el worker en Railway y repite la comprobación con los computadores
   del equipo fuera del recorrido. Registra el consumo de API, worker y base
   en el espacio de trabajo.

[Despliegue nativo y claves del panel](README.md) · [Monorepos en Railway](https://docs.railway.com/deployments/monorepo) · [Dominios en Railway](https://docs.railway.com/networking/domains/working-with-domains)

## 2. Activar y verificar WhatsApp real

Para **este** paso hace falta acceso autorizado a una app y una cuenta
WhatsApp Business (WABA) en Meta, con un número emisor y un destinatario de
prueba autorizado. Usa un entorno de piloto y una base aislada de la demo
para probar el canal real. Configura API y worker con `APP_ENV=pilot`,
`WHATSAPP_PROVIDER=meta` y `AI_PROVIDER=mock`. Ese último ajuste usa el
procesamiento local y permite probar WhatsApp aunque Gemini siga pendiente.

| Variable | De dónde sale o para qué sirve |
|---|---|
| `META_ACCESS_TOKEN` | Token vigente con acceso a la WABA y permisos de mensajería. La suscripción a la WABA requiere autorización de administración. |
| `META_PHONE_NUMBER_ID` | ID del número emisor en Meta. |
| `META_WABA_ID` | ID de la cuenta WhatsApp Business. |
| `META_APP_SECRET` | Secreto de la app de Meta para validar la firma de los webhooks. |
| `META_VERIFY_TOKEN` | Cadena aleatoria definida por el equipo. Introduce el mismo valor en Railway y en la verificación del webhook de Meta. |
| `META_GRAPH_VERSION` | Versión de Graph habilitada para la app. |

1. Introduce las variables en Railway y comprueba `/health`. En Meta registra
   `https://<dominio-del-bot>/api/v1/integrations/whatsapp/webhook` como
   callback con el token de verificación. Suscribe el campo `messages`
   y verifica también que la app esté suscrita a la WABA correcta.
2. Agrega el teléfono de prueba autorizado en Meta. Registra el mismo
   teléfono como residente activo del prototipo, usando únicamente dígitos,
   con indicativo de país y sin el signo `+`. El webhook busca una cuenta
   activa con ese número antes de procesar el mensaje. Hazlo desde una
   sesión privada del operador, ya que el comando genera un token de panel:

   ```sh
   python -m app.seed articles
   python -m app.seed user --handle vecino-meta-prueba --role resident --phone "$TEST_PHONE_DIGITS"
   ```

3. Desde ese teléfono, **envía tú** al número emisor de prueba una pregunta
   sin datos personales, por ejemplo «¿Cómo separo el cartón para reciclar?».
   Verifica el evento entrante en Railway, que el worker lo procese y que
   la respuesta llegue al mismo WhatsApp. Una verificación HTTPS o un GET
   exitoso a Graph por sí solos no prueban ese recorrido.
4. Registra el resultado con la hora, el resultado del webhook y del worker,
   y la recepción en el teléfono de prueba. Redacta teléfonos, secretos y
   tokens. Cuando cambie el token temporal de Meta, actualízalo en ambos
   servicios. Si se prueban notificaciones iniciadas por el bot, revisa
   aparte el consentimiento y las plantillas aprobadas.

[WhatsApp Cloud API de Meta](https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api) · [Suscripción a la WABA](https://www.postman.com/meta/whatsapp-business-platform/request/26gui66/subscribe-to-a-waba)

### Alternativa con Twilio Sandbox

La cuenta y el número de prueba de Meta sirven para pruebas limitadas.
En producción, Meta puede cobrar por plantillas según categoría y destino.
Si el equipo elige Twilio para la demo, su Sandbox da un número compartido.
El responsable activa el Sandbox en la consola de Twilio, el participante
envía `join <código-del-sandbox>` desde WhatsApp y Gerson configura la URL
HTTPS entrante cuando exista el adaptador. Twilio ofrece unidades de prueba
y aplica sus tarifas estándar fuera de esas unidades.

El commit actual admite `mock` y `meta`. Para Twilio, Jeremy y su Codex
tendrían que entregar un adaptador con validación de firma de Twilio,
normalización de mensajes, deduplicación por `MessageSid`, respuesta y pruebas.
Gerson desplegaría ese adaptador y configuraría el Sandbox con la URL
resultante. La ruta de Meta usa su propio formato y verificación.

[Sandbox de Twilio](https://www.twilio.com/docs/whatsapp/sandbox) · [Precios de Twilio](https://www.twilio.com/en-us/whatsapp/pricing)

## 3. Conectar los avisos con EcoConecta

Una respuesta de ida y vuelta verifica el canal. Para verificar el producto,
acuerda un contrato autenticado entre el bot y FastAPI para enviar el aviso
solo después de que el vecino lo confirme. El backend debe resolver la
identidad autorizada, validar zona y flujo, registrar la solicitud y deduplicar
reintentos con el identificador del mensaje de Meta. El bot debe conservar
el identificador devuelto por FastAPI. Usa la red privada de Railway para
esta comunicación cuando los servicios compartan proyecto y entorno.

La prueba de entrega termina cuando un aviso confirmado desde el teléfono
autorizado se guarda en la PostgreSQL principal de EcoConecta y aparece en
la bandeja web del colectivo correcto. Comprueba que un reintento produzca
una sola solicitud y registra por separado la evidencia del canal y de la
integración con la web. La demo alojada y la prueba de WhatsApp no requieren
Gemini para ese recorrido.

[Red privada de Railway](https://docs.railway.com/networking/private-networking)
