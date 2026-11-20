# Diagnóstico y propuesta de integración del frontend

Fecha: 20 de noviembre de 2026

Rama revisada: `feat/frontend`

## Hallazgos del repositorio

- La rama `feat/frontend` existe en GitHub y el checkout local está en esa rama, sincronizado al iniciar la revisión.
- El repositorio actual es una base de documentación e infraestructura mínima. No contiene `apps/web`, `src`, páginas, componentes, estilos de aplicación, `package.json`, lockfile ni configuración de Vite/Tailwind.
- Los archivos de aplicación presentes se limitan a `infra/compose.yaml`, CI de GitHub y documentación/instrucciones de agentes. Por tanto, no hay pantallas o componentes frontend implementados que se puedan preservar o evaluar visualmente.
- `AGENTS.md` y `.opencode/agents/frontend.md` asignan el frontend a React + TypeScript + Vite + Tailwind, exigen inspeccionar antes de reemplazar, consumir contratos acordados y mantener los mocks tras una capa de servicios claramente identificada.
- Hay material de producto/diseño fuera del repositorio, en la carpeta compartida `Documentos EcoConecta\Contexto FrontEnd` y junto a ella: ontología, guía de diseño, reto, agenda, guía de la Fundación, logos e imágenes de Figma. Estos recursos no están incorporados a `feat/frontend`.

## Estado de contratos y límites

- `docs/API_CONTRACTS.md` se titula y declara borrador: paths y estados son propuestas pendientes de revisión; no hay OpenAPI publicado en el checkout.
- El handoff Backend → Frontend no está completado: faltan URL base, OpenAPI final, autenticación/roles, ejemplos de request/response y errores, filtros/paginación, CORS/sesiones y datos sintéticos.
- `docs/UNIFIED_DATA_MODEL.md` y `docs/DOMAIN_MODEL.md` definen conceptos, no DTOs HTTP definitivos. Los tipos de UI no deben usarse como sustitutos del contrato de API.
- Los valores de puntos, tarifas, unidades/catálogo, cobertura y reglas de reparto no están aprobados. La UI debe mostrar valores configurados/devueltos por el backend o indicar que no están definidos; no precargar valores de negocio ficticios.
- La guía externa de diseño indica la paleta visual solicitada y existen logos/capturas, pero el repositorio `docs/DESIGN_GUIDE.md` no incorpora esos tokens ni assets. Conviene trasladar al repositorio solo los recursos autorizados y mantener las proporciones/colores oficiales.

## Diagnóstico

No existe un frontend previo que la solicitud pueda reemplazar accidentalmente. El trabajo de interfaz aún no ha comenzado en esta rama. El riesgo principal es iniciar pantallas contra contratos que siguen siendo borradores y luego acoplar navegación, formularios y mocks a endpoints o reglas que Backend no haya confirmado.

También hay dos límites de producto que deben permanecer explícitos: los paneles de Vivi y Kelly comparten patrones visuales, pero tienen operaciones diferentes; y la selección rápida de rol para una demo no sustituye autenticación ni autorización server-side de una versión conectada.

## Propuesta de implementación

### 1. Base técnica mínima

Crear `apps/web` en React + TypeScript estricto + Vite + Tailwind, siguiendo las dependencias y CI que se acuerden. Separar `app` (rutas/sesión), `features` (solicitudes, recolecciones, puntos, huerto, reciclaje, administración), `shared/ui` (primitivas visuales) y `services` (puertos/adaptadores). No añadir librerías de estado o mapas antes de validar necesidad.

### 2. Contratos y servicios

- Cuando Backend publique OpenAPI, generar o validar tipos con ese documento y centralizar el cliente HTTP, URL base por entorno, errores tipados, expiración de sesión y serialización de fechas.
- Mantener las pantallas dependientes de interfaces de servicio por caso de uso, no de `fetch` disperso ni de fixtures.
- Alojar el adaptador simulado y sus datos sintéticos en una ruta separada (por ejemplo `services/adapters/mock`) e inyectarlo solo mediante configuración explícita de demo/desarrollo. La app debe indicar visualmente cuándo opera en modo simulado.
- No usar persistencia propia para simular la API, no duplicar reglas de asignación/estados/puntos y no conectar el navegador a PostgreSQL ni al modelo de visión.
- Hasta aprobarse el contrato, evitar afirmar que un tipo local es el contrato backend. Documentar la correspondencia pendiente en un registro de integración y cerrar cada elemento al recibir el OpenAPI.

### 3. Estructura de experiencia

- Acceso: selector de rol únicamente en el modo de demostración autorizado; conservar separado el flujo real de identidad y permisos.
- Vecino y recolector: navegación móvil enfocada en tareas, pasos de solicitud, seguimiento y asignaciones.
- Vivi: bandeja, asignaciones/rutas, materiales, pesajes e ingresos; no mostrar valores económicos oficiales sin configuración backend.
- Kelly: bandeja orgánica, disponibilidad/asignación, necesidades e inventario del huerto y canjes; sin módulo económico de reciclaje.
- Administrador: usuarios/roles, eventos, catálogo, parámetros de puntos y reportes según capacidades reales de API.
- Compartir componentes de presentación, pero mantener módulos, datos y permisos delimitados por rol. La navegación cliente es ergonomía, nunca control de acceso.

### 4. Orden sugerido

1. Recibir/confirmar OpenAPI inicial y decisiones de auth, errores, paginación y demo.
2. Crear la base visual y la estructura de rutas sin duplicar el backend.
3. Definir contratos de UI únicamente para presentación; conectar adaptadores tipados acordes al OpenAPI.
4. Implementar primero el recorrido solicitud → bandeja del colectivo → asignación/programación → registro → confirmación; luego ampliar puntos, eventos y administración.
5. Validar responsive y accesibilidad en móvil y tablet, y probar con QA los estados de carga, error y vacío y los permisos por rol.

## Dependencias para iniciar integración real

Backend debe entregar OpenAPI vigente, URL configurable, autenticación y selección de rol, payloads/errores, filtros y paginación, CORS/cookies, y fixtures sintéticos. Producto debe confirmar catálogo/unidades, campos de dirección, tratamiento de fotos, regla y momento de verificación de puntos, y alcance de la demo simplificada. Diseño debe confirmar qué logos/capturas se incorporan y distribuir tokens visuales dentro del repositorio.

## Resultado de esta revisión

Este cambio documenta el diagnóstico y la propuesta. No crea una app, endpoints, modelos de respuesta ni mocks, porque no hay frontend existente ni contrato HTTP acordado en la rama. No se ejecutaron pruebas: no hay código de aplicación que probar.
