# Requisitos de EcoConecta

## 1. Procedencia
- **OFICIAL:** transcripción del Reto Oficial EcoConecta Villas de San Pablo proporcionada por el equipo el 20-11-2026.
- **ADICIONAL-FUNDACIÓN:** información operativa comunicada verbalmente al equipo y atribuida a la Fundación; pendiente de validación documental.
- **DECISIÓN-EQUIPO:** elección de implementación recomendada por el equipo.

No convertir un requisito adicional en cita textual del reto oficial.

## 2. Objetivo oficial
Plataforma digital para conectar comunidad, huerteros y recicladores en la gestión comunitaria de residuos y economía circular. Debe facilitar información ambiental, solicitudes, enrutamiento, programación, registro de recolección y reconocimiento mediante puntos.

## 3. Actores oficiales
- Hogares / comunidad.
- Unidades productivas.
- Coordinador de huerteros.
- Huertero.
- Coordinador de recicladores.
- Reciclador.
- Administrador.

## 4. Requisitos funcionales oficiales
### RF-01 Acceso y perfiles
Diferenciar solicitante, coordinador de huerteros, coordinador de recicladores, recolector y administrador. Aplicar mínimo privilegio.

### RF-02 Educación ambiental
Publicar contenidos sobre separación, gestión, buenas prácticas, huerta, horarios y rutas; consulta sencilla desde móvil/tableta.

### RF-03 Solicitud
Capturar contacto, ubicación/dirección, tipo de generador, tipo de residuo/flujo, observaciones y disponibilidad/preferencia horaria. Generar ID y estado.

### RF-04 Enrutamiento
Orgánicos → coordinador de huerteros. Reciclables → coordinador de recicladores.

### RF-05 Gestión y programación
Coordinador revisa y asigna a una persona. Registrar día, hora y persona encargada. Una solicitud no está programada si falta alguno de estos datos.

### RF-06 Trazabilidad
Estados de referencia: recibida, en revisión, programada, asignada, recolectada o cancelada. Conservar historial.

### RF-07 Cierre
El responsable registra que la recolección fue realizada. Asociar cierre con solicitud y usuario.

### RF-08 Puntos
Asignar puntos después de la recolección con regla parametrizable y documentada. La Fundación no ha definido equivalencias ni valores oficiales.

### RF-09 Comunicación
Integrar WhatsApp Business Cloud API para apoyar confirmación de recepción y comunicación de programación (día, hora, persona encargada).

### RF-10 Panel operativo
Bandejas de solicitudes pendientes, asignadas, programadas y atendidas; historial y resumen por flujo, estado y periodo.

### RF-11 Piloto
Permitir configurar usuarios piloto; no asumir que toda la comunidad está habilitada.

## 5. Criterios oficiales RN
- RN-01 Separación de flujos.
- RN-02 Programación requiere día, hora y persona.
- RN-03 Asignación asociada a coordinador y recolector.
- RN-04 ID, estado e historial.
- RN-05 Puntos solo después de recolección.
- RN-06 Cálculo explicable y parametrizable.
- RN-07 Contacto y ubicación solo visibles a perfiles que los necesitan.
- RN-08 Configuración de usuarios piloto.

## 6. Requisitos adicionales comunicados
### AD-01 Los 15 recicladores
El equipo recibió la indicación de que existen 15 recicladores distribuidos por zonas, días y horarios. La distribución es por **zonas, no por etapas**. El sistema debe permitir registrar cada reciclador, su zona/cobertura y su disponibilidad. Los 15 perfiles exactos y sus asignaciones deben cargarse solo con información validada.

### AD-02 Selección de zona/día/hora
Se mencionó la idea de preguntar zona, día y hora durante el acceso. Recomendación: no usar esos datos como credenciales. Autenticar por identidad y rol; después permitir consultar/seleccionar zona y disponibilidad como contexto operativo o filtro de agenda. Validar este flujo con la Fundación.

### AD-03 Registro por reciclador
Registrar por cada recolección: reciclador, solicitud, fecha/hora, zona, materiales, cantidades, unidad de medida y responsable que confirmó el cierre. El panel debe permitir consultar totales por reciclador, material, zona y periodo.

### AD-04 Configuración de puntos
Permitir configurar reglas por material/unidad y vigencia. No precargar puntos oficiales inventados. Mantener historial de versiones y libro de movimientos.

### AD-05 Identidad visual
Se informó que hay identidad visual, reto oficial y logotipos variados. Los archivos y lineamientos no se han recibido en esta conversación. No inventar colores, logos ni tipografías. Usar placeholders hasta recibir los assets oficiales.

## 7. Requisitos no funcionales / calidad
- Mobile-first, responsive y accesible.
- Seguridad por rol y por registro.
- Minimización de datos personales.
- Auditoría de operaciones críticas.
- Idempotencia para cierres, puntos y webhooks.
- Validación de entradas.
- Copias de seguridad y configuración segura.
- Rendimiento adecuado para el piloto; no asumir escalas no especificadas.
- Despliegue cloud y URL accesible durante evaluación.

## 8. Escenario de demostración obligatorio
1. Usuario de unidad productiva crea solicitud orgánica.
2. Coordinador de huerteros revisa y asigna huertero.
3. Registra y comunica día, hora y responsable.
4. Huertero registra recolección; estado y puntos se actualizan.
5. Segundo usuario crea solicitud reciclable y se enruta al coordinador de recicladores.

## 9. Entregables
- MVP desplegado.
- Repositorio GitHub accesible a jurados.
- README con ejecución Docker, URL, infraestructura y nombres de variables sin valores.
- Diagrama de arquitectura.
- Modelo de datos PostgreSQL.
- Demostración end-to-end.
- Sustentación con problema, usuarios, solución, decisiones, impacto y limitaciones.

## 10. Fuera de alcance hasta validación
- Tarifas, equivalencias de puntos o premios oficiales.
- Rutas GPS en tiempo real.
- Optimización automática de rutas.
- Chatbot IA autónomo que asigne o cierre solicitudes.
- Registro masivo de toda la comunidad.
- Cualquier integración no incluida en tecnologías permitidas.

> **ACTUALIZACIÓN v3:** Este documento proviene de la versión 2. Si contradice `docs/DECISION_LOG.md`, `docs/FOUNDATION_BRIEF.md` o `docs/DESIGN_GUIDE.md`, prevalece v3. En particular, Twilio está permitido para prototipo, la IA tiene libertad de elección bajo controles de privacidad/seguridad y la aplicación usa una única PostgreSQL compartida.


## Aclaraciones posteriores comunicadas por el equipo (v3)

- Twilio permitido para prototipo; WhatsApp Business Cloud API definitiva.
- Libertad para elegir IA/reconocimiento, sujeta a seguridad, privacidad, presupuesto y aprobación de tratamiento de datos.
- Modelo de reconocimiento existente con métricas reportadas altas especialmente en no orgánicos; pendiente auditoría reproducible.
- Aproximadamente 15 recicladores organizados por zonas, días y horarios; cobertura individual pendiente de confirmación.
- Registrar materiales y cantidades por evento de recolección.
- Ver `docs/FOUNDATION_BRIEF.md` para procedencia y pendientes.
