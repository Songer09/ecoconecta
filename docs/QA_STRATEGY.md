# Estrategia QA

## Herramientas
- Backend: pytest + HTTPX / FastAPI TestClient.
- Frontend: Vitest + Testing Library.
- E2E: Playwright.
- Lint/typecheck: Ruff/mypy o pyright según selección; ESLint/tsc.
Supertest se diseñó para Node/Express y no es la herramienta adecuada para FastAPI.

## Pruebas críticas
1. Orgánico se enruta solo a huerteros.
2. Reciclable se enruta solo a recicladores.
3. Programar sin día/hora/recolector debe fallar.
4. Recolector no accede a solicitudes ajenas/no asignadas.
5. Coordinador no modifica el colectivo contrario.
6. Estado conserva historial.
7. Cierre requiere rol y asignación autorizados.
8. Doble envío de cierre no duplica colección ni puntos.
9. Cambio de regla no altera ledger histórico.
10. Cantidades negativas/cero/unidades incompatibles se rechazan.
11. Webhook repetido no genera duplicados.
12. Datos de contacto/dirección no aparecen en listados públicos.
13. Piloto bloquea usuarios no habilitados cuando corresponda.
14. WhatsApp falla con manejo visible y reintento seguro.
15. Flujos responsive en móvil/tableta.

## Criterios de PR
- Tests pertinentes pasan.
- No se reduce cobertura o se desactiva una prueba para ocultar un fallo.
- QA reporta pasos de reproducción, esperado/actual, severidad y evidencia.
- QA no modifica lógica productiva para hacer pasar sus pruebas.

> **ACTUALIZACIÓN v3:** Este documento proviene de la versión 2. Si contradice `AGENTS.md`, `docs/DECISION_LOG.md`, `docs/FOUNDATION_BRIEF.md` o `docs/DESIGN_GUIDE.md`, prevalece v3. En particular, Twilio está permitido para prototipo, la IA tiene libertad de elección bajo controles de privacidad/seguridad y la aplicación usa una única PostgreSQL compartida.

