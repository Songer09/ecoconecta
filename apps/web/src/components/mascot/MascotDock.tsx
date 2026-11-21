import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from 'react'
import type { CSSProperties, RefObject } from 'react'
import type { Role } from '../../domain/types'
import { mascotArt } from './mascotConfig'
import type { MascotExpression } from './mascotConfig'
import { defaultMascotMessage, mascotLine } from './mascotMessages'
import type { MascotTourId, MascotView } from './mascotMessages'
import { useMascotActions, useMascotState } from './MascotContext'
import { markFirstGreeting, saveTour } from './mascotStorage'
import { readMascotPreview } from './mascotDevPreview'
import { MascotTour } from './MascotTour'
import './mascot.css'

const preloadedArt = new Set<string>()
const typingField = 'textarea, [contenteditable="true"], [contenteditable="plaintext-only"], input:not([type]), input[type="text"], input[type="search"], input[type="email"], input[type="url"], input[type="tel"], input[type="password"], input[type="number"]'

function useTypingFocus() {
  const [focused, setFocused] = useState(false)
  useEffect(() => {
    function update(target: EventTarget | null) {
      setFocused(target instanceof HTMLElement && Boolean(target.closest(typingField)))
    }
    const focus = (event: FocusEvent) => update(event.target)
    const blur = (event: FocusEvent) => update(event.relatedTarget)
    update(document.activeElement)
    document.addEventListener('focusin', focus)
    document.addEventListener('focusout', blur)
    return () => {
      document.removeEventListener('focusin', focus)
      document.removeEventListener('focusout', blur)
    }
  }, [])
  return focused
}

export function MascotSprite({ expression }: { expression: MascotExpression }) {
  const art = mascotArt[expression]
  const crop = {
    '--mascot-crop-x': `-${art.face.x}%`,
    '--mascot-crop-y': `-${art.face.y}%`,
    '--mascot-crop-size': `${art.face.scale * 100}%`,
  } as CSSProperties
  return <img key={art.src} className="mascot-sprite" src={art.src} width={art.width} height={art.height} alt="" draggable={false} style={crop}/>
}

export function MascotDock({ view, role, screenRef }: { view: MascotView; role: Role; screenRef: RefObject<HTMLDivElement> }) {
  const { scene, hidden: modalOpen, reminderBlocked, moment } = useMascotState()
  const { showMoment, endMoment, updateReminderContext, recordMascotInteraction } = useMascotActions()
  const [open, setOpen] = useState(false)
  const [hoveringBubble, setHoveringBubble] = useState(false)
  const [focusInBubble, setFocusInBubble] = useState(false)
  const [touchedBubble, setTouchedBubble] = useState(false)
  const [tour, setTour] = useState<MascotTourId>()
  const [preview] = useState(() => import.meta.env.DEV ? readMascotPreview() : undefined)
  const greeted = useRef(false)
  const previewReminderShown = useRef(false)
  const opener = useRef<HTMLButtonElement>(null)
  const bubble = useRef<HTMLDivElement>(null)
  const bubbleId = useId()
  const typing = useTypingFocus()
  const hidden = typing || modalOpen || Boolean(tour)
  const message = scene?.message ?? defaultMascotMessage(view, role)
  const line = mascotLine(message)
  const temporary = moment && (moment.message !== 'farewell' || view === 'welcome') ? moment : undefined
  const currentLine = temporary ? mascotLine(temporary.message) : line
  const expression = preview?.expression ?? (!open && view === 'welcome' && !temporary ? 'bienvenida' : currentLine.expression)
  const posture = preview?.posture ?? (view === 'welcome' || view === 'learning' ? 'completa' : 'mini')
  const text = preview?.text ?? (temporary ? currentLine.text : scene?.text ?? line.text)
  const timer = useRef({ sequence: -1, remaining: 0 })
  const inDashboard = view === 'dashboard'
  const coordinationTour = role === 'vivi' ? 'coordinacion-reciclaje' : role === 'kelly' ? 'coordinacion-huerta' : undefined
  const inReminder = temporary?.message.startsWith('reminder')
  const availableTour = inReminder || temporary?.message === 'tourComplete' || temporary?.message === 'farewell' ? undefined
    : view === 'welcome' ? 'inicio'
    : inDashboard && coordinationTour ? coordinationTour
    : message === 'pickupPhoto' ? 'recoleccion' : undefined
  const reminderEligible = !hidden && !open && !moment && !preview && !reminderBlocked && !line.open && !line.blocksReminder
  const slowReminder = inDashboard && (Boolean(coordinationTour) || role === 'admin')

  useLayoutEffect(() => {
    updateReminderContext({ eligible: reminderEligible, slow: slowReminder })
  }, [reminderEligible, slowReminder, updateReminderContext])

  useEffect(() => {
    if (open && !hidden && !temporary) recordMascotInteraction('message')
  }, [open, hidden, temporary, text, recordMascotInteraction])

  useEffect(() => {
    if (!preview?.reminder || previewReminderShown.current) return
    previewReminderShown.current = true
    showMoment('reminderFirst', 6000)
  }, [preview, showMoment])

  useEffect(() => {
    if (moment && !temporary) endMoment(moment.sequence)
  }, [moment, temporary, endMoment])

  useLayoutEffect(() => {
    const avatar = opener.current
    const panel = bubble.current
    const screen = screenRef.current
    const dock = avatar?.closest('.mascot-dock')
    if (!screen || !avatar || !panel || !dock) return
    if (hidden) {
      screen.style.removeProperty('--mascot-occupied-space')
      return
    }
    const surface = screen
    function updateSpace() {
      const avatarTop = avatar?.getBoundingClientRect().top ?? window.innerHeight
      const panelTop = open ? panel?.getBoundingClientRect().top ?? avatarTop : avatarTop
      const dockTop = dock?.getBoundingClientRect().top ?? avatarTop
      surface.style.setProperty('--mascot-occupied-space', `${Math.ceil(dockTop - Math.min(avatarTop, panelTop) + 20)}px`)
    }
    updateSpace()
    const frame = requestAnimationFrame(updateSpace)
    const observer = new ResizeObserver(updateSpace)
    observer.observe(avatar)
    observer.observe(panel)
    window.addEventListener('resize', updateSpace)
    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
      window.removeEventListener('resize', updateSpace)
    }
  }, [hidden, open, view, posture, screenRef])

  useEffect(() => {
    for (const { src } of Object.values(mascotArt)) {
      if (preloadedArt.has(src)) continue
      preloadedArt.add(src)
      new Image().src = src
    }
  }, [])

  useEffect(() => {
    setOpen(Boolean(preview?.open))
    setHoveringBubble(false)
    setFocusInBubble(false)
    setTouchedBubble(false)
    if (preview || view !== 'welcome' || greeted.current) return
    greeted.current = true
    if (markFirstGreeting()) {
      const words = mascotLine('welcomeGreeting').text.split(/\s+/).length
      showMoment('welcomeGreeting', Math.max(7000, words * 450))
    }
  }, [view, preview, showMoment])

  useEffect(() => {
    if (line.open) setOpen(true)
  }, [message, line.open])

  useEffect(() => {
    if (!temporary) return
    if (timer.current.sequence !== temporary.sequence) {
      timer.current = { sequence: temporary.sequence, remaining: temporary.duration }
      setOpen(true)
      setTouchedBubble(false)
    }
    if (hidden || hoveringBubble || focusInBubble || touchedBubble) return
    const started = performance.now()
    const timeout = window.setTimeout(() => {
      endMoment(temporary.sequence)
      setOpen(false)
    }, timer.current.remaining)
    return () => {
      window.clearTimeout(timeout)
      timer.current.remaining = Math.max(0, timer.current.remaining - (performance.now() - started))
    }
  }, [temporary, hidden, hoveringBubble, focusInBubble, touchedBubble, endMoment])

  function close(restoreFocus = false) {
    setOpen(false)
    setHoveringBubble(false)
    setFocusInBubble(false)
    setTouchedBubble(false)
    if (temporary) endMoment(temporary.sequence)
    if (restoreFocus) opener.current?.focus({ preventScroll: true })
  }
  function startTour(id: MascotTourId) {
    close()
    setTour(id)
  }
  const finishTour = useCallback((completed: boolean) => {
    if (!tour) return
    saveTour(tour, completed ? 'completado' : 'omitido')
    setTour(undefined)
    if (completed) showMoment('tourComplete')
    requestAnimationFrame(() => opener.current?.focus({ preventScroll: true }))
  }, [showMoment, tour])

  useEffect(() => {
    if (!open || hidden) return
    function escape(event: KeyboardEvent) {
      if (event.key !== 'Escape' || event.defaultPrevented) return
      setOpen(false)
      setHoveringBubble(false)
      setFocusInBubble(false)
      setTouchedBubble(false)
      if (temporary) endMoment(temporary.sequence)
      if (bubble.current?.contains(document.activeElement)) opener.current?.focus({ preventScroll: true })
    }
    document.addEventListener('keydown', escape)
    return () => document.removeEventListener('keydown', escape)
  }, [open, hidden, temporary, endMoment])

  return <><div className="mascot-dock" data-mascot-view={view} data-mascot-posture={posture} hidden={hidden}>
    <button ref={opener} className="mascot-trigger" type="button" aria-label="Ayuda de la oruga guía" aria-controls={bubbleId} aria-expanded={open} onClick={() => {
      recordMascotInteraction(open ? 'message' : 'opened')
      if (open) close()
      else setOpen(true)
    }}>
      <span className="mascot-art"><MascotSprite expression={expression}/></span>
    </button>
    <div id={bubbleId} ref={bubble} className="mascot-bubble" hidden={!open}
      onPointerEnter={() => setHoveringBubble(true)} onPointerLeave={() => setHoveringBubble(false)}
      onPointerDown={(event) => { if (event.pointerType === 'touch') setTouchedBubble(true) }}
      onFocus={() => setFocusInBubble(true)} onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setFocusInBubble(false) }}>
      <div className="mascot-bubble-content">
        <button className="mascot-close" type="button" aria-label="Cerrar ayuda" onClick={() => close(true)}>×</button>
        <p className="mascot-message" role="status" aria-live="polite">{text}</p>
        {availableTour && <div className="mascot-bubble-actions">
          <button className="button button-primary" type="button" onClick={() => startTour(availableTour)}>Ver recorrido</button>
          <button className="button button-secondary" type="button" onClick={() => close(true)}>Ahora no</button>
        </div>}
      </div>
    </div>
  </div>{tour && <MascotTour id={tour} onFinish={finishTour}/>}</>
}
