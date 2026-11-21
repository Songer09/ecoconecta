import type { Role } from '../domain/types'

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
}

export interface ApiErrorBody {
  code: string
  message: string
  correlation_id: string
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

export interface StaffRegistration extends Pick<ResidentRegistration, 'full_name' | 'phone' | 'password'> {
  role: 'recolector' | 'coordinador_huerteros' | 'coordinador_recicladores'
  flow: 'organico' | 'reciclable'
  zone_ids: string[]
  valid_from: string
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

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '')
let accessToken: string | null = null

async function request<T>(path: string, init: RequestInit = {}, authenticated = true): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Content-Type', 'application/json')
  if (authenticated && accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  let response: Response
  try {
    response = await fetch(`${apiBaseUrl}${path}`, { ...init, headers, cache: 'no-store' })
  } catch {
    throw new Error('No se pudo conectar con el servidor EcoConecta. Verifica que la API esté activa.')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null) as ApiErrorBody | null
    const friendlyMessage = body?.code === 'invalid_credentials' ? 'El teléfono o la contraseña no son correctos.'
      : body?.code === 'phone_in_use' ? 'Ya existe una cuenta con este teléfono.'
      : body?.code === 'login_rate_limit' ? 'Hay muchos intentos. Espera un minuto e inténtalo de nuevo.'
      : body?.code === 'forbidden' ? 'Tu sesión no tiene permiso para esta acción.'
      : body?.message || 'No se pudo completar la solicitud.'
    throw new Error(friendlyMessage)
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
  createResident: (input: ResidentRegistration) => request<PilotAccount>('/admin/users', { method: 'POST', body: JSON.stringify(input) }),
  createStaff: (input: StaffRegistration) => request<unknown>('/admin/staff', { method: 'POST', body: JSON.stringify(input) }),
}
