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

El mapa de acceso es un esquema original de sectores para orientar la navegación, no un mapa geográfico, no está a escala y no identifica calles, conjuntos ni puntos reales. Su botón abre el aprendizaje ambiental sin seleccionar un rol. No usa teselas de OpenStreetMap.

## Límites de demostración

- Los nombres de recolectores son ficticios y solo ilustran la asignación local.
- El módulo no configura precios, puntos, materiales oficiales, cobertura ni disponibilidad real.
- El cierre muestra el momento en que correspondería aplicar una regla aprobada; no inventa ni acredita cantidades de puntos.
- El selector de rol de demostración no autentica usuarios ni sustituye autorización en backend.
