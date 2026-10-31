import test from 'node:test'
import assert from 'node:assert/strict'
import {
  setFocusContext,
  getFocusContext,
  onFocusChange,
  resetFocusContext,
} from './focusContext.js'

test('focusContext: état initial et mise à jour', () => {
  resetFocusContext()
  const initial = getFocusContext()
  assert.equal(initial.category, 'general')
  assert.equal(initial.attitude, 'serene')

  setFocusContext({ category: 'coding', attitude: 'think', app: 'cursor' })
  const updated = getFocusContext()
  assert.equal(updated.category, 'coding')
  assert.equal(updated.attitude, 'think')
  assert.equal(updated.app, 'cursor')
})

test('focusContext: listener de changement de focus', () => {
  resetFocusContext()
  let captured = null
  const unsub = onFocusChange((ctx) => {
    captured = ctx
  })

  setFocusContext({ category: 'gamedev', attitude: 'curious', app: 'godot' })
  assert.ok(captured)
  assert.equal(captured.category, 'gamedev')
  assert.equal(captured.app, 'godot')

  unsub()
  setFocusContext({ category: 'terminal', attitude: 'alert' })
  assert.equal(captured.category, 'gamedev') // inchangé car unsub
})

