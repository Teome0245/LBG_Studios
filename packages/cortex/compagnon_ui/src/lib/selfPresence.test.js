import test from 'node:test'
import assert from 'node:assert/strict'
import { formatSelfLine, offerFromSelf } from './selfPresence.js'

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
      pending_will: [{ id: 'w1', title: 'Relire leçons' }],
    },
  })
  assert.equal(offer.offer, true)
  assert.match(offer.id, /^self:will:/)
  assert.match(offer.message, /Relire/)
})
