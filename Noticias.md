# Noticias de EcoConecta

**Backend · Registro de materiales · Rama `feat/backend-core` · [Pull request #3](https://github.com/Songer09/ecoconecta/pull/3)**

El recolector asignado ya puede abrir una recolección programada, registrar cantidades
por material y volver a consultar lo guardado. Si el envío se repite, se conserva un
solo registro. La solicitud continúa programada hasta la confirmación del cierre.

**Frontend.** Mostrar las asignaciones con `GET /api/v1/collector/requests` y tomar
las unidades del catálogo filtrado por flujo. Al reabrir la pantalla, recuperar la
recolección por ID de solicitud. La PR incluye también la bandeja del coordinador,
asignación y agenda. [Guía de llamadas](apps/api/README.md#registro-de-materiales-por-el-recolector) · [Contrato OpenAPI](apps/api/openapi.json)

**QA.** Pasaron seis pruebas de integración locales en PostgreSQL, incluidas la
apertura simultánea de un registro, la repetición del mismo material, el control de
acceso por asignación y el rechazo de materiales inactivos o de otro flujo.

**Siguiente decisión.** Para cerrar y acreditar puntos, el equipo debe definir
quién verifica las cantidades y qué ocurre si un material carece de regla aprobada.
