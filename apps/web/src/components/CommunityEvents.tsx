import { useEffect, useState } from 'react'
import { communityApi } from '../services/authApi'
import type { PublishedEvent } from '../services/authApi'
import { EmptyState } from './PanelStates'
import { useMascotScene } from './mascot/MascotContext'

const eventDay = new Intl.DateTimeFormat('es-CO', { timeZone: 'America/Bogota', day: 'numeric' })
const eventMonth = new Intl.DateTimeFormat('es-CO', { timeZone: 'America/Bogota', month: 'short' })
const eventTime = new Intl.DateTimeFormat('es-CO', { timeZone: 'America/Bogota', weekday: 'short', hour: 'numeric', minute: '2-digit' })

export function CommunityEvents() {
  const [events, setEvents] = useState<PublishedEvent[] | null>(null)
  const [failed, setFailed] = useState(false)
  const [attempt, setAttempt] = useState(0)
  useMascotScene(failed ? 'eventsFailed' : !events ? 'eventsLoading' : events.length ? 'eventsReady' : 'eventsEmpty')

  useEffect(() => {
    let current = true
    communityApi.listEvents()
      .then((items) => { if (current) setEvents(items) })
      .catch(() => { if (current) setFailed(true) })
    return () => { current = false }
  }, [attempt])

  if (failed) return <EmptyState title="No pudimos cargar la agenda" detail="Intenta consultar los eventos de nuevo." action="Reintentar" onClick={() => { setFailed(false); setAttempt((previous) => previous + 1) }}/>
  if (!events) return <p role="status">Cargando eventos…</p>
  if (!events.length) return <EmptyState title="Aún no hay eventos publicados" detail="Las próximas actividades de la comunidad aparecerán aquí."/>

  return <ul className="community-event-list" aria-label="Próximos eventos">{events.map((event, index) => {
    const date = new Date(event.starts_at)
    return <li className={index === 0 ? 'community-event community-event-next' : 'community-event'} key={event.id}>
      <div className="community-event-date" aria-hidden="true"><strong>{eventDay.format(date)}</strong><span>{eventMonth.format(date)}</span></div>
      <div>
        <h2>{event.title}</h2>
        <time dateTime={event.starts_at}>{eventTime.format(date)}</time>
        <p>{event.location}</p>
        {event.description && <details><summary>Más detalles</summary><p>{event.description}</p></details>}
      </div>
    </li>
  })}</ul>
}
