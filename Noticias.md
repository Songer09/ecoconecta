# Noticias de EcoConecta

En `feat/fullstack-integration` se reunió el sitio de la copia de entrega con
el alta pública de vecinos y el Dockerfile de la API. El formulario web envía
los identificadores de materiales seleccionados; la API valida el flujo, los
guarda en `request_items` y los devuelve en el detalle de la solicitud.

Las cuentas autenticadas usan los endpoints de solicitudes, operaciones,
reconocimiento, educación, eventos, puntos y administración disponibles. Se
añadió cancelación con motivo para solicitudes recibidas/en revisión y el
registro de varios materiales por recolección. La demostración sin sesión
continúa separada.

Verificado: `npm run build` y construcción de `apps/api/Dockerfile` desde la
raíz del repositorio. No se ejecutaron pruebas automatizadas ni se publicó esta
rama. WhatsApp sigue siendo una integración independiente, pendiente de
configuración del número piloto y del webhook en Meta/Railway. Los informes
administrativos y el directorio operativo aún tienen alcance informativo.
