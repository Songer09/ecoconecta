const prefix = 'ecoconecta.mascota.'
const greetingKey = `${prefix}saludo`

export function markFirstGreeting() {
  try {
    if (sessionStorage.getItem(greetingKey)) return false
    sessionStorage.setItem(greetingKey, '1')
  } catch { /* The current mount still remembers whether we greeted. */ }
  return true
}

export function saveTour(id: string, result: 'completado' | 'omitido') {
  try {
    localStorage.setItem(`${prefix}recorrido.${id}`, result)
  } catch { /* The tour remains available when storage is blocked. */ }
}

export function resetMascotStorage() {
  for (const kind of ['localStorage', 'sessionStorage'] as const) {
    try {
      const storage = window[kind]
      for (const key of Object.keys(storage)) {
        if (key.startsWith(prefix)) storage.removeItem(key)
      }
    } catch { /* Storage can be unavailable in private mode. */ }
  }
}
