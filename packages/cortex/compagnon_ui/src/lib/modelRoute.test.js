import { test } from 'node:test'
import assert from 'node:assert/strict'
import { resolveRouteTier, routeTierLabel } from './modelRoute.js'

test('resolveRouteTier prefers explicit', () => {
  assert.equal(resolveRouteTier({ route_tier: 'heavy', model: '0.8B' }), 'heavy')
  assert.equal(resolveRouteTier({ route_tier: 'light' }), 'light')
})

test('resolveRouteTier from model name', () => {
  assert.equal(resolveRouteTier({ model: 'huihui_ai/gemma-4-abliterated:12b-qat' }), 'heavy')
  assert.equal(resolveRouteTier({ model: 'huihui_ai/qwen3.5-abliterated:2B' }), 'light')
  assert.equal(resolveRouteTier({ model: 'huihui_ai/gemma-4-abliterated:e2b' }), 'light')
})

test('routeTierLabel', () => {
  assert.equal(routeTierLabel({ route_tier: 'heavy' }), 'L2 heavy')
  assert.equal(routeTierLabel({ route_tier: 'light', route_profile: 'fast' }), 'L1 fast')
})
