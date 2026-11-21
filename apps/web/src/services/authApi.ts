import type { CollectionRequest, NewRequest, RequestStatus, Role } from '../domain/types'

export interface LoginCredentials {
  phone: string
  password: string
}

interface LoginToken {
  access_token: string
  token_type: 'bearer'
  expires_in: number
}

export interface AuthenticatedIdentity {
  id: string
  role: 'solicitante' | 'recolector' | 'coordinador_huerteros' | 'coordinador_recicladores' | 'administrador'
  full_name?: string
  phone?: string
  stage?: string
  neighborhood?: string
  tower?: string
  apartment?: string
}

export interface ApiErrorBody {
  code: string
  message: string
  correlation_id: string
}

export interface PhotoSuggestion {
  status: 'recognized' | 'review_required' | 'unknown'
  material: string | null
  waste_category: 'organic' | 'inorganic' | null
  manual_review_required: boolean
}

export interface ResidentRegistration {
  full_name: string
  phone: string
  password: string
  stage: string
  neighborhood: string
  tower: string
  apartment: string
  data_treatment_accepted: true
}

export type AdminResidentRegistration = Pick<ResidentRegistration, 'full_name' | 'phone' | 'password'>
export type CollectorRegistration = Pick<ResidentRegistration, 'full_name' | 'phone' | 'password' | 'data_treatment_accepted'>

export interface StaffCoverage {
  flow: 'organico' | 'reciclable'
  zone_ids: string[]
  valid_from: string
}

export interface StaffRegistration extends AdminResidentRegistration, StaffCoverage {
  role: 'recolector' | 'coordinador_huerteros' | 'coordinador_recicladores'
}

export interface PilotAccount {
  id: string
  full_name: string
  role: AuthenticatedIdentity['role']
  is_active: boolean
  is_pilot: boolean
}

export interface ActiveZone {
  id: string
  name: string
}

export interface EducationModuleSummary {
  id: string
  title: string
  category: string
}

export interface EducationModule extends EducationModuleSummary {
  body: string
}

export interface LearningCompletion {
  module_id: string
  completed_at: string
}

export interface LearningProgress {
  completed: number
  total: number
  percentage: number
  completions: LearningCompletion[]
}

export interface GardenReward {
  id: string
  name: string
  price: number
  stock: number
}

export interface PublishedEvent {
  id: string
  title: string
  location: string
  starts_at: string
  description: string
}

export class ApiRequestError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message)
  }
}

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'https://backend-production-e3cd6aec.up.railway.app/api/v1' : '/api/v1')).replace(/\/$/, '')
let accessToken: string | null = null

export async function request<T>(path: string, init: RequestInit = {}, authenticated = true): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  if (authenticated && accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  let response: Response
  try {
    response = await fetch(`${apiBaseUrl}${path}`, { ...init, headers, cache: 'no-store' })
  } catch {
    throw new Error(`No se pudo conectar con el servidor EcoConecta (${apiBaseUrl}). Inicia la API y vuelve a intentarlo.`)
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null) as ApiErrorBody | null
    const friendlyMessage = body?.code === 'invalid_credentials' ? 'El teléfono o la contraseña no son correctos.'
      : body?.code === 'phone_in_use' ? 'Ya existe una cuenta con este teléfono.'
      : body?.code === 'login_rate_limit' ? 'Hay muchos intentos. Espera un minuto e inténtalo de nuevo.'
      : body?.code === 'registration_rate_limit' ? 'Se alcanzó el límite de registros desde esta conexión. Espera un minuto e inténtalo de nuevo.'
      : body?.code === 'collector_registration_not_pending' ? 'Esta cuenta ya no está pendiente. Actualiza el listado.'
      : body?.code === 'flow_unconfigured' ? 'Este flujo de recolección todavía no está configurado.'
      : body?.code === 'inactive_zone' ? 'Una de las zonas seleccionadas dejó de estar activa.'
      : body?.code === 'stock_unavailable' ? 'El producto se agotó.'
      : body?.code === 'insufficient_points' ? 'Tu saldo ya no alcanza para este canje.'
      : body?.code === 'forbidden' ? 'Tu sesión no tiene permiso para esta acción.'
      : body?.message || 'No se pudo completar la solicitud.'
    throw new ApiRequestError(friendlyMessage, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

const roleByApiRole: Record<AuthenticatedIdentity['role'], Role> = {
  solicitante: 'neighbor',
  recolector: 'collector',
  coordinador_huerteros: 'kelly',
  coordinador_recicladores: 'vivi',
  administrador: 'admin',
}

export const authApi = {
  async login(credentials: LoginCredentials): Promise<{ role: Role; identity: AuthenticatedIdentity }> {
    const token = await request<LoginToken>('/auth/login', { method: 'POST', body: JSON.stringify(credentials) }, false)
    accessToken = token.access_token
    try {
      const identity = await request<AuthenticatedIdentity>('/auth/me')
      return { role: roleByApiRole[identity.role], identity }
    } catch (error) {
      accessToken = null
      throw error
    }
  },
  async logout() {
    try { if (accessToken) await request<void>('/auth/logout', { method: 'POST' }) }
    finally { accessToken = null }
  },
  listZones: () => request<ActiveZone[]>('/zones'),
  listPilotUsers: () => request<PilotAccount[]>('/admin/users'),
  createResident: (input: AdminResidentRegistration) => request<PilotAccount>('/admin/users', { method: 'POST', body: JSON.stringify(input) }),
  registerResident: (input: ResidentRegistration) => request<PilotAccount>('/auth/register', { method: 'POST', body: JSON.stringify(input) }, false),
  registerCollector: (input: CollectorRegistration) => request<PilotAccount>('/auth/register/collector', { method: 'POST', body: JSON.stringify(input) }, false),
  async listPendingCollectors() {
    const users: PilotAccount[] = []
    const limit = 100
    while (true) {
      const page = await request<PilotAccount[]>(`/admin/collector-registrations?limit=${limit}&offset=${users.length}`)
      users.push(...page)
      if (page.length < limit) return users
    }
  },
  activateCollector: (id: string, input: StaffCoverage) => request<unknown>(`/admin/collector-registrations/${encodeURIComponent(id)}/activate`, { method: 'POST', body: JSON.stringify(input) }),
  createStaff: (input: StaffRegistration) => request<unknown>('/admin/staff', { method: 'POST', body: JSON.stringify(input) }),
}

export const visionApi = {
  recognize: (file: File, signal: AbortSignal) => request<PhotoSuggestion>('/users/me/photo-recognition', {
    method: 'POST',
    headers: { 'Content-Type': file.type },
    body: file,
    signal,
  }),
}

const requestFlows = { ORGANIC: 'organico', RECYCLABLE: 'reciclable' } as const
const requestStatuses = {
  recibida: 'RECEIVED',
  en_revision: 'UNDER_REVIEW',
  asignada: 'ASSIGNED',
  programada: 'SCHEDULED',
  recolectada: 'COMPLETED',
  cancelada: 'CANCELLED',
} as const satisfies Record<string, RequestStatus>

interface ResidentRequestSummary {
  id: string
  code: string
  flow: 'organico' | 'reciclable'
  status: keyof typeof requestStatuses
  created_at: string
}

interface ResidentRequestDetail extends ResidentRequestSummary {
  address: string
  observations: string | null
  preferred_time: string | null
  collector_name: string | null
  scheduled_start: string | null
}

function residentRequest(row: ResidentRequestSummary): CollectionRequest {
  return {
    id: row.id, code: row.code,
    flow: row.flow === 'organico' ? 'ORGANIC' : 'RECYCLABLE',
    status: requestStatuses[row.status],
    createdAt: new Date(row.created_at).toLocaleString('es-CO', { timeZone: 'America/Bogota' }),
    stage: '', neighborhood: '', tower: '', apartment: '', materials: [], note: '', availability: '',
  }
}

export const residentRequestsApi = {
  listMaterials(flow: NewRequest['flow'], signal: AbortSignal) {
    return request<{ id: string; name: string }[]>(`/public/materials?flow=${requestFlows[flow]}`, { signal }, false)
  },
  async create(input: NewRequest, zoneId: string, phone: string, generator: 'hogar' | 'unidad_productiva') {
    const observations = [`Materiales informados: ${input.materials.join(', ')}`, input.note].filter(Boolean).join('\n')
    if (observations.length > 1000) throw new Error('Reduce la nota o la selección de materiales para poder enviar la solicitud.')
    const row = await request<ResidentRequestSummary>('/requests', {
      method: 'POST',
      body: JSON.stringify({
        generator,
        flow: requestFlows[input.flow],
        zone_id: zoneId,
        contact_phone: phone,
        address: `${input.stage}, ${input.neighborhood}, torre ${input.tower}, apto. ${input.apartment}`,
        preferred_time: input.availability,
        observations,
      }),
    })
    return residentRequest(row)
  },
  async list(role: Role) {
    if (role === "admin") return []
    const path = role === "neighbor" ? "/users/me/requests" : role === "collector" ? "/collector/requests" : "/coordinator/requests"
    const rows: CollectionRequest[] = []
    const limit = 100
    while (true) {
      const page = await request<ResidentRequestSummary[]>(`${path}?limit=${limit}&offset=${rows.length}`)
      rows.push(...page.map(residentRequest))
      if (page.length < limit) return rows
    }
  },
  async detail(id: string, signal: AbortSignal) {
    const row = await request<ResidentRequestDetail>(`/requests/${encodeURIComponent(id)}`, { signal })
    return {
      ...residentRequest(row),
      address: row.address,
      note: row.observations ?? '',
      availability: row.preferred_time ?? '',
      assignedTo: row.collector_name ?? undefined,
      scheduledAt: row.scheduled_start ?? undefined,
    }
  },
}

export const educationApi = {
  async listModules() {
    const modules: EducationModuleSummary[] = []
    const limit = 100
    while (true) {
      const page = await request<EducationModuleSummary[]>(`/public/education?limit=${limit}&offset=${modules.length}`, {}, false)
      modules.push(...page)
      if (page.length < limit) return modules
    }
  },
  readModule: (id: string) => request<EducationModule>(`/public/education/${encodeURIComponent(id)}`, {}, false),
  async getProgress() {
    const limit = 100
    const progress = await request<LearningProgress>(`/users/me/learning-progress?limit=${limit}`)
    while (progress.completions.length < progress.completed) {
      const page = await request<LearningProgress>(`/users/me/learning-progress?limit=${limit}&offset=${progress.completions.length}`)
      if (!page.completions.length) break
      progress.completions.push(...page.completions)
    }
    return progress
  },
  complete: (id: string) => request<LearningCompletion>(`/users/me/learning-progress/${encodeURIComponent(id)}`, { method: 'PUT' }),
}

export const communityApi = {
  listEvents: () => request<PublishedEvent[]>('/public/events', {}, false),
  async getRewards() {
    const limit = 100
    const rewards: GardenReward[] = []
    while (true) {
      const page = await request<GardenReward[]>(`/rewards?limit=${limit}&offset=${rewards.length}`)
      rewards.push(...page)
      if (page.length < limit) return rewards
    }
  },
  getPoints: () => request<{ balance: string }>('/users/me/points'),
  async redeemReward(rewardId: string, idempotencyKey: string) {
    await request<unknown>('/users/me/redemptions', {
      method: 'POST',
      body: JSON.stringify({ reward_id: rewardId, quantity: 1, idempotency_key: idempotencyKey }),
    })
  },
}
