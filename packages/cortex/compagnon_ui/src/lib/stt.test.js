import test from 'node:test'
import assert from 'node:assert/strict'
import {
  cleanTranscript,
  isSttSupported,
  isSttEnabled,
  setSttEnabled,
  toggleSttEnabled,
  createVoiceInputController,
  STT_ENABLED_KEY,
} from './stt.js'

test('cleanTranscript: retire espaces multiples et passe majuscule initiale', () => {
  assert.equal(cleanTranscript('   bonjour lyra   '), 'Bonjour lyra')
  assert.equal(cleanTranscript('quel est   l état   du serveur'), 'Quel est l état du serveur')
  assert.equal(cleanTranscript(''), '')
})

test('isSttSupported: détecte SpeechRecognition ou webkitSpeechRecognition', () => {
  // Sans API dans l'environnement global Node
  assert.equal(isSttSupported(), false)

  // Avec mock SpeechRecognition
  globalThis.window = {
    webkitSpeechRecognition: class {},
  }
  assert.equal(isSttSupported(), true)

  delete globalThis.window
})

test('isSttEnabled / setSttEnabled / toggleSttEnabled', () => {
  const store = new Map()
  globalThis.localStorage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  }

  // Défaut true
  assert.equal(isSttEnabled(), true)

  setSttEnabled(false)
  assert.equal(isSttEnabled(), false)
  assert.equal(store.get(STT_ENABLED_KEY), '0')

  const next = toggleSttEnabled()
  assert.equal(next, true)
  assert.equal(isSttEnabled(), true)
})

test('createVoiceInputController: cycle de reconnaissance mock', () => {
  let started = false
  let stopped = false
  let registeredHandlers = {}

  class MockSpeechRecognition {
    constructor() {
      this.lang = ''
      this.continuous = false
      this.interimResults = false
    }
    set onstart(fn) { registeredHandlers.onstart = fn }
    set onresult(fn) { registeredHandlers.onresult = fn }
    set onerror(fn) { registeredHandlers.onerror = fn }
    set onend(fn) { registeredHandlers.onend = fn }

    start() {
      started = true
      registeredHandlers.onstart?.()
    }
    stop() {
      stopped = true
      registeredHandlers.onend?.()
    }
  }

  globalThis.window = {
    SpeechRecognition: MockSpeechRecognition,
  }

  let capturedTranscript = ''
  let capturedFinal = false
  let capturedState = 'idle'

  const ctrl = createVoiceInputController({
    onTranscript: (t, isFinal) => {
      capturedTranscript = t
      capturedFinal = isFinal
    },
    onStateChange: (st) => {
      capturedState = st
    },
  })

  assert.equal(ctrl.getState(), 'idle')
  const ok = ctrl.start()
  assert.equal(ok, true)
  assert.equal(started, true)
  assert.equal(capturedState, 'listening')

  // Simule résultat intermédiaire
  registeredHandlers.onresult?.({
    resultIndex: 0,
    results: [
      { 0: { transcript: 'bonjour compagnon' }, isFinal: false, length: 1 },
    ],
  })
  assert.equal(capturedTranscript, 'Bonjour compagnon')
  assert.equal(capturedFinal, false)

  // Simule résultat final
  registeredHandlers.onresult?.({
    resultIndex: 0,
    results: [
      { 0: { transcript: 'lance le diagnostic' }, isFinal: true, length: 1 },
    ],
  })
  assert.equal(capturedTranscript, 'Lance le diagnostic')
  assert.equal(capturedFinal, true)

  ctrl.stop()
  assert.equal(stopped, true)
  assert.equal(ctrl.getState(), 'idle')

  delete globalThis.window
})
