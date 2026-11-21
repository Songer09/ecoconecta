import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { CSSProperties, KeyboardEvent } from 'react'
import { mascotArt } from './mascotConfig'
import { mascotTours } from './mascotMessages'
import type { MascotTourId } from './mascotMessages'
import './mascotTourPlacement.css'

type Highlight = { top: number; left: number; width: number; height: number }
type Placement = 'top' | 'bottom'
type TourLayout = { highlight: Highlight | null; placement: Placement; availableSpace?: number }

const highlightPadding = 5
const cardClearance = 12

function isVisibleTarget(target: HTMLElement) {
  return target.isConnected && target.getClientRects().length > 0 && getComputedStyle(target).visibility === 'visible'
}

function measureTarget(target: HTMLElement, screen: HTMLElement | null, header: HTMLElement | null, sidebar: HTMLElement | null): TourLayout {
  const rect = target.getBoundingClientRect()
  const viewportHeight = window.innerHeight
  const viewportWidth = document.documentElement.clientWidth
  const fixedSidebar = sidebar && getComputedStyle(sidebar).position === 'fixed' ? sidebar : null
  const sidebarRect = fixedSidebar?.getBoundingClientRect()
  const boundsTop = header && !header.contains(target) ? Math.max(0, header.getBoundingClientRect().bottom) : 0
  const boundsBottom = fixedSidebar?.contains(target)
    ? viewportHeight
    : Math.min(viewportHeight, screen?.getBoundingClientRect().bottom ?? viewportHeight, sidebarRect?.top ?? viewportHeight)
  const left = Math.max(3, rect.left - highlightPadding)
  const right = Math.min(viewportWidth - 3, rect.right + highlightPadding)
  const top = Math.max(3, boundsTop, rect.top - highlightPadding)
  const bottom = Math.min(viewportHeight - 3, boundsBottom, rect.bottom + highlightPadding)
  const highlight = right > left && bottom > top ? { top, left, width: right - left, height: bottom - top } : null
  const center = highlight ? highlight.top + highlight.height / 2 : rect.top + rect.height / 2
  const placement = center >= viewportHeight * .65 ? 'top' : 'bottom'
  const availableSpace = highlight
    ? placement === 'top'
      ? top - cardClearance * 2
      : (sidebarRect?.top ?? viewportHeight) - bottom - cardClearance * 2
    : undefined
  return { highlight, placement, availableSpace }
}

export function MascotTour({ id, onFinish }: { id: MascotTourId; onFinish: (completed: boolean) => void }) {
  const [index, setIndex] = useState(0)
  const [{ highlight, placement, availableSpace }, setLayout] = useState<TourLayout>({ highlight: null, placement: 'bottom' })
  const dialog = useRef<HTMLDivElement>(null)
  const next = useRef<HTMLButtonElement>(null)
  const steps = mascotTours[id]
  const step = steps[index]
  const art = mascotArt.explicando

  useEffect(() => {
    const screen = document.querySelector<HTMLElement>('.mascot-screen')
    const previous = screen?.inert ?? false
    if (screen) screen.inert = true
    next.current?.focus({ preventScroll: true })
    return () => { if (screen) screen.inert = previous }
  }, [])

  useLayoutEffect(() => {
    const screen = document.querySelector<HTMLElement>('.mascot-screen')
    const header = screen?.querySelector<HTMLElement>('.site-header') ?? null
    const sidebar = screen?.querySelector<HTMLElement>('.app-sidebar') ?? null
    const selector = `[data-mascot-target="${step.target}"]`
    const target = Array.from(screen?.querySelectorAll<HTMLElement>(selector) ?? []).find(isVisibleTarget)
    function skip() {
      if (index + 1 < steps.length) setIndex(index + 1)
      else onFinish(true)
    }
    if (!target) {
      skip()
      return
    }

    const initial = measureTarget(target, screen, header, sidebar)
    if ((initial.highlight?.height ?? 0) < Math.min(target.getBoundingClientRect().height, 48)) {
      target.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'instant' })
    }

    let frame = 0
    function update() {
      if (!target || !isVisibleTarget(target)) {
        skip()
        return
      }
      setLayout(measureTarget(target, screen, header, sidebar))
    }
    function scheduleUpdate() {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(update)
    }
    update()
    const observer = new ResizeObserver(scheduleUpdate)
    for (const element of [target, screen, header, sidebar]) {
      if (element) observer.observe(element)
    }
    window.addEventListener('scroll', scheduleUpdate, true)
    window.addEventListener('resize', scheduleUpdate)
    window.addEventListener('orientationchange', scheduleUpdate)
    window.visualViewport?.addEventListener('resize', scheduleUpdate)
    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
      window.removeEventListener('scroll', scheduleUpdate, true)
      window.removeEventListener('resize', scheduleUpdate)
      window.removeEventListener('orientationchange', scheduleUpdate)
      window.visualViewport?.removeEventListener('resize', scheduleUpdate)
    }
  }, [index, onFinish, step, steps.length])

  function handleKeys(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'Escape') {
      event.preventDefault()
      event.stopPropagation()
      onFinish(false)
    }
    if (event.key !== 'Tab') return
    const buttons = dialog.current?.querySelectorAll('button')
    if (!buttons?.length) return
    const first = buttons[0]
    const last = buttons[buttons.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  const sizing = availableSpace === undefined ? undefined : { '--tour-card-space': `${availableSpace}px` } as CSSProperties

  return <div className="mascot-tour" data-tour={id} data-card-placement={placement} style={sizing} onKeyDown={handleKeys}>
    {highlight ? <div className="mascot-tour-highlight" style={highlight} aria-hidden="true"/> : <div className="mascot-tour-shade" aria-hidden="true"/>}
    <div className="mascot-tour-card" role="dialog" aria-modal="true" aria-label="Recorrido de Cris" ref={dialog}>
      <img src={art.src} width={art.width} height={art.height} alt="" draggable={false}/>
      <div className="mascot-tour-step" aria-live="polite"><small>Paso {index + 1} de {steps.length}</small><p>{step.text}</p></div>
      <div className="mascot-tour-actions">
        <button className="button button-primary" type="button" ref={next} onClick={() => index + 1 < steps.length ? setIndex(index + 1) : onFinish(true)}>{index + 1 < steps.length ? 'Siguiente' : 'Terminar'}</button>
        <button className="button button-secondary" type="button" onClick={() => onFinish(false)}>Omitir</button>
      </div>
    </div>
  </div>
}
