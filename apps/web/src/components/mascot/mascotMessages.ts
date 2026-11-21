import type { Role } from '../../domain/types'
import type { MascotExpression } from './mascotConfig'

type Line = { expression: MascotExpression; text: string; open?: boolean; blocksReminder?: boolean }

export const mascotMessages = {
  welcomeGreeting: { expression: 'bienvenida', text: '¡Hola! Soy Cris, tu guía. Elige tu rol para comenzar.' },
  welcomeHelp: { expression: 'explicando', text: 'Toca tu rol para entrar. ¿Quieres un recorrido rápido?' },
  login: { expression: 'explicando', text: 'Escribe tu teléfono con el +57 al inicio y tu contraseña.' },
  loginLoading: { expression: 'pensando', text: 'Verificando tus datos…', blocksReminder: true },
  loginInvalid: { expression: 'explicando', text: 'Revisa tu teléfono y tu contraseña e inténtalo de nuevo.', open: true },
  loginFailed: { expression: 'triste', text: 'Algo falló de nuestra parte. Inténtalo de nuevo en un momento.', open: true },
  register: { expression: 'explicando', text: 'Llena tus datos. La contraseña debe tener al menos 12 caracteres.' },
  registerLoading: { expression: 'pensando', text: 'Enviando tu registro…', blocksReminder: true },
  registerCreated: { expression: 'celebrando', text: '¡Listo! Tu cuenta quedó creada.' },
  collectorRegistered: { expression: 'feliz', text: 'Recibimos tu registro. Administración activará tu cuenta.' },
  registerInvalid: { expression: 'explicando', text: 'Revisa los datos señalados e inténtalo de nuevo.', open: true },
  registerFailed: { expression: 'triste', text: 'No pudimos enviar tu registro. Inténtalo de nuevo.', open: true },
  eventsLoading: { expression: 'pensando', text: 'Buscando los próximos eventos…', blocksReminder: true },
  eventsReady: { expression: 'feliz', text: 'Mira lo que viene en tu comunidad.' },
  eventsEmpty: { expression: 'explicando', text: 'Aún no hay eventos. Vuelve pronto.' },
  eventsFailed: { expression: 'triste', text: 'No pudimos cargar los eventos. Toca Reintentar.', open: true },
  educationLoading: { expression: 'pensando', text: 'Cargando tus temas…', blocksReminder: true },
  educationList: { expression: 'bienvenida', text: 'Elige un tema para aprender.' },
  educationEmpty: { expression: 'explicando', text: 'Los temas aparecerán aquí cuando el equipo los publique.' },
  educationReading: { expression: 'aprendiendo', text: 'Lee con calma. Al terminar, marca el tema como completado.' },
  educationSaving: { expression: 'pensando', text: 'Guardando tu avance…', blocksReminder: true },
  educationSaved: { expression: 'celebrando', text: '¡Tema completado! Sigue así.' },
  educationProgress: { expression: 'feliz', text: 'Elige otro tema para continuar.' },
  educationComplete: { expression: 'celebrando', text: '¡Completaste todos los temas!' },
  educationFailed: { expression: 'triste', text: 'No pudimos cargar Educación. Toca Reintentar.', open: true },
  educationExpired: { expression: 'triste', text: 'Tu sesión terminó. Inicia sesión para continuar.', open: true },
  educationSaveFailed: { expression: 'triste', text: 'No pudimos guardar tu avance. Inténtalo de nuevo.', open: true },
  pickupPhoto: { expression: 'explicando', text: 'Toma una foto de lo que vas a entregar.' },
  pickupMaterials: { expression: 'explicando', text: 'Elige qué materiales son.' },
  pickupAddress: { expression: 'explicando', text: 'Dime en qué conjunto, torre y apartamento estás.' },
  pickupCreated: { expression: 'celebrando', text: '¡Listo! Tu solicitud va en camino.' },
  neighbor: { expression: 'explicando', text: 'Pide una recolección o canjea tus puntos desde la barra.' },
  collector: { expression: 'explicando', text: 'Aquí ves tus recolecciones asignadas y tu ruta.' },
  recyclers: { expression: 'explicando', text: 'Revisa las solicitudes de reciclaje y asígnalas a un recolector.' },
  gardeners: { expression: 'explicando', text: 'Revisa las solicitudes orgánicas y asígnalas a un huertero.' },
  noCoordinationRequests: { expression: 'explicando', text: 'Las próximas solicitudes aparecerán aquí cuando lleguen.' },
  admin: { expression: 'explicando', text: 'Administra usuarios, eventos y materiales desde el menú.' },
  demoRoles: { expression: 'explicando', text: 'Elige un perfil para explorar sus pantallas.' },
  farewell: { expression: 'despedida', text: '¡Hasta pronto! Gracias por cuidar tu barrio.' },
  tourComplete: { expression: 'despedida', text: 'Listo. Si me necesitas, toca mi cara.' },
  reminderFirst: { expression: 'feliz', text: '¡Recuerda que si necesitas ayuda, estoy aquí para ti!' },
  reminderSecond: { expression: 'explicando', text: '¿Dudas? Toca mi cara y te ayudo.' },
  reminderThird: { expression: 'feliz', text: 'Estoy aquí por si me necesitas.' },
} as const satisfies Record<string, Line>

export type MascotMessage = keyof typeof mascotMessages
export type MascotView = 'welcome' | 'login' | 'register' | 'learning' | 'dashboard' | 'demo-roles' | 'events'

const roleMessages: Record<Role, MascotMessage> = {
  neighbor: 'neighbor', collector: 'collector', vivi: 'recyclers', kelly: 'gardeners', admin: 'admin',
}

export function defaultMascotMessage(view: MascotView, role: Role): MascotMessage {
  switch (view) {
    case 'welcome': return 'welcomeHelp'
    case 'login': return 'login'
    case 'register': return 'register'
    case 'learning': return 'educationLoading'
    case 'events': return 'eventsLoading'
    case 'demo-roles': return 'demoRoles'
    case 'dashboard': return roleMessages[role]
  }
}

export function learningProgressText(completed: number, total: number) {
  return `Llevas ${completed} de ${total} temas. Elige otro para continuar.`
}

export function mascotLine(message: MascotMessage): Line {
  return mascotMessages[message]
}

export const mascotTours = {
  inicio: [
    { target: 'welcome-role', text: 'Aquí eliges quién eres: vecino, recolector o coordinador.' },
    { target: 'education', text: 'En Educación aprendes a separar y reciclar. Necesitas tu cuenta.' },
    { target: 'events', text: 'En Eventos ves las actividades de tu comunidad.' },
  ],
  recoleccion: [
    { target: 'pickup-progress', text: 'Son 3 pasos: fotos, materiales y dirección.' },
    { target: 'pickup-photo', text: 'Toca aquí para tomar o elegir la foto.' },
    { target: 'pickup-next', text: 'Cuando tengas la foto, toca Continuar.' },
  ],
  'coordinacion-reciclaje': [
    { target: 'coordination-nav', text: 'Aquí están Solicitudes, Historial y Cuánto he ganado.' },
    { target: 'coordination-map', text: 'Este mapa es interactivo. Selecciona la ruta que quieres usar.' },
    { target: 'coordination-requests', text: 'Revisa las solicitudes nuevas y asígnalas a un recolector.' },
  ],
  'coordinacion-huerta': [
    { target: 'coordination-nav', text: 'Desde aquí cambias entre Solicitudes, Historial y Directorio.' },
    { target: 'coordination-map', text: 'Este mapa es interactivo. Selecciona la ruta que quieres usar.' },
    { target: 'coordination-requests', text: 'Revisa las solicitudes orgánicas y asígnalas a un huertero.' },
    { target: 'garden-inventory', text: 'En Inventario faltante y Canjes gestionas lo que necesita el huerto.' },
  ],
} as const

export type MascotTourId = keyof typeof mascotTours
