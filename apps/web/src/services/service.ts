import type { EcoConectaService } from '../domain/types'
import { demoService } from './demo/demoService'

export type DataMode = 'demo' | 'api'

// API mode is intentionally unavailable until Backend publishes an agreed OpenAPI contract.
export function createService(mode: DataMode = 'demo'): EcoConectaService {
  if (mode === 'demo') return demoService
  throw new Error('VITE_DATA_MODE=api requiere el contrato OpenAPI y el adaptador backend acordados. Usa VITE_DATA_MODE=demo para esta versión.')
}

const configuredMode = import.meta.env.VITE_DATA_MODE || 'demo'
if (configuredMode !== 'demo' && configuredMode !== 'api') {
  throw new Error(`Modo de datos desconocido: ${configuredMode}. Usa demo o api.`)
}
export const dataMode = configuredMode as DataMode
export const service = createService(dataMode)
