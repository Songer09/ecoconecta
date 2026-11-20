import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import type { CollectionRequest, EducationTopic, MaterialPointsRuleDraft, NewRequest, PointsRuleDraft, Role } from './domain/types'
import { service } from './services/service'
import { Brand } from './components/Brand'
import { StatusPill } from './components/StatusPill'
import { DemoTag } from './components/DemoTag'
import { TerritoryMap } from './components/TerritoryMap'
import { EmptyState, InfoSection, OperationPanel } from './components/PanelStates'
import { attachDemoRequestPhoto, getDemoRequestPhoto } from './services/demo/requestAttachments'

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
  neighbor: [{ id: 'home', label: 'Inicio' }, { id: 'points', label: 'Puntos y canjes' }, { id: 'learning', label: 'Educación' }, { id: 'events', label: 'Eventos' }, { id: 'profile', label: 'Perfil' }],
  collector: [{ id: 'home', label: 'Mi jornada' }, { id: 'routes', label: 'Ruta' }, { id: 'requests', label: 'Historial' }, { id: 'profile', label: 'Mi perfil' }],
  vivi: [{ id: 'home', label: 'Mapa' }, { id: 'requests', label: 'Historial' }, { id: 'income', label: 'Cuánto he ganado' }],
  kelly: [{ id: 'home', label: 'Resumen' }, { id: 'requests', label: 'Solicitudes orgánicas' }, { id: 'needs', label: 'Necesidades del huerto' }, { id: 'inventory', label: 'Inventario' }, { id: 'redemptions', label: 'Canjes' }],
  admin: [{ id: 'home', label: 'Resumen' }, { id: 'users', label: 'Usuarios y roles' }, { id: 'events', label: 'Eventos' }, { id: 'catalog', label: 'Materiales' }, { id: 'points', label: 'Configuración de puntos' }, { id: 'reports', label: 'Métricas y reportes' }],
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
    <footer className="welcome-footer"><span>EcoConecta · Villas de San Pablo, Barranquilla</span><img src="/images/logo-villas-san-pablo.png" alt="Villas de San Pablo · Megabarrio Barranquilla"/><img className="foundation-logo" src="/images/logo-fundacion-santo-domingo.png" alt="Fundación Santo Domingo"/><span>Una iniciativa para cuidar lo que compartimos</span></footer>
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
  const [photo, setPhoto] = useState<File | null>(null)
  const [photoPreview, setPhotoPreview] = useState('')
  const [error, setError] = useState('')
  const options = flow === 'RECYCLABLE' ? ['Cartón', 'Papel', 'Botellas PET', 'Latas', 'Vidrio'] : ['Restos de frutas', 'Cáscaras de verduras', 'Hojas secas', 'Restos de poda']
  useEffect(() => () => { if (photoPreview) URL.revokeObjectURL(photoPreview) }, [photoPreview])
  function selectPhoto(file: File | null) {
    setPhoto(null)
    setPhotoPreview('')
    if (!file) return
    if (!['image/jpeg', 'image/png'].includes(file.type)) { setError('La imagen debe ser JPG o PNG.'); return }
    if (file.size > 5 * 1024 * 1024) { setError('La imagen debe pesar máximo 5 MB.'); return }
    setError('')
    setPhoto(file)
    setPhotoPreview(URL.createObjectURL(file))
  }
  function selectMaterial(name: string) { setMaterials((items) => items.includes(name) ? items.filter((item) => item !== name) : [...items, name]) }
  async function submit() {
    if (!neighborhood.trim() || !tower.trim() || !apartment.trim()) { setError('Completa conjunto, torre y apartamento para que puedan encontrarte.'); return }
    if (!materials.length) { setStep(1); setError('Elige al menos un material.'); return }
    const created = await service.createRequest({ flow, stage, neighborhood: neighborhood.trim(), tower: tower.trim(), apartment: apartment.trim(), materials, availability, note: note.trim() })
    if (photo) attachDemoRequestPhoto(created.id, photo)
    onCreated(created)
  }
  return <section className="form-card"><div className="form-heading"><div><p className="eyebrow">NUEVA RECOLECCIÓN · PASO {step} DE 3</p><h2>{step === 1 ? '¿Qué necesitas entregar?' : step === 2 ? '¿Dónde y cuándo?' : 'Revisa antes de enviar'}</h2></div><button className="icon-button" onClick={onCancel} aria-label="Cerrar formulario">×</button></div>
    <div className="form-steps"><span className={step >= 1 ? 'step-current' : ''}>1 <small>Materiales</small></span><i/><span className={step >= 2 ? 'step-current' : ''}>2 <small>Dirección</small></span><i/><span className={step >= 3 ? 'step-current' : ''}>3 <small>Confirmar</small></span></div>
    {step === 1 ? <><div className="flow-choice"><button className={flow === 'RECYCLABLE' ? 'flow-option selected' : 'flow-option'} onClick={() => { setFlow('RECYCLABLE'); setMaterials([]) }}><strong>Reciclables</strong><small>Papel, cartón, envases y más</small></button><button className={flow === 'ORGANIC' ? 'flow-option selected flow-organic' : 'flow-option'} onClick={() => { setFlow('ORGANIC'); setMaterials([]) }}><strong>Orgánicos</strong><small>Aportes para la huerta comunitaria</small></button></div><fieldset className="material-fieldset"><legend>Selecciona tus materiales</legend><div className="material-options">{options.map((item) => <button type="button" key={item} className={materials.includes(item) ? 'material-chip chosen' : 'material-chip'} onClick={() => selectMaterial(item)} aria-pressed={materials.includes(item)}>{materials.includes(item) ? '✓ ' : '+ '}{item}</button>)}</div></fieldset></> : step === 2 ? <><p className="form-hint">La dirección solo se comparte con el equipo que atiende esta recolección.</p><div className="address-grid"><label>Etapa<select value={stage} onChange={(event) => setStage(event.target.value)}><option>Etapa 4</option><option>Etapa 5</option><option>Etapa 6</option><option>Etapa 7</option></select></label><label className="wide-field">Conjunto<input value={neighborhood} onChange={(event) => setNeighborhood(event.target.value)} placeholder="Nombre del conjunto" autoComplete="address-line1" /></label><label>Torre<input value={tower} onChange={(event) => setTower(event.target.value)} placeholder="Ej. 2" /></label><label>Apartamento<input value={apartment} onChange={(event) => setApartment(event.target.value)} placeholder="Ej. 304" /></label><label className="wide-field">¿Cuándo estás disponible?<select value={availability} onChange={(event) => setAvailability(event.target.value)}><option>Hoy en la tarde</option><option>Mañana en la mañana</option><option>Mañana en la tarde</option><option>Coordinar por teléfono</option></select></label><label className="wide-field">Nota para el equipo <span className="optional">(opcional)</span><textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder="Algo que debamos saber" rows={2}/></label><label className="wide-field photo-field">Imagen de los residuos <span className="optional">(opcional)</span><input type="file" accept="image/jpeg,image/png" onChange={(event) => selectPhoto(event.target.files?.[0] ?? null)}/><small>{photo ? `${photo.name} · adjunta a esta solicitud de demostración` : 'Adjunta una foto para orientar al equipo recolector.'}</small>{photoPreview && <img className="request-photo-preview" src={photoPreview} alt="Vista previa de los residuos"/>}</label></div></> : <div className="review-request"><div><span>Tipo</span><strong>{flow === 'ORGANIC' ? 'Orgánico · Huerta' : 'Reciclable · Centro de acopio'}</strong></div><div><span>Materiales</span><strong>{materials.join(', ')}</strong></div><div><span>Dirección</span><strong>{stage}, {neighborhood}, torre {tower}, apartamento {apartment}</strong></div><div><span>Disponibilidad</span><strong>{availability}</strong></div>{note && <div><span>Nota</span><strong>{note}</strong></div>}{photo && <div><span>Imagen</span><strong>{photo.name}</strong></div>}<p>La solicitud llegará a la coordinación correspondiente. La recolección y los puntos se confirman después de la verificación.</p></div>}
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
  const attachment = getDemoRequestPhoto(item.id)
  return <article className="request-card"><div className="request-top"><div><span className={`flow-label ${item.flow === 'ORGANIC' ? 'flow-label-green' : ''}`}>{flowName}</span><h3>{item.id}</h3></div><StatusPill status={item.status}/></div><div className="request-detail"><strong>{item.materials.join(' · ')}</strong><span>{address}</span><span>Disponible: {item.availability}</span>{item.note && <p>“{item.note}”</p>}{item.assignedTo && <span>Recolector: {item.assignedTo}{item.scheduledAt ? ` · ${new Date(item.scheduledAt).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })}` : ''}</span>}{attachment && <div className="request-attachment"><img src={attachment.url} alt={`Imagen de residuos para ${item.id}`}/><span>Imagen adjunta · {attachment.name}</span></div>}</div>{assigning && <div className="assignment-editor"><label>Día<input type="date" value={scheduleDate} onChange={(event) => setScheduleDate(event.target.value)}/></label><label>Hora<input type="time" value={scheduleTime} onChange={(event) => setScheduleTime(event.target.value)}/></label><button className="button button-small button-primary" disabled={!scheduleDate || !scheduleTime} onClick={() => { onAssign(`${scheduleDate}T${scheduleTime}`); setAssigning(false) }}>Confirmar asignación</button></div>}<div className="request-bottom"><small>{item.createdAt}</small><div className="request-actions">{(role === 'vivi' || role === 'kelly') && item.status === 'RECEIVED' && !assigning && <button className="button button-small button-primary" onClick={() => setAssigning(true)}>Revisar y programar</button>}{role === 'collector' && (item.status === 'ASSIGNED' || item.status === 'SCHEDULED') && <button className="button button-small button-primary" onClick={onCollect}>Registrar recolección</button>}{(role === 'vivi' || role === 'kelly') && item.status === 'COLLECTED' && <button className="button button-small button-green" onClick={onVerify}>Verificar y cerrar</button>}{item.status === 'COMPLETED' && <span className="points-notice">✓ Cierre verificado · puntos según regla configurada</span>}</div></div></article>
}

function RouteMap({ items, heading = 'Mapa esquemático de recolección' }: { items: CollectionRequest[]; heading?: string }) {
  return <section className="route-map-card"><div className="section-header"><div><p className="eyebrow">VILLAS DE SAN PABLO</p><h2>{heading}</h2><p>Esquema ilustrativo. Las ubicaciones reales requieren coordenadas validadas.</p></div><span className="route-count">{items.length} {items.length === 1 ? 'parada' : 'paradas'}</span></div><div className="route-map" role="img" aria-label="Mapa esquemático con vía, recorrido y paradas de demostración"><svg viewBox="0 0 760 300" aria-hidden="true"><path className="route-road" d="M-20 87 C90 112 119 36 250 63 S402 132 512 83 S660 33 790 78 M-20 225 C111 194 167 272 290 219 S470 164 586 217 S711 256 790 206 M156 -20 C189 79 144 143 188 320 M390 -20 C358 71 424 152 380 320 M624 -20 C596 81 650 158 616 320"/><path className="route-track" d="M120 82 C215 125 254 73 350 108 S506 165 584 106"/><path className="route-green" d="M316 184 C333 164 366 165 379 190 C391 215 370 232 347 228 C323 225 303 205 316 184Z"/><g className="route-blocks"><rect x="35" y="23" width="72" height="34" rx="7"/><rect x="259" y="19" width="73" height="32" rx="7"/><rect x="453" y="25" width="74" height="31" rx="7"/><rect x="665" y="107" width="67" height="35" rx="7"/><rect x="63" y="151" width="77" height="33" rx="7"/><rect x="455" y="251" width="83" height="29" rx="7"/></g>{items.slice(0, 4).map((item, index) => <g key={item.id} className="route-stop"><circle cx={[120, 350, 584, 480][index]} cy={[82, 108, 106, 205][index]} r="16"/><text x={[120, 350, 584, 480][index]} y={[87, 113, 111, 210][index]} textAnchor="middle">{index + 1}</text></g>)}</svg><span className="route-garden-label">Huerta comunitaria · referencia ilustrativa</span><span className="route-map-legend"><i/> Recorrido de demostración</span></div><div className="route-stop-list">{items.length ? items.slice(0, 4).map((item, index) => <div key={item.id}><b>{index + 1}</b><span><strong>{item.id} · {item.materials.join(', ')}</strong><small>{item.stage} · {item.neighborhood} · {item.status === 'COMPLETED' ? 'Recolección finalizada' : item.availability}</small></span></div>) : <p>No hay paradas asignadas por ahora.</p>}</div></section>
}

function Dashboard({ role, onExit, onRole, onLearn }: { role: Role; onExit: () => void; onRole: (role: Role) => void; onLearn: () => void }) {
  const info = roleInfo[role]
  const [section, setSection] = useState<Section>('home')
  const [showAllRequests, setShowAllRequests] = useState(false)
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
  const title = section === 'requests' ? role === 'kelly' ? 'Solicitudes orgánicas' : role === 'vivi' ? 'Historial de recolecciones' : role === 'neighbor' ? 'Mis solicitudes' : 'Historial' : section === 'routes' ? role === 'collector' ? 'Mi ruta' : 'Rutas y equipo' : navByRole[role].find((item) => item.id === section)?.label ?? info.title

  return <div className={`app-shell app-shell-${role}`}>
    <header className="app-header"><button className="brand-button" onClick={onExit} aria-label="Volver al selector de roles"><Brand compact/></button><div className="header-tools"><DemoTag/><label className="role-switch">Cambiar rol<select value={role} onChange={(event) => { setSection('home'); setShowForm(false); onRole(event.target.value as Role) }}>{roleOptions.map((item) => <option key={item} value={item}>{roleInfo[item].name}</option>)}</select></label></div></header>
    <div className="app-body"><aside className="app-sidebar"><div className={`sidebar-profile avatar-${role}`}><span>{info.initial}</span><div><strong>{info.name}</strong><small>{role === 'neighbor' ? 'Comunidad' : role === 'collector' ? 'Equipo recolector' : role === 'vivi' ? 'Equipo de reciclaje' : role === 'kelly' ? 'Equipo de huerta' : 'Administración'}</small></div></div><nav aria-label="Navegación principal">{navByRole[role].map((item) => <button key={item.id} className={`nav-item ${section === item.id ? 'nav-active' : ''}`} onClick={() => { setSection(item.id); setShowForm(false); setShowAllRequests(false) }}><span className="nav-indicator" aria-hidden="true"/>{item.label}</button>)}</nav><div className="sidebar-bottom"><button className="nav-item" onClick={onExit}>← Salir al acceso</button><small>EcoConecta · Demostración</small></div></aside>
      <main className="app-main"><div className="mobile-brand"><Brand compact/></div><div className="main-heading"><div><p className="eyebrow">{info.name.toUpperCase()} · ECOCONECTA</p><h1>{section === 'home' ? hello : title}</h1>{section === 'home' && <p>{role === 'neighbor' ? 'Esto es lo que pasa con tus aportes al barrio.' : info.description}</p>}</div>{role === 'collector' && <button className={`availability ${available ? 'available' : ''}`} onClick={() => { setAvailable(!available); announce(available ? 'Ahora apareces como no disponible.' : 'Ahora apareces como disponible.') }}><i/> {available ? 'Disponible' : 'No disponible'}</button>}</div>
        {toast && <div className="toast" role="status">{toast}</div>}
        {notification && <div className="notice-banner" role="status">{notification}<button onClick={() => setNotification('')} aria-label="Cerrar aviso">×</button></div>}
        {showForm ? <RequestForm onCancel={() => { setShowForm(false); setSection('home') }} onCreated={(item) => { setShowForm(false); setSection('home'); void refresh(`Solicitud ${item.id} creada y enviada a ${item.flow === 'ORGANIC' ? 'la coordinación de huerta' : 'la coordinación de reciclaje'}.`) }}/> : <DashboardSection role={role} section={section} requests={visibleRequests} allRequests={requests} showAllRequests={showAllRequests} onShowAll={() => setShowAllRequests(true)} onCloseAll={() => setShowAllRequests(false)} onNew={() => { setShowForm(true); setSection('new') }} onLearn={onLearn} onAction={requestActions} onSection={setSection} onNotify={setNotification}/ >}
      </main>
    </div>
  </div>
}

function DashboardSection({ role, section, requests, allRequests, showAllRequests, onShowAll, onCloseAll, onNew, onLearn, onAction, onSection, onNotify }: { role: Role; section: Section; requests: CollectionRequest[]; allRequests: CollectionRequest[]; showAllRequests: boolean; onShowAll: () => void; onCloseAll: () => void; onNew: () => void; onLearn: () => void; onAction: (item: CollectionRequest) => { onAssign: (scheduledAt: string) => void; onCollect: () => void; onVerify: () => void }; onSection: (section: Section) => void; onNotify: (message: string) => void }) {
  const pending = requests.filter((item) => item.status === 'RECEIVED').length
  const active = requests.filter((item) => item.status !== 'COMPLETED' && item.status !== 'CANCELLED').length
  if (role === 'neighbor' && section === 'home') return <>
    <div className="neighbor-welcome-banner"><div><p className="eyebrow">TU APORTE CUENTA</p><h2>Un barrio más limpio empieza con una acción.</h2><p>Comparte qué vas a entregar y el equipo comunitario te ayudará a coordinarlo.</p></div><button className="button button-primary" onClick={onNew}>＋ Solicitar recolección</button></div>
    <div className="neighbor-summary"><div className="summary-card summary-orange"><span>Recolecciones pendientes</span><strong>{active}</strong><small>En revisión o coordinación</small></div><div className="summary-card"><span>Puntos disponibles</span><strong>—</strong><small>Saldo por consultar al backend</small></div><button className="new-request-cta" onClick={onNew}><span aria-hidden="true">▧</span><strong>Adjunta una imagen</strong><small>Al crear tu solicitud</small></button></div>
    <div className="section-header"><div><h2>Mis recolecciones</h2><p>Consulta el estado de tus solicitudes recientes.</p></div>{requests.length > 2 && <button className="text-button" onClick={onShowAll}>Ver todas ({requests.length})</button>}</div>
    {requests.length ? <div className="request-list">{requests.slice(0, 2).map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="Todavía no tienes solicitudes" detail="Crea una solicitud y podrás seguir aquí su estado." action="Solicitar recolección" onClick={onNew}/>}
    <button className="learning-callout" onClick={() => onSection('learning')}><span className="learning-callout-icon">+</span><span><strong>Educación ambiental</strong><small>Aprende sobre separación, reciclables y huerta.</small></span><b>→</b></button>
    {showAllRequests && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onCloseAll() }}><section className="requests-modal" role="dialog" aria-modal="true" aria-labelledby="requests-modal-title"><div className="section-header"><div><p className="eyebrow">VECINO · DEMOSTRACIÓN</p><h2 id="requests-modal-title">Todas mis solicitudes</h2></div><button className="icon-button" onClick={onCloseAll} aria-label="Cerrar">×</button></div><div className="request-list">{requests.map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div></section></div>}
  </>
  if (role === 'neighbor' && section === 'points') return <div className="points-shop"><section className="points-balance"><span className="points-mark">✳</span><p className="eyebrow">TU SALDO</p><h2>Puntos disponibles</h2><strong>—</strong><small>El saldo real requiere consultar la cuenta del vecino en la API.</small></section><section className="points-products"><div><p className="eyebrow">ESPACIO DE CANJE</p><h2>Productos que podrás consultar</h2><p>El catálogo aún no ha sido definido por la Fundación. Aquí aparecerán las opciones disponibles y las que puedes canjear con tu saldo.</p></div><div className="product-pending-grid"><article><span>Catálogo pendiente</span><strong>Productos por definir</strong><small>No se muestran artículos ni equivalencias inventadas.</small></article><article><span>Canjes</span><strong>Disponible más adelante</strong><small>Se habilitará cuando exista catálogo y reglas aprobadas.</small></article></div></section></div>
  if (role === 'neighbor' && section === 'learning') return <div className="feature-card"><div><p className="eyebrow">APRENDIZAJE AMBIENTAL</p><h2>Aprende a tu ritmo</h2><p>Consulta los temas y marca tu avance al terminar cada uno.</p><button className="button button-primary" onClick={onLearn}>Abrir aprendizaje</button></div><div className="feature-art feature-art-green"><span>01</span><i/><i/><i/></div></div>
  if (role === 'neighbor' && section === 'events') return <InfoSection title="Eventos de la comunidad" description="Aquí se consultarán las actividades próximas cuando la coordinación las publique." badge="Sin eventos publicados" />
  if (role === 'neighbor' && section === 'profile') return <section className="neighbor-profile"><div className="profile-avatar">V</div><div><p className="eyebrow">PERFIL DE DEMOSTRACIÓN</p><h2>Vecino de Villas de San Pablo</h2><p>Los datos personales se mostrarán cuando exista una sesión autenticada.</p></div><div className="profile-points"><span>Puntos acumulados</span><strong>—</strong><small>Saldo pendiente de conexión con la API.</small></div></section>
  if (role === 'collector' && section === 'home') return <>
    <div className="collector-callout"><div><span className="eyebrow">TU JORNADA</span><h2>{requests.filter((item) => item.status === 'ASSIGNED' || item.status === 'SCHEDULED').length} recolecciones asignadas</h2><p>Revisa los detalles y registra el resultado al terminar.</p></div><button className="button button-primary" onClick={() => onSection('routes')}>Ver asignaciones</button></div>
    <div className="section-header"><div><h2>Lo próximo</h2><p>Dirección y materiales de tus recolecciones.</p></div></div>{requests.filter((item) => item.status !== 'COMPLETED').length ? <div className="request-list">{requests.filter((item) => item.status !== 'COMPLETED').map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="No tienes asignaciones por ahora" detail="Cuando te asignen una recolección, aparecerá aquí."/>}
  </>
  if (role === 'collector' && section === 'routes') return <><RouteMap items={requests.filter((item) => item.status === 'ASSIGNED' || item.status === 'SCHEDULED')}/><div className="section-header"><div><h2>Paradas asignadas</h2><p>Información de jornada para tu perfil de demostración.</p></div></div>{requests.length ? <div className="request-list">{requests.map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="No hay actividad para mostrar" detail="Las nuevas asignaciones se verán en este espacio."/>}</>
  if (role === 'collector' && section === 'requests') return <><div className="section-header"><div><h2>Historial de actividad</h2><p>Recolecciones asignadas a este perfil de demostración.</p></div></div>{requests.length ? <div className="request-list">{requests.map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="No hay actividad para mostrar" detail="Las recolecciones aparecerán aquí cuando estén asignadas."/>}</>
  if (role === 'collector' && section === 'profile') return <InfoSection title="Perfil del recolector" description="Disponibilidad de demostración. La identidad y cobertura se configurarán mediante sesión y datos validados." badge="Perfil simulado" />
  if (role === 'vivi' && section === 'home') return <><RouteMap items={requests.filter((item) => item.status !== 'COMPLETED' && item.status !== 'CANCELLED')} heading="Solicitudes de reciclaje en el territorio"/><div className="section-header"><div><h2>Solicitudes por organizar</h2><p>Revisa y programa la recolección con los datos disponibles.</p></div></div>{requests.filter((item) => item.status !== 'COMPLETED' && item.status !== 'CANCELLED').length ? <div className="request-list">{requests.filter((item) => item.status !== 'COMPLETED' && item.status !== 'CANCELLED').map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="No hay solicitudes activas" detail="Las nuevas solicitudes reciclables aparecerán en el mapa."/>}</>
  if (role === 'vivi' && section === 'requests') { const history = requests.filter((item) => item.status === 'COMPLETED' || item.status === 'COLLECTED'); return <><div className="section-header"><div><h2>Historial de reciclaje</h2><p>Recolecciones realizadas o pendientes de verificación.</p></div></div>{history.length ? <div className="request-list">{history.map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="Aún no hay recolecciones en el historial" detail="Cuando una recolección se realice, aparecerá aquí."/>}</> }
  if ((role === 'vivi' || role === 'kelly') && (section === 'home' || section === 'requests')) return <>
    <div className="coordinator-metrics"><div className="metric-card"><span>Por revisar</span><strong>{pending}</strong><small>Necesitan una asignación</small></div><div className="metric-card"><span>En seguimiento</span><strong>{active}</strong><small>Solicitudes sin cerrar</small></div><div className={`metric-card metric-accent-${role}`}><span>{role === 'vivi' ? 'Materiales por confirmar' : 'Necesidades del huerto'}</span><strong>—</strong><small>{role === 'vivi' ? 'Se registran al pesar' : 'Sin necesidades confirmadas'}</small></div></div>
    {role === 'kelly' && <div className="inline-priority"><span className="priority-mark">!</span><span><strong>Prioridad del huerto</strong><small>Revisa si los aportes orgánicos responden a una necesidad vigente.</small></span><button className="text-button" onClick={() => onSection('needs')}>Ver necesidades</button></div>}
    <div className="section-header"><div><h2>{section === 'home' ? 'Bandeja de solicitudes' : 'Solicitudes recibidas'}</h2><p>{role === 'vivi' ? 'Reciclables que requieren revisión del equipo.' : 'Aportes orgánicos para revisar y coordinar con el huerto.'}</p></div><div className="view-toggle"><button className="toggle-on">Lista</button><button disabled title="La vista de mapa queda pendiente de ubicaciones validadas">Mapa</button></div></div>
    {requests.length ? <div className="request-list">{requests.map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="La bandeja está al día" detail="Las solicitudes nuevas aparecerán aquí con su flujo correspondiente."/>}
    {role === 'vivi' && <div className="coordinator-note">Los precios, kilos y número de pacas se completan después de la recolección con información confirmada.</div>}
  </>
  if (role === 'vivi' && section === 'income') return <InfoSection title="Cuánto he ganado" description="Los ingresos aparecerán cuando el backend registre las liquidaciones confirmadas. Esta demostración no inventa tarifas ni ganancias." badge="Sin liquidaciones configuradas"/>
  if (role === 'kelly' && section === 'needs') return <OperationPanel title="Necesidades del huerto" subtitle="Ejemplos de insumos mencionados por la Fundación; la necesidad y las cantidades reales deben confirmarse con el equipo." items={['Baldes reutilizables · prioridad por confirmar', 'Abono orgánico · cantidad por registrar', 'Manguera · cantidad por registrar']} action="Registrar una necesidad" onAction={() => onNotify('Formulario de necesidades pendiente de acordar con el equipo del huerto.')}/>
  if (role === 'kelly' && section === 'inventory') return <OperationPanel title="Inventario de aportes" subtitle="Aportes recibidos y pendientes de clasificar." items={['Los aportes se reflejan desde las solicitudes orgánicas.', 'Las cantidades se confirman al recibir cada material.']} action="Revisar solicitudes orgánicas" onAction={() => onSection('requests')}/>
  if (role === 'kelly' && section === 'redemptions') return <InfoSection title="Canjes del huerto" description="Los productos, existencias y equivalencias de canje se mostrarán cuando la Fundación configure el catálogo y la regla de puntos." badge="Catálogo pendiente"/>
  if (role === 'admin') return <AdminSection section={section} requests={allRequests} onNotify={onNotify}/>
  return <InfoSection title={roleInfo[role].title} description="Este módulo se habilitará cuando el equipo confirme sus datos y el backend publique el contrato correspondiente." badge="En preparación" />
}

function AdminSection({ section, requests, onNotify }: { section: Section; requests: CollectionRequest[]; onNotify: (message: string) => void }) {
  if (section === 'home') return <div className="admin-grid"><div className="metric-card"><span>Solicitudes de demostración</span><strong>{requests.length}</strong><small>Datos temporales en este navegador</small></div><div className="metric-card"><span>Flujo orgánico</span><strong>{requests.filter((item) => item.flow === 'ORGANIC').length}</strong><small>Coordinación de huerta</small></div><div className="metric-card"><span>Flujo reciclable</span><strong>{requests.filter((item) => item.flow === 'RECYCLABLE').length}</strong><small>Coordinación de reciclaje</small></div><div className="admin-shortcuts"><h2>Herramientas de administración</h2><p>Gestiona cada módulo desde la navegación.</p><span>Usuarios · eventos · materiales · puntos · reportes</span></div></div>
  if (section === 'points') return <PointsConfiguration onNotify={onNotify}/>
  if (section === 'users') return <AdminUsersDemo onNotify={onNotify}/>
  if (section === 'events') return <AdminEventsDemo onNotify={onNotify}/>
  if (section === 'catalog') return <AdminMaterialsDemo onNotify={onNotify}/>
  if (section === 'reports') return <AdminReportsDemo requests={requests}/>
  const contents: Record<string, { title: string; description: string; items: string[] }> = {
    needs: { title: 'Administración', description: 'Selecciona un módulo desde la navegación.', items: [] },
  }
  const data = contents[section] ?? contents.needs
  return <OperationPanel title={data.title} subtitle={data.description} items={data.items} action="Entendido" onAction={() => onNotify('Los cambios administrativos estarán disponibles al definir el contrato backend.')}/>
}

function AdminUsersDemo({ onNotify }: { onNotify: (message: string) => void }) {
  const [users, setUsers] = useState<{ id: number; name: string; role: Role }[]>([])
  const [name, setName] = useState('')
  const [role, setRole] = useState<Role>('neighbor')
  function addUser(event: FormEvent) { event.preventDefault(); if (!name.trim()) return; setUsers((current) => [...current, { id: Date.now(), name: name.trim(), role }]); setName(''); onNotify('Usuario de prueba añadido solo a esta demostración.') }
  return <section className="admin-workspace"><div className="admin-panel-intro"><p className="eyebrow">ADMINISTRACIÓN · DEMOSTRACIÓN</p><h2>Usuarios y roles</h2><p>Administra registros de prueba en esta vista. La lista real y los cambios de roles requieren la API y permisos de backend.</p></div><form className="admin-inline-form" onSubmit={addUser}><label>Nombre de prueba<input value={name} onChange={(event) => setName(event.target.value)} placeholder="Escribe un nombre" required/></label><label>Rol<select value={role} onChange={(event) => setRole(event.target.value as Role)}>{roleOptions.map((option) => <option key={option} value={option}>{roleInfo[option].name}</option>)}</select></label><button className="button button-primary" type="submit">＋ Añadir registro</button></form>{users.length ? <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Usuario</th><th>Rol</th><th>Alcance</th></tr></thead><tbody>{users.map((user) => <tr key={user.id}><td>{user.name}<small>Registro de prueba</small></td><td><select aria-label={`Rol de ${user.name}`} value={user.role} onChange={(event) => { const nextRole = event.target.value as Role; setUsers((current) => current.map((row) => row.id === user.id ? { ...row, role: nextRole } : row)); onNotify('Rol simulado actualizado solo en esta vista.') }}>{roleOptions.map((option) => <option key={option} value={option}>{roleInfo[option].name}</option>)}</select></td><td>Sin permisos reales</td></tr>)}</tbody></table></div> : <div className="admin-empty"><strong>No hay usuarios de prueba agregados</strong><span>Los usuarios registrados se cargarán al conectar la API.</span></div>}</section>
}

function AdminEventsDemo({ onNotify }: { onNotify: (message: string) => void }) {
  const [events, setEvents] = useState<{ id: number; title: string; date: string; description: string }[]>([])
  const [title, setTitle] = useState('')
  const [date, setDate] = useState('')
  const [description, setDescription] = useState('')
  const todayParts = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Bogota', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date())
  const today = `${todayParts.find((part) => part.type === 'year')?.value}-${todayParts.find((part) => part.type === 'month')?.value}-${todayParts.find((part) => part.type === 'day')?.value}`
  function addEvent(event: FormEvent) { event.preventDefault(); if (!title.trim() || !date) return; setEvents((current) => [...current, { id: Date.now(), title: title.trim(), date, description: description.trim() }].sort((a, b) => a.date.localeCompare(b.date))); setTitle(''); setDate(''); setDescription(''); onNotify('Evento de prueba agregado solo a esta demostración.') }
  return <section className="admin-workspace"><div className="admin-panel-intro"><p className="eyebrow">AGENDA COMUNITARIA · DEMOSTRACIÓN</p><h2>Eventos próximos</h2><p>Agrega eventos confirmados para probar la vista. No se publica ni se avisa a la comunidad desde este formulario.</p></div><form className="admin-inline-form admin-event-form" onSubmit={addEvent}><label>Nombre del evento<input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Nombre confirmado" required/></label><label>Fecha<input type="date" min={today} value={date} onChange={(event) => setDate(event.target.value)} required/></label><label>Descripción<input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Información opcional"/></label><button className="button button-primary" type="submit">＋ Añadir borrador</button></form>{events.length ? <div className="admin-record-list">{events.map((event) => <article key={event.id}><div className="event-date"><strong>{new Date(`${event.date}T12:00:00`).toLocaleDateString('es-CO', { day: '2-digit' })}</strong><span>{new Date(`${event.date}T12:00:00`).toLocaleDateString('es-CO', { month: 'short' })}</span></div><div><strong>{event.title}</strong><small>{event.description || 'Sin descripción añadida'}</small></div><button className="text-button" onClick={() => { setEvents((current) => current.filter((row) => row.id !== event.id)); onNotify('Borrador de evento retirado de la demostración.') }}>Quitar</button></article>)}</div> : <div className="admin-empty"><strong>No hay eventos próximos cargados</strong><span>El calendario oficial se mostrará al conectar la API de eventos.</span></div>}</section>
}

function AdminMaterialsDemo({ onNotify }: { onNotify: (message: string) => void }) {
  const [materials, setMaterials] = useState<{ id: number; name: string; flow: NewRequest['flow']; unit: string }[]>([])
  const [name, setName] = useState('')
  const [flow, setFlow] = useState<NewRequest['flow']>('RECYCLABLE')
  const [unit, setUnit] = useState('')
  function addMaterial(event: FormEvent) { event.preventDefault(); if (!name.trim() || !unit.trim()) return; setMaterials((current) => [...current, { id: Date.now(), name: name.trim(), flow, unit: unit.trim() }]); setName(''); setUnit(''); onNotify('Material de prueba añadido solo a esta demostración.') }
  return <section className="admin-workspace"><div className="admin-panel-intro"><p className="eyebrow">CATÁLOGO · DEMOSTRACIÓN</p><h2>Materiales disponibles</h2><p>Prueba la captura del catálogo. La lista oficial, unidades y activación se administran en backend.</p></div><form className="admin-inline-form" onSubmit={addMaterial}><label>Material<input value={name} onChange={(event) => setName(event.target.value)} placeholder="Nombre definido por el equipo" required/></label><label>Flujo<select value={flow} onChange={(event) => setFlow(event.target.value as NewRequest['flow'])}><option value="RECYCLABLE">Reciclable</option><option value="ORGANIC">Orgánico · huerta</option></select></label><label>Unidad oficial<input value={unit} onChange={(event) => setUnit(event.target.value)} placeholder="Unidad por confirmar" required/></label><button className="button button-primary" type="submit">＋ Añadir borrador</button></form>{materials.length ? <div className="admin-record-list">{materials.map((item) => <article key={item.id}><span className={`flow-label ${item.flow === 'ORGANIC' ? 'flow-label-green' : ''}`}>{item.flow === 'ORGANIC' ? 'Orgánico' : 'Reciclable'}</span><div><strong>{item.name}</strong><small>Unidad indicada: {item.unit}</small></div><button className="text-button" onClick={() => { setMaterials((current) => current.filter((row) => row.id !== item.id)); onNotify('Borrador de material retirado de la demostración.') }}>Quitar</button></article>)}</div> : <div className="admin-empty"><strong>No hay materiales de prueba agregados</strong><span>El catálogo oficial aparecerá cuando esté configurado.</span></div>}</section>
}

function AdminReportsDemo({ requests }: { requests: CollectionRequest[] }) {
  const statuses = ['RECEIVED', 'UNDER_REVIEW', 'ASSIGNED', 'SCHEDULED', 'COLLECTED', 'COMPLETED', 'CANCELLED'] as const
  const labels: Record<typeof statuses[number], string> = { RECEIVED: 'Recibidas', UNDER_REVIEW: 'En revisión', ASSIGNED: 'Asignadas', SCHEDULED: 'Programadas', COLLECTED: 'Recolectadas', COMPLETED: 'Verificadas', CANCELLED: 'Canceladas' }
  const peak = Math.max(1, ...statuses.map((status) => requests.filter((item) => item.status === status).length))
  return <section className="admin-workspace"><div className="admin-panel-intro"><p className="eyebrow">SEGUIMIENTO · DATOS DE DEMOSTRACIÓN</p><h2>Actividad del proyecto</h2><p>Resumen de solicitudes sintéticas que están en la memoria del navegador.</p></div><div className="report-summary"><article><span>Solicitudes registradas</span><strong>{requests.length}</strong></article><article><span>Flujos orgánicos</span><strong>{requests.filter((item) => item.flow === 'ORGANIC').length}</strong></article><article><span>Flujos reciclables</span><strong>{requests.filter((item) => item.flow === 'RECYCLABLE').length}</strong></article></div><div className="report-status-list">{statuses.map((status) => { const count = requests.filter((item) => item.status === status).length; return <div key={status}><span>{labels[status]}</span><div className="report-bar"><i style={{ width: `${count / peak * 100}%` }}/></div><strong>{count}</strong></div> })}</div></section>
}

function PointsConfiguration({ onNotify }: { onNotify: (message: string) => void }) {
  const [materials, setMaterials] = useState<MaterialPointsRuleDraft[]>([{ id: 1, materialName: '', pointsPerKg: '' }])
  const [organicRule, setOrganicRule] = useState<PointsRuleDraft>({ pointsPerKg: '' })
  const [savedDraft, setSavedDraft] = useState(false)
  return <div className="points-config"><div className="points-config-intro"><p className="eyebrow">CONFIGURACIÓN ADMINISTRATIVA · DEMOSTRACIÓN</p><h2>Estándares de puntos por peso</h2><p>Define las equivalencias aprobadas por la Fundación. Los valores se mantienen vacíos hasta que sean definidos y no se publican al backend desde esta demo.</p></div><form onSubmit={(event) => { event.preventDefault(); setSavedDraft(true); onNotify('Borrador retenido en esta vista durante la demostración; no se actualizó el backend.') }}><section className="rule-editor"><div><span className="flow-label flow-label-green">HUERTA · ORGÁNICOS</span><h3>Aporte orgánico</h3><p>Establece cuántos puntos corresponden a cada kilogramo de aporte orgánico.</p></div><label className="rule-input">Puntos por kg<input type="number" min="0.000001" max="999999.999999" step="0.000001" placeholder="Sin definir" value={organicRule.pointsPerKg} onChange={(event) => { setOrganicRule({ pointsPerKg: event.target.value }); setSavedDraft(false) }}/><small>Sin equivalencia oficial configurada.</small></label></section><section className="rule-editor rule-editor-materials"><div><span className="flow-label">RECICLADORES · RECICLABLES</span><h3>Regla por material</h3><p>Añade cada material y su tarifa una vez se apruebe el catálogo oficial.</p></div><div className="material-rule-list">{materials.map((material) => <div className="material-rule-row" key={material.id}><label>Material<input placeholder="Nombre por definir" value={material.materialName} onChange={(event) => { setSavedDraft(false); setMaterials((rows) => rows.map((row) => row.id === material.id ? { ...row, materialName: event.target.value } : row)) }}/></label><label className="rule-rate-label">Puntos por kg<input type="number" min="0.000001" max="999999.999999" step="0.000001" placeholder="Sin definir" value={material.pointsPerKg} onChange={(event) => { setSavedDraft(false); setMaterials((rows) => rows.map((row) => row.id === material.id ? { ...row, pointsPerKg: event.target.value } : row)) }}/></label></div>)}<button type="button" className="text-button" onClick={() => { setSavedDraft(false); setMaterials((rows) => [...rows, { id: Date.now(), materialName: '', pointsPerKg: '' }]) }}>＋ Agregar material</button></div></section><div className="rule-form-footer"><span>{savedDraft ? 'Borrador guardado en esta vista · solo demostración' : 'Sin valores oficiales configurados · no se publica al backend'}</span><button type="submit" className="button button-primary">Guardar borrador</button></div></form></div>
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
