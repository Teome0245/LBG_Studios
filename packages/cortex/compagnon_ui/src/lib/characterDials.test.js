import test from 'node:test'
import assert from 'node:assert/strict'
import {
  clampDials,
  defaultDials,
  getDials,
  setDials,
  resetDials,
  DIAL_DEFS,
} from './characterDials.js'

test('defaultDials: 7 clés', () => {
  const d = defaultDials()
  assert.equal(DIAL_DEFS.length, 7)
  for (const def of DIAL_DEFS) {
    assert.ok(typeof d[def.id] === 'number')
  }
})

test('clampDials: borne 0–1', () => {
  const d = clampDials({ piquant: 2, ego: -1, densite: 0.5 })
  assert.equal(d.piquant, 1)
  assert.equal(d.ego, 0)
  assert.equal(d.densite, 0.5)
})

test('setDials / getDials / resetDials', () => {
  resetDials()
  setDials({ humour: 0.8 })
  assert.equal(getDials().humour, 0.8)
  resetDials()
  assert.equal(getDials().humour, defaultDials().humour)
})
