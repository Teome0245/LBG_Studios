/**
 * Consommation du SSE `POST /ask/stream` (Compagnon 1.2).
 *
 * Module pur : ni axios ni `import.meta` → testable avec `node --test`.
 * Frames : `event: <nom>` + `data: <json>` séparées par une ligne vide.
 */

function parseFrame(raw) {
  let event = 'message'
  const data = []
  for (const line of raw.split('\n')) {
    if (!line || line.startsWith(':')) continue
    const sep = line.indexOf(':')
    const field = sep === -1 ? line : line.slice(0, sep)
    let value = sep === -1 ? '' : line.slice(sep + 1)
    if (value.startsWith(' ')) value = value.slice(1)
    if (field === 'event') event = value
    else if (field === 'data') data.push(value)
  }
  if (!data.length && event === 'message') return null
  return { event, data: data.join('\n') }
}

/** Décodeur incrémental : `push(chunk)` renvoie les frames complètes. */
export function createSSEDecoder() {
  let buffer = ''
  return {
    push(chunk) {
      buffer += String(chunk).replace(/\r\n/g, '\n')
      const frames = []
      let sep
      while ((sep = buffer.indexOf('\n\n')) !== -1) {
        const raw = buffer.slice(0, sep)
        buffer = buffer.slice(sep + 2)
        const frame = parseFrame(raw)
        if (frame) frames.push(frame)
      }
      return frames
    },
    /** Frame partielle restée en buffer (diagnostic / flush). */
    pending() {
      return buffer
    },
  }
}

/** Frames d'un texte SSE complet (tests + fallback sans ReadableStream). */
export function parseSSE(text) {
  return createSSEDecoder().push(String(text || ''))
}

function safeJSON(data) {
  try {
    return JSON.parse(data)
  } catch {
    return null
  }
}

/**
 * Lit une réponse fetch en SSE et appelle `onEvent(nom, dataJson)`.
 * @param {Response} response
 * @param {{ onEvent?: (event: string, data: any) => void }} [handlers]
 */
export async function readAskStream(response, handlers = {}) {
  const { onEvent } = handlers
  const reader = response && typeof response.body?.getReader === 'function'
    ? response.body.getReader()
    : null
  if (!reader) throw new Error('flux SSE illisible (body absent)')

  const decoder = new TextDecoder()
  const sse = createSSEDecoder()
  const emit = (frames) => {
    for (const frame of frames) {
      if (onEvent) onEvent(frame.event, safeJSON(frame.data))
    }
  }

  for (;;) {
    const { value, done } = await reader.read()
    if (value) emit(sse.push(decoder.decode(value, { stream: !done })))
    if (done) {
      const tail = decoder.decode()
      if (tail) emit(sse.push(tail))
      const rest = sse.pending().trim()
      if (rest) {
        const frame = parseFrame(rest)
        if (frame && onEvent) onEvent(frame.event, safeJSON(frame.data))
      }
      return true
    }
  }
}
