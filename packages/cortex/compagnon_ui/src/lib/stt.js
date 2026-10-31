/**
 * stt.js — Reconnaissance Vocale (Voice-In / STT) pour le Compagnon LBG.
 *
 * Supporte :
 * - Web Speech API native du navigateur / Electron (SpeechRecognition / webkitSpeechRecognition).
 * - Push-to-Talk via raccourci global Electron ou bouton UI.
 * - Transcription temps réel (interim results) et finale.
 * - Nettoyage et ponctuation automatique du texte dicté.
 */

export const STT_ENABLED_KEY = 'lbg_compagnon_stt_enabled_v1'

export function isSttSupported() {
  if (typeof window === 'undefined') return false
  return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition)
}

export function isSttEnabled() {
  try {
    const v = localStorage.getItem(STT_ENABLED_KEY)
    if (v === null) return true // Activé par défaut si supporté
    return v === '1' || v === 'true'
  } catch {
    return true
  }
}

export function setSttEnabled(on) {
  try {
    localStorage.setItem(STT_ENABLED_KEY, on ? '1' : '0')
  } catch {
    /* ignore */
  }
}

export function toggleSttEnabled() {
  const next = !isSttEnabled()
  setSttEnabled(next)
  return next
}

/**
 * Nettoie et met en forme la transcription orale brute.
 * @param {string} raw
 * @returns {string}
 */
export function cleanTranscript(raw) {
  let s = String(raw || '').trim()
  if (!s) return ''
  // Normalisation des espaces multiples
  s = s.replace(/\s+/g, ' ')
  // Majuscule initiale
  s = s.charAt(0).toUpperCase() + s.slice(1)
  return s
}

/**
 * Contrôleur de saisie vocale réactif pour Vue / Compagnon.
 * @param {Object} options
 * @param {(transcript: string, isFinal: boolean) => void} options.onTranscript
 * @param {(error: string) => void} [options.onError]
 * @param {(state: 'idle'|'listening'|'processing'|'error') => void} [options.onStateChange]
 * @param {string} [options.lang='fr-FR']
 */
export function createVoiceInputController(options = {}) {
  const {
    onTranscript = () => {},
    onError = () => {},
    onStateChange = () => {},
    lang = 'fr-FR',
  } = options

  let recognition = null
  let state = 'idle' // 'idle' | 'listening' | 'processing' | 'error'
  let manualStop = false

  function setState(nextState) {
    state = nextState
    onStateChange(state)
  }

  function initRecognition() {
    if (typeof window === 'undefined') return null
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRec) return null

    const rec = new SpeechRec()
    rec.continuous = false
    rec.interimResults = true
    rec.lang = lang
    rec.maxAlternatives = 1

    rec.onstart = () => {
      manualStop = false
      setState('listening')
      notifyPresence('listening')
    }

    rec.onresult = (event) => {
      let interim = ''
      let final = ''

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const item = event.results[i]
        const text = item[0]?.transcript || ''
        if (item.isFinal) {
          final += text
        } else {
          interim += text
        }
      }

      if (final.trim()) {
        const cleaned = cleanTranscript(final)
        onTranscript(cleaned, true)
      } else if (interim.trim()) {
        onTranscript(cleanTranscript(interim), false)
      }
    }

    rec.onerror = (event) => {
      if (manualStop || event.error === 'aborted') {
        setState('idle')
        return
      }
      const msg = event.error === 'no-speech'
        ? 'Aucune voix détectée'
        : event.error === 'not-allowed'
        ? 'Accès micro refusé'
        : `Erreur vocale : ${event.error}`

      setState('error')
      onError(msg)
    }

    rec.onend = () => {
      if (state !== 'error') {
        setState('idle')
      }
      notifyPresence('idle')
    }

    return rec
  }

  function notifyPresence(mood) {
    try {
      if (typeof window !== 'undefined' && window.compagnonDesktop?.setMood) {
        window.compagnonDesktop.setMood(mood)
      }
    } catch {
      /* ignore */
    }
  }

  function start() {
    if (!isSttSupported()) {
      onError('Reconnaissance vocale non supportée sur ce navigateur')
      setState('error')
      return false
    }

    if (state === 'listening') return true

    try {
      if (!recognition) {
        recognition = initRecognition()
      }
      if (recognition) {
        recognition.start()
        return true
      }
    } catch (err) {
      onError(String(err?.message || err))
      setState('error')
    }
    return false
  }

  function stop() {
    manualStop = true
    if (recognition && state === 'listening') {
      try {
        recognition.stop()
      } catch {
        /* ignore */
      }
    }
    setState('idle')
  }

  function toggle() {
    if (state === 'listening') {
      stop()
      return false
    } else {
      return start()
    }
  }

  return {
    start,
    stop,
    toggle,
    getState: () => state,
    isSupported: isSttSupported,
  }
}
