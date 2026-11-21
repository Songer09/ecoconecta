# EcoConecta Web

Aplicación web de EcoConecta para Villas de San Pablo, construida con React, TypeScript, Vite y Tailwind CSS. Los recorridos sin sesión usan datos de demostración; las cuentas autenticadas consumen la API de EcoConecta.

## Requisitos

- Node.js 20.19 o superior (o 22.12 o superior)
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

## Conexión con el backend

Las pantallas de una cuenta autenticada usan `src/services/authApi.ts` y los componentes operativos para llamar a FastAPI. Esto incluye registro e inicio de sesión, solicitudes, consulta de catálogo y zonas, sugerencia de clasificación por imagen, asignación/programación, pesaje y confirmación, saldo y canjes, eventos, contenidos educativos, perfil, usuarios piloto y herramientas administrativas disponibles en la API.

El recorrido sin sesión se mantiene separado y claramente identificado como demostración. Sus solicitudes se guardan solo en memoria y no se envían a la API. El reconocimiento de imágenes solo se ejecuta para una sesión autenticada; la imagen original no se guarda desde el frontend.

En desarrollo, configura `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1` y `FRONTEND_ORIGINS=http://127.0.0.1:5173` en la API. En Netlify, `netlify.toml` configura `VITE_API_BASE_URL=/api/v1` y enruta ese prefijo al backend HTTPS de Railway para mantener las llamadas en el mismo origen.

## Acceso al piloto y registro de cuentas

El frontend consume `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `POST /auth/logout`, `GET /zones`, `GET/POST /admin/users` y `POST /admin/staff`. La API requiere migraciones aplicadas y PostgreSQL accesible.

El registro público crea vecinos activos del piloto con nombre, teléfono internacional, contraseña de mínimo 12 caracteres, etapa, conjunto, torre y apartamento. El consentimiento es obligatorio y se guarda con el perfil en la misma transacción. Al terminar, la web inicia la sesión del vecino. La cuenta administradora inicial debe aprovisionarla el operador de despliegue por un procedimiento seguro; administración crea las cuentas operativas.

El registro público crea vecinos activos del piloto con nombre, teléfono internacional, contraseña de mínimo 12 caracteres, etapa, conjunto, torre y apartamento. El consentimiento es obligatorio y se guarda con el perfil. Al terminar, la web inicia la sesión del vecino. `POST /auth/register` y la migración `0009_public_resident_registration` deben desplegarse junto con la API. La cuenta administradora inicial debe aprovisionarse de forma segura; administración crea las cuentas operativas.

## Alcance y límites actuales

- Las cuentas autenticadas crean y consultan solicitudes reales, consultan detalles, cancelan solicitudes recibidas/en revisión, realizan el flujo de revisión/asignación/programación, registran pesos por material y permiten confirmar el cierre desde coordinación. PostgreSQL mantiene el estado y aplica las reglas de puntos en el backend.
- La clasificación de fotos es orientativa; el usuario elige el flujo manualmente y Compost-AI puede no estar disponible.
- Educación, eventos publicados, perfil, puntos y canjes usan sus endpoints cuando están disponibles. Materiales, zonas, eventos, puntos y usuarios tienen controles administrativos conectados al backend.
- La vista de reportes de administración muestra conteos de cuentas por rol; no es todavía un informe operacional completo de recolecciones. El directorio operativo, el mapa comunitario y algunos contenidos de huerta siguen siendo informativos o dependen de datos validados.
- El prototipo de WhatsApp no se integra en este frontend. El webhook y el número piloto requieren configuración independiente en Meta/Railway.

Para compilar y desplegar la API en Railway desde la raíz del repositorio, usa `apps/api/Dockerfile`. Configura `DATABASE_URL`, `FRONTEND_ORIGINS` y las variables de visión según `apps/api/README.md`. No incluyas secretos en el frontend ni en Git.

## Mapa

Las vistas de coordinación y de rutas muestran cartografía de OpenStreetMap centrada de forma aproximada en Villas de San Pablo (10.95885, -74.8631), Barranquilla. La atribución de OpenStreetMap se mantiene visible en el mapa. La capa se puede cambiar con `VITE_OSM_TILE_URL`.

Los registros de demostración no contienen coordenadas de solicitudes ni de recolectores, así que no se dibujan pines o recorridos ficticios. Se podrán mostrar cuando Backend publique coordenadas validadas en el contrato de solicitudes. El uso de `tile.openstreetmap.org` debe respetar la política de uso de teselas: carga interactiva bajo demanda, caché del navegador y sin precarga masiva.

## Límites de demostración

- Los nombres de recolectores son ficticios y solo ilustran la asignación local.
- El módulo no configura precios, puntos, materiales oficiales, cobertura ni disponibilidad real.
- El cierre muestra el momento en que correspondería aplicar una regla aprobada; no inventa ni acredita cantidades de puntos.
- El selector abre formularios por rol. **Ver demostración** no crea una sesión ni altera los datos del piloto.

## Mascota

Cris es una guía de la interfaz. Toca la oruga para ver la ayuda de la pantalla actual. El globo ofrece recorridos opcionales en Inicio, en el primer paso de Pedir recolección y en los dos paneles de coordinación. La tarjeta cambia de lado cuando el objetivo está cerca del borde inferior. La ayuda se pausa al interactuar con el globo y se oculta mientras escribes o tienes un modal abierto.

- Las siete imágenes transparentes están en `public/images/mascota/`. Para cambiar una pose, ajusta la ruta, el tamaño original y `face` en `src/components/mascot/mascotConfig.ts`. Los valores `x` e `y` indican el centro de la cara en porcentaje y `scale` amplía la imagen dentro del círculo de 64 a 84 px. La expresión `feliz` comparte la imagen de bienvenida.
- Edita los mensajes y los recorridos en `src/components/mascot/mascotMessages.ts`. Una pantalla puede informar de su escena mediante `useMascotScene`, y de un evento breve mediante `showMoment`. Los objetivos de los recorridos se identifican por `data-mascot-target`.
- Para revisar una pose sin sesión, usa el servidor de desarrollo y agrega `?mascota=triste&postura=mini&globo=1` a la URL. Acepta los nombres de expresión del archivo de configuración y las posturas `mini` y `completa`. `globo=1` abre un mensaje largo de prueba. En ventanas de menos de 560 px de alto se usa la postura mini. `?mascota=reset` borra únicamente los datos guardados por Cris. Usa `?mascota=recordatorio` para ver de inmediato el mensaje ocasional.
- La guía de la mascota no realiza peticiones a la API. El avance de Educación se guarda mediante el servicio backend.

- Los recordatorios respetan el tiempo en primer plano, las interacciones recientes y los estados de carga o error. El proveedor conserva el límite de tres por sesión de pestaña.
