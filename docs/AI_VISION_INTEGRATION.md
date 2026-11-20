# Reconocimiento de imágenes — integración y validación

## 1. Estado conocido

El equipo informa que Codex 2 está trabajando con un modelo de reconocimiento de residuos y que obtuvo un índice de precisión alto, especialmente para residuos no orgánicos. Esta documentación no ha inspeccionado el repositorio, dataset ni reporte de métricas; por tanto, el resultado se considera **reportado, no verificado**.

La primera tarea no es entrenar otro modelo: es auditar lo existente y hacerlo reproducible.

## 2. Responsabilidad de Codex 2

1. Inspeccionar código, pesos, notebooks, dependencias y dataset disponible.
2. Documentar el pipeline reproducible desde preparación hasta inferencia.
3. Identificar clases y definición operativa de cada una.
4. Evaluar dataset: origen, licencias, consentimiento, duplicados, desbalance, calidad y posibles datos personales.
5. Confirmar separación sin fuga entre train/validation/test (idealmente por origen/sesión/objeto, no imágenes casi idénticas en splits distintos).
6. Reportar métricas por clase: precision, recall, F1, support y matriz de confusión; además de accuracy balanceada cuando aplique.
7. Medir latencia, tamaño, memoria, coste y hardware.
8. Documentar limitaciones, condiciones de captura y ataques/entradas anómalas.
9. Proponer umbral de confianza y política de abstención.
10. Exponer interfaz de inferencia estable y pruebas.

## 3. Reglas de producto

- Reconocimiento es asistencia, no autoridad operativa.
- La predicción no cambia por sí sola el tipo de solicitud, el enrutamiento, el estado, la asignación, la recolección ni los puntos.
- Mostrar al usuario una sugerencia entendible y permitir confirmar/corregir.
- Si no hay confianza suficiente, clase desconocida, mala calidad o clases múltiples ambiguas: abstenerse y pedir selección manual.
- No afirmar “precisión alta” en UI o pitch sin métrica, dataset, tamaño de muestra y evaluación reproducible.
- Especial atención a residuos orgánicos: no extrapolar resultados de no orgánicos.
- El sistema debe permitir operar manualmente si el modelo está caído.

## 4. Contrato interno sugerido

Entrada:
- imagen binaria o referencia privada validada;
- `request_id` opcional;
- contexto mínimo no personal.

Salida:
- `inference_id`;
- `model_name`, `model_version`;
- lista de `predictions` con `class_id`, `label`, `confidence`;
- `needs_human_review`;
- `warnings` (p.ej. blur, baja luz, clase desconocida);
- `created_at`;
- `processing_ms`.

No devolver rutas internas, stack traces ni metadatos privados.

## 5. Seguridad de imágenes

- Validar MIME real y firma del archivo; no confiar en extensión.
- Limitar tamaño, dimensiones, resolución y formatos admitidos.
- Decodificar en entorno controlado; proteger contra archivos malformados/decompresión abusiva.
- Renombrar archivos; no usar nombre suministrado por cliente como ruta.
- Evitar ejecución de macros, scripts o contenido embebido.
- Escanear/aislar cuando el entorno lo permita.
- Eliminar EXIF/GPS antes de almacenar o compartir.
- Guardar fuera del webroot y usar URLs firmadas de corta duración si hay almacenamiento de objetos.
- Control de acceso por rol/objeto; no exponer imágenes públicas.
- Definir retención y borrado.
- No registrar imagen ni base64 en logs.
- No enviar imágenes a APIs externas sin autorización y evaluación de privacidad/coste.

## 6. Interfaz y despliegue

El backend invoca el módulo. El navegador nunca llama directamente a proveedor/modelo con secretos.

Preferir primero librería local/servicio interno si el modelo puede ejecutarse de forma segura y viable. Si se usa API externa, documentar proveedor, región, tratamiento de datos, retención, coste, contrato y fallback.

No introducir una segunda base de datos para el módulo de visión. Artefactos del modelo pueden ser ficheros versionados o almacenamiento de objetos autorizado.

## 7. Pruebas mínimas

- imagen válida de cada clase;
- clase no soportada;
- baja confianza;
- imagen borrosa/oscura;
- varias clases/objetos;
- formato falso o corrupto;
- tamaño excesivo;
- intento de acceso a imagen de otro usuario;
- timeout/fallo del modelo;
- versión del modelo incorrecta;
- reproducibilidad de métricas.

## 8. Entregable de Codex 2

Crear `docs/VISION_MODEL_CARD.md` con:
- nombre y versión;
- propósito y usos no permitidos;
- clases;
- dataset y licencias;
- métricas globales y por clase;
- matriz de confusión;
- límites y riesgos;
- requisitos de ejecución;
- interfaz de inferencia;
- evaluación reproducible;
- decisión recomendada de despliegue.

No ocultar métricas desfavorables ni combinar categorías para inflar resultados.
