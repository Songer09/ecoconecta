export type MascotExpression = 'bienvenida' | 'explicando' | 'pensando' | 'feliz' | 'aprendiendo' | 'celebrando' | 'triste' | 'despedida'
export type MascotPosture = 'completa' | 'mini'

type Artwork = {
  src: string
  width: number
  height: number
  // Position of the face in the image, plus rendered width as a multiple of the mini circle.
  face: { x: number; y: number; scale: number }
}

const welcomeArt: Artwork = {
  src: '/images/mascota/bienvenida.png', width: 355, height: 370,
  face: { x: 57, y: 43, scale: 1.85 },
}

export const mascotArt: Record<MascotExpression, Artwork> = {
  bienvenida: welcomeArt,
  explicando: { src: '/images/mascota/explicando.png', width: 362, height: 370, face: { x: 54, y: 44, scale: 1.95 } },
  pensando: { src: '/images/mascota/pensando.png', width: 320, height: 357, face: { x: 55, y: 44, scale: 1.8 } },
  feliz: welcomeArt,
  aprendiendo: { src: '/images/mascota/aprendiendo.png', width: 299, height: 351, face: { x: 49, y: 41, scale: 1.65 } },
  celebrando: { src: '/images/mascota/celebrando.png', width: 379, height: 365, face: { x: 53, y: 43, scale: 2.05 } },
  triste: { src: '/images/mascota/triste.png', width: 446, height: 559, face: { x: 55.5, y: 43.6, scale: 1.96 } },
  despedida: { src: '/images/mascota/despedida.png', width: 456, height: 547, face: { x: 54.3, y: 43.8, scale: 1.99 } },
}
