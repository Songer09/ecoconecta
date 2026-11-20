# Instrucciones — Codex 2: Reconocimiento de imágenes

Leer primero `AGENTS.md`, `docs/00_START_HERE.md`, `docs/FOUNDATION_BRIEF.md`, `docs/AI_VISION_INTEGRATION.md` y `docs/SECURITY_2026_2027.md`.

Tu responsabilidad es el módulo de reconocimiento de residuos ya existente. No rehagas el modelo sin demostrar que el actual no cumple.

Primera fase:
1. Inspeccionar código, notebooks, pesos, dependencias y datasets disponibles.
2. Reproducir el resultado reportado por el equipo.
3. Documentar clases, dataset, splits y licencias.
4. Calcular métricas por clase y matriz de confusión; no reportar solo accuracy.
5. Evaluar especialmente residuos orgánicos, porque el resultado reportado es mejor para no orgánicos.
6. Medir latencia, recursos, tamaño, coste y limitaciones.
7. Crear `docs/VISION_MODEL_CARD.md`.

Segunda fase:
1. Definir interfaz de inferencia estable.
2. Empaquetar para el entorno de ejecución acordado.
3. Añadir validación segura de imágenes y pruebas de entradas malformadas.
4. Implementar abstención/revisión humana ante baja confianza o clase desconocida.
5. Coordinar integración con Codex Backend.
6. Entregar instrucciones reproducibles y variables de entorno necesarias.

No conectar directamente a PostgreSQL. No escribir estados, asignaciones ni puntos. No exponer claves en frontend. No enviar imágenes a un proveedor externo sin aprobación explícita. No afirmar precisión sin evidencia reproducible.
