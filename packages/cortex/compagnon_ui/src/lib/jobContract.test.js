import test from 'node:test'
import assert from 'node:assert/strict'
import {
  buildJobContract,
  formatJobBrief,
  jobContractToPilotContext,
  inferJobContractFromText,
} from './jobContract.js'

test('buildJobContract: champs requis + defaults', () => {
  const c = buildJobContract({ objective: 'Selfcheck LAN' })
  assert.equal(c.objective, 'Selfcheck LAN')
  assert.ok(c.input)
  assert.ok(c.output)
  assert.ok(c.format)
  assert.ok(c.gates.includes('L2'))
})

test('buildJobContract: refuse objective vide', () => {
  assert.throws(() => buildJobContract({ objective: '  ' }), /objective/)
})

test('formatJobBrief: 4 lignes + gardes', () => {
  const brief = formatJobBrief(
    buildJobContract({
      objective: 'Brief matin',
      input: 'Self',
      output: 'brief',
      format: '5 lignes',
      gates: ['lecture seule'],
    }),
  )
  assert.match(brief, /^Tâche : Brief matin/)
  assert.match(brief, /Entrée : Self/)
  assert.match(brief, /Gardes : lecture seule/)
})

test('jobContractToPilotContext: clé job_contract', () => {
  const ctx = jobContractToPilotContext(
    buildJobContract({ objective: 'X', recipeId: 'recipe_x' }),
  )
  assert.equal(ctx.job_contract.objective, 'X')
  assert.equal(ctx.job_contract.recipe_id, 'recipe_x')
})

test('inferJobContractFromText: mail → lecture seule', () => {
  const c = inferJobContractFromText('regarde mes mails récents')
  assert.equal(c.kind, 'mail')
  assert.ok(c.gates.includes('lecture seule'))
})

test('inferJobContractFromText: ouvre → desktop', () => {
  const c = inferJobContractFromText('ouvre vghd sur mon pc')
  assert.equal(c.kind, 'desktop')
})
