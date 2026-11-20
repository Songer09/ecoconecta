# Checklist de entrega entre agentes

## Codex Backend → Frontend
- [ ] URL base por entorno.
- [ ] OpenAPI actualizado.
- [ ] Autenticación y roles documentados.
- [ ] Ejemplos de request/response y errores.
- [ ] Paginación/filtros documentados.
- [ ] CORS y cookies/tokens definidos.
- [ ] Datos sintéticos disponibles.
- [ ] Cambios breaking comunicados.

## Codex Visión → Backend
- [ ] Model Card y evaluación reproducible.
- [ ] Clases y etiquetas acordadas.
- [ ] Esquema de entrada/salida versionado.
- [ ] Umbral y abstención definidos con evidencia.
- [ ] Dependencias/licencias revisadas.
- [ ] Tiempo de inferencia y recursos medidos.
- [ ] Fallback manual probado.
- [ ] No requiere acceso directo a PostgreSQL.

## Backend → QA
- [ ] Migraciones y fixtures.
- [ ] Contratos y reglas.
- [ ] Usuarios/roles de prueba.
- [ ] Escenarios negativos esperados.
- [ ] Instrucciones para levantar PostgreSQL y API.

## Frontend → QA
- [ ] Flujos por rol.
- [ ] Estados loading/error/empty.
- [ ] Datos mock identificados o sustituidos por API real.
- [ ] Instrucciones para levantar app.
- [ ] Selectores estables para E2E.

## Antes de demo
- [ ] Base PostgreSQL única.
- [ ] Sin secretos en repositorio.
- [ ] Twilio o Cloud API claramente identificado.
- [ ] Modelo y métricas de IA correctamente descritos.
- [ ] Datos de demostración sintéticos.
- [ ] Flujo orgánico y reciclable completo.
- [ ] Materiales/cantidades y puntos trazables.
- [ ] Pruebas ejecutadas y resultados registrados.
