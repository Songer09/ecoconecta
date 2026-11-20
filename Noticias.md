# Noticias de EcoConecta

En `feat/backend-core` quedó corregido QA-01. Registrar una parada fallida elimina su posición reciente antes de reprogramarla. Pasaron las 17 pruebas en PostgreSQL, incluida la regresión de QA.

El backend puede consultar Compost-AI mediante `COMPOST_AI_BASE_URL`. Se verificó el contrato HTTP con un servicio simulado. Visión debe proporcionar los artefactos entrenados o una instancia accesible para verificar la inferencia real. [Revisión de visión](https://github.com/Songer09/ecoconecta/pull/10)
