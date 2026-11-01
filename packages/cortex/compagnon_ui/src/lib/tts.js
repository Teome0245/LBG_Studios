/**
 * tts.js — Synthèse Vocale (Voice-Out / TTS) & Contrôleur Lip-Sync pour le Compagnon LBG.
 *
 * Supporte :
 * - Lecture audio locale Piper / Kokoro avec streaming et visèmes synchronisés.
 * - Repli transparent Web Speech API (window.speechSynthesis) sans dépendance réseau.
 * - Nettoyage du texte (suppression des balises Markdown, code blocks et URL pour une diction fluide).
 * - Synchronisation en temps réel avec le contrôleur VRM (morph targets labiales).
 */

export const TTS_ENABLED_KEY = 'lbg_compagnon_tts_enabled_v1'
export const TTS_VOICE_KEY = 'lbg_compagnon_tts_voice_v1'
export const TTS_MAX_CHARS = 480

/** @type {HTMLAudioElement | null} */
let globalCurrentAudio = null
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

function notifyDesktopPresence(payload) {
  try {
    if (typeof window !== 'undefined' && window.compagnonDesktop?.notifyPresence) {
      window.compagnonDesktop.notifyPresence(payload)
    }
  } catch {
    /* ignore — hors Electron */
  }
}

/**
 * Génère une séquence de visèmes VRM côté client pour synchroniser les lèvres.
 * @param {string} text
 * @param {number} [speed=1.0]
 */
export function generateClientVisemes(text, speed = 1.0) {
  const clean = String(text || '').toLowerCase()
  const visemes = []
  let t = 0.04
  const step = 0.095 / Math.max(0.5, speed)
  for (let i = 0; i < clean.length; i++) {
    const ch = clean[i]
    let v = null
    if ('aàâä'.includes(ch)) v = 'aa'
    else if ('iîïy'.includes(ch)) v = 'ih'
    else if ('uùûüw'.includes(ch)) v = 'ou'
    else if ('eéèêë'.includes(ch)) v = 'ee'
    else if ('oôö'.includes(ch)) v = 'oh'
    if (v) {
      visemes.push({
        time_offset: Number(t.toFixed(3)),
        duration: Number((step * 1.15).toFixed(3)),
        viseme: v,
        weight: 0.82,
      })
      t += step
    } else if (ch === ' ' || ',;:.!?'.includes(ch)) {
      t += step * 0.65
    }
  }
  return visemes
}

export function isTtsSupported() {
  if (typeof window === 'undefined') return false
  return Boolean(window.speechSynthesis || typeof window.Audio !== 'undefined')
}

export function isTtsEnabled() {
  try {
    if (typeof localStorage === 'undefined') return true
    const v = localStorage.getItem(TTS_ENABLED_KEY)
    if (v === null) return true // Activé par défaut
    return v === '1' || v === 'true'
  } catch {
    return true
  }
}

export function setTtsEnabled(on) {
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(TTS_ENABLED_KEY, on ? '1' : '0')
    }
  } catch {
    /* ignore */
  }
}

export function toggleTtsEnabled() {
  const next = !isTtsEnabled()
  setTtsEnabled(next)
  return next
}

export function getPreferredVoice() {
  try {
    if (typeof localStorage !== 'undefined') {
      return localStorage.getItem(TTS_VOICE_KEY) || 'fr_FR-siwis-medium'
    }
    return 'fr_FR-siwis-medium'
  } catch {
    return 'fr_FR-siwis-medium'
  }
}

export function setPreferredVoice(voiceId) {
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(TTS_VOICE_KEY, voiceId)
    }
  } catch {
    /* ignore */
  }
}

/**
 * Nettoie le texte Markdown pour une diction orale naturelle.
 * Supprime le code, les liens bruts et la ponctuation technique.
 * @param {string} rawText
 * @returns {string}
 */
export function cleanTextForSpeech(rawText) {
  let s = String(rawText || '').trim()
  if (!s) return ''

  // 1. Supprime les blocs de code markdown ```...```
  s = s.replace(/```[\s\S]*?```/g, '')

  // 2. Supprime les extraits de code inline `...`
  s = s.replace(/`([^`]+)`/g, '$1')

  // 3. Transforme [texte](url) en texte simple
  s = s.replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')

  // 4. Supprime les URL brutes
  s = s.replace(/https?:\/\/[^\s]+/g, '')

  // 5. Supprime les puces markdown, titres et formattages gras/italique
  s = s.replace(/^[ \t]*[#*-]+[ \t]+/gm, '')
  s = s.replace(/\*\*([^*]+)\*\*/g, '$1')
  s = s.replace(/\*([^*]+)\*/g, '$1')

  // 6. Nettoyage des espaces multiples et retours chariots consécutifs
  s = s.replace(/\s+/g, ' ').trim()
  return s
}

/**
 * Appelle l'endpoint backend /v1/tts/synthesize
 * @param {string} apiBaseUrl
 * @param {string} text
 * @param {Object} [options]
 * @returns {Promise<Object>}
 */
export async function fetchSynthesizeSpeech(apiBaseUrl, text, options = {}) {
  const clean = cleanTextForSpeech(text)
  if (!clean) {
    throw new Error('empty_text')
  }
  const base = String(apiBaseUrl || '').replace(/\/$/, '')
  const voice = options.voice || getPreferredVoice()
  const speed = options.speed || 1.0

  const res = await fetch(`${base}/v1/tts/synthesize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: clean, voice, speed }),
  })

  if (!res.ok) {
    throw new Error(`tts_http_error_${res.status}`)
  }
  return res.json()
}

/**
 * Contrôleur de synthèse vocale connectant l'audio au modèle VRM.
 * @param {Object} [cfg]
 */
export function createSpeechOutputController(cfg = {}) {
  const apiBase = cfg.apiBaseUrl || ''
  const getVrmPet = cfg.getVrmPet || (() => (typeof window !== 'undefined' ? window.vrmPet : null))
  let currentAudio = null

  function stop() {
    if (currentAudio) {
      try {
        currentAudio.pause()
        currentAudio.currentTime = 0
      } catch (_) {}
      currentAudio = null
    }
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      try {
        window.speechSynthesis.cancel()
      } catch (_) {}
    }
    const pet = getVrmPet()
    if (pet && typeof pet.setTalking === 'function') {
      pet.setTalking(false)
    }
  }

  async function speak(text, opts = {}) {
    if (!isTtsEnabled()) return { spoken: false, reason: 'disabled' }
    const clean = cleanTextForSpeech(text)
    if (!clean) return { spoken: false, reason: 'empty' }

    stop()

    try {
      // 1. Tente la synthèse haute fidélité avec visèmes via le backend Cortex
      const synth = await fetchSynthesizeSpeech(apiBase, clean, opts)
      if (synth && synth.ok && synth.audio_b64) {
        const pet = getVrmPet()
        if (pet && typeof pet.playVisemes === 'function') {
          pet.playVisemes(synth.visemes, synth.duration_sec * 1000)
        } else if (pet && typeof pet.setTalking === 'function') {
          pet.setTalking(synth.duration_sec * 1000)
        }

        // Lecture du flux audio si non-mock
        if (synth.audio_b64.length > 200 && typeof Audio !== 'undefined') {
          const audio = new Audio(`data:audio/wav;base64,${synth.audio_b64}`)
          currentAudio = audio
          audio.play().catch(() => {
            // Lecture automatique bloquée par le navigateur : fallback silencieux
          })
        }
        return { spoken: true, provider: synth.provider, visemesCount: synth.visemes?.length || 0 }
      }
    } catch (_) {
      // 2. Fallback Web Speech API native du navigateur / Electron
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        const utterance = new SpeechSynthesisUtterance(clean)
        utterance.lang = opts.lang || 'fr-FR'
        utterance.rate = opts.speed || 1.0

        const pet = getVrmPet()
        const durEstMs = Math.min(15000, Math.max(1000, clean.length * 60))
        if (pet && typeof pet.setTalking === 'function') {
          pet.setTalking(durEstMs)
        }

        utterance.onend = () => {
          if (pet && typeof pet.setTalking === 'function') {
            pet.setTalking(false)
          }
        }
        window.speechSynthesis.speak(utterance)
        return { spoken: true, provider: 'web_speech' }
      }
    }

    return { spoken: false, reason: 'unsupported' }
  }

  return {
    speak,
    stop,
    isTtsEnabled,
    setTtsEnabled,
    toggleTtsEnabled,
  }
}

/** Nettoyage markdown / bruit pour oral avec troncature intelligente. */
export function sanitizeForSpeech(text, maxChars = TTS_MAX_CHARS) {
  let s = cleanTextForSpeech(text)
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

export function stopTts() {
  try {
    if (globalCurrentAudio) {
      globalCurrentAudio.pause()
      if (typeof globalCurrentAudio.removeAttribute === 'function') {
        globalCurrentAudio.removeAttribute('src')
      }
      if (typeof globalCurrentAudio.load === 'function') {
        globalCurrentAudio.load()
      }
    }
  } catch {
    /* ignore */
  }
  globalCurrentAudio = null
  if (currentObjectUrl) {
    try {
      URL.revokeObjectURL(currentObjectUrl)
    } catch {
      /* ignore */
    }
    currentObjectUrl = null
  }
  try {
    const pet = typeof window !== 'undefined' ? (window.__vrmPetInstance || window.vrmPet) : null
    if (pet && typeof pet.setTalking === 'function') {
      pet.setTalking(false)
    }
  } catch {
    /* ignore */
  }
  notifyDesktopPresence({ kind: 'idle', talking: false })
}

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
  globalCurrentAudio = audio

  const estMs = Math.min(12000, Math.max(900, 55 * spoken.length))
  const visemes = generateClientVisemes(spoken, opts.speed || 1.0)
  try {
    const pet = typeof window !== 'undefined' ? (window.__vrmPetInstance || window.vrmPet) : null
    if (pet && typeof pet.playVisemes === 'function') {
      pet.playVisemes(visemes, estMs)
    } else if (pet && typeof pet.setTalking === 'function') {
      pet.setTalking(estMs)
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
    visemes,
  })

  try {
    await audio.play()
  } catch (e) {
    return { played: false, reason: `play:${String(e?.message || e).slice(0, 80)}`, chars: spoken.length }
  }
  return { played: true, chars: spoken.length, visemesCount: visemes.length }
}
