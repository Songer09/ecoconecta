# Qué necesita la Fundación — EcoConecta

## 1. Propósito del MVP

Una plataforma digital para facilitar la gestión comunitaria de residuos y economía circular en Villas de San Pablo. Debe conectar a la comunidad, unidades productivas, huerteros y recicladores, reforzando la coordinación comunitaria y no sustituyendo el voz a voz ni los liderazgos locales.

## 2. Flujo funcional principal

- Información y educación ambiental.
- Registro de solicitudes de recolección.
- Clasificación del flujo: orgánico o reciclable.
- Enrutamiento al colectivo coordinador correspondiente.
- Revisión y asignación a una persona recolectora.
- Acuerdo y registro de día/hora/responsable.
- Consulta de estado e historial.
- Registro de recolección y materiales/cantidades.
- Acreditación de puntos después de confirmar la recolección.
- Panel operativo e informes básicos.

## 3. Actores previstos

- Hogar/comunidad.
- Unidad productiva.
- Coordinador de huerteros.
- Huertero.
- Coordinador de recicladores.
- Reciclador.
- Administrador.

Los permisos concretos deben corresponder al rol y a la operación asignada. No confiar en que ocultar controles en la interfaz sea suficiente.

## 4. Datos mínimos de una solicitud

- Identificador único.
- Persona de contacto y canal de contacto.
- Ubicación/dirección o referencia de ubicación.
- Tipo de generador.
- Flujo/tipo de residuo.
- Observaciones.
- Disponibilidad horaria.
- Estado actual e historial de cambios.

Recoger solo los datos necesarios. La ubicación y el teléfono son datos personales: restringir acceso, limitar exposición y definir retención con el responsable del proyecto.

## 5. Estados y reglas

Estados contemplados: recibida, en revisión, programada, asignada, recolectada y cancelada. Definir transiciones válidas y conservar historial.

Reglas:
- Orgánico → coordinación de huerteros.
- Reciclable → coordinación de recicladores.
- No considerar programada una solicitud sin fecha, hora y responsable.
- Una asignación debe estar asociada a coordinador y recolector.
- Toda solicitud debe tener ID, estado e historial.
- Los puntos se generan solo después de recolección confirmada.
- La regla de puntos debe ser explicable y parametrizable.
- Piloto con usuarios configurados; no activar automáticamente a toda la comunidad.

## 6. Aclaraciones adicionales comunicadas por el equipo

Estas son aclaraciones verbales del equipo tras conversar con Daniel, director de TI. Se incorporan como contexto de trabajo y deben confirmarse si una decisión de producción o contractual depende de ellas.

- **Twilio puede usarse para el prototipo/prueba.**
- **WhatsApp Business Cloud API será la integración definitiva.**
- **Se permite usar IA libremente**, sujeto a las condiciones de privacidad, seguridad, presupuesto y aprobación de servicios externos.
- El equipo tiene libertad para desarrollar/usar reconocimiento de imágenes.
- Se informó que existen aproximadamente **15 recicladores**, organizados por zonas, días y horarios. Se debe confirmar la cobertura individual antes de cargarla.
- El equipo quiere registrar los materiales y cantidades recolectados por cada reciclador.
- Se necesita un sistema de puntos configurable.
- Se planteó solicitar zona/día/hora al inicio de sesión. Recomendación: no usar estos datos como credenciales. La identidad se autentica primero; zona, día y horario se usan como perfil operativo, disponibilidad o filtros posteriores.

## 7. Reconocimiento de imágenes

El equipo reporta que ya existe un modelo y que ha obtenido un índice de precisión alto, especialmente con residuos no orgánicos. Este dato es un **resultado reportado, todavía no auditado en esta documentación**.

Antes de integrarlo, Codex Visión debe registrar:
- modelo, versión, framework y dependencias;
- clases soportadas y definición exacta de cada clase;
- dataset, procedencia, licencias y separación train/validation/test;
- métricas por clase, no solo accuracy global;
- matriz de confusión, precision, recall, F1 y soporte por clase;
- condiciones de captura y casos no soportados;
- umbral de confianza y política de abstención;
- riesgos de falsos positivos, falsos negativos y sesgo por iluminación/fondo/cámara;
- coste, latencia, hardware y tamaño del artefacto;
- instrucciones para reproducir evaluación.

La predicción es **orientativa**. No asigna recolector, no cierra solicitudes, no determina puntos ni sustituye confirmación humana. Si la confianza es baja, la imagen es ambigua o la clase no está soportada, solicitar selección manual.

## 8. Mensajería

- Prototipo: Twilio permitido por la aclaración verbal.
- Producción/definitivo: WhatsApp Business Cloud API oficial.
- Diseñar una interfaz de proveedor para no acoplar el dominio al SDK de Twilio o Meta.
- El backend sigue siendo fuente de verdad; el mensaje no es una transacción de negocio.
- Webhooks autenticados/verificados, idempotentes y con manejo de reintentos.

## 9. Demostración mínima esperada

1. Unidad productiva registra solicitud orgánica.
2. Coordinador de huerteros la revisa y asigna huertero.
3. Se registra y comunica fecha, hora y responsable.
4. Huertero registra la recolección.
5. Estado e historial se actualizan y se acreditan puntos según regla configurada.
6. Otro usuario registra solicitud reciclable y esta llega al coordinador de recicladores.

## 10. Pendientes que requieren confirmación humana

- Cobertura exacta por zona, reciclador, días y franjas horarias.
- Operación y cobertura de huerteros.
- Catálogo de materiales, unidades y categorías oficiales.
- Reglas/valores de puntos y quién puede modificarlos.
- Campos personales obligatorios, aviso de privacidad, consentimiento/base legal y retención.
- Proveedor cloud autorizado, región, presupuesto, dominio y recursos.
- Credenciales y cuenta WhatsApp Business/API definitiva.
- Si la IA se ejecutará localmente o en proveedor externo y quién asume el coste.
- Política para imágenes: almacenamiento, consentimiento, retención, eliminación y acceso.
- Identidad visual y archivos de diseño/logotipos.
