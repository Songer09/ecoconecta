import { mascotArt } from './mascotConfig'
import type { MascotExpression, MascotPosture } from './mascotConfig'
import { resetMascotStorage } from './mascotStorage'

export function readMascotPreview() {
  const url = new URL(window.location.href)
  const value = url.searchParams.get('mascota')
  if (value === 'reset') {
    resetMascotStorage()
    url.searchParams.delete('mascota')
    history.replaceState(history.state, '', url)
    return
  }

  const expression = value && Object.prototype.hasOwnProperty.call(mascotArt, value) ? value as MascotExpression : undefined
  const requestedPosture = url.searchParams.get('postura')
  const posture: MascotPosture | undefined = requestedPosture === 'completa' || requestedPosture === 'mini' ? requestedPosture : undefined
  const open = url.searchParams.get('globo') === '1'
  const reminder = value === 'recordatorio'
  if (!expression && !posture && !open && !reminder) return
  return {
    expression, posture, open, reminder,
    text: open && !reminder
      ? 'Vista de prueba de Cris. El globo puede mostrar instrucciones más largas que las habituales. Este mensaje sirve para revisar cómo se acomoda el texto en distintas pantallas, cómo se desplaza la lectura y si el botón de cerrar sigue al alcance.'
      : undefined,
  }
}
