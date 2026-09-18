import test from 'node:test'
import assert from 'node:assert/strict'
import {
  fingerprintFromStatus,
  canShowInitiative,
  markInitiativeShown,
  snoozeInitiative,
  isInitiativeSnoozed,
  shouldOfferFromStatus,
} from './initiativeQuota.js'

test('fingerprintFromStatus: privilégie ad_agent_down plutôt qu un last_job_id changeant', () => {
  const status1 = {
    enabled: true,
    last_job_id: 'uuid-1111',
    infra_signals: { ad_agent_down: true },
  }
  const status2 = {
    enabled: true,
    last_job_id: 'uuid-2222',
    infra_signals: { ad_agent_down: true },
  }
  // Le fingerprint doit rester identique pour le même problème infra
  assert.equal(fingerprintFromStatus(status1), 'infra:ad_agent_down')
  assert.equal(fingerprintFromStatus(status2), 'infra:ad_agent_down')
})

test('fingerprintFromStatus: utilise job:uuid uniquement si aucun signal prioritaire', () => {
  const status = {
    enabled: true,
    last_job_id: 'uuid-job-3333',
    infra_signals: { ad_agent_reachable: true, orchestrator_reachable: true },
  }
  assert.equal(fingerprintFromStatus(status), 'job:uuid-job-3333')
})

test('snoozeInitiative: snooze un fingerprint et empêche son affichage', () => {
  const id = 'infra:test_snooze'
  assert.equal(isInitiativeSnoozed(id), false)

  snoozeInitiative(id, 2)
  assert.equal(isInitiativeSnoozed(id), true)

  const gate = canShowInitiative(id)
  assert.equal(gate.ok, false)
  assert.equal(gate.reason, 'snoozed')

  // Snoozer infra:ad_agent_down
  snoozeInitiative('infra:ad_agent_down', 2)
  const status = {
    enabled: true,
    silence_seconds_est: 200,
    infra_signals: { ad_agent_down: true },
  }
  const offer = shouldOfferFromStatus(status)
  assert.equal(offer.offer, false)
  assert.equal(offer.reason, 'snoozed')
})
