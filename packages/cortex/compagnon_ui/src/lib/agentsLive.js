/**
 * Fleet Team live pour le side-panel Compagnon (:5174).
 * Source : GET /api/pilot/team/fleet — pas de clone Pilot office.
 */

import { unwrapPilot } from './missionWatch.js'

/** @typedef {{
 *   agentId: string,
 *   displayName: string,
 *   role?: string,
 *   status: string,
 *   currentAction?: string,
 *   taskId?: string,
 *   location?: string,
 *   awaitingHumanApproval?: boolean,
 *   orphan?: boolean,
 * }} AgentsLiveRow */

const STATUS_RANK = {
  busy: 0,
  review: 1,
  failed: 2,
  idle: 3,
}

/**
 * @param {unknown} data
 * @returns {{
 *   ok: boolean,
 *   agents: AgentsLiveRow[],
 *   metrics: Record<string, unknown>,
 *   jobs: Record<string, unknown>,
 *   campus: Record<string, unknown>,
 *   l2PendingCount: number,
 *   ts?: number,
 * }}
 */
export function normalizeFleet(data) {
  const body = unwrapPilot(data)
  const rawAgents = Array.isArray(body.agents) ? body.agents : []
  /** @type {AgentsLiveRow[]} */
  const agents = rawAgents
    .map((a) => {
      if (!a || typeof a !== 'object') return null
      const agentId = String(a.agent_id || a.agentId || '').trim()
      if (!agentId) return null
      return {
        agentId,
        displayName: String(a.display_name || a.displayName || agentId),
        role: a.role != null ? String(a.role) : undefined,
        status: String(a.status || 'idle').toLowerCase(),
        currentAction:
          a.current_action != null && String(a.current_action).trim()
            ? String(a.current_action).trim()
            : undefined,
        taskId: a.task_id != null && String(a.task_id) ? String(a.task_id) : undefined,
        location: a.location != null ? String(a.location) : undefined,
        awaitingHumanApproval: Boolean(a.awaiting_human_approval || a.approval_required),
        orphan: Boolean(a.orphan),
      }
    })
    .filter(Boolean)

  agents.sort((a, b) => {
    const ra = STATUS_RANK[a.status] ?? 9
    const rb = STATUS_RANK[b.status] ?? 9
    if (ra !== rb) return ra - rb
    return a.displayName.localeCompare(b.displayName, 'fr')
  })

  const team = body.team && typeof body.team === 'object' ? body.team : {}
  const metrics = body.metrics && typeof body.metrics === 'object' ? body.metrics : {}
  const jobs = body.jobs && typeof body.jobs === 'object' ? body.jobs : {}
  const campus = body.campus && typeof body.campus === 'object' ? body.campus : {}
  const l2PendingCount = Number(
    team.l2_pending_count ?? metrics.team_l2_pending ?? jobs.waiting_approval_count ?? 0,
  )

  return {
    ok: body.ok !== false,
    agents,
    metrics,
    jobs,
    campus,
    l2PendingCount: Number.isFinite(l2PendingCount) ? l2PendingCount : 0,
    ts: typeof body.ts === 'number' ? body.ts : undefined,
  }
}

/** Pastille couleur selon status fleet. */
export function statusDotClass(status) {
  const s = String(status || '').toLowerCase()
  if (s === 'busy') return 'bg-amber-400 shadow-[0_0_6px_rgba(251,191,36,0.55)]'
  if (s === 'review') return 'bg-violet-400 shadow-[0_0_6px_rgba(167,139,250,0.5)]'
  if (s === 'failed') return 'bg-rose-400'
  return 'bg-emerald-400/80'
}

export function statusLabel(status) {
  const s = String(status || '').toLowerCase()
  if (s === 'busy') return 'occupé'
  if (s === 'review') return 'revue'
  if (s === 'failed') return 'échec'
  if (s === 'idle') return 'idle'
  return s || '—'
}

/**
 * @param {{ signal?: AbortSignal }} [opts]
 */
export async function fetchAgentsLive(opts = {}) {
  const res = await fetch('/api/pilot/team/fleet', {
    headers: { Accept: 'application/json' },
    signal: opts.signal,
  })
  if (!res.ok) {
    return {
      ok: false,
      agents: [],
      metrics: {},
      jobs: {},
      campus: {},
      l2PendingCount: 0,
      error: `HTTP ${res.status}`,
    }
  }
  const data = await res.json()
  return normalizeFleet(data)
}
