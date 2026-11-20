# Esquema inicial y coordinación

La definición revisada está en `schema.sql`; reemplaza el antiguo `bdd.txt.txt`
sin perder su contenido revisado. Es SQL para una base vacía, no una migración.
No ejecutarlo sobre tablas existentes. Alembic será la única fuente
de migraciones cuando se inicialice backend; no mantener dos esquemas divergentes.

## Revisión realizada

Se conservan los nombres del diseño entregado. Correspondencia con los nombres
conceptuales de `docs/UNIFIED_DATA_MODEL.md`:

| Concepto documental | Tabla del SQL |
|---|---|
| collection_requests | pickup_requests |
| assignments / schedules | request_assignments / request_schedules |
| collection_events / collected_materials | collections / collection_items |
| materials | waste_types |
| collector_profiles | collective_members con member_role=recolector |
| notifications / audit_events | whatsapp_messages / audit_log |

No crear tablas alternativas con el mismo propósito. El flujo del recolector se
deriva del colectivo y su cobertura de `collector_zone_coverage` + `zones`.

Correcciones: cobertura y franjas estructuradas, coherencia solicitud/asignación,
una asignación y agenda vigentes, cierre confirmado, unidades de materiales,
reglas versionadas, saldo derivado y ledger inmutable con crédito por material.
Callbacks de proveedor se separan de mensajes. No se precargan tasas ni datos reales.

Los triggers diferidos permiten confirmar colección y cambiar solicitud a
`recolectada` en la misma transacción; validan el estado final al COMMIT. Los triggers
no implementan toda la máquina de estados ni autorización. Backend debe bloquear
primero la solicitud (`SELECT ... FOR UPDATE`), validar permisos por rol/objeto,
piloto, cobertura, vigencia, disponibilidad, transiciones y mantener historial.
El usuario runtime no debe ser propietario de tablas ni superusuario.

## Decisiones que todavía necesitan coordinación

- El SQL original tiene un rol por usuario; el modelo conceptual permite varios.
  Se conserva el original hasta acordar si se necesita `user_roles`; no duplicar
  autoridad entre `users.role` y una nueva tabla.
- Se conserva una recolección por solicitud. Recolecciones parciales y correcciones
  de cierres requieren política y migración acordadas; no borrar eventos confirmados.
- Acordar unidades oficiales, precisión de negocio, conversiones y redondeo. El
  almacenamiento decimal no define la política de puntos. No activar reglas hasta
  contar con aprobación y garantizar selección inequívoca por material y fecha;
  falta acordar cómo impedir intervalos solapados al publicar versiones nuevas.
- Sin regla aprobada, no inventar puntos. Decidir si el cierre queda pendiente o
  permite acreditar posteriormente; el esquema no decide esa política.
- No hay sesiones aún: decidir patrón de auth antes de implementar login. Tener
  teléfono o recibir WhatsApp no equivale a una sesión web autenticada.
- El compañero de `feat/whatsapp-chatbot` prepara el ChatBot. Sus tablas no autorizan
  SQL directo: invoca casos de uso limitados del backend. No puede asignar, cerrar ni
  otorgar puntos automáticamente. Coordinar retención de conversaciones y datos.
- Retención de contactos, consentimiento revocado, cuerpos de mensajes, imágenes y
  ubicación; validación y gestión de datos del piloto; identidad visual web.

Estas diferencias se comunican aquí antes de implementar API/ORM/UI. El diseño web
puede conservar los flujos del diseño móvil, adaptando navegación, responsive y
accesibilidad, sin introducir tecnologías distintas de las acordadas.

## PostgreSQL local preparado en este equipo

Base de desarrollo: `ecoconecta`, servidor `127.0.0.1`, puerto `5432`, PostgreSQL 16.
`ecoconecta_owner` es propietario para instalación/migraciones; `ecoconecta_app`
es runtime sin privilegios administrativos ni DDL. No hay datos reales ni tasas
oficiales precargadas. Los datos están fuera de Git y de la carpeta temporal.

En Windows el estado está en `%LOCALAPPDATA%/EcoConecta/postgresql16`: `runtime/`
(binarios PostgreSQL), `tools/` (node-postgres auxiliar), `data/` (datos),
`credentials.xml` (contraseñas aleatorias cifradas con Windows DPAPI) y el log local.
No compartir esa carpeta ni subirla. Las credenciales están ligadas al usuario
Windows de este equipo; no son credenciales de GitHub.

Arranque manual tras reiniciar el PC, desde la raíz del repositorio:

```powershell
.\infra\start-local-postgres.ps1
. .\infra\use-local-db.ps1
# DATABASE_URL queda en la sesión; no imprimir su valor ni ponerlo en Git.
```

Para migraciones, usar `use-local-db.ps1 -Role Owner` solo en la sesión autorizada.
No se registra un servicio de Windows ni un arranque automático. El servidor escucha
solo en loopback y exige contraseña SCRAM. Frontend y ChatBot no reciben conexión
directa a la base. No ejecutar simultáneamente Compose en el mismo puerto.

En otro PC instalar binarios nativos PostgreSQL 16 en `runtime/` del directorio de
estado y `pg@8.23.1` con `npm install --prefix <estado>/tools --ignore-scripts pg@8.23.1`,
o usar PostgreSQL 16 instalado por el equipo e importar `schema.sql` en una base
vacía con pgAdmin/psql. El script local no instala proveedores cloud ni sobrescribe
bases existentes. El SQL contiene funciones, vistas y triggers que drawDB podría
no representar. Ejecutar la importación como una sola transacción con rollback ante error.

## Aplicación a una base existente

Confirmar primero dónde está PostgreSQL y obtener un esquema sin datos ni secretos.
Compararlo con este diseño y crear una revisión Alembic incremental con backfill y
plan de reversión. Retirar el saldo cacheado, cambiar unidades/fechas y modificar
claves únicas requiere revisar datos existentes; no usar DROP, reinicializar ni
ejecutar este CREATE TABLE encima de una base activa.

## Validación reproducible

`verify-schema.cjs` es una comprobación auxiliar del diseño SQL, no parte del
runtime Python. Requiere Node y `pg` (node-postgres) en una carpeta temporal o en
el entorno de herramientas de QA; no añade dependencias al backend.

Crear manualmente una base **vacía y desechable** `ecoconecta_schema_test` en
PostgreSQL 16 local aislado. El verificador rechaza otro nombre y esquemas `public`
con tablas. Instala el esquema, conserva las tablas para inspección y revierte los
datos sintéticos de prueba; nunca elimina tablas ni bases. Ejecutar una vez por base
vacía. Ejemplo PowerShell desde la raíz, sin credenciales reales en el comando:

```powershell
$validationTools = Join-Path ([IO.Path]::GetTempPath()) ('ecoconecta-check-' + [guid]::NewGuid())
npm install --prefix $validationTools --ignore-scripts --no-audit --no-fund pg@8.23.1
$env:NODE_PATH = Join-Path $validationTools 'node_modules'
# Configurar DATABASE_URL fuera de Git apuntando SOLO a la base desechable.
$env:ECOCONECTA_SCHEMA_TEST = '1'
node db/verify-schema.cjs
```

Cubre creación real del esquema, asignación/agenda únicas, relación entre solicitud
y agenda, estados con cierre válido, flujo/unidad/cantidad, dos materiales, saldo
derivado, ledger y cierre inmutables, versión de regla usada y callbacks duplicados.
No verifica autorización HTTP, concurrencia entre conexiones, cobertura temporal,
política de puntos ni integración real con Twilio: requieren backend y QA.
