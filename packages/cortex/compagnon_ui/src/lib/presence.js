/**
 * Bus présence Compagnon — réactions lisibles (pas un diaporama).
 * Jamais d’auto-exec : pure UI.
 */

/** @typedef {{
 *   mood?: string,
 *   talk?: string,
 *   pulse?: 'ok'|'warn'|'alert',
 *   label?: string,
 *   result?: string,
 *   holdMs?: number,
 * }} PresenceEvent */

const listeners = new Set()
/** @type {PresenceEvent | null} */
let last = null

function applyToFaceRig(evt) {
  if (typeof window === 'undefined' || !window.FaceRig) return
  try {
    if (evt.mood) window.FaceRig.setMood(evt.mood)
    // talk court seulement (évite cycle bouche long / bruit)
    if (evt.talk && String(evt.talk).length <= 80) {
      window.FaceRig.say(evt.talk)
    } else if (evt.mood === 'happy' || evt.mood === 'curious') {
      window.FaceRig.setTalking?.(700)
    }
    if (evt.pulse && typeof window.FaceRig.pulse === 'function') {
      window.FaceRig.pulse(evt.pulse)
    }
  } catch {
    /* ignore */
  }
}

/**
 * @param {PresenceEvent} evt
 */
export function presenceReact(evt) {
  if (!evt || typeof evt !== 'object') return
  last = { ...evt, at: Date.now() }
  applyToFaceRig(evt)
  listeners.forEach((fn) => {
    try {
      fn(last)
    } catch {
      /* ignore */
    }
  })
}

/** Réponse chat : humeur légère, pas de lip-sync sur le pavé LLM. */
export function presenceTalk(text, mood = 'curious') {
  presenceReact({
    mood,
    pulse: mood === 'tense' ? 'warn' : 'ok',
    label: mood === 'tense' ? '…' : 'répond',
    // pas de talk long → évite succession de frames
  })
}

export function presenceAgirResult(ok, summary = '') {
  const short = String(summary || '')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 96)
  presenceReact({
    mood: ok ? 'happy' : 'tense',
    talk: ok ? 'ok' : 'hmm',
    pulse: ok ? 'ok' : 'warn',
    label: ok ? 'Réel · ok' : 'À revoir',
    result: short || (ok ? 'Action terminée (ok).' : 'Action en échec / revue.'),
    holdMs: 8000,
  })
}

export function presenceInitiative(message) {
  presenceReact({
    mood: 'tense',
    talk: '!',
    pulse: 'alert',
    label: 'Initiative',
    result: String(message || 'Je vois quelque chose — Agir ?').slice(0, 120),
    holdMs: 10000,
  })
}

/** @param {(e: PresenceEvent) => void} fn */
export function onPresence(fn) {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

export function lastPresence() {
  return last
}
