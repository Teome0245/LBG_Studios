import test from 'node:test'
import assert from 'node:assert/strict'
import {
  COMPAGNON_RECIPES,
  recipesForEmptyState,
  getRecipe,
  recipesAsPilotageActions,
} from './recipes.js'

test('COMPAGNON_RECIPES: exactement 10', () => {
  assert.equal(COMPAGNON_RECIPES.length, 10)
})

test('chaque recette a un contrat complet', () => {
  for (const r of COMPAGNON_RECIPES) {
    assert.ok(r.id.startsWith('recipe_'), r.id)
    assert.ok(r.contract?.objective, r.id)
    assert.ok(r.contract?.input, r.id)
    assert.ok(r.contract?.output, r.id)
    assert.ok(r.contract?.format, r.id)
    assert.equal(r.contract.recipeId, r.id)
    if (r.kind === 'agir') assert.ok(r.sourceText, r.id)
    if (r.kind === 'ask') {
      assert.ok(r.prompt, r.id)
      assert.match(r.prompt, /Tâche :/)
    }
  }
})

test('recipesForEmptyState: sous-ensemble utile', () => {
  const empty = recipesForEmptyState(7)
  assert.ok(empty.length >= 5)
  assert.ok(empty.length <= 7)
  assert.ok(empty.every((r) => r.emptyState))
})

test('getRecipe + pilotage', () => {
  const r = getRecipe('recipe_selfcheck')
  assert.equal(r?.kind, 'agir')
  const pal = recipesAsPilotageActions()
  assert.equal(pal.length, 10)
  assert.ok(pal[0].label.startsWith('Recette ·'))
  assert.ok(pal[0].jobContract)
})
