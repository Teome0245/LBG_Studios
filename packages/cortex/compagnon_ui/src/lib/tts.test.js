import test from 'node:test'
import assert from 'node:assert/strict'
import { sanitizeForSpeech, isTtsEnabled, setTtsEnabled, TTS_ENABLED_KEY } from './tts.js'

test('sanitizeForSpeech: retire fences et liens', () => {
  const s = sanitizeForSpeech('Salut **toi** — voir [doc](http://x) et `code`\n```\nblock\n```fin')
  assert.ok(!s.includes('```'))
  assert.ok(!s.includes('http'))
  assert.ok(s.includes('doc'))
  assert.ok(s.includes('code'))
  assert.ok(!s.includes('**'))
})

test('sanitizeForSpeech: tronque long texte', () => {
  const long = 'Phrase. '.repeat(200)
  const s = sanitizeForSpeech(long, 120)
  assert.ok(s.length <= 121)
  assert.ok(s.endsWith('…') || s.endsWith('.'))
})

test('setTtsEnabled / isTtsEnabled (memory storage stub)', () => {
  const store = new Map()
  globalThis.localStorage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  }
  setTtsEnabled(false)
  assert.equal(isTtsEnabled(), false)
  assert.equal(store.get(TTS_ENABLED_KEY), '0')
  setTtsEnabled(true)
  assert.equal(isTtsEnabled(), true)
})
