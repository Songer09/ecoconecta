# Backlog del backend a partir de las pantallas

Revisión de las 16 referencias de `Imagenes Frontend/`. La API ya cubre el acceso
al piloto, las bandejas básicas, la revisión, la asignación individual, la agenda
sin solapamientos y el registro de cantidades por material. Este anexo organiza
lo que falta y distingue los acuerdos actuales de las referencias de diseño.

## 1. Cierre y puntos · prioridad inmediata

- **Alta · Cierre y acreditación.** El recolector abre el registro de campo.
  El coordinador autorizado ingresa o corrige los pesos al verificarlos, y
  confirma el cierre. Quedan registrados el actor, la fecha y las cantidades.
  El servidor comprueba
  permisos, materiales, unidades y cantidades. Cada recolección realizada se
  cierra después de acreditar los puntos, en una única transacción de PostgreSQL.
  Reintentar la confirmación devuelve el resultado original. Si falla la
  acreditación, la misma recolección queda pendiente para reintento.
- **Alta · Configuración administrativa obligatoria.** La vista de administración
  tendrá API para consultar, publicar y reemplazar versiones de reglas con
  vigencia, validación y auditoría. Para reciclaje, sumar por material
  `kg × tarifa en puntos/kg del material`. Para huerta, partir de
  `kg × factor general del flujo orgánico` con un valor inicial de
  10 puntos/kg, editable por administración. Conservar decimales y registrar qué
  versión se aplicó. Los pesos se capturan en kg y cualquier conversión se define
  explícitamente. Preparar la configuración para que cada material habilitado
  tenga regla aplicable antes de operar. Si falta una regla en datos existentes,
  indicar al administrador cuál falta y permitir reintentar después de publicarla.
- **Media · Saldo e historial.** Exponer el saldo y los movimientos del vecino a
  partir del libro de puntos. El vecino solicitante es el beneficiario previsto
  en el modelo actual. Los saldos, bonos y ganancias del perfil de recolector
  requieren una regla propia antes de incorporarlos. La organización que recibe
  lo recolectado suministra la tabla de compra en COP/kg. Administración
  configura las tarifas en puntos/kg. Los reportes en COP y el saldo de puntos
  llevan sus propias unidades.
- **Temas para QA.** Ambos flujos con datos sintéticos, falta de reglas,
  permisos, cambios de versión, fallos dentro de la transacción y concurrencia
  al confirmar. Diferenciar el resultado `No se pudo` de una recolección
  realizada. Su reintento o reprogramación requiere una política explícita.

## 2. Operación y paneles

| Pantalla | Pendiente de backend | Complejidad |
| --- | --- | --- |
| Acceso y usuarios/roles | Alta y gestión del piloto, permisos y asignación de zonas. El servidor determina el rol desde la cuenta autenticada. | Media |
| Perfil del vecino | Edición de datos autorizados e historial de sus solicitudes, además de saldo y movimientos. | Media |
| Mapa de coordinador y ruta del recolector | Consultar paradas y asignar una ruta al recolector. En la última fase, sugerir un orden optimizado editable por el coordinador. | Alta |
| Disponibilidad del recolector | Leer y cambiar el estado operativo propio. Distinguirlo de las franjas de cobertura y del estado de las citas ya asignadas. | Media |
| Historial de coordinación | Filtros por período, estado y zona, con resúmenes autorizados. Definir reprogramación y motivo para `No se pudo`. | Media |
| Foto | Carga validada, acceso restringido e integración con visión como sugerencia de clasificación. Mantener selección manual. | Alta |
| Educación | Servir contenido publicado y definir su flujo editorial. | Baja–media |
| Eventos y administración | Crear, publicar y listar eventos. Los avisos por WhatsApp usan consentimiento y un trabajo coordinado con mensajería. | Media–alta |
| Canjes | Catálogo y stock, transacción para descontar puntos y existencias, historial y control de duplicados. Los valores de las imágenes son referencias de pantalla. | Alta |
| Inventario faltante del huerto | Gestionar insumos, cantidades y estado del faltante. Confirmar si se conecta al catálogo de canje. | Media |
| Ganancias y reportes | Agregados por período y ámbito. Las ganancias en COP requieren precios oficiales, beneficiarios y una definición de qué cuenta como ganado. | Media–alta |

## 3. Ubicación para coordinación · última fase

Cuando el flujo principal esté listo, implementar ubicación del recolector en
tiempo real durante la operación. El mapa irá al centro de la pantalla de
solicitudes y mostrará los recolectores del ámbito autorizado, con precisión y
hora de lectura. La sugerencia de ruta será opcional. El coordinador podrá
ajustar el orden o elegir otro antes de asignar las paradas. Definir el criterio
de optimización, el permiso de ubicación, la duración y la retención. Mostrar
`sin ubicación` o `desactualizada` cuando corresponda.

El recolector declara que realizó la parada. El coordinador puede contrastar
la ubicación respecto al punto de recolección y registrar su verificación.
GPS ofrece un indicio de presencia y puede fallar. El flujo de cierre conserva
una vía manual cuando el dispositivo carece de señal o permiso. Confirmar en
esta fase si se requiere confirmación humana adicional y cómo se registra.
