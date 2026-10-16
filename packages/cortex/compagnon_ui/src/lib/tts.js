/**
 * TTS Compagnon — lecture via POST `/tts` (Edge DeniseNeural, fallback Piper `.111`).
 * Mute localStorage ; jamais d’auto-play si désactivé.
 */

export const TTS_ENABLED_KEY = 'lbg_compagnon_tts_enabled_v1'
export const TTS_MAX_CHARS = 480

/** @type {HTMLAudioElement | null} */
let currentAudio = null
/** @type {string | null} */
let currentObjectUrl = null
let lastHealth = { ok: false, checkedAt: 0 }

function ttsApiUrl(path) {
  const p = path.startsWith('/') ? path : `/${path}`
  try {
    const fromEnv = String(
      (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) || '',
    )
      .trim()
      .replace(/\/$/, '')
    if (fromEnv) return `${fromEnv}${p}`
    if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.PROD) {
      return `/api${p}`
    }
  } catch {
    /* node:test */
  }
  return p
}

export function isTtsEnabled() {
  try {
    const v = localStorage.getItem(TTS_ENABLED_KEY)
    if (v === null) return false
    return v === '1' || v === 'true'
  } catch {
    return false
  }
}

export function setTtsEnabled(on) {
  try {
    localStorage.setItem(TTS_ENABLED_KEY, on ? '1' : '0')
  } catch {
    /* ignore */
  }
  if (!on) stopTts()
}

export function toggleTtsEnabled() {
  const next = !isTtsEnabled()
  setTtsEnabled(next)
  return next
}

/** Nettoyage markdown / bruit pour oral. */
export function sanitizeForSpeech(text, maxChars = TTS_MAX_CHARS) {
  let s = String(text || '')
  s = s.replace(/```[\s\S]*?```/g, ' ')
  s = s.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
  s = s.replace(/`([^`]+)`/g, '$1')
  s = s.replace(/[*_~]{1,3}/g, '')
  s = s.replace(/[|#]/g, ' ')
  s = s.replace(/\s+/g, ' ').trim()
  if (s.length > maxChars) {
    let cut = s.slice(0, maxChars - 1)
    for (const sep of ['. ', '! ', '? ', '; ', ', ']) {
      const idx = cut.lastIndexOf(sep)
      if (idx >= Math.max(40, Math.floor(maxChars / 3))) {
        cut = cut.slice(0, idx + 1)
        break
      }
    }
    s = `${cut.replace(/[ ,;:]+$/, '')}…`
  }
  return s
}

function notifyDesktopPresence(payload) {
  try {
    if (typeof window !== 'undefined' && window.compagnonDesktop?.notifyPresence) {
      window.compagnonDesktop.notifyPresence(payload)
    }
  } catch {
    /* ignore — hors Electron */
  }
}

export function stopTts() {
  try {
    if (currentAudio) {
      currentAudio.pause()
      currentAudio.removeAttribute('src')
      currentAudio.load()
    }
  } catch {
    /* ignore */
  }
  currentAudio = null
  if (currentObjectUrl) {
    try {
      URL.revokeObjectURL(currentObjectUrl)
    } catch {
      /* ignore */
    }
    currentObjectUrl = null
  }
  notifyDesktopPresence({ kind: 'idle', talking: false })
}

/**
 * @returns {Promise<{ok: boolean, enabled?: boolean, voice?: string, error?: string}>}
 */
export async function fetchTtsHealth() {
  try {
    const res = await fetch(ttsApiUrl('/tts/health'), { headers: { Accept: 'application/json' } })
    if (!res.ok) {
      lastHealth = { ok: false, checkedAt: Date.now() }
      return { ok: false, error: `HTTP ${res.status}` }
    }
    const data = await res.json()
    lastHealth = { ok: Boolean(data?.ok), checkedAt: Date.now() }
    return {
      ok: Boolean(data?.ok),
      enabled: Boolean(data?.enabled),
      voice: data?.voice,
      upstream: data?.upstream,
    }
  } catch (e) {
    lastHealth = { ok: false, checkedAt: Date.now() }
    return { ok: false, error: String(e?.message || e).slice(0, 120) }
  }
}

export function lastTtsHealth() {
  return lastHealth
}

/**
 * Synthèse + lecture. No-op si mute / texte vide.
 * @param {string} text
 * @param {{ force?: boolean, voice?: string }} [opts]
 * @returns {Promise<{played: boolean, reason?: string, chars?: number}>}
 */
export async function speakText(text, opts = {}) {
  if (!opts.force && !isTtsEnabled()) {
    return { played: false, reason: 'muted' }
  }
  const spoken = sanitizeForSpeech(text)
  if (!spoken) return { played: false, reason: 'empty' }

  stopTts()

  const res = await fetch(ttsApiUrl('/tts'), {
    method: 'POST',
    headers: {
      Accept: 'audio/mpeg, audio/wav, application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text: spoken, voice: opts.voice || undefined }),
  })
  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const j = await res.json()
      detail = j?.detail || detail
    } catch {
      /* ignore */
    }
    return { played: false, reason: String(detail).slice(0, 160), chars: spoken.length }
  }

  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  currentObjectUrl = url
  const audio = new Audio(url)
  currentAudio = audio

  // Lip-sync VRM / FaceRig ≈ durée estimée (si dispo) + bridge desktop avatar
  const estMs = Math.min(12000, Math.max(900, 55 * spoken.length))
  try {
    if (typeof window !== 'undefined' && window.__vrmPetInstance?.setTalking) {
      window.__vrmPetInstance.setTalking(estMs)
    } else if (typeof window !== 'undefined' && window.FaceRig?.setTalking) {
      window.FaceRig.setTalking(estMs)
    } else if (typeof window !== 'undefined' && window.FaceRig?.say) {
      window.FaceRig.say(spoken.slice(0, 80))
    }
  } catch {
    /* ignore */
  }
  notifyDesktopPresence({
    kind: 'talking',
    talking: true,
    text: spoken.slice(0, 140),
    ms: estMs,
  })

  try {
    await audio.play()
  } catch (e) {
    return { played: false, reason: `play:${String(e?.message || e).slice(0, 80)}`, chars: spoken.length }
  }
  return { played: true, chars: spoken.length }
}
