import type { RequestStatus } from '../domain/types'

const labels: Record<RequestStatus, string> = {
  RECEIVED: 'Recibida', UNDER_REVIEW: 'En revisión', ASSIGNED: 'Asignada', SCHEDULED: 'Programada',
  COLLECTED: 'Recolectada · por verificar', COMPLETED: 'Completada', CANCELLED: 'Cancelada',
}

export function StatusPill({ status }: { status: RequestStatus }) {
  return <span className={`status status-${status.toLowerCase()}`}><span aria-hidden="true">●</span> {labels[status]}</span>
}
