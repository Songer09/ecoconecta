# Sistema parametrizable de puntos

## Principio
La Fundación no ha definido equivalencias ni valores oficiales. No incluir tasas, puntos por kilogramo ni premios inventados.

## Acuerdo de producto para implementar

- Reciclaje acredita la suma de los kilos por material multiplicados por su tarifa en puntos/kg.
- Huerta usa el peso total en kilos. Administración puede publicar el valor inicial de 10 puntos/kg o elegir otro.
- La configuración desde una vista administrativa y su API es obligatoria. Publicar reglas con
  vigencia y auditoría. El registro de cada acreditación conserva la versión aplicada.
- El cierre de toda recolección realizada confirma el crédito y el nuevo estado en la
  misma transacción. El coordinador autorizado verifica los pesos al confirmar. El servidor
  valida alcance, material, unidad y cantidad.
- La tabla de compra en COP/kg proviene de la organización que recibe lo recolectado.
  Administración publica las tarifas en puntos/kg. Los informes monetarios se expresan en COP.

## Configuración propuesta
Cada regla contiene:
- material_id
- unidad_base
- points_per_unit (NUMERIC)
- minimum_quantity (opcional, solo si lo aprueba la Fundación)
- maximum_points_per_collection (opcional, solo si lo aprueba)
- valid_from / valid_until
- version
- active
- created_by / approved_by

## Cálculo
1. El recolector abre el registro y puede adelantar el detalle de los materiales.
2. El coordinador autorizado ingresa los pesos verificados y confirma.
3. Backend determina la regla vigente para material y fecha.
4. Convierte cantidad a unidad base con conversión explícita y validada.
5. Calcula puntos en servidor.
6. Inserta movimiento en PointLedgerEntry dentro de la misma transacción que confirma el cierre.
7. La clave única de idempotencia evita doble acreditación.

## Auditoría
- No editar ni borrar movimientos históricos.
- Correcciones mediante movimiento compensatorio y motivo.
- Guardar regla/version exacta aplicada.
- Los cambios de regla solo afectan recolecciones futuras, salvo decisión formal y proceso de ajuste auditado.

## Pendiente de validación FSD
Materiales elegibles, unidades, equivalencias, topes, redondeo, tratamiento de contaminación/rechazo, validadores y aprobación de reglas.

> **ACTUALIZACIÓN v3:** Este documento proviene de la versión 2. Si contradice `AGENTS.md`, `docs/DECISION_LOG.md`, `docs/FOUNDATION_BRIEF.md` o `docs/DESIGN_GUIDE.md`, prevalece v3. En particular, Twilio está permitido para prototipo, la IA tiene libertad de elección bajo controles de privacidad/seguridad y la aplicación usa una única PostgreSQL compartida.

