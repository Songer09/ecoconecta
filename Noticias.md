# Noticias de EcoConecta · entrega para continuar desde otro equipo

El repositorio es `Songer09/ecoconecta`. La rama principal de integración se llama `chore/add-project-documentation`. El desarrollo del servidor sigue en `feat/backend-core`. Al inicio de esta nota, la rama de integración estaba en `887e06e`, con las PR #1 a #12 pertinentes ya fusionadas, incluidas las de QA, visión y fotos de cámara.

## Qué está hecho

- **Base y acceso.** FastAPI y PostgreSQL compartido con migraciones Alembic hasta `0008_purchase_rates`. Autenticación, roles y zonas, altas de vecinos y personal del piloto, cobertura y disponibilidad.
- **Recolección.** Solicitud, revisión, asignación, agenda sin solapamientos, registro de pesos, cierre por coordinación, acreditación atómica y reprogramación con motivo. La huerta parte de 10 puntos/kg como regla configurable. Reciclaje usa tarifas configurables por material. Hay saldo, historial de puntos, canjes con control de existencias y reportes de pesos y valor de compra en COP.
- **Portal.** Catálogo y progreso educativo por perfil, editor administrativo, agenda de eventos y fichas públicas de Villas de San Pablo y la Fundación Santo Domingo. También hay registro de faltantes del huerto.
- **Rutas.** Coordinación puede ordenar paradas con una sugerencia basada en distancia en línea recta. El seguimiento es opcional y viene apagado. Solo coordinación de la zona y colectivo puede ver la última lectura. Detener el envío borra la posición y una lectura vence a los cinco minutos. QA-01 quedó corregido en la PR #11. Una parada fallida elimina su lectura en la misma transacción.
- **Imágenes.** La API de EcoConecta recibe la foto en `POST /api/v1/users/me/photo-recognition`, la prepara en memoria y consulta Compost-AI por HTTP. El resultado guía la clasificación y conserva la selección manual. Con la PR #12 el límite es 24 megapíxeles y 5 MiB en JPEG o PNG. Se corrige la orientación y se eliminan metadatos antes del envío.

## Qué quedó probado

Pasaron **17 pruebas del backend en PostgreSQL** con datos sintéticos, incluida la regresión de ubicación, canjes simultáneos y una foto sintética de 3120 × 4160 con orientación EXIF. El equipo de visión probó el flujo real en el Mac de Jeremy con una foto de cáscara de banano reducida. EcoConecta devolvió HTTP 200, `recognized`, `manual_review_required=false` y modelo `0.3.0-bdwaste-individual-experimental`. La prueba de la foto original con la PR #12 sigue pendiente. Fue una prueba con un caso, y la evaluación de precisión requiere más fotos representativas.

## Qué falta para la presentación

1. **Web.** La rama `feat/frontend` tiene autenticación y alta de cuentas conectadas. El formulario de foto sigue en modo demo. Conectar el formulario al endpoint real y mostrar la sugerencia para que el vecino pueda confirmarla o seguir con la selección manual.
2. **Servicio de visión.** El código de Compost-AI ya está integrado. Los pesos están en el Mac de Jeremy, fuera de Git, en `Compost-AI/artifacts/model_bdwaste_individual/`. Para la prueba integrada se usó Compost-AI en el puerto 8000 y EcoConecta en el 8091 con una base temporal. En Docker Desktop para Mac se configuró `COMPOST_AI_BASE_URL=http://host.docker.internal:8000` en el backend. El equipo que hará la demo necesita una instancia accesible con esos pesos. Ensayar también la foto original, el caso de revisión manual y la ausencia del servicio.
3. **WhatsApp.** `feat/whatsapp-chatbot` contiene la preparación de la integración. Queda conectar el servicio del compañero y probar recepción y programación, consentimiento y reintento de mensajes.
4. **Datos del piloto.** Preparar cuentas, zonas, horarios, materiales, tarifas y contenidos aprobados para el entorno de presentación. Una salida local de inspección de Docker mostró una credencial de PostgreSQL. Si esa salida se compartió con terceros, corresponde rotar la credencial y actualizar los servicios que dependan de ella. Para la presentación basta mostrar la aplicación o salidas redactadas.

## Cómo retomar en casa

Clona el repositorio o actualiza el clon de casa y abre esa carpeta en Codex. La nota está publicada en `feat/backend-core`. Para revisar primero los cambios y el estado del entorno:

```bash
git fetch origin
git switch feat/backend-core
git pull --ff-only
git status -sb
```

En un clon nuevo puedes usar `git clone --branch feat/backend-core https://github.com/Songer09/ecoconecta.git`. Para retomar la tarea en una sesión nueva, escribe «Lee AGENTS.md y Noticias.md, revisa las ramas remotas y continúa con el próximo pendiente del backend». La base local, la configuración del entorno, los pesos y las imágenes de referencia sin versionar requieren su propia copia autorizada. Para ejecutar el backend o las pruebas, sigue la [guía local](apps/api/README.md). Los [contratos de API](docs/API_CONTRACTS.md) y la [estrategia de QA](docs/QA_STRATEGY.md) contienen las interfaces y casos reproducibles.
