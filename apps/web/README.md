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

El frontend consume el backend de `feat/backend-core` para `POST /auth/login`, `GET /auth/me`, `POST /auth/logout`, `GET /zones`, `GET/POST /admin/users` y `POST /admin/staff`. Configura `VITE_API_BASE_URL` con la URL base del backend (por defecto `http://127.0.0.1:8000/api/v1`) y, en la API local, permite el origen del frontend mediante `FRONTEND_ORIGINS=http://127.0.0.1:5173`.

El login requiere teléfono internacional (`+` y de 7 a 15 dígitos) y contraseña. La API identifica el rol de la cuenta; el rol seleccionado en la pantalla debe coincidir. El token se mantiene solo en memoria y se elimina al cerrar sesión.

El backend no ofrece auto-registro público ni una ruta para crear el primer administrador. La cuenta administradora inicial debe aprovisionarla el operador de despliegue por un procedimiento seguro. Después, administración crea cuentas piloto desde Usuarios: residentes con nombre, teléfono y contraseña de mínimo 12 caracteres; personal operativo requiere también rol, flujo, una o más zonas activas y fecha de inicio. No inventar ni compartir credenciales en la interfaz; entregarlas al titular de forma segura. Las operaciones de solicitudes del frontend aún siguen en modo demo hasta contar con el adaptador de datos correspondiente.

## Mapa

Las vistas de coordinación y de rutas muestran cartografía de OpenStreetMap centrada de forma aproximada en Villas de San Pablo (10.95885, -74.8631), Barranquilla. La atribución de OpenStreetMap se mantiene visible en el mapa. La capa se puede cambiar con `VITE_OSM_TILE_URL`.

Los registros de demostración no contienen coordenadas de solicitudes ni de recolectores, así que no se dibujan pines o recorridos ficticios. Se podrán mostrar cuando Backend publique coordenadas validadas en el contrato de solicitudes. El uso de `tile.openstreetmap.org` debe respetar la política de uso de teselas: carga interactiva bajo demanda, caché del navegador y sin precarga masiva.

## Límites de demostración

- Los nombres de recolectores son ficticios y solo ilustran la asignación local.
- El módulo no configura precios, puntos, materiales oficiales, cobertura ni disponibilidad real.
- El cierre muestra el momento en que correspondería aplicar una regla aprobada; no inventa ni acredita cantidades de puntos.
- El selector abre formularios de acceso por rol. El contrato API propone `POST /auth/login`, pero Backend aún no publica esquema ni servicio; por ahora el formulario informa que no se enviaron las credenciales y no concede una sesión.
