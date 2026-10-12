import test from 'node:test'
import assert from 'node:assert/strict'
import { formatSelfLine, offerFromSelf, offerFromEvolutionSeed } from './selfPresence.js'

test('formatSelfLine: drives + intent', () => {
  const line = formatSelfLine({
    enabled: true,
    state: {
      identity: { display_name: 'Cortex' },
      intent: { primary: 'monitor' },
      drives: { curiosity: 1, tension: 0.45, social_hunger: 0.2 },
    },
  })
  assert.match(line, /Cortex/)
  assert.match(line, /monitor/)
  assert.match(line, /curiosité 100%/)
})

test('formatSelfLine: memory_refs leçons', () => {
  const line = formatSelfLine({
    enabled: true,
    state: {
      identity: { display_name: 'Cortex' },
      intent: { primary: 'monitor' },
      drives: { curiosity: 0.5, tension: 0 },
      memory_refs: { lessons_count: 12 },
    },
  })
  assert.match(line, /12 leçons/)
})

test('offerFromSelf: curiosity haute → Team L1', () => {
  const offer = offerFromSelf({
    enabled: true,
    state: {
      drives: { curiosity: 0.95, tension: 0.2, social_hunger: 0.1 },
      pending_will: [],
    },
  })
  assert.equal(offer.offer, true)
  assert.equal(offer.id, 'self:curiosity')
  assert.ok(offer.intents?.some((i) => i.teamSpawn))
})

test('offerFromSelf: pending_will prioritaire', () => {
  const offer = offerFromSelf({
    enabled: true,
    state: {
      drives: { curiosity: 1 },
      pending_will: [{ id: 'w1', title: 'Relire leçons', kind: 'evolution' }],
    },
  })
  assert.equal(offer.offer, true)
  assert.match(offer.id, /^self:will:/)
  assert.match(offer.message, /Relire/)
  assert.equal(offer.willId, 'w1')
  assert.ok(offer.intents?.some((i) => i.teamSpawn))
})

test('offerFromSelf: morning_brief → intent Agir brief', () => {
  const offer = offerFromSelf({
    enabled: true,
    state: {
      drives: { curiosity: 0.2 },
      pending_will: [
        { id: 'morning_brief:2026-09-30', kind: 'morning_brief', title: 'Brief du matin' },
      ],
    },
  })
  assert.equal(offer.offer, true)
  assert.equal(offer.autoValidate, 'brief')
  assert.ok(offer.intents?.some((i) => i.sourceText === 'fais mon brief du matin'))
})

test('offerFromEvolutionSeed: score suffisant', () => {
  const offer = offerFromEvolutionSeed({
    text: 'Ajouter un dial spontanéité côté Character',
    score: 1.5,
    will_id: 'evo:abc',
  })
  assert.equal(offer.offer, true)
  assert.match(offer.id, /evo/)
  assert.ok(offer.intents?.some((i) => i.teamSpawn))
})

test('offerFromEvolutionSeed: score bas → refuse', () => {
  const offer = offerFromEvolutionSeed({ text: 'trop faible idée', score: 0.1 })
  assert.equal(offer.offer, false)
})
