import type { CollectionRequest, EcoConectaService, EducationTopic, NewRequest } from '../../domain/types'

const requests: CollectionRequest[] = [
  {
    id: 'EC-204', flow: 'ORGANIC', status: 'RECEIVED', createdAt: 'Hoy, 9:20 a. m.', stage: 'Etapa 4', neighborhood: 'Conjunto Arrayán', tower: '2', apartment: '304',
    materials: ['Restos de frutas', 'Cáscaras de verduras'], note: 'Separados en un balde con tapa.', availability: 'Hoy después de las 3:00 p. m.',
  },
  {
    id: 'EC-203', flow: 'RECYCLABLE', status: 'ASSIGNED', createdAt: 'Ayer, 4:10 p. m.', stage: 'Etapa 4', neighborhood: 'Conjunto Ceiba', tower: '1', apartment: '102',
    materials: ['Cartón', 'Botellas PET'], note: 'Material limpio y seco.', availability: 'Mañana en la mañana', assignedTo: 'Reciclador asignado (dato ficticio)',
  },
]

const topics: EducationTopic[] = [
  { id: 'separation', title: 'Separación de residuos', summary: 'Cómo preparar los residuos antes de entregarlos.', minutes: 3, body: ['Mantén separados los residuos orgánicos y los reciclables.', 'Enjuaga los envases y déjalos secar antes de guardarlos.', 'Entrega los residuos en recipientes limpios y seguros.'] },
  { id: 'recyclables', title: 'Materiales reciclables', summary: 'Reconoce los materiales que pueden aprovecharse.', minutes: 4, body: ['Cartón y papel limpios pueden aprovecharse.', 'Aplasta las botellas para ocupar menos espacio.', 'Si un material está sucio o mezclado, consulta antes de entregarlo.'] },
  { id: 'organic', title: 'Residuos orgánicos', summary: 'Qué puede llegar al huerto comunitario.', minutes: 3, body: ['Separa restos vegetales de otros residuos.', 'Evita mezclar plásticos, vidrio o productos químicos.', 'Usa un recipiente con tapa mientras se programa la recolección.'] },
  { id: 'compost', title: 'Compostaje en casa', summary: 'Ideas sencillas para aprovechar restos vegetales.', minutes: 5, body: ['Alterna material húmedo y material seco.', 'Mantén el compost aireado y evita agregar carnes o aceites.', 'Si tienes dudas, comparte una foto con la coordinación.'] },
  { id: 'garden', title: 'La huerta comunitaria', summary: 'Cómo se conectan los aportes con las necesidades del huerto.', minutes: 3, body: ['El equipo de la huerta revisa los aportes recibidos.', 'Las necesidades cambian según las tareas de cada temporada.', 'Consulta con la coordinación de huerta antes de llevar un insumo especial.'] },
  { id: 'good-practices', title: 'Buenas prácticas ambientales', summary: 'Pequeñas acciones que ayudan al barrio.', minutes: 2, body: ['Reduce los desechables cuando sea posible.', 'Reutiliza recipientes seguros y en buen estado.', 'Comparte información clara y confirmada con tus vecinos.'] },
]

let sequence = 205
const completedKey = 'ecoconecta.demo.education.completed'

function nextStatus(id: string, update: (item: CollectionRequest) => CollectionRequest): Promise<CollectionRequest> {
  const index = requests.findIndex((item) => item.id === id)
  if (index < 0) return Promise.reject(new Error('No encontramos esta solicitud.'))
  requests[index] = update(requests[index])
  return Promise.resolve({ ...requests[index] })
}

export const demoService: EcoConectaService = {
  async listRequests() { return requests.map((item) => ({ ...item, materials: [...item.materials] })) },
  async createRequest(input: NewRequest) {
    const created: CollectionRequest = { ...input, id: `EC-${sequence++}`, status: 'RECEIVED', createdAt: 'Ahora', materials: [...input.materials] }
    requests.unshift(created)
    return { ...created }
  },
  assignRequest(id, collectorName, scheduledAt) { return nextStatus(id, (item) => ({ ...item, status: 'SCHEDULED', assignedTo: collectorName, scheduledAt })) },
  registerCollection(id) { return nextStatus(id, (item) => ({ ...item, status: 'COLLECTED', collectedAt: 'Hoy' })) },
  verifyAndClose(id) { return nextStatus(id, (item) => ({ ...item, status: 'COMPLETED' })) },
  listEducationTopics() { return topics },
  getCompletedTopics() {
    try { return JSON.parse(localStorage.getItem(completedKey) ?? '[]') as string[] } catch { return [] }
  },
  setTopicCompleted(id, completed) {
    const current = new Set(this.getCompletedTopics())
    if (completed) current.add(id); else current.delete(id)
    localStorage.setItem(completedKey, JSON.stringify([...current]))
  },
}
