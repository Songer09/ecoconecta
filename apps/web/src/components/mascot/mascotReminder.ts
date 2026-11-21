const storageKey = 'ecoconecta.mascota.recordatorios'
const minute = 60_000
const reminderMessages = ['reminderFirst', 'reminderSecond', 'reminderThird'] as const

export type ReminderContext = { eligible: boolean; slow: boolean }
export type MascotInteraction = 'message' | 'opened'

type ReminderLedger = {
  elapsed: number
  shown: number
  lastSlotAt: number | null
  lastMessageAt: number | null
  lastOpenedAt: number | null
}

function readLedger(): ReminderLedger {
  const empty: ReminderLedger = {
    elapsed: 0, shown: 0, lastSlotAt: null, lastMessageAt: null, lastOpenedAt: null,
  }
  try {
    const saved = JSON.parse(sessionStorage.getItem(storageKey) ?? 'null') as Partial<ReminderLedger> | null
    if (!saved || typeof saved.elapsed !== 'number' || !Number.isFinite(saved.elapsed) || saved.elapsed < 0) return empty
    const elapsed = saved.elapsed
    const timestamp = (value?: number | null) => typeof value === 'number' && value >= 0 && value <= elapsed ? value : null
    return {
      elapsed,
      shown: typeof saved.shown === 'number' && Number.isInteger(saved.shown)
        ? Math.min(reminderMessages.length, Math.max(0, saved.shown)) : 0,
      lastSlotAt: timestamp(saved.lastSlotAt),
      lastMessageAt: timestamp(saved.lastMessageAt),
      lastOpenedAt: timestamp(saved.lastOpenedAt),
    }
  } catch {
    return empty
  }
}

export function createMascotReminder(show: (message: typeof reminderMessages[number], duration: number) => void) {
  let ledger: ReminderLedger | undefined
  let context: ReminderContext = { eligible: false, slow: false }
  let momentActive = false
  let visibleSince: number | null = null
  let timeout: number | undefined
  let started = false

  const session = () => ledger ??= readLedger()
  const activeTime = () => session().elapsed
    + (visibleSince === null ? 0 : Math.max(0, performance.now() - visibleSince))

  function persist() {
    try {
      sessionStorage.setItem(storageKey, JSON.stringify({ ...session(), elapsed: activeTime() }))
    } catch { /* The session still works when storage is blocked. */ }
  }

  function dueAt() {
    const { lastSlotAt } = session()
    const interval = lastSlotAt === null ? (context.slow ? 4 : 2) : (context.slow ? 10 : 5)
    return (lastSlotAt ?? 0) + interval * minute
  }

  function openedRecently(now: number) {
    const { lastOpenedAt } = session()
    return lastOpenedAt !== null && now - lastOpenedAt < 3 * minute
  }

  function quietAt() {
    const { lastMessageAt } = session()
    return lastMessageAt === null ? 0 : lastMessageAt + 30_000
  }

  function clearTimer() {
    if (timeout !== undefined) window.clearTimeout(timeout)
    timeout = undefined
  }

  function canSchedule() {
    return started && visibleSince !== null && document.visibilityState === 'visible'
      && session().shown < reminderMessages.length
  }

  function schedule() {
    clearTimer()
    if (!canSchedule()) return
    const now = activeTime()
    const due = dueAt()
    if (now < due) {
      timeout = window.setTimeout(tick, Math.ceil(due - now))
    } else if (openedRecently(now) || (context.eligible && !momentActive)) {
      const next = openedRecently(now) ? now : quietAt()
      timeout = window.setTimeout(tick, Math.max(0, Math.ceil(next - now)))
    }
  }

  function tick() {
    timeout = undefined
    if (!canSchedule()) return
    const now = activeTime()
    if (now >= dueAt()) {
      const current = session()
      if (openedRecently(now)) {
        // An open help bubble already did the job. Skip this slot without spending a reminder.
        current.lastSlotAt = now
        persist()
      } else if (context.eligible && !momentActive && now >= quietAt()) {
        const message = reminderMessages[current.shown]
        current.shown += 1
        current.lastSlotAt = now
        current.lastMessageAt = now
        persist()
        show(message, 6000)
      }
    }
    schedule()
  }

  function pauseClock() {
    if (visibleSince === null) return
    session().elapsed = activeTime()
    visibleSince = null
  }

  function synchronizeVisibility() {
    if (document.visibilityState === 'visible') {
      visibleSince ??= performance.now()
    } else {
      pauseClock()
      persist()
    }
    schedule()
  }

  function suspend() {
    pauseClock()
    persist()
    clearTimer()
  }

  return {
    start() {
      started = true
      document.addEventListener('visibilitychange', synchronizeVisibility)
      window.addEventListener('pagehide', suspend)
      window.addEventListener('pageshow', synchronizeVisibility)
      synchronizeVisibility()
      return () => {
        started = false
        document.removeEventListener('visibilitychange', synchronizeVisibility)
        window.removeEventListener('pagehide', suspend)
        window.removeEventListener('pageshow', synchronizeVisibility)
        suspend()
      }
    },
    updateContext(next: ReminderContext) {
      if (context.eligible === next.eligible && context.slow === next.slow) return
      context = next
      schedule()
    },
    record(kind: MascotInteraction) {
      const now = activeTime()
      const current = session()
      current.lastMessageAt = now
      if (kind === 'opened') current.lastOpenedAt = now
      persist()
      schedule()
    },
    setMomentActive(active: boolean) {
      if (momentActive === active) return
      momentActive = active
      schedule()
    },
  }
}
