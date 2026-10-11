import test from 'node:test'
import assert from 'node:assert/strict'
import {
  fingerprintFromStatus,
  canShowInitiative,
  snoozeInitiative,
  isInitiativeSnoozed,
  shouldOfferFromStatus,
  recordInitiativeFeedback,
  formatDiscussReply,
} from './initiativeQuota.js'
import { resetStudioGoalFeedback, patchStudioGoal } from './studioGoal.js'
import { resetMandate, setMandate } from './mandate.js'

function baseStatus(extra = {}) {
  return {
    enabled: true,
    silence_seconds_est: 200,
    infra_signals: { ad_agent_reachable: true, orchestrator_reachable: true },
    ...extra,
  }
}

function resetAll() {
  resetStudioGoalFeedback()
  resetMandate()
  patchStudioGoal({ goalId: 'jobs_l2', enabled: true, feedback: {} })
}

test('fingerprintFromStatus: privilégie desktop_agent_down plutôt qu un last_job_id changeant', () => {
  const status1 = {
    enabled: true,
    last_job_id: 'uuid-1111',
    infra_signals: { desktop_agent_down: true },
  }
  const status2 = {
    enabled: true,
    last_job_id: 'uuid-2222',
    infra_signals: { desktop_agent_down: true },
  }
  assert.equal(fingerprintFromStatus(status1), 'infra:desktop_agent_down')
  assert.equal(fingerprintFromStatus(status2), 'infra:desktop_agent_down')
})

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
  resetAll()
  setMandate(['jobs_l2'])
  const id = 'infra:test_snooze'
  assert.equal(isInitiativeSnoozed(id), false)

  snoozeInitiative(id, 2)
  assert.equal(isInitiativeSnoozed(id), true)

  const gate = canShowInitiative(id)
  assert.equal(gate.ok, false)
  assert.equal(gate.reason, 'snoozed')

  snoozeInitiative('infra:ad_agent_down', 2)
  const status = baseStatus({ infra_signals: { ad_agent_down: true } })
  const offer = shouldOfferFromStatus(status)
  assert.equal(offer.offer, false)
  assert.equal(offer.reason, 'snoozed')
})

test('shouldOfferFromStatus: teinte le message avec l objectif Jobs L2', () => {
  resetAll()
  setMandate(['jobs_l2'])
  const status = baseStatus({
    tension: 0.9,
    tension_causes: ['jobs_l2:2'],
  })
  const offer = shouldOfferFromStatus(status)
  assert.equal(offer.offer, true)
  assert.equal(offer.id, 'jobs:l2:2')
  assert.equal(offer.offerType, 'garde')
  assert.match(offer.message, /Jobs L2|job/i)
  assert.equal(offer.goal?.id, 'jobs_l2')
})

test('feedback: 2 ignores sans accept freinent le signal', () => {
  resetAll()
  setMandate(['jobs_l2'])
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

test('sans mandat: propose mandate:ask avant opportunité idle', () => {
  resetAll()
  const status = baseStatus({
    tension: 0.45,
    curiosite: 1,
    silence_seconds_est: 200,
    tension_causes: ['silence'],
    last_action: {
      kind: 'plan',
      cause: 'silence',
      message: 'Silence prolongé (aucune alerte infra) — je propose…',
    },
  })
  const offer = shouldOfferFromStatus(status)
  assert.equal(offer.offer, true)
  assert.equal(offer.id, 'mandate:ask')
  assert.equal(offer.offerType, 'mandat')
  assert.ok(offer.intents?.some((i) => i.mandatePick))
})

test('silence prolongé + mandat frais: fingerprint jobs:idle et offre toast', () => {
  resetAll()
  setMandate(['jobs_l2'])
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
  assert.equal(offer.offerType, 'opportunite')
  assert.ok(offer.intents?.length >= 1)
  assert.match(offer.message, /Silence prolongé|mails|Jobs/i)
})

test('formatDiscussReply: Détails ancré sur toast LAN, pas job L2 du statut', () => {
  resetAll()
  setMandate(['lan'])
  const status = baseStatus({
    last_job_id: '55ff02f951c448619df80a758dd61527',
    last_action: {
      kind: 'plan',
      message: 'Plan léger conseillé pour clarifier l’objectif.',
    },
  })
  const text = formatDiscussReply(status, {
    message:
      'Plan léger conseillé pour clarifier l’objectif. (objectif · Veiller le LAN)',
    intents: [
      {
        id: 'open_jobs_job',
        label: 'Revue job L2',
        sourceText: 'ouvre http://192.168.0.140:8080/#/jobs dans le navigateur',
        hint: 'job 55ff02f9…',
      },
    ],
    goal: {
      id: 'lan_watch',
      title: 'Veiller le LAN',
      description: 'Selfcheck, sondes AD/orch, inventaire — lecture seule prioritaire.',
    },
  })
  assert.match(text, /Veiller le LAN/)
  assert.match(text, /rappel de cap|Selfcheck LAN/i)
  assert.doesNotMatch(text, /Revue job L2/)
})

test('mandat studio + silence long: offre studio:idle', () => {
  resetAll()
  setMandate(['studio'])
  const status = baseStatus({
    tension: 0.4,
    curiosite: 1,
    silence_seconds_est: 2000,
    tension_causes: ['silence'],
    last_action: { kind: 'plan', cause: 'silence', message: 'Silence prolongé…' },
  })
  const offer = shouldOfferFromStatus(status)
  assert.equal(offer.offer, true)
  assert.equal(offer.id, 'studio:idle')
  assert.equal(offer.offerType, 'studio')
})
