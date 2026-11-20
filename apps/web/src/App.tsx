import { useEffect, useMemo, useState } from 'react'
import type { CollectionRequest, EducationTopic, NewRequest, Role } from './domain/types'
import { service } from './services/service'
import { Brand } from './components/Brand'
import { StatusPill } from './components/StatusPill'
import { DemoTag } from './components/DemoTag'
import { TerritoryMap } from './components/TerritoryMap'
import { EmptyState, InfoSection, OperationPanel } from './components/PanelStates'

type View = 'welcome' | 'learning' | 'dashboard'
type Section = 'home' | 'requests' | 'new' | 'points' | 'learning' | 'events' | 'profile' | 'routes' | 'materials' | 'income' | 'needs' | 'inventory' | 'redemptions' | 'users' | 'catalog' | 'reports'

const roleInfo: Record<Role, { name: string; title: string; description: string; initial: string }> = {
  neighbor: { name: 'Vecino', title: 'Tu hogar también transforma', description: 'Solicita una recolección, aprende y sigue tus aportes.', initial: 'V' },
  collector: { name: 'Recolector', title: 'Tu jornada, más clara', description: 'Consulta tus asignaciones y registra cada recolección.', initial: 'R' },
  vivi: { name: 'Vivi', title: 'Coordinación de reciclaje', description: 'Organiza solicitudes, personas y materiales reciclables.', initial: 'V' },
  kelly: { name: 'Kelly', title: 'Coordinación de huerta', description: 'Conecta los aportes orgánicos con las necesidades del huerto.', initial: 'K' },
  admin: { name: 'Administrador', title: 'Gestión de EcoConecta', description: 'Administra las herramientas comunitarias del sistema.', initial: 'A' },
}

const navByRole: Record<Role, { id: Section; label: string }[]> = {
  neighbor: [{ id: 'home', label: 'Inicio' }, { id: 'requests', label: 'Mis solicitudes' }, { id: 'points', label: 'Mis puntos' }, { id: 'learning', label: 'Aprendizaje' }, { id: 'events', label: 'Eventos' }],
  collector: [{ id: 'home', label: 'Mi jornada' }, { id: 'routes', label: 'Asignaciones' }, { id: 'requests', label: 'Historial' }, { id: 'profile', label: 'Mi perfil' }],
  vivi: [{ id: 'home', label: 'Resumen' }, { id: 'requests', label: 'Solicitudes' }, { id: 'routes', label: 'Rutas y equipo' }, { id: 'materials', label: 'Pesajes' }, { id: 'income', label: 'Ingresos' }],
  kelly: [{ id: 'home', label: 'Resumen' }, { id: 'requests', label: 'Solicitudes orgánicas' }, { id: 'needs', label: 'Necesidades del huerto' }, { id: 'inventory', label: 'Inventario' }, { id: 'redemptions', label: 'Canjes' }],
  admin: [{ id: 'home', label: 'Resumen' }, { id: 'users', label: 'Usuarios y roles' }, { id: 'events', label: 'Eventos' }, { id: 'catalog', label: 'Catálogos y puntos' }, { id: 'reports', label: 'Reportes' }],
}

const roleOptions: Role[] = ['neighbor', 'collector', 'vivi', 'kelly', 'admin']

function Welcome({ onRole, onLearn }: { onRole: (role: Role) => void; onLearn: () => void }) {
  return <main className="welcome-page">
    <header className="welcome-header"><Brand /><a href="#roles">Entrar a EcoConecta <span aria-hidden="true">↓</span></a></header>
    <div className="welcome-grid">
      <section className="welcome-copy">
        <p className="eyebrow">COMUNIDAD · RECICLAJE · HUERTA</p>
        <h1>Un barrio más limpio empieza <em>en comunidad.</em></h1>
        <p className="welcome-lede">Conectamos a vecinos, recolectores y coordinadoras para aprovechar mejor lo que tenemos.</p>
        <div className="welcome-points"><span><i className="dot orange"/> Recolecciones organizadas</span><span><i className="dot green"/> Aprendizaje para todos</span></div>
        <section className="role-picker" id="roles">
          <div className="role-picker-heading"><div><p className="eyebrow">ACCESO DE DEMOSTRACIÓN</p><h2>¿Cómo quieres entrar?</h2></div><span className="role-count">5 experiencias</span></div>
          <div className="role-grid">
            {roleOptions.map((role) => <button key={role} className="role-card" onClick={() => onRole(role)}><span className={`role-avatar avatar-${role}`}>{roleInfo[role].initial}</span><span className="role-copy"><strong>{roleInfo[role].name}</strong><small>{roleInfo[role].description}</small></span><span className="role-arrow" aria-hidden="true">↗</span></button>)}
          </div>
          <p className="demo-note">En esta demostración puedes entrar sin credenciales. Los cambios son datos de prueba en este navegador.</p>
        </section>
      </section>
      <aside className="welcome-aside"><TerritoryMap onLearn={onLearn}/><div className="community-note"><div className="community-leaf" aria-hidden="true">+</div><div><strong>Una acción a la vez</strong><p>Separa, solicita y participa. El equipo comunitario te acompaña.</p></div></div></aside>
    </div>
    <footer className="welcome-footer"><span>EcoConecta · Villas de San Pablo, Barranquilla</span><img src="/images/logo-villas-san-pablo.png" alt="Villas de San Pablo · Megabarrio Barranquilla"/><span>Una iniciativa para cuidar lo que compartimos</span></footer>
  </main>
}

function Education({ onBack, onNeighbor }: { onBack: () => void; onNeighbor: () => void }) {
  const [topics] = useState<EducationTopic[]>(() => service.listEducationTopics())
  const [completed, setCompleted] = useState<string[]>(() => service.getCompletedTopics())
  const [active, setActive] = useState<string | null>(null)
  const percent = Math.round((completed.length / topics.length) * 100)
  const selected = topics.find((topic) => topic.id === active)
  function toggleTopic(topicId: string) {
    const isDone = completed.includes(topicId)
    service.setTopicCompleted(topicId, !isDone)
    setCompleted(service.getCompletedTopics())
  }
  return <main className="education-page">
    <header className="simple-header"><button className="text-button" onClick={onBack}>← Volver</button><Brand compact/><button className="button button-secondary header-neighbor" onClick={onNeighbor}>Entrar como vecino</button></header>
    <div className="education-wrap">
      <div className="education-intro"><p className="eyebrow">APRENDER PARA APROVECHAR</p><h1>Aprendamos juntos</h1><p>Ideas sencillas para separar mejor y cuidar nuestra huerta y nuestro barrio.</p></div>
      <section className="progress-card" aria-label={`Has completado ${percent}% del aprendizaje`}><div className="progress-top"><div><span className="eyebrow">TU AVANCE</span><strong>{percent}% <small>completado</small></strong></div><span className="progress-count">{completed.length} de {topics.length} temas</span></div><div className="progress-track" role="progressbar" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100}><span style={{ width: `${percent}%` }}/></div></section>
      <div className="education-layout">
        <section className="topic-list" aria-label="Temas de aprendizaje">
          {topics.map((topic, index) => {
            const done = completed.includes(topic.id)
            const status = done ? 'Completado' : active === topic.id ? 'En progreso' : 'Pendiente'
            return <button key={topic.id} className={`topic-row ${active === topic.id ? 'topic-row-active' : ''}`} onClick={() => setActive(topic.id)}><span className={`topic-number ${done ? 'topic-number-done' : ''}`}>{done ? '✓' : String(index + 1).padStart(2, '0')}</span><span className="topic-copy"><strong>{topic.title}</strong><small>{topic.summary}</small></span><span className={`topic-status ${done ? 'topic-status-done' : ''}`}>{status}</span></button>
          })}
        </section>
        <section className="lesson-card" aria-live="polite">
          {selected ? <><p className="eyebrow">LECTURA · {selected.minutes} MIN</p><h2>{selected.title}</h2><p className="lesson-summary">{selected.summary}</p><ul>{selected.body.map((line) => <li key={line}>{line}</li>)}</ul><button className={`button ${completed.includes(selected.id) ? 'button-secondary' : 'button-primary'}`} onClick={() => toggleTopic(selected.id)}>{completed.includes(selected.id) ? 'Marcar como pendiente' : 'Marcar tema como completado'}</button></> : <div className="lesson-empty"><span className="lesson-sun" aria-hidden="true">✳</span><h2>Elige un tema para comenzar</h2><p>Tu avance se guarda en este navegador durante la demostración.</p></div>}
        </section>
      </div>
      <div className="education-bottom"><span>El contenido es educativo y no reemplaza las indicaciones del equipo recolector.</span><button className="text-button" onClick={onBack}>Volver al inicio ↑</button></div>
    </div>
  </main>
}

function RequestForm({ onCreated, onCancel }: { onCreated: (item: CollectionRequest) => void; onCancel: () => void }) {
  const [step, setStep] = useState(1)
  const [flow, setFlow] = useState<NewRequest['flow']>('RECYCLABLE')
  const [materials, setMaterials] = useState<string[]>([])
  const [stage, setStage] = useState('Etapa 4')
  const [neighborhood, setNeighborhood] = useState('')
  const [tower, setTower] = useState('')
  const [apartment, setApartment] = useState('')
  const [availability, setAvailability] = useState('Mañana en la mañana')
  const [note, setNote] = useState('')
  const [photoName, setPhotoName] = useState('')
  const [error, setError] = useState('')
  const options = flow === 'RECYCLABLE' ? ['Cartón', 'Papel', 'Botellas PET', 'Latas', 'Vidrio'] : ['Restos de frutas', 'Cáscaras de verduras', 'Hojas secas', 'Restos de poda']
  function selectMaterial(name: string) { setMaterials((items) => items.includes(name) ? items.filter((item) => item !== name) : [...items, name]) }
  async function submit() {
    if (!neighborhood.trim() || !tower.trim() || !apartment.trim()) { setError('Completa conjunto, torre y apartamento para que puedan encontrarte.'); return }
    if (!materials.length) { setStep(1); setError('Elige al menos un material.'); return }
    const created = await service.createRequest({ flow, stage, neighborhood: neighborhood.trim(), tower: tower.trim(), apartment: apartment.trim(), materials, availability, note: note.trim() })
    onCreated(created)
  }
  return <section className="form-card"><div className="form-heading"><div><p className="eyebrow">NUEVA RECOLECCIÓN · PASO {step} DE 3</p><h2>{step === 1 ? '¿Qué necesitas entregar?' : step === 2 ? '¿Dónde y cuándo?' : 'Revisa antes de enviar'}</h2></div><button className="icon-button" onClick={onCancel} aria-label="Cerrar formulario">×</button></div>
    <div className="form-steps"><span className={step >= 1 ? 'step-current' : ''}>1 <small>Materiales</small></span><i/><span className={step >= 2 ? 'step-current' : ''}>2 <small>Dirección</small></span><i/><span className={step >= 3 ? 'step-current' : ''}>3 <small>Confirmar</small></span></div>
    {step === 1 ? <><div className="flow-choice"><button className={flow === 'RECYCLABLE' ? 'flow-option selected' : 'flow-option'} onClick={() => { setFlow('RECYCLABLE'); setMaterials([]) }}><strong>Reciclables</strong><small>Papel, cartón, envases y más</small></button><button className={flow === 'ORGANIC' ? 'flow-option selected flow-organic' : 'flow-option'} onClick={() => { setFlow('ORGANIC'); setMaterials([]) }}><strong>Orgánicos</strong><small>Aportes para la huerta comunitaria</small></button></div><fieldset className="material-fieldset"><legend>Selecciona tus materiales</legend><div className="material-options">{options.map((item) => <button type="button" key={item} className={materials.includes(item) ? 'material-chip chosen' : 'material-chip'} onClick={() => selectMaterial(item)} aria-pressed={materials.includes(item)}>{materials.includes(item) ? '✓ ' : '+ '}{item}</button>)}</div></fieldset></> : step === 2 ? <><p className="form-hint">La dirección solo se comparte con el equipo que atiende esta recolección.</p><div className="address-grid"><label>Etapa<select value={stage} onChange={(event) => setStage(event.target.value)}><option>Etapa 4</option><option>Etapa 5</option><option>Etapa 6</option><option>Etapa 7</option></select></label><label className="wide-field">Conjunto<input value={neighborhood} onChange={(event) => setNeighborhood(event.target.value)} placeholder="Nombre del conjunto" autoComplete="address-line1" /></label><label>Torre<input value={tower} onChange={(event) => setTower(event.target.value)} placeholder="Ej. 2" /></label><label>Apartamento<input value={apartment} onChange={(event) => setApartment(event.target.value)} placeholder="Ej. 304" /></label><label className="wide-field">¿Cuándo estás disponible?<select value={availability} onChange={(event) => setAvailability(event.target.value)}><option>Hoy en la tarde</option><option>Mañana en la mañana</option><option>Mañana en la tarde</option><option>Coordinar por teléfono</option></select></label><label className="wide-field">Nota para el equipo <span className="optional">(opcional)</span><textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder="Algo que debamos saber" rows={2}/></label><label className="wide-field photo-field">Foto del material <span className="optional">(opcional)</span><input type="file" accept="image/*" onChange={(event) => setPhotoName(event.target.files?.[0]?.name ?? '')}/><small>{photoName ? `Seleccionada: ${photoName}` : 'La foto solo se conserva en esta demostración; no se envía ni se almacena.'}</small></label></div></> : <div className="review-request"><div><span>Tipo</span><strong>{flow === 'ORGANIC' ? 'Orgánico · Huerta' : 'Reciclable · Centro de acopio'}</strong></div><div><span>Materiales</span><strong>{materials.join(', ')}</strong></div><div><span>Dirección</span><strong>{stage}, {neighborhood}, torre {tower}, apartamento {apartment}</strong></div><div><span>Disponibilidad</span><strong>{availability}</strong></div>{note && <div><span>Nota</span><strong>{note}</strong></div>}<p>La solicitud llegará a la coordinación correspondiente. La recolección y los puntos se confirman después de la verificación.</p></div>}
    {error && <p className="form-error" role="alert">{error}</p>}
    <div className="form-actions"><button className="button button-secondary" onClick={step === 1 ? onCancel : () => { setStep(step - 1); setError('') }}>{step === 1 ? 'Cancelar' : 'Atrás'}</button><button className="button button-primary" onClick={() => { setError(''); if (step === 1) materials.length ? setStep(2) : setError('Elige al menos un material.'); else if (step === 2) !neighborhood.trim() || !tower.trim() || !apartment.trim() ? setError('Completa conjunto, torre y apartamento para que puedan encontrarte.') : setStep(3); else void submit() }}>{step === 1 ? 'Continuar' : step === 2 ? 'Revisar solicitud' : 'Confirmar y enviar'}</button></div>
  </section>
}

function RequestCard({ item, role, onAssign, onCollect, onVerify }: { item: CollectionRequest; role: Role; onAssign: (scheduledAt: string) => void; onCollect: () => void; onVerify: () => void }) {
  const [assigning, setAssigning] = useState(false)
  const [scheduleDate, setScheduleDate] = useState('')
  const [scheduleTime, setScheduleTime] = useState('')
  const flowName = item.flow === 'ORGANIC' ? 'Orgánicos · Huerta' : 'Reciclables · Centro de acopio'
  const address = `${item.stage}, ${item.neighborhood}, torre ${item.tower}, apto. ${item.apartment}`
  return <article className="request-card"><div className="request-top"><div><span className={`flow-label ${item.flow === 'ORGANIC' ? 'flow-label-green' : ''}`}>{flowName}</span><h3>{item.id}</h3></div><StatusPill status={item.status}/></div><div className="request-detail"><strong>{item.materials.join(' · ')}</strong><span>{address}</span><span>Disponible: {item.availability}</span>{item.note && <p>“{item.note}”</p>}{item.assignedTo && <span>Recolector: {item.assignedTo}{item.scheduledAt ? ` · ${new Date(item.scheduledAt).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })}` : ''}</span>}</div>{assigning && <div className="assignment-editor"><label>Día<input type="date" value={scheduleDate} onChange={(event) => setScheduleDate(event.target.value)}/></label><label>Hora<input type="time" value={scheduleTime} onChange={(event) => setScheduleTime(event.target.value)}/></label><button className="button button-small button-primary" disabled={!scheduleDate || !scheduleTime} onClick={() => { onAssign(`${scheduleDate}T${scheduleTime}`); setAssigning(false) }}>Confirmar asignación</button></div>}<div className="request-bottom"><small>{item.createdAt}</small><div className="request-actions">{(role === 'vivi' || role === 'kelly') && item.status === 'RECEIVED' && !assigning && <button className="button button-small button-primary" onClick={() => setAssigning(true)}>Revisar y programar</button>}{role === 'collector' && (item.status === 'ASSIGNED' || item.status === 'SCHEDULED') && <button className="button button-small button-primary" onClick={onCollect}>Registrar recolección</button>}{(role === 'vivi' || role === 'kelly') && item.status === 'COLLECTED' && <button className="button button-small button-green" onClick={onVerify}>Verificar y cerrar</button>}{item.status === 'COMPLETED' && <span className="points-notice">✓ Cierre verificado · puntos según regla configurada</span>}</div></div></article>
}

function Dashboard({ role, onExit, onRole, onLearn }: { role: Role; onExit: () => void; onRole: (role: Role) => void; onLearn: () => void }) {
  const info = roleInfo[role]
  const [section, setSection] = useState<Section>('home')
  const [requests, setRequests] = useState<CollectionRequest[]>([])
  const [showForm, setShowForm] = useState(false)
  const [toast, setToast] = useState('')
  const [available, setAvailable] = useState(true)
  const [notification, setNotification] = useState('')
  useEffect(() => { void service.listRequests().then(setRequests) }, [])
  function announce(message: string) { setToast(message); window.setTimeout(() => setToast(''), 3800) }
  async function refresh(message?: string) { const rows = await service.listRequests(); setRequests(rows); if (message) announce(message) }
  const visibleRequests = useMemo(() => {
    if (role === 'neighbor') return requests
    if (role === 'collector') return requests.filter((item) => item.status === 'ASSIGNED' || item.status === 'SCHEDULED' || item.status === 'COLLECTED' || item.status === 'COMPLETED')
    if (role === 'vivi') return requests.filter((item) => item.flow === 'RECYCLABLE')
    if (role === 'kelly') return requests.filter((item) => item.flow === 'ORGANIC')
    return requests
  }, [requests, role])
  async function assign(item: CollectionRequest, scheduledAt: string) { const who = item.flow === 'ORGANIC' ? 'María T. · Huertera (dato ficticio)' : 'Andrés R. · Reciclador (dato ficticio)'; await service.assignRequest(item.id, who, scheduledAt); await refresh('Solicitud programada y asignada. La persona responsable ya puede verla en su jornada.') }
  async function collect(item: CollectionRequest) { await service.registerCollection(item.id); await refresh('Recolección registrada. La coordinadora puede verificar el cierre.') }
  async function verify(item: CollectionRequest) { await service.verifyAndClose(item.id); await refresh('Recolección verificada y cerrada. El sistema de puntos podrá aplicar la regla configurada.') }
  const requestActions = (item: CollectionRequest) => ({ onAssign: (scheduledAt: string) => void assign(item, scheduledAt), onCollect: () => void collect(item), onVerify: () => void verify(item) })
  const hello = role === 'neighbor' ? 'Hola, vecina' : role === 'collector' ? 'Hola, Andrés' : `Hola, ${info.name}`
  const title = section === 'requests' ? role === 'kelly' ? 'Solicitudes orgánicas' : role === 'vivi' ? 'Solicitudes de reciclaje' : role === 'neighbor' ? 'Mis solicitudes' : 'Historial' : section === 'routes' ? role === 'collector' ? 'Mis asignaciones' : 'Rutas y equipo' : navByRole[role].find((item) => item.id === section)?.label ?? info.title

  return <div className={`app-shell app-shell-${role}`}>
    <header className="app-header"><button className="brand-button" onClick={onExit} aria-label="Volver al selector de roles"><Brand compact/></button><div className="header-tools"><DemoTag/><label className="role-switch">Cambiar rol<select value={role} onChange={(event) => { setSection('home'); setShowForm(false); onRole(event.target.value as Role) }}>{roleOptions.map((item) => <option key={item} value={item}>{roleInfo[item].name}</option>)}</select></label></div></header>
    <div className="app-body"><aside className="app-sidebar"><div className={`sidebar-profile avatar-${role}`}><span>{info.initial}</span><div><strong>{info.name}</strong><small>{role === 'neighbor' ? 'Comunidad' : role === 'collector' ? 'Equipo recolector' : role === 'vivi' ? 'Equipo de reciclaje' : role === 'kelly' ? 'Equipo de huerta' : 'Administración'}</small></div></div><nav aria-label="Navegación principal">{navByRole[role].map((item) => <button key={item.id} className={`nav-item ${section === item.id ? 'nav-active' : ''}`} onClick={() => { setSection(item.id); setShowForm(false) }}><span className="nav-indicator" aria-hidden="true"/>{item.label}</button>)}</nav><div className="sidebar-bottom"><button className="nav-item" onClick={onExit}>← Salir al acceso</button><small>EcoConecta · Demostración</small></div></aside>
      <main className="app-main"><div className="mobile-brand"><Brand compact/></div><div className="main-heading"><div><p className="eyebrow">{info.name.toUpperCase()} · ECOCONECTA</p><h1>{section === 'home' ? hello : title}</h1>{section === 'home' && <p>{role === 'neighbor' ? 'Esto es lo que pasa con tus aportes al barrio.' : info.description}</p>}</div>{role === 'collector' && <button className={`availability ${available ? 'available' : ''}`} onClick={() => { setAvailable(!available); announce(available ? 'Ahora apareces como no disponible.' : 'Ahora apareces como disponible.') }}><i/> {available ? 'Disponible' : 'No disponible'}</button>}</div>
        {toast && <div className="toast" role="status">{toast}</div>}
        {notification && <div className="notice-banner" role="status">{notification}<button onClick={() => setNotification('')} aria-label="Cerrar aviso">×</button></div>}
        {showForm ? <RequestForm onCancel={() => { setShowForm(false); setSection('home') }} onCreated={(item) => { setShowForm(false); setSection('requests'); void refresh(`Solicitud ${item.id} creada y enviada a ${item.flow === 'ORGANIC' ? 'la coordinación de huerta' : 'la coordinación de reciclaje'}.`) }}/> : <DashboardSection role={role} section={section} requests={visibleRequests} allRequests={requests} onNew={() => { setShowForm(true); setSection('new') }} onLearn={onLearn} onAction={requestActions} onSection={setSection} onNotify={setNotification}/ >}
      </main>
    </div>
  </div>
}

function DashboardSection({ role, section, requests, allRequests, onNew, onLearn, onAction, onSection, onNotify }: { role: Role; section: Section; requests: CollectionRequest[]; allRequests: CollectionRequest[]; onNew: () => void; onLearn: () => void; onAction: (item: CollectionRequest) => { onAssign: (scheduledAt: string) => void; onCollect: () => void; onVerify: () => void }; onSection: (section: Section) => void; onNotify: (message: string) => void }) {
  const pending = requests.filter((item) => item.status === 'RECEIVED').length
  const active = requests.filter((item) => item.status !== 'COMPLETED' && item.status !== 'CANCELLED').length
  if (role === 'neighbor' && (section === 'home' || section === 'requests')) return <>
    <div className="neighbor-summary"><div className="summary-card summary-orange"><span>Solicitudes en proceso</span><strong>{active}</strong><small>Te avisaremos cuando haya cambios</small></div><div className="summary-card"><span>Puntos de EcoConecta</span><strong>—</strong><small>Se muestran al cerrar la recolección</small></div><button className="new-request-cta" onClick={onNew}><span aria-hidden="true">＋</span><strong>Solicitar recolección</strong><small>Reciclables u orgánicos</small></button></div>
    <div className="section-header"><div><h2>{section === 'home' ? 'Tus solicitudes recientes' : 'Todas tus solicitudes'}</h2><p>El estado se actualiza cuando el equipo revisa tu solicitud.</p></div>{section === 'home' && <button className="text-button" onClick={() => onSection('requests')}>Ver todas</button>}</div>
    {requests.length ? <div className="request-list">{requests.map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="Todavía no tienes solicitudes" detail="Cuando hagas una solicitud, podrás seguirla aquí." action="Solicitar recolección" onClick={onNew}/>}
    {section === 'home' && <button className="learning-callout" onClick={onLearn}><span className="learning-callout-icon">+</span><span><strong>Aprende y cuida tu barrio</strong><small>Explora temas sencillos sobre separación y huerta.</small></span><b>→</b></button>}
  </>
  if (role === 'neighbor' && section === 'points') return <div className="content-card points-explainer"><div className="points-mark">✳</div><p className="eyebrow">RECONOCIMIENTO A TU PARTICIPACIÓN</p><h2>Mis puntos</h2><p>Los puntos aparecen después de que el equipo verifica y cierra la recolección, según la regla configurada por la Fundación.</p><div className="points-value">{allRequests.filter((item) => item.status === 'COMPLETED').length ? 'Recolección verificada' : 'Aún no hay puntos acreditados'}</div><small>No se muestra una equivalencia hasta que la regla oficial esté configurada.</small><button className="button button-secondary" onClick={() => onSection('requests')}>Ver estado de mis solicitudes</button></div>
  if (role === 'neighbor' && section === 'learning') return <div className="feature-card"><div><p className="eyebrow">APRENDIZAJE AMBIENTAL</p><h2>Aprende a tu ritmo</h2><p>Consulta los temas y marca tu avance al terminar cada uno.</p><button className="button button-primary" onClick={onLearn}>Abrir aprendizaje</button></div><div className="feature-art feature-art-green"><span>01</span><i/><i/><i/></div></div>
  if (role === 'neighbor' && (section === 'events' || section === 'profile')) return <InfoSection title={section === 'events' ? 'Actividades de la comunidad' : 'Tu perfil'} description={section === 'events' ? 'Los eventos se publicarán aquí cuando la coordinación los comparta.' : 'El acceso de demostración no usa datos personales ni guarda un perfil real.'} badge={section === 'events' ? 'Sin eventos publicados' : 'Perfil de demostración'} />
  if (role === 'collector' && section === 'home') return <>
    <div className="collector-callout"><div><span className="eyebrow">TU JORNADA</span><h2>{requests.filter((item) => item.status === 'ASSIGNED' || item.status === 'SCHEDULED').length} recolecciones asignadas</h2><p>Revisa los detalles y registra el resultado al terminar.</p></div><button className="button button-primary" onClick={() => onSection('routes')}>Ver asignaciones</button></div>
    <div className="section-header"><div><h2>Lo próximo</h2><p>Dirección y materiales de tus recolecciones.</p></div></div>{requests.filter((item) => item.status !== 'COMPLETED').length ? <div className="request-list">{requests.filter((item) => item.status !== 'COMPLETED').map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="No tienes asignaciones por ahora" detail="Cuando te asignen una recolección, aparecerá aquí."/>}
  </>
  if (role === 'collector' && (section === 'routes' || section === 'requests')) return <><div className="section-header"><div><h2>{section === 'routes' ? 'Solicitudes asignadas' : 'Actividad reciente'}</h2><p>Solo aparecen las recolecciones asignadas a tu perfil de demostración.</p></div></div>{requests.length ? <div className="request-list">{requests.map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="No hay actividad para mostrar" detail="Las nuevas asignaciones se verán en este espacio."/>}</>
  if ((role === 'vivi' || role === 'kelly') && (section === 'home' || section === 'requests')) return <>
    <div className="coordinator-metrics"><div className="metric-card"><span>Por revisar</span><strong>{pending}</strong><small>Necesitan una asignación</small></div><div className="metric-card"><span>En seguimiento</span><strong>{active}</strong><small>Solicitudes sin cerrar</small></div><div className={`metric-card metric-accent-${role}`}><span>{role === 'vivi' ? 'Materiales por confirmar' : 'Necesidades del huerto'}</span><strong>—</strong><small>{role === 'vivi' ? 'Se registran al pesar' : 'Sin necesidades confirmadas'}</small></div></div>
    {role === 'kelly' && <div className="inline-priority"><span className="priority-mark">!</span><span><strong>Prioridad del huerto</strong><small>Revisa si los aportes orgánicos responden a una necesidad vigente.</small></span><button className="text-button" onClick={() => onSection('needs')}>Ver necesidades</button></div>}
    <div className="section-header"><div><h2>{section === 'home' ? 'Bandeja de solicitudes' : 'Solicitudes recibidas'}</h2><p>{role === 'vivi' ? 'Reciclables que requieren revisión del equipo.' : 'Aportes orgánicos para revisar y coordinar con el huerto.'}</p></div><div className="view-toggle"><button className="toggle-on">Lista</button><button disabled title="La vista de mapa queda pendiente de ubicaciones validadas">Mapa</button></div></div>
    {requests.length ? <div className="request-list">{requests.map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="La bandeja está al día" detail="Las solicitudes nuevas aparecerán aquí con su flujo correspondiente."/>}
    {role === 'vivi' && <div className="coordinator-note">Los precios, kilos y número de pacas se completan después de la recolección con información confirmada.</div>}
  </>
  if (role === 'vivi' && section === 'routes') return <OperationPanel title="Rutas y equipo" subtitle="Personas disponibles para organizar las próximas recolecciones." items={['Andrés R. · Reciclador', 'Luisa M. · Recicladora', 'Carlos P. · Reciclador']} action="Consultar disponibilidad" onAction={() => onNotify('Disponibilidad de demostración. La cobertura real debe configurarse desde backend.')}/>
  if (role === 'vivi' && section === 'materials') return <OperationPanel title="Pesajes de material" subtitle="Registra kilos y pacas al recibir el material en el centro de acopio." items={['Los materiales se agregan al cerrar una recolección.', 'El catálogo y las unidades están pendientes de validación.']} action="Ver solicitudes recolectadas" onAction={() => onSection('requests')}/>
  if (role === 'vivi' && section === 'income') return <InfoSection title="Ingresos por reciclaje" description="Los precios y las reglas de reparto deben ser validados por Vivi antes de mostrarse. Esta demostración no inventa valores económicos." badge="Sin tarifas configuradas"/>
  if (role === 'kelly' && section === 'needs') return <OperationPanel title="Necesidades del huerto" subtitle="Ejemplos de insumos mencionados por la Fundación; la necesidad y las cantidades reales deben confirmarse con el equipo." items={['Baldes reutilizables · prioridad por confirmar', 'Abono orgánico · cantidad por registrar', 'Manguera · cantidad por registrar']} action="Registrar una necesidad" onAction={() => onNotify('Formulario de necesidades pendiente de acordar con el equipo del huerto.')}/>
  if (role === 'kelly' && section === 'inventory') return <OperationPanel title="Inventario de aportes" subtitle="Aportes recibidos y pendientes de clasificar." items={['Los aportes se reflejan desde las solicitudes orgánicas.', 'Las cantidades se confirman al recibir cada material.']} action="Revisar solicitudes orgánicas" onAction={() => onSection('requests')}/>
  if (role === 'kelly' && section === 'redemptions') return <InfoSection title="Canjes del huerto" description="Los productos, existencias y equivalencias de canje se mostrarán cuando la Fundación configure el catálogo y la regla de puntos." badge="Catálogo pendiente"/>
  if (role === 'admin') return <AdminSection section={section} requests={allRequests} onNotify={onNotify}/>
  return <InfoSection title={roleInfo[role].title} description="Este módulo se habilitará cuando el equipo confirme sus datos y el backend publique el contrato correspondiente." badge="En preparación" />
}

function AdminSection({ section, requests, onNotify }: { section: Section; requests: CollectionRequest[]; onNotify: (message: string) => void }) {
  if (section === 'home') return <div className="admin-grid"><div className="metric-card"><span>Solicitudes de demostración</span><strong>{requests.length}</strong><small>Datos temporales en este navegador</small></div><div className="metric-card"><span>Flujo orgánico</span><strong>{requests.filter((item) => item.flow === 'ORGANIC').length}</strong><small>Coordinación de huerta</small></div><div className="metric-card"><span>Flujo reciclable</span><strong>{requests.filter((item) => item.flow === 'RECYCLABLE').length}</strong><small>Coordinación de reciclaje</small></div><div className="admin-shortcuts"><h2>Herramientas de administración</h2><p>Gestiona cada módulo desde la navegación.</p><span>Usuarios · eventos · materiales · puntos · reportes</span></div></div>
  const contents: Record<string, { title: string; description: string; items: string[] }> = {
    users: { title: 'Usuarios y roles', description: 'El piloto debe habilitar usuarios validados por la Fundación.', items: ['Vecinos y unidades productivas', 'Recolectores y disponibilidad', 'Coordinadoras y roles'] },
    events: { title: 'Eventos comunitarios', description: 'Publica actividades confirmadas para los conjuntos.', items: ['Aún no hay eventos publicados', 'Los datos de contacto deben ser validados'] },
    catalog: { title: 'Catálogos y puntos', description: 'El equipo aún no ha confirmado materiales, unidades ni equivalencias oficiales.', items: ['Catálogo de materiales pendiente de validar', 'Reglas de puntos sin valores configurados', 'No se cargaron tarifas de demostración'] },
    reports: { title: 'Reportes generales', description: 'Los indicadores usan solo datos de la demostración.', items: [`${requests.length} solicitudes registradas en este navegador`, `${requests.filter((item) => item.status === 'COMPLETED').length} recolecciones verificadas`, 'Sin datos personales exportados'] },
  }
  const data = contents[section] ?? contents.users
  return <OperationPanel title={data.title} subtitle={data.description} items={data.items} action="Entendido" onAction={() => onNotify('Los cambios administrativos estarán disponibles al definir el contrato backend.')}/>
}

export default function App() {
  const [view, setView] = useState<View>('welcome')
  const [educationReturnView, setEducationReturnView] = useState<View>('welcome')
  const [role, setRole] = useState<Role>('neighbor')
  const openLearning = () => { setEducationReturnView(view); setView('learning') }
  if (view === 'learning') return <Education onBack={() => setView(educationReturnView)} onNeighbor={() => { setRole('neighbor'); setView('dashboard') }}/>
  if (view === 'dashboard') return <Dashboard role={role} onExit={() => setView('welcome')} onRole={(selected) => { setRole(selected) }} onLearn={openLearning}/>
  return <Welcome onRole={(selected) => { setRole(selected); setView('dashboard') }} onLearn={openLearning}/>
}
