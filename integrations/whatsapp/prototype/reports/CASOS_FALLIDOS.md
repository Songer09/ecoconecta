# Casos que siguen fallando

La batería de aceptación de 56 frases y los 12 diálogos previstos pasaron sus comparaciones finales. La batería adicional de reto encontró estos límites del clasificador local.

| Escenario | Esperado | Resultado | Causa observada |
|---|---|---|---|
| H06 · «Quedaron 2 cajas de papel reciclado en el local» | Aviso | Orientación de reciclaje | La expresión de disponibilidad «quedaron» no activa el aviso y el adjetivo «reciclado» activa la regla educativa. La extracción sí identifica papel, dos y cajas. |
| H07 · «Y esas bolsas negras del negocio, ¿se recuperan?» | Pregunta sobre material | Fuera de alcance | No se reconoce «se recuperan» como consulta ambiental cuando el tipo de bolsa está por aclarar. |
| H08 · «Revísame en qué quedó lo que iban a llevarse» | Seguimiento | Ambiguo | La referencia al aviso no contiene una de las formulaciones que reconoce el clasificador local. |
| H09 · «¿Hay algún encuentro donde expliquen cómo armar una compostera?» | Capacitación | Educación sobre compostaje | Reconoce el tema, pero no detecta la solicitud de una actividad por la construcción «encuentro donde expliquen». |
| H04 · «¿Cómo preparo las latas, el cartón y las botellas de vidrio?» | Reconocimiento y flujo de los tres residuos | Identifica los tres y responde sobre reciclaje. Queda pendiente el flujo operativo del vidrio. | El catálogo de demostración carece de una ruta autorizada para vidrio. La métrica de flujo cuenta ese material como error, aunque no se creó un aviso ni se asignó una ruta. |

El conjunto incluye cantidades compuestas y contenedores descritos con números en palabras. La versión final conserva «un costal y medio» como 1,5 costales y «unas doce» como aproximación cuando acompaña a un material contable. La exactitud de intención del reto adicional quedó en 8/12. Los resultados no estiman el desempeño de Gemini ni el uso real de la comunidad.
