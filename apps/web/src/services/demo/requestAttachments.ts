const images = new Map<string, { url: string; name: string }>()

export function attachDemoRequestPhoto(requestId: string, file: File) {
  const previous = images.get(requestId)
  if (previous) URL.revokeObjectURL(previous.url)
  images.set(requestId, { url: URL.createObjectURL(file), name: file.name })
}

export function getDemoRequestPhoto(requestId: string) {
  return images.get(requestId)
}
