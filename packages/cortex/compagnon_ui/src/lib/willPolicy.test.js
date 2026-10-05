import test from 'node:test'
import assert from 'node:assert/strict'
import {
  isSmokeWill,
  autoValidateMode,
  intentsForWill,
  willAutoValidateEnabled,
} from './willPolicy.js'

test('isSmokeWill: id et title', () => {
  assert.equal(isSmokeWill({ id: 'evo:smoke1', title: 'x' }), true)
  assert.equal(isSmokeWill({ id: 'evo:ce21', title: 'Smoke évolution' }), true)
  assert.equal(isSmokeWill({ id: 'evo:ce21', title: 'Brancher seeds' }), false)
})

test('autoValidateMode: brief vs evolution', () => {
  assert.equal(autoValidateMode({ kind: 'morning_brief', id: 'morning_brief:d' }), 'brief')
  assert.equal(autoValidateMode({ kind: 'evolution', id: 'evo:smoke1', title: 'Smoke' }), 'team_l1')
  assert.equal(autoValidateMode({ kind: 'evolution', id: 'evo:real', title: 'Idée' }), null)
})

test('intentsForWill: morning_brief', () => {
  const intents = intentsForWill({
    id: 'morning_brief:2026-09-30',
    kind: 'morning_brief',
    title: 'Brief du matin',
  })
  assert.ok(intents.some((i) => i.sourceText === 'fais mon brief du matin'))
})

test('willAutoValidateEnabled: défaut true', () => {
  assert.equal(willAutoValidateEnabled(), true)
})
