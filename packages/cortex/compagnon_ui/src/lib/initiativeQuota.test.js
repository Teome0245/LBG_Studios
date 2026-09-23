import test from 'node:test'
import assert from 'node:assert/strict'
import {
  fingerprintFromStatus,
  canShowInitiative,
  markInitiativeShown,
  snoozeInitiative,
  isInitiativeSnoozed,
  shouldOfferFromStatus,
  recordInitiativeFeedback,
} from './initiativeQuota.js'
import { resetStudioGoalFeedback } from './studioGoal.js'

function baseStatus(extra = {}) {
  return {
    enabled: true,
    silence_seconds_est: 200,
    infra_signals: { ad_agent_reachable: true, orchestrator_reachable: true },
    ...extra,
  }
}

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
  const status = baseStatus({ infra_signals: { ad_agent_down: true } })
  const offer = shouldOfferFromStatus(status)
  assert.equal(offer.offer, false)
  assert.equal(offer.reason, 'snoozed')
})

test('shouldOfferFromStatus: teinte le message avec l objectif Jobs L2', () => {
  resetStudioGoalFeedback()
  const status = baseStatus({
    tension: 0.9,
    tension_causes: ['jobs_l2:2'],
  })
  const offer = shouldOfferFromStatus(status)
  assert.equal(offer.offer, true)
  assert.equal(offer.id, 'jobs:l2:2')
  assert.match(offer.message, /Jobs L2|job/i)
  assert.equal(offer.goal?.id, 'jobs_l2')
})

test('feedback: 2 ignores sans accept freinent le signal', () => {
  resetStudioGoalFeedback()
  recordInitiativeFeedback('jobs:l2:2', 'dismiss')
  recordInitiativeFeedback('jobs:l2:2', 'dismiss')
  const status = baseStatus({
    tension: 0.9,
    tension_causes: ['jobs_l2:2'],
  })
  const offer = shouldOfferFromStatus(status)
  assert.equal(offer.offer, false)
  assert.equal(offer.reason, 'learned_dismiss')
})

test('silence prolongé: fingerprint jobs:idle et offre toast (vivant)', () => {
  resetStudioGoalFeedback()
  const status = baseStatus({
    tension: 0.45,
    curiosite: 1,
    silence_seconds_est: 14190,
    tension_causes: ['silence'],
    last_job_id: '55ff02f951c448619df80a758dd61527',
    last_action: {
      kind: 'plan',
      cause: 'silence',
      message:
        'Silence prolongé (aucune alerte infra) — je propose une action concrète : mails récents, selfcheck LAN ou revue Pilot Jobs L2.',
    },
  })
  assert.equal(fingerprintFromStatus(status), 'jobs:idle')
  const offer = shouldOfferFromStatus(status)
  assert.equal(offer.offer, true)
  assert.equal(offer.id, 'jobs:idle')
  assert.ok(offer.intents?.length >= 1)
  assert.match(offer.message, /Silence prolongé|mails|Jobs/i)
})
