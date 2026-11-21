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

> **ACTUALIZACIÓN v3:** Este documento proviene de la versión 2. Si contradice `docs/DECISION_LOG.md`, `docs/FOUNDATION_BRIEF.md` o `docs/DESIGN_GUIDE.md`, prevalece v3. En particular, Twilio está permitido para prototipo, la IA tiene libertad de elección bajo controles de privacidad/seguridad y la aplicación usa una única PostgreSQL compartida.



## Seguimiento y reprogramación

Los casos nuevos viven en `apps/api/tests/test_route_qa.py`. Usan datos sintéticos
y un esquema desechable por módulo. Desde `apps/api`, configurar
`TEST_DATABASE_URL` para una base PostgreSQL terminada en `_test` y ejecutar
`uv run --no-sync pytest -q`. Para ejecutar la regresión QA-01,
ejecutar `uv run --no-sync pytest tests/test_route_qa.py -k reused`.

| Caso | Resultado esperado |
| --- | --- |
| Dos lecturas para el mismo recolector | Solo queda la más reciente. |
| Consulta de ubicación | Coordinación del colectivo y zona asignados puede consultar. Coordinación de otro ámbito recibe lista vacía y otros perfiles no tienen acceso. |
| Detener el envío | DELETE es repetible, solo borra la posición propia y la fila desaparece de PostgreSQL. |
| Cinco minutos sin lectura | La posición deja de estar disponible para verificación y el proceso de limpieza la elimina. |
| Parada fallida | Solo coordinación del ámbito registra un motivo válido. Dos intentos simultáneos producen una transición, desactivan la cita y conservan la asignación, sin recolección ni crédito. |
| Reprogramar una parada con posición reciente | La cita nueva requiere una lectura nueva. Regresión QA-01. |

### QA-01 · La posición reaparece después de reprogramar

Severidad alta para el piloto con seguimiento. Enviar una posición durante una
cita de hoy. Registrar la parada como fallida y, antes de cinco minutos,
programar otra fecha para la misma asignación. Consultar la ubicación desde
coordinación. Antes de la corrección, el mapa volvía a devolver las coordenadas antiguas. La posición
debería permanecer ausente hasta que el recolector vuelva a compartir en la
nueva cita. La API elimina la posición de la asignación al registrar la parada fallida en la misma transacción. QA-01 se ejecuta como prueba ordinaria.

## Pruebas de integración pendientes

- WhatsApp: firma válida e inválida, eventos repetidos, callbacks fuera de
  orden, número sin consentimiento y fallo temporal con reintento. Verificar
  que un mensaje no cambie asignaciones, estados ni puntos sin acción autorizada.
- Visión: respuesta válida, clase no reconocida, baja confianza, tiempo de
  espera agotado y respuesta malformada. La selección manual debe seguir
  disponible. Verificar que la sugerencia por sí sola no altera solicitudes
  ni puntos. Ejecutar con el contrato y artefactos que publique el equipo de visión.
