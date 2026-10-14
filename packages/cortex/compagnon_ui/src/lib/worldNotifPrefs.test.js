/**
 * node --test src/lib/worldNotifPrefs.test.js
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  categoryForEventKind,
  defaultWorldNotifPrefs,
  filterWorldEvents,
} from './worldNotifPrefs.js'

test('defaults: tout allumé (ops_jobs inclus)', () => {
  const p = defaultWorldNotifPrefs()
  assert.equal(p.world_marking, true)
  assert.equal(p.companion_social, true)
  assert.equal(p.ops_jobs, true)
})

test('filterWorldEvents: coupe world_marking sans toucher escort', () => {
  const prefs = {
    world_marking: false,
    companion_social: true,
    ops_jobs: true,
  }
  const out = filterWorldEvents(
    [
      { kind: 'boss_defeated', text: 'boss' },
      { kind: 'companion.escort', text: 'nix' },
    ],
    prefs,
  )
  assert.equal(out.length, 1)
  assert.equal(out[0].kind, 'companion.escort')
})

test('categoryForEventKind', () => {
  assert.equal(categoryForEventKind('companion.escort'), 'companion_social')
  assert.equal(categoryForEventKind('boss_defeated'), 'world_marking')
})
