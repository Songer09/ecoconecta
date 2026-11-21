# Diagnóstico del frontend EcoConecta

Fecha de revisión: 20 de noviembre de 2026
Rama solicitada: `feat/frontend`

## Estado real encontrado

La documentación anterior afirmaba que `apps/web` no existía. Esa descripción está desactualizada: el checkout ya contiene una aplicación React, TypeScript y Vite, varios flujos por rol, componentes y un adaptador de demostración.

La carpeta `C:\Users\mkls\Documents\EcoConecta` y el repositorio `C:\Users\mkls\Desktop\ecoconecta` parten del mismo commit y rama. La copia de Documentos tenía un cambio local en `apps/web/postcss.config.js`; ese archivo no se copió ni se modificó durante esta revisión.

## Ya está implementado

- La página inicial muestra de inmediato opciones para vecino, recolector, coordinación de reciclaje, coordinación de huerta y administración.
- El acceso usa teléfono internacional y contraseña; `authApi` centraliza login, cierre de sesión y carga de usuarios piloto y zonas.
- El formulario de solicitud separa reciclaje de orgánicos, permite elegir materiales, recoge etapa, conjunto, torre, apartamento, disponibilidad y nota, y ofrece una foto opcional.
- Vecinos pueden consultar solicitudes, educación ambiental, puntos y eventos. El saldo, los canjes y los eventos sin publicar se identifican como pendientes.
- Recolectores tienen control visible de disponibilidad, una vista de ruta y acciones para registrar una recolección.
- Las vistas de Vivi y Kelly separan los dos flujos, muestran bandejas, permiten programar solicitudes y ofrecen módulos específicos para reciclaje o huerta.
- Administración tiene pantallas para aprovisionar usuarios, eventos, catálogo, borradores de puntos y reportes. El formulario de vecino captura nombre, celular, etapa, conjunto, torre, apartamento y una autorización obligatoria de uso de datos.
- Los datos de recolección viven en `demoService`. El modo `api` se detiene deliberadamente hasta acordar OpenAPI; login y algunas operaciones administrativas tienen clientes HTTP propios.
- El logo de EcoConecta ya es PNG RGBA con transparencia. El fondo blanco que se veía como placa venía de reglas CSS, no de la imagen.

## Cambios de interfaz aplicados en esta revisión

- Se añadió la sección **Conócenos** bajo la selección inmediata de rol, con información institucional, territorial y el ciclo comunitario.
- Se creó una entrada de **Directorio** para Vivi y Kelly. Los nombres y roles están en los documentos; teléfonos y zonas no se encontraron y se muestran expresamente como pendientes de confirmación.
- Se amplió el formulario de vecino para enviar dirección estructurada y aceptación de tratamiento de datos a través del endpoint existente `POST /admin/users`.
- Se aplicaron los colores pedidos en la solicitud más reciente: fondo cálido `#FAF8F5`, naranja `#E65C19`, hover `#C94B0F`, verde `#6CA62A`, amarillo `#FFC21A`, texto oscuro y campos `#F3EFEA`.
- Se retiró la placa blanca CSS del logo transparente y se cambió el CTA principal a naranja con texto de contraste alto.

## Pendientes y límites

| Bloque | Estado actual | Dependencia para completarlo |
|---|---|---|
| Registro completo del vecino | Administración aprovisiona cuentas. El formulario ahora recoge nombre, celular, etapa, conjunto, torre, apartamento y autorización obligatoria, y envía esos campos a `POST /admin/users`. El acceso sigue siendo provisionado por administración; no hay alta pública. | El backend no está en este checkout y OpenAPI no documenta esos campos. Debe aceptar y validar el payload ampliado, conservar la dirección y registrar la autorización antes de considerar el flujo integrado. El envío aún no se pudo probar contra el servidor. |
| Directorio operativo | La vista ya está disponible; Vivi y Kelly figuran con teléfono y zonas pendientes. | Coordinación debe confirmar teléfonos y cobertura. No inferir ni publicar datos personales o zonas. |
| Coincidencia con faltantes de huerta | La coordinación muestra un recordatorio para revisar prioridades, pero no compara materiales contra inventario vigente. | Backend/producto debe entregar un inventario y una respuesta de coincidencia actualizados; no convertir ejemplos de materiales en necesidades reales. |
| Rutas y asignaciones | El modo demo permite programar y registrar estados, pero usa asignaciones de muestra y la disponibilidad es local a la pantalla. | OpenAPI, identidad del recolector, cobertura, horario y ubicaciones confirmadas; el frontend no debe asignar personas ni marcar puntos por su cuenta. |
| Puntos, ingresos, canjes y reportes | Hay lugares para estos módulos. Los valores oficiales y datos reales no se inventan; varios controles solo guardan borradores locales o muestran vacíos. | Reglas, catálogo, ledger, permisos y contratos de consulta/escritura del backend. |
| Eventos y catálogo | La administración mantiene ejemplos solo en estado de la vista; no están persistidos. | Endpoint, permisos, formatos y contenido aprobado para publicación. |
| Integración completa | Solicitudes y operación usan datos sintéticos del demo. `VITE_DATA_MODE=api` no tiene adaptador. | OpenAPI vigente, autenticación, respuestas y errores, filtros, paginación, CORS y datos sintéticos coordinados. |
| Imágenes | El formulario acepta JPEG/PNG y crea una vista previa; no se integra almacenamiento remoto ni clasificación por IA. | Contrato, consentimiento, retención y acceso antes de conectar carga o reconocimiento. |

## Plan por cambios y publicación

1. **Perfil vecino y orientación comunitaria** — este cambio: paleta cálida, logo sin placa, Conócenos, directorio y registro vecino con domicilio y autorización. Commit previsto: `feat(frontend): add resident profile and community screens`.
2. **Contrato del registro** — actualizar OpenAPI/backend para aceptar y persistir el payload ampliado; después alinear la UI al esquema publicado y comprobar el envío. Commit previsto: `feat(frontend): align resident registration with API contract`.
3. **Operación de huerta y directorio real** — conectar inventario faltante, coincidencias y teléfonos/zonas confirmados. Commit previsto: `feat(frontend): connect garden priorities and coordinator directory`.
4. **Integración de solicitudes y módulos por rol** — consumir OpenAPI y sustituir el demo con estados de carga, error y vacío. Commit previsto: `feat(frontend): integrate role workflows with API`.
5. **Cierre de calidad** — revisar responsive, contraste y flujos cuando QA y los contratos estén disponibles; publicar cada hito en `origin/feat/frontend` después de revisar los archivos preparados.

Los cambios de esta revisión son estrictamente de interfaz y presentación. No añaden endpoints, persistencia de negocio, tarifas, puntos, cobertura ni datos personales ficticios.
