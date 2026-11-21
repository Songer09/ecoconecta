# Estado de la integración Meta, Gemini y EcoConecta web

> Seguimiento del 21 de noviembre: hay una demo Railway pública con IA y
> mensajería simuladas, verificada por HTTPS; el token Meta local ahora es
> rechazado. El estado actualizado y el traspaso están en
> [ENTREGA_JEREMY_RAILWAY.md](../deploy/ENTREGA_JEREMY_RAILWAY.md).
> Las secciones fechadas el 20 de noviembre conservan la evidencia histórica.

Actualizado: 20 de noviembre de 2026, hora de Bogotá. Rama objetivo: feat/whatsapp-chatbot. HEAD remoto comprobado al iniciar: bbd414cb0f3ba506c13960bcd2200cf262fdf83f.

## Estado por evidencia

| Tramo | Estado | Evidencia actual |
|---|---|---|
| Adaptador WhatsApp Cloud API | IMPLEMENTADO | Código de webhook, firma, normalización, worker y adaptador Meta dentro del prototipo. La instancia que está corriendo conserva WHATSAPP_PROVIDER=mock. |
| Credencial Meta actual | PROBADO CON API REAL | GET del número de prueba y GET de WABA/subscribed_apps devolvieron HTTP 200 desde un contenedor temporal de Compose. La respuesta mostró una app asociada, pero no incluyó subscribed_fields. |
| Vencimiento del token Meta | PENDIENTE | La credencial actual es temporal. Los GET aceptados demuestran que estaba activa durante la prueba, pero debug_token devolvió error OAuth de Graph 190 al intentar obtener su vencimiento. No se determinó la fecha de expiración. |
| Token temporal anterior expuesto | PENDIENTE | El propietario lo rotó. El valor anterior no está disponible para consultar si Meta lo invalidó automáticamente; debe considerarse comprometido hasta revocarlo en Meta. |
| Destinatario autorizado | NO CONFIRMADO | No hay evidencia verificable de un destinatario de prueba registrado en Meta. |
| Webhook HTTPS público | NO IMPLEMENTADO | No hay URL pública ni servicio de staging. El API local escucha solo en 127.0.0.1:55074. |
| Suscripción Meta a mensajes | NO CONFIGURADO | WABA/subscribed_apps devolvió una app asociada, pero no incluyó el campo subscribed_fields. No se cambió la suscripción ni se activó un webhook. |
| Envío o recepción real WhatsApp | NO PROBADO | No envié mensajes ni hay evidencia de un mensaje entrante real. |
| Gemini: catálogo/modelo | PROBADO CON API REAL | El endpoint de metadatos devolvió HTTP 200 para gemini-3.8-flash y enumeró generateContent entre los métodos permitidos. |
| Gemini: generación | BLOQUEADO POR PROVEEDOR | El adaptador agotó 12 s y luego una repetición acotada de 45 s. Una generación mínima estructurada con el texto sintético solicitado devolvió HTTP 503 UNAVAILABLE en 1,8 s. No se obtuvo interpretación generada por Gemini. |
| Flujo del prototipo y PostgreSQL | PROBADO CON MOCK | 53 pruebas aprobaron sobre PostgreSQL temporal. No validan la entrega real de WhatsApp ni la disponibilidad de Gemini. |
| Aplicación web completa | NO INTEGRADO | La rama WhatsApp contiene el prototipo aislado; los módulos web y de API compartida no están juntos en esta rama. |
| Despliegue de staging | NO IMPLEMENTADO | No se creó recurso cloud, dominio, base gestionada ni servicio público. |

## Gemini

El servicio local en 127.0.0.1:55074 respondió health HTTP 200 con entorno demo, proveedor IA gemini y canal mock. Esto confirma la configuración del proceso, no una generación válida.

Pruebas de proveedor, con texto sintético y sin datos personales:

- Consulta de metadatos del modelo configurado: HTTP 200; modelo models/gemini-3.8-flash; admite generateContent.
- Solicitud del adaptador con el límite configurado: ReadTimeout alrededor de 12,5 s.
- Misma solicitud con límite diagnóstico acotado a 45 s, sin cambiar archivos: ReadTimeout alrededor de 45,3 s.
- Solicitud reducida con JSON estructurado y el texto “Tengo dos bolsas de cartón y un balde de cáscaras de banano”: HTTP 503 UNAVAILABLE.

El catálogo, la clave y el modelo no explican por sí solos el fallo. La evidencia actual apunta a disponibilidad/latencia de generateContent; no permite atribuirlo a una cuota sin una respuesta 429. El respaldo local existente sigue siendo necesario. No aumenté el timeout persistente ni lo dejé ilimitado.

La generación requerida no está validada: Gemini no devolvió materiales ni cantidades en esta sesión.

## Meta y WhatsApp

La configuración local de Meta permanece en integrations/whatsapp/prototype/.env, ignorada por Git y con modo 0600. No se muestran sus valores en este reporte. El contenedor persistente ecoconecta-gemini-real-api-1 no tiene esas variables META en su entorno actual. Compose sí las resuelve desde el .env actual. Para las consultas Graph se utilizó un contenedor temporal de Compose, eliminado al finalizar; no se reinició la instancia activa.

Las dos consultas Graph de lectura respondieron HTTP 200. La asociación de una app con la WABA no equivale a una suscripción a mensajes. La respuesta de esa ruta no incluyó el campo subscribed_fields. El intento de debug_token devolvió Graph OAuth error code 190, por lo que el vencimiento sigue sin conocerse. No se hicieron cambios de permisos, suscripciones, número de prueba ni webhook.

La autorización de Meta cubre whatsapp_business_management y whatsapp_business_messaging para una cuenta de WhatsApp, según el consentimiento completado en la UI. La app continúa en modo de desarrollo. El prototipo no puede recibir webhooks porque solo escucha en loopback. No se enviaron mensajes.

## Auditoría de integración del proyecto

La inspección se hizo sobre la rama objetivo y las ramas remotas publicadas, sin modificar otras ramas:

- feat/whatsapp-chatbot contiene integrations/whatsapp/prototype con FastAPI, su panel, worker y migraciones aisladas. Su compose configura una PostgreSQL propia de demo. No se debe presentar esta base como la PostgreSQL unificada.
- El árbol de integración chore/add-project-documentation contiene apps/api, db/migrations y el módulo de visión. No contiene apps/web.
- La API FastAPI de feat/backend-core implementa autenticación, solicitudes, coordinación, asignación, programación, recolección y migraciones Alembic sobre el modelo compartido. En ese árbol no aparece el endpoint de WhatsApp que necesita el prototipo. Su infra/compose.yaml levanta PostgreSQL local; no hay Dockerfile de despliegue ni infraestructura cloud.
- feat/frontend sí contiene React, TypeScript y Vite. Su servicio de datos del dashboard sigue en demoService; seleccionar VITE_DATA_MODE=api lanza un error deliberado hasta acordar el adaptador. El README de esa rama también señala que los flujos operativos del dashboard no envían datos a la API. La integración pública de registro vive en feat/backend-public-registration y no forma parte del árbol web integrado.
- El árbol de integración actual no contiene apps/web. No hay un recorrido verificable desde WhatsApp hasta una bandeja web compartida.

El PR 13 integró una versión anterior del chatbot en chore/add-project-documentation desde el commit 35dd1d1. La rama feat/whatsapp-chatbot está ahora en bbd414c; no moví ni fusioné ramas. No existe una rama llamada main en el repositorio remoto: el default branch es chore/add-project-documentation. No se modificó ese default branch ni ninguna otra rama.

Para integrar solicitudes de WhatsApp sin persistencia duplicada, el paso de backend debe adaptar el evento normalizado del webhook al caso de uso de creación de solicitudes de apps/api y a users, pickup_requests, colectivos e historial existentes. No deben copiarse las tablas collection_requests del prototipo ni sus tokens de usuario.

## Servicios y pruebas locales

Contenedores observados:

- ecoconecta-gemini-real: API, worker y PostgreSQL de demostración; PostgreSQL healthy. API expuesta solo en 127.0.0.1:55074.
- ecoconecta-chatbot: otra instancia local en modo mock, expuesta en 127.0.0.1:8092.
- Ninguna de estas instancias es staging ni usa la PostgreSQL compartida del backend.

Verificación ejecutada en esta actualización:

- pytest con PostgreSQL temporal: 53 passed, dos advertencias (deprecación de Starlette/AnyIO y caché de pytest no escribible en /srv).
- Ruff: All checks passed usando caché temporal en /tmp.
- La base temporal ecoconecta_codex_20261120_test y el override de Compose fueron eliminados tras las pruebas.
- No ejecuté pruebas de apps/api o apps/web en este checkout: esos módulos no están presentes en la rama de trabajo. No ejecuté la generación sintética como prueba aprobada de Gemini; sus resultados reales se detallan arriba.

## Proveedor de hosting y presupuesto

No se encontró una plataforma cloud aprobada en las decisiones del proyecto. La conexión de Vercel solicitó reautenticación, así que no se pudieron consultar proyectos existentes. La cuenta conectada a AppDeploy no tenía apps; no la usé ni la considero aprobación para un proveedor nuevo.

Estimación orientativa en USD, consultada el 20 de noviembre de 2026; no son cotizaciones ni autorizaciones:

| Proveedor | Recursos considerados | Estimación publicada |
|---|---|---|
| Render | Sitio estático; API 512 MB; worker 512 MB; PostgreSQL gestionado 1 GB | Aproximadamente $33/mes antes de almacenamiento, transferencia adicional y uso de Gemini. El sitio estático no consume cómputo. |
| DigitalOcean App Platform | Sitio estático; API basic-xxs; worker basic-xxs; base de desarrollo PostgreSQL 512 MB | Aproximadamente $17/mes antes de transferencia; la base citada es de desarrollo. |
| Railway Hobby | Tres servicios always-on de unos 512 MB cada uno | Cerca de $15/mes de memoria a plena disponibilidad, más CPU, almacenamiento y transferencia; el total depende del uso. |

Fuentes oficiales: [planes y precios Render](https://render.com/docs/compute-plans), [ejemplo de precios Render](https://render.com/articles/production-rails-hosting-guide), [precios de App Platform y base de desarrollo de DigitalOcean](https://docs.digitalocean.com/products/app-platform/details/pricing/), [precios y consumo Railway](https://railway.com/pricing).

Recomendación técnica pendiente de aprobación: Render para el staging, con API, worker persistente, PostgreSQL gestionada única y frontend estático cuando el frontend consuma la API. Para dimensionar PostgreSQL en 1 GB y mantener un margen para almacenamiento/transferencia, propongo un tope de $45 USD al mes. El importe no incluye Gemini, dominio propio ni impuestos. No se creó ningún recurso. Los precios deben confirmarse antes de contratar.

## Bloqueos concretos para terminar el flujo

1. La rama autorizada no incluye apps/api ni apps/web integrados. La rama frontend es demo en operaciones y no está conectada a los contratos operativos; no incorporé código de otros agentes ni alteré ramas compartidas.
2. Meta todavía no tiene campos de webhook messages suscritos ni endpoint HTTPS público.
3. No se confirmó un destinatario de prueba autorizado.
4. Gemini devuelve timeout/503; hasta recibir una generación válida, el recorrido con Gemini real no está probado.
5. No hay proveedor cloud aprobado ni presupuesto de staging.

No se deben enviar datos personales a Gemini ni de residentes a una nube antes de aprobar el tratamiento. No se debe publicar la app Meta para atender a toda la comunidad. No se presentó el prototipo como plataforma completa.

## Próximas autorizaciones necesarias

- Aprobación del proveedor y presupuesto de staging antes de crear API, worker, PostgreSQL o endpoint HTTPS público.
- Después de aprobar el hosting y disponer del backend/frontend integrados, aprobación para configurar la URL y suscribir messages en Meta.
- Aprobación explícita de un mensaje de prueba real y destinatario autorizado antes del primer envío.
- Rotar el token temporal Meta por una credencial apropiada para el piloto; no reutilizarlo como secreto de producción.

Criterio final aún no alcanzado: recibir un mensaje desde un teléfono autorizado, responder por WhatsApp, guardar la solicitud en la PostgreSQL compartida y verla en el panel web operativo mediante HTTPS.


## Propuesta de PR

- Título: Actualiza evidencia de integración Meta, Gemini y staging.
- Rama origen: feat/whatsapp-chatbot.
- Rama destino: chore/add-project-documentation, el default branch actual; no hay rama main.
- Tipo: borrador, para revisar el informe de auditoría, la evidencia real de Meta/Gemini y los bloqueos de staging.
- No fusionar hasta aprobar proveedor/presupuesto, completar la integración con las bandejas compartidas y validar el recorrido real.

La publicación del commit en la rama origen sí se completó. El PR no se pudo crear desde esta sesión: GitHub MCP devolvió 403 Resource not accessible by integration y gh CLI no tiene una sesión autenticada. No se modificó la rama destino.

## 2026-11-21 — Ejecución nativa y accesos portables

La persona responsable no autorizó gastos. No se contrató alojamiento ni se
activó un servicio público. Solicitó que el panel pudiera ejecutarse fuera de
Docker y que sus accesos se pudieran conservar al subirlo a la web.

Estado: IMPLEMENTADO y comprobado localmente fuera de Docker; recorrido
conversacional PROBADO CON MOCK. No DESPLEGADO EN STAGING.

Cambios en el módulo de WhatsApp:

- `deploy/build.sh`, `deploy/start-web.sh`, `Procfile` y `.python-version`:
  construcción y ejecución nativas con Python 3.12, Node 24, puerto configurable,
  procesos separados API/worker y migración explícita.
- `app/access.py`: importar claves desde variables privadas del servidor,
  conservar únicamente hashes en la tabla existente, repetición idempotente y
  rotación explícita. No cambia roles ni reactiva cuentas deshabilitadas.
- `deploy/.env.example` y `deploy/README.md`: configuración sin valores secretos,
  ejecución por dominio HTTPS y conservación de cuentas. El fichero privado
  `.env.panel-access` contiene localmente las mismas claves entregadas al
  propietario; está ignorado por Git y tiene permisos 0600. Sus valores deben
  cargarse en el gestor de secretos del alojamiento.
- `.dockerignore`: excluir también `.local` del contexto de construcción.
- `tests/test_access.py`: autenticación, rechazo de claves inválidas,
  prohibición de escalada/reactivación, rotación, idempotencia y salida sanitizada.

Pruebas realizadas el 21 de noviembre de 2026 (America/Bogota):

- `npm ci --no-audit --no-fund` y `npm run build`: panel compilado correctamente.
- Python 3.12.16 y PostgreSQL 18.7 nativos: 61 pruebas pytest aprobadas, una
  advertencia de deprecación de Starlette/AnyIO. PostgreSQL temporal por socket
  privado, sin publicar puertos ni modificar las bases locales existentes.
- Ruff: todos los controles aprobados. Ambos scripts superaron `sh -n`.
- API real por HTTP en loopback, fuera de Docker: panel y JavaScript HTTP 200;
  las claves existentes de vecino/admin importadas en una base vacía dieron
  acceso. Clave inválida HTTP 401 y residente en ruta administrativa HTTP 403.
- Conversación sintética mediante proveedor mock: solicitud registrada,
  consultable por administración y conservada tras reiniciar la API. Las mismas
  claves siguieron autenticando tras el reinicio. Worker nativo activo durante
  la comprobación. API/worker temporales detenidos al finalizar.

Para reproducir: seguir `deploy/README.md`, utilizar PostgreSQL de pruebas,
configurar `TEST_DATABASE_URL` y ejecutar `python -m pytest -q`; crear datos de
demo e importar las claves con `python -m app.access` antes de comprobar el
panel y los permisos por HTTP. El procedimiento de rollback está en esa guía.

No hubo llamadas nuevas a Gemini ni Meta en esta fase. Sus bloqueos previos
continúan. El cambio permite desplegar el prototipo en un servidor adecuado;
no integra el frontend/backend compartidos ni autoriza aplicar estas migraciones
sobre la PostgreSQL definitiva. El servidor/proveedor sin gasto adicional aún
debe identificarse antes de publicar y validar HTTPS.
