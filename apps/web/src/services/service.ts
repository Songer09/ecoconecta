import type { EcoConectaService } from '../domain/types'
import { demoService } from './demo/demoService'

// This adapter is only for the explicitly unauthenticated demo. Signed-in
// screens use the API clients in authApi.ts and their feature components.
export type DataMode = 'demo'

export function createService(): EcoConectaService {
  return demoService
}

export const dataMode: DataMode = 'demo'
export const service = createService()
