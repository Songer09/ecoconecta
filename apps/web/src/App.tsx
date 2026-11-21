import { useEffect, useMemo, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { useRef } from 'react'
import * as L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { CollectionRequest, MaterialPointsRuleDraft, NewRequest, PointsRuleDraft, Role } from './domain/types'
import { service } from './services/service'
import { Brand } from './components/Brand'
import { StatusPill } from './components/StatusPill'
import { DemoTag } from './components/DemoTag'
import { EmptyState, InfoSection, OperationPanel } from './components/PanelStates'
import { attachDemoRequestPhoto, getDemoRequestPhoto } from './services/demo/requestAttachments'
import { ApiRequestError, authApi } from './services/authApi'
import { CoordinatorDirectory } from './components/CoordinatorDirectory'
import { CommunityFooter, VillasStorySection } from './components/LandingSections'
import { EducationContent } from './components/EducationContent'
import { GardenRedemptions } from './components/GardenRedemptions'
import { CommunityEvents } from './components/CommunityEvents'
import { MascotProvider, useMascotActions, useMascotHidden, useMascotReminderBlock, useMascotScene } from './components/mascot/MascotContext'
import { MascotDock } from './components/mascot/MascotDock'
import type { MascotMessage, MascotView } from './components/mascot/mascotMessages'

type View = MascotView
type Session = Awaited<ReturnType<typeof authApi.login>>
type Section = 'home' | 'requests' | 'history' | 'new' | 'points' | 'learning' | 'events' | 'profile' | 'routes' | 'materials' | 'income' | 'needs' | 'inventory' | 'redemptions' | 'users' | 'catalog' | 'reports' | 'team'
type NeighborProfile = { fullName: string; phone: string; stage: string; neighborhood: string; tower: string; apartment: string }
const emptyNeighborProfile: NeighborProfile = { fullName: '', phone: '', stage: '', neighborhood: '', tower: '', apartment: '' }

function scrollScreenToTop() {
  document.querySelector('.mascot-screen')?.scrollTo(0, 0)
}

const roleInfo: Record<Role, { name: string; title: string; description: string }> = {
  neighbor: { name: 'Vecino', title: 'Tu hogar también transforma', description: 'Solicita una recolección, aprende y sigue tus aportes.' },
  collector: { name: 'Recolector', title: 'Tu jornada, más clara', description: 'Consulta tus asignaciones y registra cada recolección.' },
  vivi: { name: 'Coordinador de recicladores', title: 'Gestión de reciclables', description: 'Organiza solicitudes, ubicaciones, rutas e historial de materiales reciclables.' },
  kelly: { name: 'Coordinador de huerteros', title: 'Gestión de la huerta comunitaria', description: 'Revisa solicitudes orgánicas, asigna huerteros y consulta las necesidades de la huerta.' },
  admin: { name: 'Administrador', title: 'Gestión de EcoConecta', description: 'Administra las herramientas comunitarias del sistema.' },
}

const navByRole: Record<Role, { id: Section; label: string }[]> = {
  neighbor: [{ id: 'new', label: 'Pedir' }, { id: 'points', label: 'Canjear' }, { id: 'events', label: 'Eventos' }, { id: 'learning', label: 'Aprender' }, { id: 'profile', label: 'Mi perfil' }],
  collector: [{ id: 'home', label: 'Mi jornada' }, { id: 'routes', label: 'Ruta' }, { id: 'requests', label: 'Historial' }, { id: 'profile', label: 'Mi perfil' }],
  vivi: [{ id: 'home', label: 'Solicitudes' }, { id: 'requests', label: 'Historial' }, { id: 'income', label: 'Cuánto he ganado' }],
  kelly: [{ id: 'home', label: 'Solicitudes' }, { id: 'history', label: 'Historial' }, { id: 'inventory', label: 'Inventario faltante' }, { id: 'redemptions', label: 'Canjes' }, { id: 'team', label: 'Directorio' }],
  admin: [{ id: 'home', label: 'Resumen' }, { id: 'users', label: 'Usuarios y roles' }, { id: 'events', label: 'Eventos' }, { id: 'catalog', label: 'Materiales' }, { id: 'points', label: 'Configuración de puntos' }, { id: 'reports', label: 'Métricas y reportes' }],
}

const roleOptions: Role[] = ['neighbor', 'collector', 'vivi', 'kelly', 'admin']

function RoleIcon({ role }: { role: Role }) {
  const paths: Record<Role, string> = {
    neighbor: 'M3 11.5 12 4l9 7.5M5.5 10v10h13V10M9 20v-6h6v6',
    collector: 'M12 3v5m0-5 3 3m-3-3-3 3M5.5 10A8 8 0 1 0 19 7M4 6l1.5 4L9 8',
    vivi: 'M12 3v18m0-18 6 3-6 3m0 2-6 3 6 3m0 2 6 3-6 3',
    kelly: 'M12 21v-9m0 3c-5 0-7-3-7-7 5 0 7 3 7 7Zm0-3c0-5 3-7 7-7 0 5-2 7-7 7Z',
    admin: 'M12 3 20 6v5c0 5-3.5 8.5-8 11-4.5-2.5-8-6-8-11V6l8-3Zm-3 9 2 2 4-4',
  }
  return <svg className="role-icon" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d={paths[role]}/></svg>
}

function SiteHeader({ onHome, onEducation, onEvents, active, tools }: { onHome: () => void; onEducation: () => void; onEvents: () => void; active?: 'education' | 'events'; tools?: ReactNode }) {
  const whatsappUrl = import.meta.env.VITE_ECOCONECTA_WHATSAPP_URL?.trim()
  const whatsappLabel = <><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M20.8 11.9a8.8 8.8 0 0 1-13 7.7l-4.5 1.2 1.2-4.4a8.8 8.8 0 1 1 16.3-4.5Z"/><path d="M8.6 7.7h1l1.1 2.5-.9 1c.7 1.5 1.8 2.5 3.2 3.2l1-1 2.4 1.1v1c0 .6-.8 1.2-1.5 1.2-3.6-.3-7.1-3.7-7.4-7.4 0-.7.5-1.6 1.1-1.6Z"/></svg>WhatsApp</>
  return <header className="site-header">
    <button className="site-brand-button" onClick={onHome} aria-label="Volver al inicio"><Brand/></button>
    <nav className="site-header-nav" aria-label="Navegación del sitio">
      <button className="site-home-button" onClick={onHome} aria-label="Inicio" title="Inicio"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1V10Z"/></svg></button>
      <button className={active === 'education' ? 'site-nav-active' : ''} data-mascot-target="education" onClick={onEducation}>Educación</button>
      <button className={active === 'events' ? 'site-nav-active' : ''} data-mascot-target="events" onClick={onEvents}>Eventos</button>
    </nav>
    <div className="site-header-actions">
      {whatsappUrl ? <a className="site-whatsapp" href={whatsappUrl} target="_blank" rel="noopener noreferrer">{whatsappLabel}</a>
        : <button type="button" className="site-whatsapp" title="WhatsApp estará disponible próximamente" disabled>{whatsappLabel}</button>}
      {tools && <div className="site-header-tools">{tools}</div>}
    </div>
  </header>
}

function Welcome({ onHome, onRole, onDemo, onLearn, onEvents, onPanel }: { onHome: () => void; onRole: (role: Role) => void; onDemo?: () => void; onLearn: () => void; onEvents: () => void; onPanel?: () => void }) {
  return <main className="welcome-page">
    <SiteHeader onHome={onHome} onEducation={onLearn} onEvents={onEvents} tools={onPanel && <button className="button button-secondary" onClick={onPanel}>Mi panel</button>}/>
    <div className="welcome-grid">
      <section className="welcome-copy">
        <p className="eyebrow">BIENVENIDO</p>
        <h1>Bienvenido a <em>EcoConecta</em></h1>
        <p className="welcome-lede">Selecciona tu perfil para iniciar sesión.</p>
        <section className="role-picker" id="roles">
          <div className="role-picker-heading"><div><p className="eyebrow">ACCESO A ECOCONECTA</p><h2>Elige tu rol</h2></div></div>
          <div className="role-grid">
            {roleOptions.map((role) => <button key={role} className="role-card" data-mascot-target={role === 'neighbor' ? 'welcome-role' : undefined} onClick={() => onRole(role)}><span className={`role-avatar avatar-${role}`}><RoleIcon role={role}/></span><span className="role-copy"><strong>{roleInfo[role].name}</strong></span><span className="role-arrow" aria-hidden="true">↗</span></button>)}
          </div>
          {onDemo && <div className="welcome-actions"><button className="button button-secondary welcome-demo-button" onClick={onDemo}>Ver demostración</button></div>}
        </section>
      </section>
      <aside className="welcome-aside" aria-label="Accesos directos">
        <button className="welcome-resource-card education-resource" onClick={onLearn}><img src="/images/education-community.jpeg" alt="Personas participando en la huerta comunitaria"/><span className="resource-action"><span><small>APRENDIZAJE AMBIENTAL</small><strong>Educación</strong></span><b aria-hidden="true">→</b></span></button>
        <button className="welcome-resource-card events-resource" onClick={onEvents}><img src="/images/community-events.jpg" alt="Actividad comunitaria en Villas de San Pablo"/><span className="resource-action"><span><small>AGENDA COMUNITARIA</small><strong>Eventos</strong></span><b aria-hidden="true">→</b></span></button>
      </aside>
    </div>
    <VillasStorySection/>
    <CommunityFooter/>
  </main>
}

function DemoRolePicker({ onBack, onEducation, onEvents, onChoose }: { onBack: () => void; onEducation: () => void; onEvents: () => void; onChoose: (role: Role) => void }) {
  return <main className="demo-role-page">
    <SiteHeader onHome={onBack} onEducation={onEducation} onEvents={onEvents}/>
    <section className="demo-role-content">
      <p className="eyebrow">RECORRIDO SIN INICIAR SESIÓN</p>
      <h1>Explora las pantallas</h1>
      <p>Abre cada perfil con datos de demostración. No crea cuentas ni cambia información real.</p>
      <div className="role-grid demo-role-grid">{roleOptions.map((role) => <button key={role} className="role-card" onClick={() => onChoose(role)}><span className={`role-avatar avatar-${role}`}><RoleIcon role={role}/></span><span className="role-copy"><strong>{roleInfo[role].name}</strong></span><span className="role-arrow" aria-hidden="true">↗</span></button>)}</div>
      <p className="demo-role-footnote"><DemoTag/></p>
    </section>
  </main>
}

function LoginScreen({ role, forEducation, onHome, onEducation, onEvents, onRegister, onSuccess }: { role: Role; forEducation: boolean; onHome: () => void; onEducation: () => void; onEvents: () => void; onRegister: () => void; onSuccess: (session: Session, phone: string) => void }) {
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [mascotIssue, setMascotIssue] = useState<MascotMessage>()
  useMascotScene(busy ? 'loginLoading' : mascotIssue)
  const canRegister = role === 'neighbor' || role === 'collector'
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setMessage('')
    setMascotIssue(undefined)
    setBusy(true)
    try {
      const session = await authApi.login({ phone: phone.trim(), password })
      if (!forEducation && session.role !== role) {
        await authApi.logout()
        setMessage(`Esta cuenta pertenece al perfil “${roleInfo[session.role].name}”. Elige ese perfil para continuar.`)
        setMascotIssue('loginInvalid')
        return
      }
      onSuccess(session, phone.trim())
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo iniciar sesión.')
      setMascotIssue(error instanceof ApiRequestError && error.status >= 400 && error.status < 500 ? 'loginInvalid' : 'loginFailed')
    } finally {
      setBusy(false)
    }
  }
  return <main className="login-page">
    <SiteHeader onHome={onHome} onEducation={onEducation} onEvents={onEvents} active={forEducation ? 'education' : undefined}/>
    <section className="login-card">
      <div className={`role-avatar avatar-${role}`}><RoleIcon role={role}/></div>
      <p className="eyebrow">INICIO DE SESIÓN</p>
      <h1>{forEducation ? 'Ingresa a Educación' : roleInfo[role].name}</h1>
      {forEducation && <p className="login-description">Inicia sesión para guardar los temas que completes y continuar desde donde quedaste.</p>}
      <form className="login-form" onSubmit={submit} onInvalid={() => setMascotIssue('loginInvalid')} onInput={() => setMascotIssue(undefined)}>
        <label>Teléfono con indicativo internacional<input type="tel" name="phone" autoComplete="username" inputMode="tel" pattern="\+[1-9][0-9]{6,14}" placeholder="+573001234567" value={phone} onChange={(event) => setPhone(event.target.value)} required/></label>
        <label>Contraseña<input type="password" name="password" autoComplete="current-password" placeholder="Ingresa tu contraseña" value={password} onChange={(event) => setPassword(event.target.value)} required/></label>
        <div className={canRegister ? 'login-actions login-actions-split' : 'login-actions'}>
          <button className="button button-primary" type="submit" disabled={busy}>{busy ? 'Verificando…' : 'Iniciar sesión'}</button>
          {canRegister && <button className="button button-secondary" type="button" disabled={busy} onClick={onRegister}>Registrarse</button>}
        </div>
      </form>
      {message && <p className="login-api-notice" role="alert">{message}</p>}
      {canRegister && <p className="login-help">¿No tienes cuenta? <button type="button" className="inline-register-link" disabled={busy} onClick={onRegister}>Regístrate aquí</button></p>}
      <p className="login-help">El teléfono debe incluir + y el indicativo del país.</p>
    </section>
  </main>
}

function RegistrationScreen({ collector, onHome, onEducation, onEvents, onLogin, onSuccess }: { collector: boolean; onHome: () => void; onEducation: () => void; onEvents: () => void; onLogin: () => void; onSuccess: (session: Session, profile: NeighborProfile) => void }) {
  const [fullName, setFullName] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [stage, setStage] = useState('')
  const [neighborhood, setNeighborhood] = useState('')
  const [tower, setTower] = useState('')
  const [apartment, setApartment] = useState('')
  const [dataTreatmentAccepted, setDataTreatmentAccepted] = useState(false)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [accountCreated, setAccountCreated] = useState(false)
  const [mascotIssue, setMascotIssue] = useState<MascotMessage>()
  const { showMoment } = useMascotActions()
  useMascotScene(accountCreated ? (collector ? 'collectorRegistered' : 'registerCreated') : busy ? 'registerLoading' : mascotIssue)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setMessage('')
    setMascotIssue(undefined)
    if (password !== confirmPassword) { setMessage('Las contraseñas no coinciden.'); setMascotIssue('registerInvalid'); return }
    if (!dataTreatmentAccepted) { setMessage('Debes autorizar el tratamiento de datos para crear tu cuenta.'); setMascotIssue('registerInvalid'); return }
    setBusy(true)
    let created = false
    try {
      if (collector) {
        await authApi.registerCollector({ full_name: fullName.trim(), phone: phone.trim(), password, data_treatment_accepted: true })
        setAccountCreated(true)
        setMessage('Recibimos tu registro. Podrás iniciar sesión cuando administración active tu cuenta.')
        showMoment('collectorRegistered')
        return
      }
      await authApi.registerResident({
        full_name: fullName.trim(), phone: phone.trim(), password,
        stage: stage.trim(), neighborhood: neighborhood.trim(), tower: tower.trim(), apartment: apartment.trim(),
        data_treatment_accepted: true,
      })
      created = true
      setAccountCreated(true)
      const session = await authApi.login({ phone: phone.trim(), password })
      if (session.role !== 'neighbor') throw new Error('La cuenta se creó, pero no tiene el perfil de vecino esperado.')
      onSuccess(session, { fullName: fullName.trim(), phone: phone.trim(), stage: stage.trim(), neighborhood: neighborhood.trim(), tower: tower.trim(), apartment: apartment.trim() })
      showMoment('registerCreated')
    } catch (error) {
      if (created) showMoment('registerCreated')
      else setMascotIssue(error instanceof ApiRequestError && error.status >= 400 && error.status < 500 ? 'registerInvalid' : 'registerFailed')
      setMessage(created
        ? 'Tu cuenta quedó creada y activa. Inicia sesión con el teléfono y la contraseña que registraste.'
        : error instanceof Error ? error.message : 'No se pudo completar el registro.')
    } finally { setBusy(false) }
  }

  return <main className="register-page">
    <SiteHeader onHome={onHome} onEducation={onEducation} onEvents={onEvents}/>
    <section className="register-card">
      <h1>Registro de {collector ? 'recolector' : 'vecino'}</h1>
      <p className="register-description">{collector ? 'Crea tu cuenta. Administración revisará el registro y asignará tus zonas de recolección.' : 'Crea tu cuenta para solicitar recolecciones y participar en tu comunidad.'}</p>
      {accountCreated ? <><p className="register-success" role="status">{message}</p><button type="button" className="button button-primary" onClick={collector ? onHome : onLogin}>{collector ? 'Volver al inicio' : 'Ir a iniciar sesión'}</button></> : <form className="register-form" onSubmit={submit} onInvalid={() => setMascotIssue('registerInvalid')} onInput={() => setMascotIssue(undefined)}>
        <label>Nombre completo<input autoComplete="name" maxLength={200} value={fullName} onChange={(event) => setFullName(event.target.value)} required/></label>
        <label>Celular con indicativo internacional<input type="tel" inputMode="tel" autoComplete="tel" pattern="\+[1-9][0-9]{6,14}" placeholder="+573001234567" value={phone} onChange={(event) => setPhone(event.target.value)} required/></label>
        {!collector && <div className="address-grid resident-address-grid">
          <label>Etapa<input maxLength={80} placeholder="Ej. Etapa 4" value={stage} onChange={(event) => setStage(event.target.value)} required/></label>
          <label className="wide-field">Conjunto<input maxLength={120} autoComplete="address-line1" value={neighborhood} onChange={(event) => setNeighborhood(event.target.value)} required/></label>
          <label>Torre<input maxLength={30} value={tower} onChange={(event) => setTower(event.target.value)} required/></label>
          <label>Apartamento<input maxLength={30} value={apartment} onChange={(event) => setApartment(event.target.value)} required/></label>
        </div>}
        <label>Contraseña<input type="password" minLength={12} maxLength={256} autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} required/><small>Usa al menos 12 caracteres.</small></label>
        <label>Confirma tu contraseña<input type="password" minLength={12} maxLength={256} autoComplete="new-password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required/></label>
        <label className="register-consent"><input type="checkbox" checked={dataTreatmentAccepted} onChange={(event) => setDataTreatmentAccepted(event.target.checked)} required/><span><strong>Autorizo el tratamiento de mis datos personales.</strong> {collector ? 'Se usarán para revisar mi registro y gestionar mi participación en las recolecciones.' : 'Se usarán para gestionar mis solicitudes, registrar los puntos que correspondan y enviarme avisos operativos o comunitarios.'} <a href="https://fundacionsantodomingo.org/conocenos/politica-de-proteccion-de-datos/" target="_blank" rel="noreferrer">Consulta la política de protección de datos.</a></span></label>
        {message && <p className="login-api-notice" role="alert">{message}</p>}
        <button className="button button-primary" type="submit" disabled={busy}>{busy ? 'Enviando registro…' : collector ? 'Enviar registro' : 'Crear mi cuenta'}</button>
      </form>}
      <p className="login-help">¿Ya tienes una cuenta? <button type="button" className="inline-register-link" onClick={onLogin}>Inicia sesión</button></p>
    </section>
  </main>
}

const demoMapStops: { position: L.LatLngTuple; area: string }[] = [
  { position: [10.95997, -74.86312], area: 'Sector del Centro de Integración Ciudadana' },
  { position: [10.95948, -74.86214], area: 'Sector residencial de Villas de San Pablo' },
  { position: [10.95931, -74.86101], area: 'Sector del Mega Colegio' },
]

function RealCommunityMap({ demo }: { demo: boolean }) {
  const element = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!element.current) return
    const center: L.LatLngExpression = [10.95885, -74.8631]
    const map = L.map(element.current, { scrollWheelZoom: false }).setView(center, 15)
    const tileUrl = import.meta.env.VITE_OSM_TILE_URL || 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
    L.tileLayer(tileUrl, { maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors' }).addTo(map)
    if (demo) {
      const route = L.polyline(demoMapStops.map(({ position }) => position), {
        color: '#155987', weight: 5, dashArray: '10 8',
      }).addTo(map)
      map.fitBounds(route.getBounds(), { padding: [52, 52], maxZoom: 17, animate: false })
      demoMapStops.forEach(({ position, area }, index) => {
        const label = `Parada ficticia ${index + 1}: ${area}`
        const marker = L.divIcon({
          className: 'demo-map-stop', html: String(index + 1), iconSize: [34, 34], iconAnchor: [17, 17], popupAnchor: [0, -14],
        })
        L.marker(position, { icon: marker, title: label, alt: label })
          .addTo(map)
          .bindPopup(label)
      })
    } else {
      L.circleMarker(center, { radius: 9, color: '#FFFFFF', weight: 3, fillColor: '#168A2E', fillOpacity: 1 })
        .addTo(map).bindPopup('Centro aproximado de Villas de San Pablo')
    }
    const resize = window.setTimeout(() => map.invalidateSize({ pan: false }), 0)
    return () => { window.clearTimeout(resize); map.remove() }
  }, [demo])
  return <div className="community-map-frame">
    <div ref={element} className="real-community-map" role="application" aria-label={demo ? 'Ruta de ejemplo con tres paradas ficticias en Villas de San Pablo' : 'Mapa de OpenStreetMap centrado en Villas de San Pablo'}/>
    {demo && <div className="demo-map-legend"><strong>Ruta de ejemplo</strong><span>3 paradas ficticias</span></div>}
  </div>
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
  useMascotScene(step === 1 ? 'pickupPhoto' : step === 2 ? 'pickupMaterials' : 'pickupAddress')
  useMascotReminderBlock(Boolean(error))
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
    if (!photo) { setStep(1); setError('Agrega una foto para continuar.'); return }
    if (!materials.length) { setStep(2); setError('Elige al menos un material.'); return }
    if (!neighborhood.trim() || !tower.trim() || !apartment.trim()) { setError('Completa conjunto, torre y apartamento para que puedan encontrarte.'); return }
    const created = await service.createRequest({ flow, stage, neighborhood: neighborhood.trim(), tower: tower.trim(), apartment: apartment.trim(), materials, availability, note: note.trim() })
    if (photo) attachDemoRequestPhoto(created.id, photo)
    onCreated(created)
  }
  return <section className="form-card resident-request-form"><div className="form-heading"><div><p className="eyebrow">VILLAS DE SAN PABLO</p><h1>{step === 1 ? 'Pedir recolección' : step === 2 ? '¿Qué vas a entregar?' : '¿Dónde podemos recogerlo?'}</h1></div><button className="icon-button" onClick={onCancel} aria-label="Cerrar formulario">×</button></div>
    <div className="resident-request-progress" data-mascot-target="pickup-progress"><span>Paso {step} de 3</span><span>{step === 1 ? 'Fotos' : step === 2 ? 'Materiales' : 'Dirección'}</span><i><b style={{ width: `${step / 3 * 100}%` }}/></i></div>
    {step === 1 ? <label className="photo-dropzone" data-mascot-target="pickup-photo"><span className="photo-camera-icon" aria-hidden="true">◎</span>{photoPreview ? <img className="request-photo-preview" src={photoPreview} alt="Vista previa de tus residuos"/> : <><strong>Muéstranos tus residuos</strong><span>Toma una foto clara. Así podremos enviarlos al lugar correcto.</span></>}<input type="file" accept="image/jpeg,image/png" capture="environment" onChange={(event) => selectPhoto(event.target.files?.[0] ?? null)}/><b className="button button-primary">◎ {photo ? 'Cambiar foto' : 'Tomar foto'}</b></label> : step === 2 ? <><div className="flow-choice"><button className={flow === 'RECYCLABLE' ? 'flow-option selected' : 'flow-option'} onClick={() => { setFlow('RECYCLABLE'); setMaterials([]) }}><strong>Reciclables</strong><small>Papel, cartón, envases y más</small></button><button className={flow === 'ORGANIC' ? 'flow-option selected flow-organic' : 'flow-option'} onClick={() => { setFlow('ORGANIC'); setMaterials([]) }}><strong>Orgánicos</strong><small>Aportes para la huerta comunitaria</small></button></div><fieldset className="material-fieldset"><legend>¿Qué vas a entregar?</legend><div className="material-options">{options.map((item) => <button type="button" key={item} className={materials.includes(item) ? 'material-chip chosen' : 'material-chip'} onClick={() => selectMaterial(item)} aria-pressed={materials.includes(item)}>{materials.includes(item) ? '✓ ' : '+ '}{item}</button>)}</div></fieldset></> : <><p className="form-hint">La dirección se comparte con el equipo que atiende tu solicitud.</p><div className="address-grid"><label>Etapa<select value={stage} onChange={(event) => setStage(event.target.value)}><option>Etapa 4</option><option>Etapa 5</option><option>Etapa 6</option><option>Etapa 7</option></select></label><label className="wide-field">Conjunto<input value={neighborhood} onChange={(event) => setNeighborhood(event.target.value)} placeholder="Nombre del conjunto" autoComplete="address-line1" required/></label><label>Torre<input value={tower} onChange={(event) => setTower(event.target.value)} placeholder="Ej. 2" required/></label><label>Apartamento<input value={apartment} onChange={(event) => setApartment(event.target.value)} placeholder="Ej. 304" required/></label><label className="wide-field">¿Cuándo estás disponible?<select value={availability} onChange={(event) => setAvailability(event.target.value)}><option>Hoy en la tarde</option><option>Mañana en la mañana</option><option>Mañana en la tarde</option><option>Coordinar por teléfono</option></select></label><label className="wide-field">Nota para el equipo <span className="optional">(opcional)</span><textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder="Algo que debamos saber" rows={2}/></label></div></>}
    {error && <p className="form-error" role="alert">{error}</p>}
    <div className="form-actions"><button className="button button-secondary" onClick={step === 1 ? onCancel : () => { setStep(step - 1); setError('') }}>{step === 1 ? 'Cancelar' : 'Atrás'}</button><button className="button button-primary" data-mascot-target={step === 1 ? 'pickup-next' : undefined} onClick={() => { setError(''); if (step === 1) photo ? setStep(2) : setError('Agrega una foto para continuar.'); else if (step === 2) materials.length ? setStep(3) : setError('Elige al menos un material.'); else void submit() }}>{step < 3 ? 'Continuar' : 'Enviar solicitud'}</button></div>
  </section>
}

function RequestCard({ item, role, onAssign, onCollect, onVerify, onReject }: { item: CollectionRequest; role: Role; onAssign: (scheduledAt: string) => void; onCollect: () => void; onVerify: () => void; onReject: () => void }) {
  const [assigning, setAssigning] = useState(false)
  const [scheduleDate, setScheduleDate] = useState('')
  const [scheduleTime, setScheduleTime] = useState('')
  const flowName = item.flow === 'ORGANIC' ? 'Orgánicos · Huerta' : 'Reciclables · Centro de acopio'
  const address = `${item.stage}, ${item.neighborhood}, torre ${item.tower}, apto. ${item.apartment}`
  const attachment = getDemoRequestPhoto(item.id)
  return <article className="request-card"><div className="request-top"><div><span className={`flow-label ${item.flow === 'ORGANIC' ? 'flow-label-green' : ''}`}>{flowName}</span><h3>{item.id}</h3></div><StatusPill status={item.status}/></div><div className="request-detail"><strong>{item.materials.join(' · ')}</strong><span>{address}</span><span>Disponible: {item.availability}</span>{item.note && <p>“{item.note}”</p>}{item.assignedTo && <span>Recolector: {item.assignedTo}{item.scheduledAt ? ` · ${new Date(item.scheduledAt).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })}` : ''}</span>}{attachment && <div className="request-attachment"><img src={attachment.url} alt={`Imagen de residuos para ${item.id}`}/><span>Imagen adjunta · {attachment.name}</span></div>}</div>{assigning && <div className="assignment-editor"><label>Día<input type="date" value={scheduleDate} onChange={(event) => setScheduleDate(event.target.value)}/></label><label>Hora<input type="time" value={scheduleTime} onChange={(event) => setScheduleTime(event.target.value)}/></label><button className="button button-small button-primary" disabled={!scheduleDate || !scheduleTime} onClick={() => { onAssign(`${scheduleDate}T${scheduleTime}`); setAssigning(false) }}>Confirmar asignación</button></div>}<div className="request-bottom"><small>{item.createdAt}</small><div className="request-actions">{(role === 'vivi' || role === 'kelly') && item.status === 'RECEIVED' && !assigning && <><button className="button button-small button-primary" onClick={() => setAssigning(true)}>Aceptar</button><button className="button button-small button-secondary" onClick={onReject}>Rechazar</button></>}{role === 'collector' && (item.status === 'ASSIGNED' || item.status === 'SCHEDULED') && <button className="button button-small button-primary" onClick={onCollect}>Registrar recolección</button>}{(role === 'vivi' || role === 'kelly') && item.status === 'COLLECTED' && <button className="button button-small button-green" onClick={onVerify}>Verificar y cerrar</button>}{item.status === 'COMPLETED' && <span className="points-notice">✓ Cierre verificado · puntos según regla configurada</span>}</div></div></article>
}

function RouteMap({ items, demo }: { items: CollectionRequest[]; demo: boolean }) {
  return <section className="route-map-card"><div className="section-header"><div><p className="eyebrow">VILLAS DE SAN PABLO · BARRANQUILLA</p><h2>Mapa de recolección</h2>{!demo && <p>Vista geográfica del sector. Faltan coordenadas confirmadas para ubicar cada solicitud.</p>}</div><span className="route-count">{items.length} {items.length === 1 ? 'solicitud' : 'solicitudes'}</span></div><RealCommunityMap demo={demo}/></section>
}

function CoordinatorMapLayout({ requests, role, demo, onAction }: { requests: CollectionRequest[]; demo: boolean; role: 'kelly' | 'vivi'; onAction: (item: CollectionRequest) => { onAssign: (scheduledAt: string) => void; onCollect: () => void; onVerify: () => void; onReject: () => void } }) {
  const pendingRequests = requests.filter((item) => item.status === 'RECEIVED' || item.status === 'UNDER_REVIEW')
  return <div className="coordinator-map-layout coordinator-map-layout-wide"><div className="coordinator-map-canvas" data-mascot-target="coordination-map"><RealCommunityMap demo={demo}/></div><aside className="coordinator-request-panel"><div className="coordinator-request-heading" data-mascot-target="coordination-requests"><div><h2>Solicitudes pendientes</h2><span>{pendingRequests.length} por revisar</span></div><span className="route-count">{pendingRequests.length}</span></div><div className="coordinator-request-list">{pendingRequests.length ? pendingRequests.map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>) : <EmptyState title="No hay solicitudes pendientes" detail="Las nuevas solicitudes aparecerán en este panel."/>}</div></aside></div>
}

function Dashboard({ role, profile, accountId, onHome, onExit, onLearn, onEvents }: { role: Role; profile: NeighborProfile; accountId?: string; onHome: () => void; onExit: () => void; onLearn: () => void; onEvents: () => void }) {
  const info = roleInfo[role]
  const [section, setSection] = useState<Section>(() => role === 'neighbor' ? 'new' : 'home')
  const [showAllRequests, setShowAllRequests] = useState(false)
  const [requests, setRequests] = useState<CollectionRequest[]>([])
  const [toast, setToast] = useState('')
  const [available, setAvailable] = useState(true)
  const [notification, setNotification] = useState('')
  const { showMoment } = useMascotActions()
  useMascotHidden(showAllRequests)
  // Canjear handles loading and errors internally. Keep reminders quiet while the catalog is open.
  useMascotReminderBlock(role === 'neighbor' && section === 'points')
  useEffect(() => { void service.listRequests().then(setRequests) }, [])
  useEffect(scrollScreenToTop, [section])
  function announce(message: string) { setToast(message); window.setTimeout(() => setToast(''), 3800) }
  async function refresh(message?: string) { const rows = await service.listRequests(); setRequests(rows); if (message) announce(message) }
  const visibleRequests = useMemo(() => {
    if (role === 'neighbor') return requests
    if (role === 'collector') return requests.filter((item) => item.status === 'ASSIGNED' || item.status === 'SCHEDULED' || item.status === 'COLLECTED' || item.status === 'COMPLETED')
    if (role === 'vivi') return requests.filter((item) => item.flow === 'RECYCLABLE')
    if (role === 'kelly') return requests.filter((item) => item.flow === 'ORGANIC')
    return requests
  }, [requests, role])
  const emptyQueue = section === 'home' && (role === 'vivi' || role === 'kelly')
    && !visibleRequests.some(({ status }) => status === 'RECEIVED' || status === 'UNDER_REVIEW')
  useMascotScene(emptyQueue ? 'noCoordinationRequests' : undefined)
  async function assign(item: CollectionRequest, scheduledAt: string) { const who = item.flow === 'ORGANIC' ? 'Huertero asignado (dato ficticio)' : 'Reciclador asignado (dato ficticio)'; await service.assignRequest(item.id, who, scheduledAt); await refresh('Solicitud programada y asignada. La persona responsable ya puede verla en su jornada.') }
  async function collect(item: CollectionRequest) { await service.registerCollection(item.id); await refresh('Recolección registrada. La coordinadora puede verificar el cierre.') }
  async function verify(item: CollectionRequest) { await service.verifyAndClose(item.id); await refresh('Recolección verificada y cerrada. El sistema de puntos podrá aplicar la regla configurada.') }
  const requestActions = (item: CollectionRequest) => ({ onAssign: (scheduledAt: string) => void assign(item, scheduledAt), onCollect: () => void collect(item), onVerify: () => void verify(item), onReject: () => announce('La acción de rechazo se conectará con el backend.') })
  const hello = role === 'neighbor' ? 'Hola, vecina' : role === 'collector' ? 'Hola, recolector' : `Hola, ${info.name}`
  const title = section === 'new' ? 'Pedir recolección' : section === 'points' && role === 'neighbor' ? 'Canjear mis puntos' : section === 'requests' ? role === 'kelly' ? 'Solicitudes orgánicas' : role === 'vivi' ? 'Historial de reciclaje' : role === 'neighbor' ? 'Mis solicitudes' : 'Historial' : section === 'history' ? 'Historial orgánico' : section === 'routes' ? role === 'collector' ? 'Mi ruta' : 'Rutas y equipo' : navByRole[role].find((item) => item.id === section)?.label ?? info.title
  const heading = section === 'home' && (role === 'vivi' || role === 'kelly') ? 'Solicitudes' : section === 'home' ? hello : title
  const subtitleByRole = { neighbor: 'Comunidad', collector: 'Equipo recolector', vivi: 'Equipo de reciclaje', kelly: 'Equipo de huerta', admin: 'Administración' }
  const requesting = role === 'neighbor' && section === 'new'

  return <div className={`app-shell app-shell-${role}`}>
    <SiteHeader onHome={onHome} onEducation={onLearn} onEvents={onEvents}/>
    <div className="app-body">
      <aside className="app-sidebar">
        <div className="sidebar-profile">
          <span className={`sidebar-profile-icon avatar-${role}`}><RoleIcon role={role}/></span>
          <div><strong>{info.name}</strong><small>{subtitleByRole[role]}</small></div>
        </div>
        <nav aria-label="Navegación principal" data-mascot-target={role === 'vivi' || role === 'kelly' ? 'coordination-nav' : undefined}>
          {navByRole[role].map((item) => <button key={item.id} className={`nav-item ${section === item.id ? 'nav-active' : ''}`} aria-current={section === item.id ? 'page' : undefined} data-mascot-target={role === 'kelly' && item.id === 'inventory' ? 'garden-inventory' : undefined} onClick={() => {
            if (item.id === 'learning') { onLearn(); return }
            setSection(item.id)
            setShowAllRequests(false)
          }}><span className="nav-indicator" aria-hidden="true"/>{item.label}</button>)}
        </nav>
        <div className="sidebar-bottom"><button className="nav-item" onClick={onExit}>← {accountId ? 'Cerrar sesión' : 'Salir de la demostración'}</button><small>EcoConecta · {accountId ? 'Piloto' : 'Demostración'}</small></div>
      </aside>
      <main className="app-main">{!requesting && !(section === 'home' && (role === 'vivi' || role === 'kelly')) && <div className="main-heading"><div><p className="eyebrow">{info.name.toUpperCase()} · ECOCONECTA</p><h1>{heading}</h1>{section === 'home' && <p>{role === 'neighbor' ? 'Esto es lo que pasa con tus aportes al barrio.' : info.description}</p>}</div>{role === 'collector' && <button className={`availability ${available ? 'available' : ''}`} onClick={() => { setAvailable(!available); announce(available ? 'Ahora apareces como no disponible.' : 'Ahora apareces como disponible.') }}><i/> {available ? 'Disponible' : 'No disponible'}</button>}</div>}
        {toast && <div className="toast" role="status">{toast}</div>}
        {notification && <div className="notice-banner" role="status">{notification}<button onClick={() => setNotification('')} aria-label="Cerrar aviso">×</button></div>}
        {requesting ? <RequestForm onCancel={() => setSection('home')} onCreated={(item) => { setSection('home'); showMoment('pickupCreated'); void refresh(`Solicitud ${item.id} creada y enviada a ${item.flow === 'ORGANIC' ? 'la coordinación de huerta' : 'la coordinación de reciclaje'}.`) }}/>
          : role === 'neighbor' && section === 'points' ? <GardenRedemptions accountId={accountId}/>
          : role === 'neighbor' && section === 'events' ? <CommunityEvents/>
          : <DashboardSection demo={import.meta.env.DEV && !accountId} role={role} profile={profile} section={section} requests={visibleRequests} allRequests={requests} showAllRequests={showAllRequests} onShowAll={() => setShowAllRequests(true)} onCloseAll={() => setShowAllRequests(false)} onNew={() => setSection('new')} onLearn={onLearn} onAction={requestActions} onSection={setSection} onNotify={setNotification}/>}
      </main>
    </div>
  </div>
}

function DashboardSection({ demo, role, profile, section, requests, allRequests, showAllRequests, onShowAll, onCloseAll, onNew, onLearn, onAction, onSection, onNotify }: { demo: boolean; role: Role; profile: NeighborProfile; section: Section; requests: CollectionRequest[]; allRequests: CollectionRequest[]; showAllRequests: boolean; onShowAll: () => void; onCloseAll: () => void; onNew: () => void; onLearn: () => void; onAction: (item: CollectionRequest) => { onAssign: (scheduledAt: string) => void; onCollect: () => void; onVerify: () => void; onReject: () => void }; onSection: (section: Section) => void; onNotify: (message: string) => void }) {
  const pending = requests.filter((item) => item.status === 'RECEIVED').length
  const active = requests.filter((item) => item.status !== 'COMPLETED' && item.status !== 'CANCELLED').length
  if (role === 'neighbor' && section === 'home') return <>
    <div className="neighbor-welcome-banner"><div><p className="eyebrow">TU APORTE CUENTA</p><h2>Un barrio más limpio empieza con una acción.</h2><p>Comparte qué vas a entregar y el equipo comunitario te ayudará a coordinarlo.</p></div><button className="button button-primary" onClick={onNew}>＋ Solicitar recolección</button></div>
    <div className="neighbor-summary"><div className="summary-card summary-orange"><span>Recolecciones pendientes</span><strong>{active}</strong><small>En revisión o coordinación</small></div><div className="summary-card"><span>Puntos disponibles</span><strong>—</strong><small>Saldo por consultar al backend</small></div><button className="new-request-cta" onClick={onNew}><span aria-hidden="true">▧</span><strong>Adjunta una imagen</strong><small>Al crear tu solicitud</small></button></div>
    <div className="section-header"><div><h2>Mis recolecciones</h2><p>Consulta el estado de tus solicitudes recientes.</p></div>{requests.length > 2 && <button className="text-button" onClick={onShowAll}>Ver todas ({requests.length})</button>}</div>
    {requests.length ? <div className="request-list">{requests.slice(0, 2).map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="Todavía no tienes solicitudes" detail="Crea una solicitud y podrás seguir aquí su estado." action="Solicitar recolección" onClick={onNew}/>}
    <button className="learning-callout" onClick={onLearn}><span className="learning-callout-icon">+</span><span><strong>Educación ambiental</strong><small>Aprende sobre separación, reciclables y huerta.</small></span><b>→</b></button>
    {showAllRequests && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onCloseAll() }}><section className="requests-modal" role="dialog" aria-modal="true" aria-labelledby="requests-modal-title"><div className="section-header"><div><p className="eyebrow">VECINO · DEMOSTRACIÓN</p><h2 id="requests-modal-title">Todas mis solicitudes</h2></div><button className="icon-button" onClick={onCloseAll} aria-label="Cerrar">×</button></div><div className="request-list">{requests.map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div></section></div>}
  </>
  if (role === 'neighbor' && section === 'profile') return <section className="neighbor-profile"><div className="profile-avatar"><RoleIcon role="neighbor"/></div><div className="neighbor-profile-identity"><p className="eyebrow">MI PERFIL</p><h2>{profile.fullName || 'Mi cuenta de vecino'}</h2><p>{profile.neighborhood || 'Villas de San Pablo'}</p></div><div className="neighbor-profile-details"><article><span>Celular</span><strong>{profile.phone || 'Disponible al iniciar sesión'}</strong></article><article><span>Etapa</span><strong>{profile.stage || 'Pendiente de cargar'}</strong></article><article><span>Conjunto</span><strong>{profile.neighborhood || 'Villas de San Pablo'}</strong></article><article><span>Torre · apartamento</span><strong>{profile.tower || profile.apartment ? `${profile.tower || '—'} · ${profile.apartment || '—'}` : 'Pendiente de cargar'}</strong></article></div><div className="profile-points"><span>Puntos acumulados</span><strong>—</strong><small>Saldo actualizado al consultar tu cuenta.</small></div></section>
  if (role === 'collector' && section === 'home') return <>
    <div className="collector-callout"><div><span className="eyebrow">TU JORNADA</span><h2>{requests.filter((item) => item.status === 'ASSIGNED' || item.status === 'SCHEDULED').length} recolecciones asignadas</h2><p>Revisa los detalles y registra el resultado al terminar.</p></div><button className="button button-primary" onClick={() => onSection('routes')}>Ver asignaciones</button></div>
    <div className="section-header"><div><h2>Lo próximo</h2><p>Dirección y materiales de tus recolecciones.</p></div></div>{requests.filter((item) => item.status !== 'COMPLETED').length ? <div className="request-list">{requests.filter((item) => item.status !== 'COMPLETED').map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="No tienes asignaciones por ahora" detail="Cuando te asignen una recolección, aparecerá aquí."/>}
  </>
  if (role === 'collector' && section === 'routes') return <><RouteMap demo={demo} items={requests.filter((item) => item.status === 'ASSIGNED' || item.status === 'SCHEDULED')}/><div className="section-header"><div><h2>Paradas asignadas</h2><p>Información de jornada para tu perfil de demostración.</p></div></div>{requests.length ? <div className="request-list">{requests.map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="No hay actividad para mostrar" detail="Las nuevas asignaciones se verán en este espacio."/>}</>
  if (role === 'collector' && section === 'requests') return <><div className="section-header"><div><h2>Historial de actividad</h2><p>Recolecciones asignadas a este perfil de demostración.</p></div></div>{requests.length ? <div className="request-list">{requests.map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="No hay actividad para mostrar" detail="Las recolecciones aparecerán aquí cuando estén asignadas."/>}</>
  if (role === 'collector' && section === 'profile') return <InfoSection title="Perfil del recolector" description="Disponibilidad de demostración. La identidad y cobertura se configurarán mediante sesión y datos validados." badge="Perfil simulado" />
  if ((role === 'vivi' || role === 'kelly') && section === 'home') return <CoordinatorMapLayout demo={demo} requests={requests} role={role} onAction={onAction}/>
  if (role === 'vivi' && section === 'requests') { const history = requests.filter((item) => item.status === 'COMPLETED' || item.status === 'COLLECTED'); return <><div className="section-header"><div><h2>Historial de reciclaje</h2><p>Recolecciones realizadas o pendientes de verificación.</p></div></div>{history.length ? <div className="request-list">{history.map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="Aún no hay recolecciones en el historial" detail="Cuando una recolección se realice, aparecerá aquí."/>}</> }
  if ((role === 'vivi' || role === 'kelly') && section === 'requests') return <>
    <div className="coordinator-metrics"><div className="metric-card"><span>Por revisar</span><strong>{pending}</strong><small>Necesitan una asignación</small></div><div className="metric-card"><span>En seguimiento</span><strong>{active}</strong><small>Solicitudes sin cerrar</small></div><div className={`metric-card metric-accent-${role}`}><span>{role === 'vivi' ? 'Materiales por confirmar' : 'Necesidades del huerto'}</span><strong>—</strong><small>{role === 'vivi' ? 'Se registran al pesar' : 'Sin necesidades confirmadas'}</small></div></div>
    {role === 'kelly' && <div className="inline-priority"><span className="priority-mark">!</span><span><strong>Prioridad del huerto</strong><small>Revisa si los aportes orgánicos responden a una necesidad vigente.</small></span><button className="text-button" onClick={() => onSection('needs')}>Ver necesidades</button></div>}
    <div className="section-header"><div><h2>Solicitudes recibidas</h2><p>{role === 'vivi' ? 'Reciclables que requieren revisión del equipo.' : 'Aportes orgánicos para revisar y coordinar con el huerto.'}</p></div><div className="view-toggle"><button className="toggle-on">Lista</button><button disabled title="La vista de mapa queda pendiente de ubicaciones validadas">Mapa</button></div></div>
    {requests.length ? <div className="request-list">{requests.map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="La bandeja está al día" detail="Las solicitudes nuevas aparecerán aquí con su flujo correspondiente."/>}
    {role === 'vivi' && <div className="coordinator-note">Los precios, kilos y número de pacas se completan después de la recolección con información confirmada.</div>}
  </>
  if (role === 'kelly' && section === 'history') { const history = requests.filter((item) => item.status === 'COMPLETED' || item.status === 'COLLECTED'); return <><div className="section-header"><div><h2>Historial orgánico</h2><p>Solicitudes y recolecciones anteriores del flujo de la huerta.</p></div></div>{history.length ? <div className="request-list">{history.map((item) => <RequestCard key={item.id} item={item} role={role} {...onAction(item)}/>)}</div> : <EmptyState title="Aún no hay recolecciones en el historial" detail="Las solicitudes orgánicas cerradas aparecerán aquí."/>}</> }
  if (role === 'vivi' && section === 'income') return <RecyclerEarnings/>
  if (role === 'kelly' && section === 'inventory') return <InfoSection title="Inventario faltante" description="Los insumos, cantidades y prioridades aparecerán cuando el equipo de la huerta los registre y confirme." badge="Sin insumos registrados"/>
  if (role === 'kelly' && section === 'redemptions') return <InfoSection title="Canjes del huerto" description="Los productos, existencias y equivalencias de canje se mostrarán cuando la Fundación configure el catálogo y la regla de puntos." badge="Catálogo pendiente"/>
  if (role === 'kelly' && section === 'team') return <CoordinatorDirectory/>
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

function RecyclerEarnings() {
  return <section className="recycler-earnings">
    <div className="earnings-heading"><p className="eyebrow">OPERACIÓN DE RECICLAJE</p><h2>Lista de precios</h2></div>
    <div className="earnings-price-table-wrap"><table className="earnings-price-table"><thead><tr><th>Material</th><th>Precio por kg</th></tr></thead><tbody><tr><td colSpan={2}>Los materiales y precios aparecerán cuando se publique la lista oficial.</td></tr></tbody></table></div>
  </section>
}

function AdminUsersDemo({ onNotify }: { onNotify: (message: string) => void }) {
  const [users, setUsers] = useState<Awaited<ReturnType<typeof authApi.listPilotUsers>>>([])
  const [zones, setZones] = useState<Awaited<ReturnType<typeof authApi.listZones>>>([])
  const [accountType, setAccountType] = useState<'resident' | 'staff' | 'activation'>('resident')
  const [pendingCollectors, setPendingCollectors] = useState<typeof users>([])
  const [pendingCollectorId, setPendingCollectorId] = useState('')
  const [loadingPending, setLoadingPending] = useState(false)
  const [fullName, setFullName] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [staffRole, setStaffRole] = useState<'recolector' | 'coordinador_huerteros' | 'coordinador_recicladores'>('recolector')
  const [collectorFlow, setCollectorFlow] = useState<'organico' | 'reciclable'>('reciclable')
  const [zoneIds, setZoneIds] = useState<string[]>([])
  const [validFrom, setValidFrom] = useState(() => new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Bogota', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date()))
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [loadingAccounts, setLoadingAccounts] = useState(true)
  useMascotReminderBlock(loadingAccounts || loadingPending || busy || Boolean(error))
  async function reload() {
    const [loadedUsers, loadedZones] = await Promise.all([authApi.listPilotUsers(), authApi.listZones()])
    setUsers(loadedUsers); setZones(loadedZones)
  }
  useEffect(() => { void reload().catch((reason) => setError(reason instanceof Error ? reason.message : 'No se pudieron cargar las cuentas.')).finally(() => setLoadingAccounts(false)) }, [])
  async function showAccountType(type: typeof accountType) {
    setAccountType(type)
    setError('')
    setZoneIds([])
    setPendingCollectorId('')
    if (type !== 'activation') return
    setLoadingPending(true)
    try { setPendingCollectors(await authApi.listPendingCollectors()) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudieron cargar los registros pendientes.') }
    finally { setLoadingPending(false) }
  }
  async function createAccount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setBusy(true)
    try {
      if (accountType === 'activation') {
        await authApi.activateCollector(pendingCollectorId, { flow: collectorFlow, zone_ids: zoneIds, valid_from: validFrom })
        setPendingCollectors((current) => current.filter((item) => item.id !== pendingCollectorId))
        setPendingCollectorId('')
        setZoneIds([])
        onNotify('Cuenta de recolector activada. La persona ya puede iniciar sesión.')
        await reload()
        return
      }
      if (accountType === 'resident') await authApi.createResident({ full_name: fullName.trim(), phone: phone.trim(), password })
      else {
        const flow = staffRole === 'coordinador_huerteros' ? 'organico' : staffRole === 'coordinador_recicladores' ? 'reciclable' : collectorFlow
        await authApi.createStaff({ full_name: fullName.trim(), phone: phone.trim(), password, role: staffRole, flow, zone_ids: zoneIds, valid_from: validFrom })
      }
      setFullName(''); setPhone(''); setPassword(''); setZoneIds([])
      await reload()
      onNotify('Cuenta piloto creada. Entrega el teléfono y la contraseña al titular de forma segura.')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo crear la cuenta.') }
    finally { setBusy(false) }
  }
  const activating = accountType === 'activation'
  return <section className="admin-workspace"><div className="admin-panel-intro"><p className="eyebrow">CUENTAS PILOTO · ADMINISTRACIÓN</p><h2>Registro de personas</h2><p>Crea cuentas del piloto o activa el registro de una persona recolectora después de asignar su cobertura.</p></div>
    <div className="admin-account-tabs">
      <button className={accountType === 'resident' ? 'account-tab active' : 'account-tab'} disabled={busy || loadingPending} onClick={() => void showAccountType('resident')}>Vecino o unidad productiva</button>
      <button className={accountType === 'staff' ? 'account-tab active' : 'account-tab'} disabled={busy || loadingPending} onClick={() => void showAccountType('staff')}>Personal operativo</button>
      <button className={activating ? 'account-tab active' : 'account-tab'} disabled={busy || loadingPending} onClick={() => void showAccountType('activation')}>Activar recolectores</button>
    </div>
    <form className="admin-account-form" onSubmit={createAccount}>
      {activating ? <label>Registro pendiente<select value={pendingCollectorId} onChange={(event) => setPendingCollectorId(event.target.value)} required>
        <option value="" disabled>{loadingPending ? 'Cargando registros…' : pendingCollectors.length ? 'Selecciona un registro' : 'No hay registros pendientes'}</option>
        {pendingCollectors.map((user) => <option key={user.id} value={user.id}>{user.full_name} · {user.id.slice(-8)}</option>)}
      </select></label> : <>
      <label>Nombre completo<input value={fullName} onChange={(event) => setFullName(event.target.value)} minLength={1} maxLength={200} required/></label>
      <label>Teléfono con indicativo<input type="tel" inputMode="tel" pattern="\+[1-9][0-9]{6,14}" placeholder="+573001234567" value={phone} onChange={(event) => setPhone(event.target.value)} required/></label>
      <label>Contraseña inicial<input type="password" minLength={12} maxLength={256} autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} required/><small>Mínimo 12 caracteres. Entrégala al titular de forma segura.</small></label>
      </>}
      {accountType !== 'resident' && <>
        {!activating && <label>Rol operativo<select value={staffRole} onChange={(event) => setStaffRole(event.target.value as typeof staffRole)}><option value="recolector">Recolector</option><option value="coordinador_huerteros">Coordinación de huerta</option><option value="coordinador_recicladores">Coordinación de reciclaje</option></select></label>}
        {(activating || staffRole === 'recolector') && <label>Flujo de recolección<select value={collectorFlow} onChange={(event) => setCollectorFlow(event.target.value as typeof collectorFlow)}><option value="reciclable">Reciclable</option><option value="organico">Orgánico</option></select></label>}
        <label>Vigente desde<input type="date" value={validFrom} onChange={(event) => setValidFrom(event.target.value)} required/></label>
        <fieldset className="account-zones"><legend>Zonas asignadas</legend>{zones.length ? zones.map((zone) => <label key={zone.id}><input type="checkbox" checked={zoneIds.includes(zone.id)} onChange={() => setZoneIds((current) => current.includes(zone.id) ? current.filter((id) => id !== zone.id) : [...current, zone.id])}/>{zone.name}</label>) : <small>No hay zonas activas disponibles.</small>}</fieldset>
      </>}
      {error && <p className="login-api-notice" role="alert">{error}</p>}
      <button className="button button-primary" type="submit" disabled={busy || (accountType !== 'resident' && !zoneIds.length) || (activating && (!pendingCollectorId || loadingPending))}>{busy ? 'Guardando…' : activating ? 'Activar cuenta' : 'Crear cuenta piloto'}</button>
    </form>
    <div className="admin-account-list"><h3>Cuentas existentes</h3>{users.length ? <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Nombre</th><th>Rol</th><th>Estado piloto</th></tr></thead><tbody>{users.map((user) => <tr key={user.id}><td>{user.full_name}</td><td>{user.role}</td><td>{user.is_active && user.is_pilot ? 'Activa' : 'Inactiva'}</td></tr>)}</tbody></table></div> : <p>{error ? 'Inicia sesión como administración y confirma la conexión con el backend.' : 'No hay cuentas registradas.'}</p>}</div>
  </section>
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
  return <MascotProvider><EcoConectaApp/></MascotProvider>
}

function EcoConectaApp() {
  const [view, setView] = useState<View>('welcome')
  const [role, setRole] = useState<Role>('neighbor')
  const [session, setSession] = useState<Session | null>(null)
  const [residentProfile, setResidentProfile] = useState<NeighborProfile>(emptyNeighborProfile)
  const [loginForEducation, setLoginForEducation] = useState(false)
  const screenRef = useRef<HTMLDivElement>(null)
  const { showMoment } = useMascotActions()

  useEffect(scrollScreenToTop, [view])

  function home() {
    scrollScreenToTop()
    setView('welcome')
  }
  function openEducationLogin() {
    setSession(null)
    setRole('neighbor')
    setLoginForEducation(true)
    setView('login')
  }
  function openEducation() {
    if (session) setView('learning')
    else openEducationLogin()
  }
  function openRole(selected: Role) {
    setLoginForEducation(false)
    setRole(selected)
    if (session?.role === selected) {
      setView('dashboard')
    } else {
      if (session) void authApi.logout().catch(() => {})
      setSession(null)
      setView('login')
    }
  }
  function finishSignIn(nextSession: Session, profile: NeighborProfile) {
    setSession(nextSession)
    setRole(nextSession.role)
    setResidentProfile(profile)
    setView(loginForEducation ? 'learning' : 'dashboard')
  }
  function exit() {
    setSession(null)
    setResidentProfile(emptyNeighborProfile)
    void authApi.logout().catch(() => {})
    home()
    showMoment('farewell', 5000)
  }
  const openEvents = () => setView('events')
  const showPanel = () => setView('dashboard')
  const panelButton = session && <button className="button button-secondary" onClick={showPanel}>Mi panel</button>
  const siteNavigation = { onHome: home, onEducation: openEducation, onEvents: openEvents }

  function renderScreen() {
    if (view === 'events') return <main className="education-page">
      <SiteHeader {...siteNavigation} active="events" tools={panelButton}/>
      <div className="education-wrap education-account-wrap"><h1>Eventos</h1><CommunityEvents/></div>
    </main>
    if (view === 'learning' && session) return <main className="education-page">
      <SiteHeader {...siteNavigation} active="education" tools={panelButton}/>
      <div className="education-wrap education-account-wrap">
        <header className="education-intro"><h1>Aprender</h1><p>Consejos cortos para separar mejor y cuidar nuestra comunidad.</p></header>
        <EducationContent key={session.identity.id} onSignIn={openEducationLogin}/>
      </div>
    </main>
    if (view === 'register') return <RegistrationScreen {...siteNavigation} collector={role === 'collector'} onLogin={() => setView('login')} onSuccess={finishSignIn}/>
    if (view === 'login') return <LoginScreen key={loginForEducation ? 'education' : role} {...siteNavigation} role={role} forEducation={loginForEducation} onRegister={() => setView('register')} onSuccess={(signedIn, phone) => {
      const identity = signedIn.identity
      finishSignIn(signedIn, signedIn.role === 'neighbor' ? { fullName: identity.full_name || '', phone: identity.phone || phone, stage: identity.stage || '', neighborhood: identity.neighborhood || '', tower: identity.tower || '', apartment: identity.apartment || '' } : emptyNeighborProfile)
    }}/>
    if (view === 'dashboard') return <Dashboard key={session?.identity.id ?? role} role={session?.role ?? role} profile={residentProfile} accountId={session?.identity.id} onHome={home} onExit={exit} onLearn={openEducation} onEvents={openEvents}/>
    if (view === 'demo-roles' && import.meta.env.DEV) return <DemoRolePicker onBack={home} onEducation={openEducation} onEvents={openEvents} onChoose={(selected) => { setRole(selected); showPanel() }}/>
    return <Welcome onHome={home} onRole={openRole} onDemo={import.meta.env.DEV && !session ? () => setView('demo-roles') : undefined} onLearn={openEducation} onEvents={openEvents} onPanel={session ? showPanel : undefined}/>
  }

  return <>
    <div ref={screenRef} className="mascot-screen" data-mascot-screen={view}>{renderScreen()}</div>
    <MascotDock view={view} role={session?.role ?? role} screenRef={screenRef}/>
  </>
}
