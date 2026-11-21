import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import type { MascotMessage } from './mascotMessages'
import { createMascotReminder } from './mascotReminder'
import type { MascotInteraction, ReminderContext } from './mascotReminder'

type Scene = { message: MascotMessage; text?: string }
type Moment = { message: MascotMessage; duration: number; sequence: number }
type Report = { scene?: Scene; hidden?: boolean; blocksReminder?: boolean }
type Actions = {
  report: (id: symbol, entry?: Report) => void
  showMoment: (message: MascotMessage, duration?: number) => void
  endMoment: (sequence: number) => void
  updateReminderContext: (context: ReminderContext) => void
  recordMascotInteraction: (kind: MascotInteraction) => void
}

const MascotActions = createContext<Actions>({
  report: () => {}, showMoment: () => {}, endMoment: () => {},
  updateReminderContext: () => {}, recordMascotInteraction: () => {},
})
const MascotState = createContext<{ scene?: Scene; hidden: boolean; reminderBlocked: boolean; moment?: Moment }>({ hidden: false, reminderBlocked: false })

export function MascotProvider({ children }: { children: ReactNode }) {
  const [reports, setReports] = useState(new Map<symbol, Report>())
  const [moment, setMoment] = useState<Moment>()
  const counter = useRef(0)
  const activeMoment = useRef<number>()
  const reminder = useRef<ReturnType<typeof createMascotReminder>>()

  const report = useCallback((id: symbol, entry?: Report) => {
    setReports((current) => {
      if (!entry && !current.has(id)) return current
      const next = new Map(current)
      if (entry) next.set(id, entry)
      else next.delete(id)
      return next
    })
  }, [])
  const showMoment = useCallback((message: MascotMessage, duration = 4000) => {
    counter.current += 1
    const sequence = counter.current
    activeMoment.current = sequence
    reminder.current?.setMomentActive(true)
    reminder.current?.record('message')
    setMoment({ message, duration, sequence })
  }, [])
  const endMoment = useCallback((sequence: number) => {
    if (activeMoment.current !== sequence) return
    activeMoment.current = undefined
    reminder.current?.setMomentActive(false)
    setMoment(undefined)
  }, [])

  reminder.current ??= createMascotReminder(showMoment)
  const reminders = reminder.current
  useEffect(reminders.start, [reminders])

  const actions = useMemo(() => ({
    report, showMoment, endMoment,
    updateReminderContext: reminders.updateContext,
    recordMascotInteraction: reminders.record,
  }), [report, showMoment, endMoment, reminders])
  const entries = Array.from(reports.values())
  const scene = entries.reverse().find((entry) => entry.scene)?.scene
  return <MascotActions.Provider value={actions}>
    <MascotState.Provider value={{ hidden: entries.some((entry) => entry.hidden), reminderBlocked: entries.some((entry) => entry.blocksReminder), scene, moment }}>{children}</MascotState.Provider>
  </MascotActions.Provider>
}

export function useMascotScene(message?: MascotMessage, text?: string) {
  const { report } = useContext(MascotActions)
  const id = useRef(Symbol('mascot scene'))
  useEffect(() => {
    if (!message) return
    const token = id.current
    report(token, { scene: { message, text } })
    return () => report(token)
  }, [message, text, report])
}

export function useMascotHidden(hidden: boolean) {
  const { report } = useContext(MascotActions)
  const id = useRef(Symbol('mascot hidden'))
  useEffect(() => {
    if (!hidden) return
    const token = id.current
    report(token, { hidden: true })
    return () => report(token)
  }, [hidden, report])
}

export function useMascotReminderBlock(blocked: boolean) {
  const { report } = useContext(MascotActions)
  const id = useRef(Symbol('mascot reminder block'))
  useEffect(() => {
    if (!blocked) return
    const token = id.current
    report(token, { blocksReminder: true })
    return () => report(token)
  }, [blocked, report])
}

export const useMascotActions = () => useContext(MascotActions)
export const useMascotState = () => useContext(MascotState)
