import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  wantsMissionNotify,
  evaluateWatch,
  offerFromMissionDone,
  watchMission,
  listWatches,
  requestNotify,
  markNotified,
  nextMissionOffer,
  ackNotifyMessage,
} from './missionWatch.js'

// localStorage shim for node tests
const store = new Map()
globalThis.localStorage = {
  getItem: (k) => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: (k) => store.delete(k),
}

test('wantsMissionNotify detects retour quand', () => {
  assert.equal(
    wantsMissionNotify('nickel, tu peux me faire un retour quand la team a traité ce sujet ?'),
    true,
  )
  assert.equal(wantsMissionNotify('préviens-moi à la clôture'), true)
  assert.equal(wantsMissionNotify('bonjour ça va'), false)
})

test('watch + notify + evaluate closable', () => {
  store.clear()
  const w = watchMission({
    missionId: 'abc-123-def',
    objective: 'Présence → zone entraînement',
    notify: true,
  })
  assert.ok(w)
  assert.equal(listWatches().length, 1)

  const snap = {
    status: {
      mission: { id: 'abc-123-def', objective: 'Présence → zone entraînement', status: 'open' },
      decision: { mission_closable: true },
    },
    closure: { closable: true, task_stats: { pending: 0, done: 4 } },
  }
  const ev = evaluateWatch(snap, w)
  assert.equal(ev.ready, true)
  assert.equal(ev.kind, 'closable')

  const hit = nextMissionOffer(snap)
  assert.ok(hit?.offer?.offer)
  assert.match(hit.offer.message, /Team/)
  assert.match(hit.offer.id, /^mission:done:/)

  markNotified(w.missionId, 'closable')
  assert.equal(nextMissionOffer(snap), null)
})

test('evaluate replaced when other mission open', () => {
  store.clear()
  watchMission({ missionId: 'old-mission', objective: 'Plan MMORPG', notify: true })
  const snap = {
    status: { mission: { id: 'new-mission', status: 'open' } },
    closure: { closable: false },
  }
  const hit = nextMissionOffer(snap)
  assert.equal(hit?.eval?.kind, 'replaced')
})

test('requestNotify and ack', () => {
  store.clear()
  watchMission({ missionId: 'm1', objective: 'X', notify: false })
  const again = requestNotify()
  assert.equal(again?.notify, true)
  assert.match(ackNotifyMessage(again), /surveille/)
  assert.match(ackNotifyMessage(null), /noté/)
})

test('offerFromMissionDone has pilot intent', () => {
  const offer = offerFromMissionDone(
    { missionId: 'zzzzzzzz-1111', objective: 'Test' },
    { kind: 'closed', detail: 'done' },
  )
  assert.ok(offer.intents.some((i) => /Pilot/i.test(i.label)))
})
