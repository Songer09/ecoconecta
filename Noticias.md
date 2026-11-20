# Noticias de EcoConecta

**20 de noviembre de 2026 · Backend · `feat/backend-core`**

El coordinador ya puede llevar una solicitud desde **recibida → en revisión → asignada → programada**.
El solicitante puede volver al detalle para ver el nombre del recolector y la hora acordada.

**Para frontend.** En la bandeja del coordinador, abrir la revisión, mostrar las franjas
por recolector y enviar la asignación y la cita. La cita necesita inicio y fin con zona
horaria. Si dos personas reservan al mismo recolector para horas que se cruzan, la API
devuelve `409 schedule_overlap` a la segunda. Mantener el formulario abierto para elegir
otro horario. [Secuencia de llamadas](apps/api/README.md#revisión-asignación-y-programación) · [Contrato OpenAPI](apps/api/openapi.json)

**Verificado.** Pasaron cinco pruebas de integración en PostgreSQL, incluida una reserva
simultánea y otra contigua. La entrega usa las tablas existentes.

**Pendiente.** Registrar los materiales recolectados y cerrar la recolección. Para
acreditar puntos hace falta acordar quién confirma el cierre y qué hacer cuando
todavía no hay una regla aprobada.
