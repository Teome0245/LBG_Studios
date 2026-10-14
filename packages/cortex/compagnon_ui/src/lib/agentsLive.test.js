import { test } from 'node:test'
import assert from 'node:assert/strict'
import { normalizeFleet, statusDotClass, statusLabel } from './agentsLive.js'

test('normalizeFleet unwrap + sort busy first', () => {
  const snap = normalizeFleet({
    body: {
      ok: true,
      ts: 42,
      agents: [
        { agent_id: 'tess', display_name: 'Tess', status: 'idle', role: 'qa' },
        {
          agent_id: 'vulcan',
          display_name: 'Vulcan',
          status: 'busy',
          current_action: 'smoke LAN',
          task_id: 'task-abc',
        },
        { agent_id: 'nix', status: 'failed' },
      ],
      team: { l2_pending_count: 2 },
      jobs: { total: 5, waiting_approval_count: 1 },
      campus: { busy_agent_count: 1 },
    },
  })
  assert.equal(snap.ok, true)
  assert.equal(snap.agents.length, 3)
  assert.equal(snap.agents[0].agentId, 'vulcan')
  assert.equal(snap.agents[0].currentAction, 'smoke LAN')
  assert.equal(snap.l2PendingCount, 2)
  assert.equal(snap.ts, 42)
})

test('normalizeFleet OkEnvelope plat + ignore sans id', () => {
  const snap = normalizeFleet({
    ok: true,
    agents: [{ display_name: 'ghost' }, { agent_id: 'lia', status: 'review' }],
  })
  assert.equal(snap.agents.length, 1)
  assert.equal(snap.agents[0].agentId, 'lia')
  assert.equal(snap.agents[0].status, 'review')
})

test('status helpers', () => {
  assert.match(statusDotClass('busy'), /amber/)
  assert.equal(statusLabel('idle'), 'idle')
  assert.equal(statusLabel('busy'), 'occupé')
})
