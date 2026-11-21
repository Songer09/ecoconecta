# 00 — Introducción a EcoConecta

## Qué estamos construyendo

EcoConecta es un MVP para conectar hogares/unidades productivas con huerteros y recicladores de oficio para gestionar solicitudes de recolección, programarlas, registrar lo recolectado y reconocer la participación mediante puntos.

El producto debe apoyar la organización comunitaria existente, no reemplazar el liderazgo ni asumir que todos los residentes usan la plataforma.

## Objetivo de integración

No basta con que cada módulo funcione por separado. El entregable es un flujo completo:

1. Usuario registra solicitud.
2. Backend la enruta según flujo de residuo.
3. Coordinador revisa y asigna recolector.
4. Se registra programación completa.
5. Recolector registra cantidades/materiales y confirma recolección.
6. Backend actualiza estado e historial y calcula puntos en una transacción.
7. Usuario puede consultar el resultado y recibir notificación.

## Qué no asumir

- No asumir que las 15 personas recicladoras cubren todas las zonas o todos los horarios; cargar cobertura real confirmada.
- No asumir que huerteros tienen el mismo modelo de cobertura que recicladores.
- No asumir que el modelo de visión clasifica orgánicos con la misma calidad que no orgánicos.
- No inventar precisión, matriz de confusión, umbrales ni catálogo de materiales.
- No inventar reglas de puntos.
- No dar por conectada WhatsApp Cloud API si solo funciona Twilio o un mock.
- No presentar una demo con datos reales de residentes sin autorización.

## Entrega de cada agente

Cada agente debe entregar:
- alcance implementado;
- contratos/interfaces;
- archivos tocados;
- pruebas ejecutadas y resultados;
- limitaciones conocidas;
- instrucciones de integración;
- variables de entorno requeridas (nombres, nunca valores secretos).
