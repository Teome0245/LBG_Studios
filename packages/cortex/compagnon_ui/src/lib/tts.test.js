import test from 'node:test'
import assert from 'node:assert/strict'
import {
  cleanTextForSpeech,
  sanitizeForSpeech,
  generateClientVisemes,
  isTtsSupported,
  isTtsEnabled,
  setTtsEnabled,
  toggleTtsEnabled,
  getPreferredVoice,
  setPreferredVoice,
  createSpeechOutputController,
  TTS_ENABLED_KEY,
  TTS_VOICE_KEY,
} from './tts.js'

test('sanitizeForSpeech: nettoie et tronque proprement avec générations de visèmes', () => {
  const long = 'Phrase de test avec voyelles. '.repeat(30)
  const s = sanitizeForSpeech(long, 120)
  assert.ok(s.length <= 121)
  const visemes = generateClientVisemes('Salut Lyra')
  assert.ok(visemes.length >= 3)
  assert.equal(visemes[0].viseme, 'aa')
})

test('cleanTextForSpeech: élimine code markdown, liens et url pour diction propre', () => {
  const raw = 'Bonjour ! Regarde ce code ```python\nprint("hello")\n``` et visite [mon site](https://lbg.studio) pour voir `app.py`.'
  const cleaned = cleanTextForSpeech(raw)
  assert.equal(cleaned, 'Bonjour ! Regarde ce code et visite mon site pour voir app.py.')
  assert.equal(cleanTextForSpeech(''), '')
  assert.equal(cleanTextForSpeech('   ### Titre **gras** et *italique*  '), 'Titre gras et italique')
})

test('isTtsSupported: détecte window.speechSynthesis ou Audio', () => {
  assert.equal(isTtsSupported(), false)

  globalThis.window = {
    speechSynthesis: {},
    Audio: class {},
  }
  assert.equal(isTtsSupported(), true)

  delete globalThis.window
})

test('isTtsEnabled / setTtsEnabled / toggleTtsEnabled', () => {
  const store = new Map()
  globalThis.localStorage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  }

  assert.equal(isTtsEnabled(), true)

  setTtsEnabled(false)
  assert.equal(isTtsEnabled(), false)
  assert.equal(store.get(TTS_ENABLED_KEY), '0')

  const next = toggleTtsEnabled()
  assert.equal(next, true)
  assert.equal(isTtsEnabled(), true)
})

test('getPreferredVoice / setPreferredVoice', () => {
  const store = new Map()
  globalThis.localStorage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  }

  assert.equal(getPreferredVoice(), 'fr_FR-siwis-medium')

  setPreferredVoice('fr_FR-upmc-pierre')
  assert.equal(getPreferredVoice(), 'fr_FR-upmc-pierre')
  assert.equal(store.get(TTS_VOICE_KEY), 'fr_FR-upmc-pierre')
})

test('createSpeechOutputController: synthèse et pilotage de vrmPet avec visèmes', async () => {
  let playedVisemes = null
  let talkingDuration = null

  const mockVrmPet = {
    playVisemes: (visemes, dur) => {
      playedVisemes = visemes
      talkingDuration = dur
    },
    setTalking: (val) => {
      talkingDuration = val
    },
  }

  // Mock fetch pour l'API /v1/tts/synthesize
  globalThis.fetch = async () => ({
    ok: true,
    json: async () => ({
      ok: true,
      provider: 'piper',
      audio_b64: 'MOCK_AUDIO_DATA_LONG_ENOUGH_TO_PASS_CHECK_123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890',
      duration_sec: 2.5,
      visemes: [
        { time_offset: 0.1, duration: 0.15, viseme: 'aa', weight: 0.85 },
        { time_offset: 0.3, duration: 0.2, viseme: 'ee', weight: 0.8 },
      ],
    }),
  })

  const controller = createSpeechOutputController({
    apiBaseUrl: 'http://127.0.0.1:8000',
    getVrmPet: () => mockVrmPet,
  })

  const res = await controller.speak('Bonjour, je teste la voix.')
  assert.equal(res.spoken, true)
  assert.equal(res.provider, 'piper')
  assert.equal(res.visemesCount, 2)
  assert.equal(playedVisemes.length, 2)
  assert.equal(talkingDuration, 2500)

  // Test du stop
  controller.stop()
  assert.equal(talkingDuration, false)

  delete globalThis.fetch
})
