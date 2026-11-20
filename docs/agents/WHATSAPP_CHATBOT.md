# Agente de WhatsApp / ChatBot

Rama: `feat/whatsapp-chatbot`. Coordinación: agente principal Backend/Integración.
Leer AGENTS.md, TEAM_WORK_PROTOCOL, API_CONTRACTS, UNIFIED_DATA_MODEL,
SECURITY_2026_2027 y `integrations/whatsapp/README.md` antes de modificar código.

Propiedad: `integrations/whatsapp/**`, documentación y pruebas de su adaptador.
Proponer al principal las rutas/archivos ejecutables bajo `apps/api` para evitar
colisiones. No hay permiso para crear persistencia paralela ni modificar esquema,
migraciones o contratos compartidos sin coordinar.

Preparar Twilio para el prototipo y ChatBot con herramientas explícitas y acotadas:
educación, preguntas frecuentes y consulta de solicitudes del usuario autenticado.
No usar SQL generado por IA ni credenciales PostgreSQL desde el bot. Identificar
un teléfono no concede automáticamente todos los permisos de una cuenta.
Registro de solicitudes mediante bot requiere el mismo caso de uso validado del
backend y confirmación del usuario; no asignar, cerrar ni acreditar puntos por IA.

No activar servicios pagos ni enviar datos personales a un proveedor de IA sin
acuerdo del responsable humano. El principal coordina decisiones técnicas; el
equipo humano conserva aprobación de negocio, privacidad y paso a producción.

Entregar contrato, lista de archivos, pruebas reales, limitaciones y PR hacia la
rama de integración acordada. No integrar su propio PR a main. La implementación
del backend principal permanece pendiente de confirmación del usuario.
