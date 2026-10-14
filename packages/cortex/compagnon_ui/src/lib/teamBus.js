/**
 * Client bus Team ADR 0019 — Compagnon ↔ agents / jobs.
 * Proxy : /api/pilot/team/messages (pas de 2ᵉ bus).
 */

import { unwrapPilot } from './missionWatch.js'

export const COMPAGNON_BUS_AGENT = 'compagnon'
export const VALID_KINDS = Object.freeze(['consult', 'gap', 'propose', 'ack', 'verify_result'])

const SEEN_KEY = 'lbg_compagnon_team_bus_seen_v1'
const MAX_SEEN = 80

/**
 * @typedef {{
 *   id: string,
 *   fromAgent: string,
 *   toAgent: string,
 *   kind: string,
 *   payload: Record<string, unknown>,
 *   taskId: string,
 *   createdTs: number,
 *   actorId: string,
 * }} TeamBusMessage
 */

function seenSet() {
  try {
    const raw = JSON.parse(localStorage.getItem(SEEN_KEY) || '[]')
    return new Set(Array.isArray(raw) ? raw.map(String) : [])
  } catch {
    return new Set()
  }
}

function persistSeen(ids) {
  try {
    localStorage.setItem(SEEN_KEY, JSON.stringify([...ids].slice(-MAX_SEEN)))
  } catch {
    /* ignore */
  }
}

/** @param {string} id */
export function markBusSeen(id) {
  const s = seenSet()
  s.add(String(id))
  persistSeen(s)
}

/** @param {string} id */
export function wasBusSeen(id) {
  return seenSet().has(String(id))
}

/**
 * @param {unknown} raw
 * @returns {TeamBusMessage|null}
 */
export function normalizeMessage(raw) {
  if (!raw || typeof raw !== 'object') return null
  const id = String(raw.id || '').trim()
  if (!id) return null
  return {
    id,
    fromAgent: String(raw.from_agent || raw.fromAgent || ''),
    toAgent: String(raw.to_agent || raw.toAgent || ''),
    kind: String(raw.kind || '').toLowerCase(),
    payload: raw.payload && typeof raw.payload === 'object' ? raw.payload : {},
    taskId: String(raw.task_id || raw.taskId || ''),
    createdTs: Number(raw.created_ts || raw.createdTs || 0) || 0,
    actorId: String(raw.actor_id || raw.actorId || ''),
  }
}

/**
 * @param {unknown} data
 * @returns {TeamBusMessage[]}
 */
export function normalizeMessageList(data) {
  const body = unwrapPilot(data)
  const list = Array.isArray(body.messages) ? body.messages : Array.isArray(body) ? body : []
  return list.map(normalizeMessage).filter(Boolean)
}

/**
 * Ligne compacte pour panneau / chat.
 * @param {TeamBusMessage} msg
 */
export function formatBusLine(msg) {
  if (!msg) return ''
  const kind = msg.kind || '?'
  const from = msg.fromAgent || '?'
  const to = msg.toAgent || '?'
  const summary =
    String(msg.payload?.summary || msg.payload?.objective || msg.payload?.result || '').trim() ||
    String(msg.payload?.text || '').trim()
  const head = `${from} → ${to} · ${kind}`
  if (!summary) return head
  return `${head} — ${summary.slice(0, 120)}`
}

/**
 * Offre initiative / ping chat pour messages destinés au Compagnon.
 * @param {TeamBusMessage[]} messages
 * @returns {{ offer: { id: string, offer: true, message: string, themes: string[] }, msg: TeamBusMessage }|null}
 */
export function nextBusInboxOffer(messages) {
  const inbox = (messages || [])
    .filter((m) => m && m.toAgent === COMPAGNON_BUS_AGENT)
    .filter((m) => m.kind === 'verify_result' || m.kind === 'ack' || m.kind === 'propose')
    .filter((m) => !wasBusSeen(m.id))
    .sort((a, b) => b.createdTs - a.createdTs)
  const msg = inbox[0]
  if (!msg) return null
  const line = formatBusLine(msg)
  return {
    msg,
    offer: {
      id: `bus:${msg.id}`,
      offer: true,
      message: `Bus Team · ${line}`,
      themes: ['team', 'bus', msg.kind],
    },
  }
}

/**
 * @param {{
 *   toAgent?: string,
 *   fromAgent?: string,
 *   kind?: string,
 *   taskId?: string,
 *   limit?: number,
 *   signal?: AbortSignal,
 * }} [opts]
 */
export async function listMessages(opts = {}) {
  const params = new URLSearchParams()
  params.set('limit', String(Math.max(1, Math.min(opts.limit || 40, 100))))
  if (opts.toAgent) params.set('to_agent', opts.toAgent)
  if (opts.fromAgent) params.set('from_agent', opts.fromAgent)
  if (opts.kind) params.set('kind', opts.kind)
  if (opts.taskId) params.set('task_id', opts.taskId)
  const res = await fetch(`/api/pilot/team/messages?${params}`, {
    headers: { Accept: 'application/json' },
    signal: opts.signal,
  })
  if (!res.ok) {
    return { ok: false, messages: [], error: `HTTP ${res.status}` }
  }
  const data = await res.json()
  const messages = normalizeMessageList(data)
  return { ok: true, messages }
}

/**
 * @param {{
 *   fromAgent?: string,
 *   toAgent: string,
 *   kind: string,
 *   payload?: Record<string, unknown>,
 *   taskId?: string,
 *   actorId?: string,
 * }} input
 */
export async function postMessage(input) {
  const kind = String(input.kind || '').toLowerCase()
  if (!VALID_KINDS.includes(kind)) {
    return { ok: false, error: `kind_invalide:${kind}` }
  }
  const body = {
    from_agent: String(input.fromAgent || COMPAGNON_BUS_AGENT).trim() || COMPAGNON_BUS_AGENT,
    to_agent: String(input.toAgent || '').trim(),
    kind,
    payload: input.payload && typeof input.payload === 'object' ? input.payload : {},
    task_id: String(input.taskId || ''),
    actor_id: String(input.actorId || 'ui:compagnon'),
  }
  if (!body.to_agent) return { ok: false, error: 'to_agent_required' }

  const res = await fetch('/api/pilot/team/messages', {
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
  const msg = normalizeMessage(unwrapPilot(json)) || normalizeMessage(json)
  return { ok: true, message: msg, raw: json }
}

/**
 * Ping bus après spawn L1 Compagnon → agent rôle (handoff visible).
 * @param {{ taskId?: string, role?: string, objective?: string, toAgent?: string }} opts
 */
export async function announceSpawn(opts) {
  const role = String(opts.role || 'qa').toLowerCase()
  const toAgent = String(opts.toAgent || roleToAgent(role))
  return postMessage({
    fromAgent: COMPAGNON_BUS_AGENT,
    toAgent,
    kind: 'propose',
    taskId: opts.taskId || '',
    payload: {
      summary: String(opts.objective || '').slice(0, 200),
      source: 'compagnon_spawn',
      role,
    },
  })
}

/** Mapping léger rôle → agent id (aligné bus_hooks ROLE_TO_AGENT). */
export function roleToAgent(role) {
  const r = String(role || '').toLowerCase()
  const map = {
    pm: 'themis',
    qa: 'argus',
    ops: 'hephaistos',
    admin_infra: 'atlas',
    dev_godot: 'iris',
    dev_game: 'dedale',
    player_ia: 'choeur',
  }
  return map[r] || 'themis'
}
