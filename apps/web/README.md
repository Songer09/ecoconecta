# EcoConecta Web

Aplicación frontend demostrativa para Villas de San Pablo. Está construida con React, TypeScript, Vite y Tailwind CSS.

## Requisitos

- Node.js 20 o superior
- npm

## Ejecutar

```powershell
cd apps/web
npm install
npm run dev
```

`npm run dev` inicia Vite y abre la dirección local HTTP en el navegador (normalmente `http://localhost:5173`). No abras `index.html` directamente ni uses una dirección que empiece por `file:///`: el navegador bloqueará los módulos TypeScript por CORS. También puedes usar **Terminal → Run Task → EcoConecta: iniciar frontend** en VS Code.

Para generar el bundle:

```powershell
npm run build
```

## Modo de datos

La primera versión funciona en modo `demo`. Los datos de solicitudes están aislados en `src/services/demo/demoService.ts`, detrás del puerto tipado `EcoConectaService`. La selección de proveedor está centralizada en `src/services/service.ts`.

El recorrido de crear solicitud, asignar y programar, registrar la recolección y verificar el cierre comparte el estado en memoria mientras la aplicación está abierta. El avance educativo usa almacenamiento local del navegador para que la barra de progreso sobreviva a una recarga. Todo lleva la etiqueta **Modo demostración · datos ficticios**.

Las solicitudes y operaciones del dashboard aún usan el modo demo; no se envían solicitudes, imágenes ni direcciones a la API. Las fotos seleccionadas no se envían ni se guardan. El acceso al piloto usa los endpoints publicados en la rama de backend descritos abajo.

## Acceso al piloto y registro de cuentas

El frontend consume `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `POST /auth/logout`, `GET /zones`, `GET/POST /admin/users` y `POST /admin/staff`. Configura `VITE_API_BASE_URL` con la URL base del backend (por defecto `http://127.0.0.1:8000/api/v1`) y, en la API local, permite el origen del frontend mediante `FRONTEND_ORIGINS=http://127.0.0.1:5173`.

El registro público crea vecinos activos del piloto con nombre, teléfono internacional, contraseña de mínimo 12 caracteres, etapa, conjunto, torre y apartamento. El consentimiento es obligatorio y se guarda con el perfil en la misma transacción. Al terminar, la web inicia la sesión del vecino. La cuenta administradora inicial debe aprovisionarla el operador de despliegue por un procedimiento seguro; administración crea las cuentas operativas.

El endpoint de registro y su migración están en la rama `feat/backend-public-registration` hasta que se integren con el backend. Para utilizarlo, inicia esa API en `127.0.0.1:8000`, aplica `uv run alembic upgrade head` y mantén el frontend en `127.0.0.1:5173`. Si aparece “No se pudo conectar”, la API no está ejecutándose en la URL indicada; la web incluye el botón **Ver demostración** para consultar el dashboard mientras la API está apagada. Las solicitudes del dashboard siguen usando datos de demostración.

## Mapa

Las vistas de coordinación y de rutas muestran cartografía de OpenStreetMap centrada de forma aproximada en Villas de San Pablo (10.95885, -74.8631), Barranquilla. La atribución de OpenStreetMap se mantiene visible en el mapa. La capa se puede cambiar con `VITE_OSM_TILE_URL`.

Los registros de demostración no contienen coordenadas de solicitudes ni de recolectores, así que no se dibujan pines o recorridos ficticios. Se podrán mostrar cuando Backend publique coordenadas validadas en el contrato de solicitudes. El uso de `tile.openstreetmap.org` debe respetar la política de uso de teselas: carga interactiva bajo demanda, caché del navegador y sin precarga masiva.

## Límites de demostración

- Los nombres de recolectores son ficticios y solo ilustran la asignación local.
- El módulo no configura precios, puntos, materiales oficiales, cobertura ni disponibilidad real.
- El cierre muestra el momento en que correspondería aplicar una regla aprobada; no inventa ni acredita cantidades de puntos.
- El selector abre formularios de acceso por rol. El contrato API propone `POST /auth/login`, pero Backend aún no publica esquema ni servicio; por ahora el formulario informa que no se enviaron las credenciales y no concede una sesión.

## Mascota

Cris es una guía de la interfaz. Toca la oruga para ver la ayuda de la pantalla actual. El globo ofrece recorridos opcionales en Inicio, en el primer paso de Pedir recolección y en los dos paneles de coordinación. La tarjeta cambia de lado cuando el objetivo está cerca del borde inferior. La ayuda se pausa al interactuar con el globo y se oculta mientras escribes o tienes un modal abierto.

- Las siete imágenes transparentes están en `public/images/mascota/`. Para cambiar una pose, ajusta la ruta, el tamaño original y `face` en `src/components/mascot/mascotConfig.ts`. Los valores `x` e `y` indican el centro de la cara en porcentaje y `scale` amplía la imagen dentro del círculo de 64 a 84 px. La expresión `feliz` comparte la imagen de bienvenida.
- Edita los mensajes y los recorridos en `src/components/mascot/mascotMessages.ts`. Una pantalla puede informar de su escena mediante `useMascotScene`, y de un evento breve mediante `showMoment`. Los objetivos de los recorridos se identifican por `data-mascot-target`.
- Para revisar una pose sin sesión, usa el servidor de desarrollo y agrega `?mascota=triste&postura=mini&globo=1` a la URL. Acepta los nombres de expresión del archivo de configuración y las posturas `mini` y `completa`. `globo=1` abre un mensaje largo de prueba. En ventanas de menos de 560 px de alto se usa la postura mini. `?mascota=reset` borra únicamente los datos guardados por Cris. Usa `?mascota=recordatorio` para ver de inmediato el mensaje ocasional.
- La guía no hace peticiones a la API. Los eventos y el avance real de Educación siguen dependiendo del servicio existente.

- Los recordatorios respetan el tiempo en primer plano, las interacciones recientes y los estados de carga o error. El proveedor conserva el límite de tres por sesión de pestaña.

## Mapa de calles

`VITE_OSM_TILE_URL` permite configurar la capa de calles al compilar. Por defecto se usa la capa humanitaria de OSM France, con atribución visible a OpenStreetMap, HOT y OSM France. Si falla, se intenta la capa estándar de OpenStreetMap. Cada intento tiene un límite de ocho segundos si no carga ninguna tesela; si ambas capas fallan, se muestra un aviso con reintento y un enlace al mapa. No se descargan mapas por adelantado. El tamaño se recalcula al cambiar el espacio disponible mediante ResizeObserver.

El punto central indica el centro aproximado del barrio; no representa una solicitud ni seguimiento GPS. Las bandejas muestran las solicitudes reales del piloto, con su ámbito por rol.
