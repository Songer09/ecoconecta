# Ejecución web sin Docker

Este módulo FastAPI y su panel pueden ejecutarse con Python y Node, sin Docker.
GitHub almacena el código y las plantillas; el servidor ejecuta API y worker.
GitHub Pages o un alojamiento de archivos estáticos no ejecutan este backend.

El alcance sigue siendo el prototipo: no es el frontend completo ni el backend
unificado de EcoConecta. Sus migraciones solo se aplican en una PostgreSQL de
pruebas vacía. No ejecutarlas sobre la base compartida del producto. La integración
del modelo y de la identidad definitiva requiere revisión del equipo de backend.

## Construir y arrancar

Directorio raíz del servicio: `integrations/whatsapp/prototype` en la rama
`feat/whatsapp-chatbot`. Requisitos: Python 3.12, Node 24 y PostgreSQL accesible
desde el servidor. La base no debe exponer su puerto públicamente.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
sh deploy/build.sh
```

Configurar las variables de `deploy/.env.example` en el gestor de secretos del
alojamiento. API, worker y las tareas de migración/acceso usan el mismo
`DATABASE_URL`. La API no crea una base de datos ni inicia Docker.

Para probar en una base vacía de demo, ejecutar una vez:

```sh
python -m alembic upgrade head
# Solo datos sintéticos de demo. Guardar la salida fuera de logs públicos.
mkdir -p .local
chmod 700 .local
umask 077
python -m app.seed demo > .local/bootstrap-access.txt
```

Configurar dos procesos persistentes, con reinicio por el supervisor del servidor:

| Proceso | Comando |
| --- | --- |
| API y panel | `sh deploy/start-web.sh` |
| Worker | `python -m app.worker` |

El `Procfile` describe esos procesos y la tarea de migración para plataformas que
lo soporten. No implica un despliegue automático ni crea recursos.
La construcción necesita Node; los procesos de ejecución solo necesitan Python
y las dependencias instaladas.

El script web acepta `PORT` del alojamiento. Por defecto escucha en
`127.0.0.1:8000`. En el servidor, configurar `HOST=0.0.0.0` si su red privada o
proxy lo requiere. Publicar mediante HTTPS en la raíz del dominio:
`https://DOMINIO/panel`, con `/health` como comprobación del servicio y las rutas
`/api/v1/` accesibles en el mismo origen. Configurar `FORWARDED_ALLOW_IPS` solo
con las IP del proxy de confianza; no confiar en todas las IP por defecto.

## Conservar las mismas claves al desplegar

Las claves del panel son tokens aleatorios personales. El servidor conserva su
hash en la tabla existente `users`; no necesita el valor en el código ni en Git.
Conservar la misma PostgreSQL conserva las cuentas y conversaciones. Si la base
de demo es nueva, importar las claves mediante variables privadas del servidor:

```sh
python -m app.access --handle acceso-vecino-demo --role resident --token-env PANEL_RESIDENT_TOKEN
python -m app.access --handle acceso-admin-demo --role admin --token-env PANEL_ADMIN_TOKEN
```

El usuario recibe las claves por un canal privado y las pega en el panel.
Las variables tienen exactamente los mismos valores que las claves ya entregadas
para el Mac, si se desea mantener esos accesos. El fichero privado
`.env.panel-access` preparado localmente contiene los nombres y valores para
copiarlos al gestor de secretos, nunca al repositorio ni al código del navegador.
Para sesiones locales, cargarlo únicamente en la terminal privada del operador:

```sh
set -a
. ./.env.panel-access
set +a
```

Volver a ejecutar el comando con la misma cuenta/clave es idempotente. Si existe
otra clave, el comando falla; `--replace-token` la rota explícitamente y revoca
la anterior. No modifica roles, flujos ni reactiva cuentas. La salida no incluye
claves. Para coordinadores/recolectores se requiere `--flow organic` o
`--flow recyclable`. Usar tokens distintos para cuentas distintas.

## Gemini, Meta y publicación

`AI_PROVIDER=mock` y `WHATSAPP_PROVIDER=mock` mantienen una demo local sin llamadas
externas. Para Gemini, configurar su clave en el gestor de secretos y seleccionar
`AI_PROVIDER=gemini`; esto no demuestra una generación válida. No utilizar la
clave del panel como credencial de Gemini, Meta o de acceso al repositorio GitHub.

Meta requiere un entorno `pilot`, credenciales propias y webhook HTTPS verificado;
seguir el README principal y las aprobaciones de privacidad y envío. Los accesos
de demo no habilitan por sí mismos WhatsApp real.

No se ha contratado ni activado alojamiento. Quedan pendientes la elección de un
servidor aprobado sin gasto adicional, HTTPS, permisos y comprobaciones externas.
Antes de admitir datos reales deben integrarse la identidad y la PostgreSQL del
backend compartido. La importación de claves no sustituye esa integración.

## Comprobaciones y rollback

Comprobar `/health`, cargar `/panel` y sus recursos, verificar `/api/v1/me` con
cada clave, y comprobar que el residente recibe 403 en las rutas administrativas.
Verificar el worker y el recorrido de solicitudes antes de declarar un despliegue
funcional. No guardar encabezados de autenticación en logs ni capturas.

Para revertir código, reconstruir el commit anterior y reiniciar API/worker.
No borrar la base ni ejecutar downgrade de migraciones automáticamente. Si se
cambió una clave, restaurarla solo mediante una rotación explícita o generar otra
y entregarla por un canal privado. Hacer copia de PostgreSQL antes de migrar.

Referencia de configuración de proceso y proxy: [Uvicorn](https://uvicorn.dev/settings/).
