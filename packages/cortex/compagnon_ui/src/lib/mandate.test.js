import test from 'node:test'
import assert from 'node:assert/strict'
import {
  getMandate,
  setMandate,
  resetMandate,
  mandateNeedsAsk,
  mandateAllows,
  filterIntentsByMandate,
} from './mandate.js'
import { getStudioGoal, patchStudioGoal } from './studioGoal.js'

test('resetMandate: pas frais, défaut jobs_l2 soft', () => {
  resetMandate()
  patchStudioGoal({ goalId: 'jobs_l2', enabled: true })
  assert.equal(mandateNeedsAsk(), true)
  assert.equal(mandateAllows('jobs_l2'), true)
  assert.equal(mandateAllows('studio'), false)
})

test('setMandate: TTL frais + aligne studioGoal', () => {
  resetMandate()
  const m = setMandate(['studio', 'lan'])
  assert.equal(m.fresh, true)
  assert.deepEqual(m.watch, ['studio', 'lan'])
  assert.equal(mandateNeedsAsk(), false)
  assert.equal(mandateAllows('studio'), true)
  assert.equal(mandateAllows('mail'), false)
  assert.equal(getStudioGoal().goalId, 'studio_craft')
})

test('filterIntentsByMandate: garde passe, mail filtré', () => {
  resetMandate()
  setMandate(['jobs_l2'])
  const intents = [
    { id: 'mail', label: 'Mails' },
    { id: 'jobs', label: 'Jobs' },
    { id: 'selfcheck', label: 'Selfcheck' },
  ]
  const guard = filterIntentsByMandate(intents, { isGuard: true })
  assert.equal(guard.length, 3)
  const filtered = filterIntentsByMandate(intents, { isGuard: false })
  assert.ok(filtered.some((i) => i.id === 'jobs'))
  assert.ok(!filtered.some((i) => i.id === 'mail'))
})

test('getMandate: scopes catalogue exposés', () => {
  const m = getMandate()
  assert.ok(m.scopes.length >= 4)
  assert.ok(m.scopes.some((s) => s.id === 'studio'))
})
