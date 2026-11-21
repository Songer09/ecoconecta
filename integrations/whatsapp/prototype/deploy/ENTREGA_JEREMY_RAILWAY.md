# Entrega de Jeremy para Railway

Actualizado: 21 de noviembre de 2026, America/Bogota.
Respuesta a [RAILWAY_WHATSAPP.md](RAILWAY_WHATSAPP.md). Este documento no contiene
credenciales ni autoriza crear recursos facturables.

## 1. Versión y procesos

La versión funcional de entrega es **`0842ed255515986c82aa2e8caf6493b7f604ff6e`**.
Los commits posteriores de este traspaso añaden documentación, sin cambiar esa
implementación. El commit `93ff4c9` contiene la guía de Gerson y `136338a`
registra la demo alojada. Desplegar API y worker desde el mismo SHA revisado,
en `feat/whatsapp-chatbot`.

La PR #14 ya está fusionada: su head fue `3e38b4c`. La
[PR #15](https://github.com/Songer09/ecoconecta/pull/15) está abierta en borrador
con el arranque nativo y los accesos portables de `0842ed2`, además de esta
documentación. Destino de revisión: `chore/add-project-documentation`. No se
fusiona ni se modifica directamente la rama destino desde este traspaso.

Directorio raíz de ambos servicios: `integrations/whatsapp/prototype`.

| Operación | Comando |
| --- | --- |
| Construcción nativa (Python 3.12, Node 24) | `sh deploy/build.sh` |
| Migración, una vez antes de iniciar procesos | `python -m alembic upgrade head` |
| API y panel | `sh deploy/start-web.sh` |
| Worker | `python -m app.worker` |
| Salud y panel | `/health` y `/panel` |

Variables compartidas en la primera fase: `DATABASE_URL` de PostgreSQL de
pruebas, `APP_ENV=demo`, `AI_PROVIDER=mock`, `WHATSAPP_PROVIDER=mock`.
En la API: `HOST=0.0.0.0`, `PORT=8000` y `FORWARDED_ALLOW_IPS` con el proxy de
confianza que corresponda. No confiar en todas las IP sin una red que lo limite.
La plantilla [deploy/.env.example](.env.example) contiene solo nombres y ejemplos.
El worker no necesita dominio público. La API necesita HTTPS en la raíz del
dominio, con el panel y las rutas `/api/v1/` en el mismo origen.

Definir `PANEL_RESIDENT_TOKEN` y `PANEL_ADMIN_TOKEN` no crea cuentas por sí solo.
Ejecutar explícitamente los dos comandos `python -m app.access` de
[README.md](README.md#conservar-las-mismas-claves-al-desplegar), en una sesión
privada. Se pueden generar claves nuevas para Railway, distintas para cada rol.
Las claves locales existentes se conservan en ficheros ignorados por Git, con
modo 0600. No están incluidas en el repositorio ni en esta entrega pública.

## 2. App de Meta y responsable

La interfaz de Meta, consultada en esta entrega, muestra:

- App **EcoConecta Chatbot**, sin publicar.
- Un número emisor marcado como **número de prueba**, con Phone Number ID e
  identificador de cuenta de WhatsApp visibles en la sesión privada del titular.
- **Jeremy Restrepo** como administrador de la app. El negocio **Ecoconecta**
  administra la aplicación; sus administradores gestionan roles y configuración.

El 21 de noviembre a las 00:51:56 de Bogotá se repitieron dos consultas Graph de
solo lectura usando las variables locales existentes. Tanto la consulta del
número como `WABA/subscribed_apps` devolvieron **HTTP 401**, error OAuth **190**,
subcódigo **463**. El token guardado no es una credencial operativa vigente.
La comprobación anterior HTTP 200 es evidencia histórica, no el estado actual.
No se determinó en esta comprobación una nueva fecha de vencimiento.

La existencia del número/WABA en la UI está confirmada. El acceso actual por
Graph debe volver a comprobarse con un token renovado. No se confirmó un
destinatario autorizado, ni se configuró webhook, ni se enviaron mensajes.
Jeremy es el responsable identificado para renovar el acceso, autorizar el
destinatario y configurar Meta cuando esté disponible la URL HTTPS.

**Renovación ejecutada:** el 21 de noviembre a las **01:19:36 de Bogotá**,
después del consentimiento completado por el titular en Meta, se verificó el
token nuevo con consultas de lectura. El número configurado devolvió HTTP 200 y
su identificador coincidió; `WABA/subscribed_apps` devolvió HTTP 200 con una app
asociada. Esto sustituye el estado rechazado del token anterior. Es un token
temporal: no se determinó su nueva fecha de expiración ni se acredita una
credencial de producción. La asociación de la app no prueba la suscripción a
`messages` ni la recepción de webhooks.

## 3. Entrega privada de variables

La demo alojada de Gerson funciona sin secretos de Meta ni Gemini.
Para el canal real se requieren, en API y worker: `APP_ENV=pilot`,
`AI_PROVIDER=mock`, `WHATSAPP_PROVIDER=meta`, `DATABASE_URL` de pruebas del piloto,
`META_ACCESS_TOKEN`, `META_PHONE_NUMBER_ID`, `META_WABA_ID`, `META_APP_SECRET`,
`META_VERIFY_TOKEN` y `META_GRAPH_VERSION`. Los nombres ya están documentados en
la guía; los valores nunca se introducen en el PR, issues o logs de despliegue.

El 21 de noviembre de 2026 Jeremy autorizó usar su app **EcoConecta Chatbot**
para el piloto y entregar privadamente a Gerson un token renovado, el secreto de
la app y las variables de verificación para cargarlos en Railway.
Después precisó que **él mismo cargará las variables directamente en Railway**.
Se preparó para el titular el fichero privado local `.env.railway-meta`, con
permisos 0600 y excluido de Git. Contiene las seis variables Meta y
`APP_ENV=pilot`, `AI_PROVIDER=mock`, `WHATSAPP_PROVIDER=meta`; no contiene
`DATABASE_URL`, que debe conservar el valor de la base de pruebas del piloto
configurado por Gerson. No se enviaron valores a Gerson ni se usaron Git, PR,
issues o logs para compartirlos.

Procedimiento autorizado y estado de ejecución:

1. Gerson entrega la URL HTTPS del bot y los nombres de los servicios/entorno.
2. Completado: token temporal renovado y Graph verificado con HTTP 200, sin
   ampliar el alcance anterior de los dos permisos de WhatsApp.
3. Jeremy carga las variables desde el fichero privado local en el gestor de
   secretos de API y worker del piloto en Railway. La carga está pendiente del
   titular; no se han cambiado las variables del alojamiento desde esta sesión.
4. Jeremy configura callback `/api/v1/integrations/whatsapp/webhook`, el mismo
   verify token y la suscripción `messages` de la app/WABA correspondiente.
5. El participante autorizado realiza la prueba de WhatsApp. Registrar resultados
   redactados, sin teléfonos ni encabezados Authorization.

No se distribuye el token anterior rechazado. El nuevo token debe volver a
validarse si transcurre tiempo antes de cargarlo, por su duración limitada.

## 4. Guion y evidencia

Primera fase: demo pública disponible en
[Railway](https://whatsapp-web-production-c49ad447.up.railway.app/panel).
Se comprobó directamente por HTTPS, desde este entorno y sin sesión:

| Recurso | Resultado real |
| --- | --- |
| `/health` | HTTP 200, `status=ok`, `channel=mock`, `ai=mock`, `environment=demo` |
| `/panel` | HTTP 200, HTML |
| `/panel/panel.js` | HTTP 200, JavaScript |
| `/panel/panel.css` | HTTP 200, CSS |
| `/api/v1/me` sin clave | HTTP 401 |

La guía de Gerson informa además accesos de vecino/administrador, una respuesta
simulada y servicios web/worker/PostgreSQL alojados con volumen persistente.
Esa parte se registra como evidencia reportada por Gerson: no se inició sesión
en el panel cloud ni se inspeccionó Railway desde esta sesión. Las claves nuevas
del panel de Railway no son las locales. Faltan por comprobar aquí la conversación
autenticada y la persistencia tras reiniciar los servicios cloud. Esta URL es la
demo; no se utilizará como callback Meta antes de preparar el piloto separado.

Canal Meta: comenzar con «¿Cómo separo el cartón para reciclar?», sin datos
personales. Cargar los artículos y un residente de prueba autorizado como indica
la guía, y comprobar entrada firmada, worker y respuesta recibida en el teléfono.
Para probar después «Tengo cartón para recoger», también hacen falta materiales
aceptados y responsables/coordinadores configurados. `app.seed demo` solo sirve
en `demo/mock`, no en `pilot/meta`. La prueba educativa no demuestra el registro
de avisos ni la integración con la bandeja principal.

Evidencia local ya ejecutada para `0842ed2`: compilación del panel correcta,
**61 pruebas pytest aprobadas** con PostgreSQL nativo y una advertencia de
deprecación Starlette/AnyIO; Ruff aprobado; API/panel HTTP 200; ambas claves
aceptadas; permisos negativos HTTP 401/403; solicitud sintética conservada tras
reiniciar API. El worker nativo estuvo activo durante la comprobación. El
proveedor conversacional fue mock. No se repitió esa batería al añadir solo esta
documentación. Los detalles y reproducción están en el
[informe de integración](../reports/INTEGRACION_REAL_GEMINI_WHATSAPP.md).

## 5. Decisión humana sobre la base principal

El 21 de noviembre de 2026 Jeremy confirmó que **Supabase está aprobado para la
base principal**. Esta decisión humana explícita más reciente sustituye la
prohibición específica de Supabase en `AGENTS.md`, conforme al orden de autoridad
del repositorio. Se conserva el requisito de **una sola PostgreSQL operacional**
como fuente de verdad del producto.

La aprobación no autoriza una segunda persistencia operacional ni crea recursos
facturables. La base aislada descrita aquí es exclusivamente para pruebas. La
actualización coordinada de los documentos compartidos queda a cargo del
responsable de Backend/Integración; esta entrega solo registra la decisión en el
ámbito de WhatsApp.

Las migraciones del prototipo no se aplican sobre la base principal. El contrato
autenticado con FastAPI, su deduplicación y la visualización de avisos en la web
siguen pendientes de integración y revisión del equipo de backend.

El propietario no autorizó gastos. Railway y sus bases/servicios quedan a cargo
de Gerson según la guía. No se crearon recursos ni se activaron servicios públicos;
tampoco se ampliaron permisos externos ni se enviaron mensajes reales en esta entrega.
