import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  normalizeMessageList,
  formatBusLine,
  nextBusInboxOffer,
  markBusSeen,
  roleToAgent,
  VALID_KINDS,
} from './teamBus.js'

const store = new Map()
globalThis.localStorage = {
  getItem: (k) => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: (k) => store.delete(k),
}

test('normalizeMessageList + format', () => {
  const msgs = normalizeMessageList({
    ok: true,
    messages: [
      {
        id: 'm1',
        from_agent: 'argus',
        to_agent: 'compagnon',
        kind: 'verify_result',
        payload: { summary: 'smoke OK' },
        created_ts: 100,
      },
    ],
  })
  assert.equal(msgs.length, 1)
  assert.match(formatBusLine(msgs[0]), /argus → compagnon/)
  assert.match(formatBusLine(msgs[0]), /smoke OK/)
})

test('nextBusInboxOffer respects seen', () => {
  store.clear()
  const msgs = normalizeMessageList({
    messages: [
      {
        id: 'm2',
        from_agent: 'lyra',
        to_agent: 'compagnon',
        kind: 'ack',
        payload: { text: 'noted' },
        created_ts: 200,
      },
      {
        id: 'm3',
        from_agent: 'argus',
        to_agent: 'themis',
        kind: 'ack',
        created_ts: 300,
      },
    ],
  })
  const hit = nextBusInboxOffer(msgs)
  assert.ok(hit?.offer?.offer)
  assert.match(hit.offer.message, /Bus Team/)
  markBusSeen(hit.msg.id)
  assert.equal(nextBusInboxOffer(msgs), null)
})

test('roleToAgent + kinds', () => {
  assert.equal(roleToAgent('qa'), 'argus')
  assert.ok(VALID_KINDS.includes('propose'))
})
