/**
 * Spawn tâche Team L1 depuis Compagnon (jamais destructeur).
 * Proxy : POST /api/pilot/team/tasks (+ run optionnel si pas d’approval).
 */

/**
 * @param {{
 *   objective: string,
 *   role?: string,
 *   priority?: string,
 *   context?: Record<string, unknown>,
 *   run?: boolean,
 * }} opts
 */
export async function spawnTeamL1(opts) {
  const objective = String(opts.objective || '').trim()
  if (!objective) return { ok: false, error: 'objective_required' }

  const role = String(opts.role || 'qa').trim() || 'qa'
  const body = {
    role,
    objective,
    actor_id: 'ui:compagnon',
    priority: opts.priority || 'normal',
    approval_required: false,
    context: {
      source: 'compagnon_initiative',
      maturity: 'M3',
      autonomy: 'L1',
      ...(opts.context && typeof opts.context === 'object' ? opts.context : {}),
    },
  }

  const res = await fetch('/api/pilot/team/tasks', {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const json = await res.json().catch(() => ({}))
  if (!res.ok || json?.ok === false) {
    return {
      ok: false,
      error: json?.error || json?.detail || `HTTP ${res.status}`,
      body: json,
    }
  }

  const taskId = json.id || json.task_id
  let ran = null
  if (opts.run !== false && taskId && !json.approval_required) {
    try {
      const runRes = await fetch(`/api/pilot/team/tasks/${encodeURIComponent(taskId)}/run`, {
        method: 'POST',
        headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      ran = await runRes.json().catch(() => ({}))
    } catch (e) {
      ran = { ok: false, error: e?.message || String(e) }
    }
  }

  // Leçon légère (best-effort) — mémoire équipe
  try {
    await fetch('/api/pilot/team/memory', {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_id: 'compagnon',
        kind: 'initiative_spawn',
        summary: `Compagnon a délégué L1 (${role}) : ${objective.slice(0, 160)}`,
        tags: ['m3', 'compagnon', 'l1'],
        task_id: taskId || '',
        meta: { maturity: 'M3' },
      }),
    })
  } catch {
    /* ignore */
  }

  // Bus ADR 0019 — handoff visible Compagnon → agent (best-effort)
  let bus = null
  try {
    const { announceSpawn } = await import('./teamBus.js')
    bus = await announceSpawn({ taskId, role, objective })
  } catch {
    bus = null
  }

  return {
    ok: true,
    id: taskId,
    status: ran?.status || json.status,
    role,
    objective,
    ran: ran && ran.ok !== false ? ran : null,
    run_error: ran && ran.ok === false ? ran.error || ran.detail : null,
    bus: bus && bus.ok ? bus.message : null,
  }
}

/**
 * Objectif par défaut depuis un message d’initiative.
 * @param {string} message
 * @param {string} [fallback]
 */
export function teamObjectiveFromInitiative(message, fallback) {
  const msg = String(message || '').trim()
  if (fallback) return String(fallback).trim()
  if (!msg) {
    return 'Revue studio L1 (lecture seule) : Self + Compagnon health — 5 lignes OK/KO.'
  }
  return `Suite initiative Compagnon (L1, lecture seule si possible) : ${msg.slice(0, 280)}`
}
