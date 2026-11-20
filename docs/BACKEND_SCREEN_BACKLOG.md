# Estado de las funciones del backend

El contrato de FastAPI está en [OpenAPI](../apps/api/openapi.json). El equipo de frontend puede usar datos sintéticos para conectar las pantallas. La integración de servicios y la carga de datos del piloto se verifican por separado.

| Pantalla | Función disponible | Trabajo de integración o decisión pendiente |
| --- | --- | --- |
| Acceso | Alta de vecinos y personal operativo, gestión de acceso, colectivos, zonas de coordinación, cobertura y franjas de recolección. | Cargar personal, zonas y horarios validados. |
| Perfil del vecino | Perfil editable, solicitudes propias, saldo, movimientos, historial de canjes y progreso educativo. | Conectar las vistas. |
| Solicitudes | Recepción, revisión por ámbito, asignación, agenda, cancelación temprana y reprogramación tras una parada fallida. | Validar el procedimiento para incidencias después de abrir un registro de campo. |
| Cierre | El coordinador verifica pesos y acredita antes de cerrar. Las reglas en puntos/kg quedan versionadas. | Cargar los valores aprobados por administración. |
| Huerta y canjes | Inventario de faltantes por zona y catálogo con precio y existencias. Los canjes registran el débito y reducen stock en una transacción. | Cargar insumos y premios reales. |
| Reportes | Conteos por flujo y estado, pesos confirmados por material, recolector y zona, valor de compra estimado por colectivo. | La organización receptora proporciona sus tarifas COP/kg. El reparto de ingresos personales requiere reglas. |
| Rutas | Consulta por día y zona, sugerencia por distancia, orden editable, disponibilidad operativa y posición reciente opcional. | Conectar el mapa y validar consentimiento, precisión y retención antes del uso con personas reales. |
| Fotos | Recepción privada, validación y normalización temporal de JPEG/PNG. Selección manual de flujo disponible. | Conectar el formulario web y configurar el servicio y los pesos en el entorno del piloto. El equipo de visión completó una prueba local del modelo real por HTTP. |
| Portal comunitario | Educación, progreso, fichas institucionales, eventos y horarios vigentes. | Conectar pantallas y publicar contenidos aprobados. |
| WhatsApp | Los datos de recepción, asignación y programación existen en el backend. | Conectar y validar el servicio de mensajería, sus permisos, consentimiento y reintentos. |
