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

No hay adaptador API activo: `docs/API_CONTRACTS.md` sigue siendo borrador. Cuando Backend publique OpenAPI y el handoff, se podrá añadir el adaptador real sin cambiar las pantallas. El modo demo no envía solicitudes, imágenes o direcciones a un servidor. Las fotos seleccionadas no se envían ni se guardan.

## Mapa

Las vistas de coordinación y de rutas muestran cartografía de OpenStreetMap centrada de forma aproximada en Villas de San Pablo (10.95885, -74.8631), Barranquilla. La atribución de OpenStreetMap se mantiene visible en el mapa. La capa se puede cambiar con `VITE_OSM_TILE_URL`.

Los registros de demostración no contienen coordenadas de solicitudes ni de recolectores, así que no se dibujan pines o recorridos ficticios. Se podrán mostrar cuando Backend publique coordenadas validadas en el contrato de solicitudes. El uso de `tile.openstreetmap.org` debe respetar la política de uso de teselas: carga interactiva bajo demanda, caché del navegador y sin precarga masiva.

## Límites de demostración

- Los nombres de recolectores son ficticios y solo ilustran la asignación local.
- El módulo no configura precios, puntos, materiales oficiales, cobertura ni disponibilidad real.
- El cierre muestra el momento en que correspondería aplicar una regla aprobada; no inventa ni acredita cantidades de puntos.
- El selector abre formularios de acceso por rol. El contrato API propone `POST /auth/login`, pero Backend aún no publica esquema ni servicio; por ahora el formulario informa que no se enviaron las credenciales y no concede una sesión.
