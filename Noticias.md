# Noticias de EcoConecta

En `feat/backend-core` ya se puede consultar el catálogo educativo público y
marcar módulos como completados desde una sesión. El perfil devuelve el avance
sobre los módulos publicados. Frontend puede conectar el catálogo y el botón
«Marcar como completado» con los [contratos de la API](docs/API_CONTRACTS.md).

La migración 0004 está aplicada en PostgreSQL local. Pasaron las siete pruebas
del backend, incluidas las de progreso privado y finalizaciones simultáneas.
Quedan la carga de contenido, las pantallas y la integración con visión cuando
se publique la API del modelo.
