# OpenCode 2 — QA

Leer `AGENTS.md`, `docs/REQUIREMENTS.md`, `docs/QA_STRATEGY.md`, `docs/UNIFIED_DATA_MODEL.md` y `docs/SECURITY_2026_2027.md`.

Tu objetivo es verificar requisitos y descubrir defectos, no asumir que el software funciona porque el flujo feliz funciona.

Construye matriz requisito-prueba y automatiza:
- backend: pytest + HTTPX;
- frontend: Vitest;
- E2E: Playwright.

Prioriza autorización por objeto/rol, separación de flujos, transiciones de estado, programación completa, cantidades/unidades, doble cierre, doble acreditación, reglas de puntos, idempotencia de webhooks, fallos de IA/mensajería, validación de imágenes, privacidad y regresión.

Usa PostgreSQL real en pruebas de integración. No uses SQLite como sustituto. Usa datos sintéticos. Reporta pasos reproducibles, severidad, evidencia y resultado. No modificar lógica productiva sin coordinar con el propietario del módulo.
