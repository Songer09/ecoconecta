# Auditoría de experiencia de EcoConecta Chatbot

Revisión del servicio FastAPI existente, su adaptador Gemini, el clasificador local, la búsqueda de contenido, la persistencia, la cola de WhatsApp y el panel de coordinación. La revisión no requirió cambios en el clasificador visual.

## Qué cambió

| Problema reproducido | Corrección |
|---|---|
| El borrador pedía cantidad, tipo de generador, lugar y horario antes de resumir. Algunos datos ya entregados se perdían mientras el bot esperaba un campo distinto. | Recupera los datos de cada turno antes de decidir qué falta. Para un aviso basta material reconocible y dirección o referencia. Si falta ubicación, se puede pedir con la preferencia en un mismo mensaje. La preferencia y el tipo de generador quedan opcionales. |
| El contrato de IA devolvía un solo material. El borrador podía reemplazar la lista anterior por la del último turno. | El contrato tipado devuelve una lista con una cita por material. Conserva materiales previos, admite correcciones por material y agrupa por el flujo autorizado en PostgreSQL. |
| El esquema exigía cantidad y unidad numéricas. | Guarda cantidad y unidad declaradas cuando existen, junto con el indicador aproximado y la descripción. Las declaraciones desconocidas pueden quedar sin número ni unidad. El cierre registra por separado la medición verificada. |
| Una consulta educativa sobre dos materiales recuperaba un solo artículo. | Busca una respuesta para cada material identificado en el banco publicado. El borrador permanece disponible. |
| Un material ambiguo o especial podía descartar el resto del borrador. | Guarda los materiales identificados y pide una aclaración o decisión antes de confirmar. El vecino puede solicitar revisión o autorizar que continúe solo con los materiales reconocidos. |

## Ejemplos

- «Buenas tardes, tengo unas tres bolsas de cartón en la manzana 12 casa 8 y pueden pasar mañana en la tarde». Un resumen con lugar, preferencia y tres bolsas aproximadas. Luego basta confirmar por escrito.
- «Tengo cartón», «Manzana 9 casa 2», «Sí». Un aviso recibido con cantidad sin indicar. El panel muestra esa condición al equipo.
- «Tengo dos bolsas de papel, tres costales de cartón y un balde de cáscaras, manzana 4 casa 3». Una confirmación crea dos avisos. Recicladores reciben un aviso con papel y cartón. Huerteros reciben un aviso con cáscaras. Cada aviso tiene su propio ID e historial.
- «Tengo tres bolsas de papel», «Perdón, son cuatro». La corrección conserva la unidad y actualiza el borrador.
- «¿Cómo separo cáscaras de banano y papel?». El bot responde sobre ambos materiales. Las solicitudes solo se guardan tras confirmación.

## Datos y control operativo

`002_conversation_ux` migra los avisos y cierres anteriores al detalle por material. Los campos históricos de cantidad y unidad del aviso siguen disponibles para el primer material. El detalle `items` expone las cantidades declaradas y las verificadas de cada material. El peso verificado en kilogramos tiene valor únicamente si el recolector registra esa unidad. La API conserva el cuerpo histórico de cierre para avisos de un material y acepta una lista de verificaciones para los avisos agrupados.

El servidor valida el material contra el catálogo aceptado, serializa la confirmación y limita la asignación, programación y cierre a sus roles. Los puntos se asignan dentro del cierre humano con reglas para el material y la unidad efectivamente verificada. La agenda se limita a registros publicados. Gemini sigue detrás del adaptador, con instrucciones para extraer todos los materiales y evidencia literal. La decisión de crear avisos y el enrutamiento se verifican en el backend. La variante oficial exige autorización escrita para habilitar Gemini.

## Verificación de la demo

Docker Compose aplicó la revisión `002`. Por HTTP se verificó el panel, la API de métricas y la creación de dos avisos recibidos sin peso a partir de un solo mensaje de papel y cáscaras y una confirmación.

## Límites de evidencia

El ZIP de auditoría citado no estaba disponible en los archivos entregados. Se añadieron 56 frases sintéticas de aceptación, 12 frases adicionales de reto y 12 diálogos de extremo a extremo. Las métricas se obtuvieron en modo local con PostgreSQL. Queda pendiente incorporar el ZIP original y evaluar Gemini y WhatsApp con credenciales. Los flujos de botella genérica y botella de plástico del catálogo de demostración son datos sintéticos.
