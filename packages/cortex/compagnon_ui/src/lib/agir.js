/**
 * Agir — proposer → dry-run → réel via Cortex Pilot (.140).
 * Miroir de pilot_assistant.js (assistantPropose / assistantRunRouteFromProposal).
 */

const ACTOR = 'ui:compagnon'
const TOKEN_KEY = 'lbg_orch_desktop_approval_token'
/** Même clé que Pilot Desktop — reprise auto si déjà saisi côté ops */
const PILOT_TOKEN_KEY = 'lbg_pilot_desktop_approval_v1'

export function loadApprovalToken() {
  try {
    const local = localStorage.getItem(TOKEN_KEY)
    if (local) return local
    const fromPilot = localStorage.getItem(PILOT_TOKEN_KEY)
    if (fromPilot) {
      localStorage.setItem(TOKEN_KEY, fromPilot)
      return fromPilot
    }
    return ''
  } catch {
    return ''
  }
}

export function saveApprovalToken(token) {
  try {
    const t = String(token || '').trim()
    if (t) {
      localStorage.setItem(TOKEN_KEY, t)
      // garder Pilot à jour si l'utilisateur colle ici
      localStorage.setItem(PILOT_TOKEN_KEY, t)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  } catch {
    /* ignore */
  }
}

export function hasApprovalToken() {
  return Boolean(loadApprovalToken().trim())
}

/**
 * Récupère le jeton serveur LAN (:5174 → backend .100) et l’écrit en localStorage.
 * Corrige les jetons navigateur périmés qui ne matchent plus ``C:\\Agent_IA\\desktop.env``.
 * @param {{ force?: boolean }} [opts]
 * @returns {Promise<string>}
 */
export async function bootstrapApprovalToken(opts = {}) {
  const force = Boolean(opts.force)
  if (!force) {
    const existing = loadApprovalToken().trim()
    // On resynchronise toujours depuis le serveur LAN quand dispo —
    // un jeton local faux est la cause n°1 des « Jeton incorrect ».
  }
  try {
    const res = await fetch('/api/desktop-approval', {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    })
    if (!res.ok) return loadApprovalToken()
    const json = await res.json()
    const tok = typeof json?.token === 'string' ? json.token.trim() : ''
    if (json?.ok && tok) {
      saveApprovalToken(tok)
      return tok
    }
  } catch {
    /* offline / pas d’endpoint */
  }
  return loadApprovalToken()
}

/** @param {string} path ex. `/action-proposal` */
function pilotUrl(path) {
  const p = path.startsWith('/') ? path : `/${path}`
  // Même origine : nginx `/api/pilot/` → Pilot .140 ; Vite proxy en dev
  return `/api/pilot${p}`
}

async function postPilot(path, body) {
  const res = await fetch(pilotUrl(path), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(body),
  })
  let json = null
  const text = await res.text()
  try {
    json = text ? JSON.parse(text) : null
  } catch {
    json = null
  }
  return { status: res.status, json, text }
}

/**
 * @param {string} text
 * @param {Record<string, unknown>} [context]
 */
export async function proposeAction(text, context = {}) {
  const trimmed = String(text || '').trim()
  if (!trimmed) throw new Error('Demande vide')
  const out = await postPilot('/action-proposal', {
    actor_id: ACTOR,
    text: trimmed,
    context: context && typeof context === 'object' ? context : {},
  })
  if (out.status !== 200 || !out.json || out.json.ok === false) {
    const err =
      out.json?.error ||
      out.json?.reason ||
      out.json?.detail ||
      `HTTP ${out.status}`
    throw new Error(typeof err === 'string' ? err : JSON.stringify(err))
  }
  return {
    proposal: out.json.proposal || null,
    reason: out.json.reason || null,
    raw: out.json,
  }
}

/**
 * Construit le context Pilot à partir d'une proposal + mode.
 * @param {Record<string, unknown>} proposal
 * @param {'dry_run'|'real'} mode
 * @param {string} [approvalToken]
 * @param {Record<string, unknown>} [baseContext]
 */
export function contextFromProposal(proposal, mode, approvalToken = '', baseContext = {}) {
  let ctx = { ...(baseContext && typeof baseContext === 'object' ? baseContext : {}) }
  const patch =
    proposal?.context_patch && typeof proposal.context_patch === 'object'
      ? proposal.context_patch
      : {}
  ctx = { ...ctx, ...patch }

  const key = typeof proposal?.action_context_key === 'string' ? proposal.action_context_key : ''
  const action = proposal?.action && typeof proposal.action === 'object' ? proposal.action : null
  if (key && action) ctx[key] = action

  const capability = typeof proposal?.capability === 'string' ? proposal.capability : ''
  const token = String(approvalToken || '').trim()

  if (mode === 'dry_run') {
    if (capability === 'desktop_control') ctx.desktop_dry_run = true
    if (capability === 'devops_probe') ctx.devops_dry_run = true
    if (capability === 'prototype_game') ctx.opengame_dry_run = true
  } else if (mode === 'real') {
    if (capability === 'desktop_control') delete ctx.desktop_dry_run
    if (capability === 'devops_probe') delete ctx.devops_dry_run
    if (capability === 'prototype_game') ctx.opengame_dry_run = false
    if (token) {
      if (capability === 'desktop_control') ctx.desktop_approval = token
      else if (capability === 'devops_probe') ctx.devops_approval = token
      else if (capability === 'prototype_game') ctx.opengame_approval = token
    }
  }
  return ctx
}

export function routeLooksSuccessful(routePayload) {
  if (!routePayload || routePayload.ok === false) return false
  const out = routePayload.result && routePayload.result.output
  if (!out) return false
  // Dry-run agent réussi même si certaines couches mettent ok=false ailleurs
  if (out.outcome === 'dry_run') return true
  if (out.ok === false) return false
  const pol = out.policy
  if (pol && pol.allowed === false) return false
  return true
}

/**
 * @param {Record<string, unknown>} proposal
 * @param {'dry_run'|'real'} mode
 * @param {{ text?: string, approvalToken?: string, context?: Record<string, unknown> }} [opts]
 */
export async function runRouteFromProposal(proposal, mode, opts = {}) {
  const text =
    String(opts.text || '').trim() ||
    String(proposal?.summary || 'action compagnon')
  const ctx = contextFromProposal(proposal, mode, opts.approvalToken || '', opts.context || {})
  const out = await postPilot('/route', {
    actor_id: ACTOR,
    text,
    context: ctx,
  })
  if (out.status !== 200 || !out.json) {
    throw new Error(out.text?.slice(0, 200) || `HTTP ${out.status}`)
  }
  return out.json
}

/** Résumé court pour le chat après route. */
export function summarizeRouteResult(routePayload, mode) {
  if (!routePayload) return 'Pas de réponse'
  if (routePayload.ok === false) {
    return `Échec : ${routePayload.error || routePayload.detail || 'route KO'}`
  }
  const result = routePayload.result || {}
  const output = result.output || {}
  const policy = output.policy
  const decision = policy?.decision ? String(policy.decision) : ''
  const outcome = output.outcome ? String(output.outcome) : ''
  const reply =
    (typeof output.reply === 'string' && output.reply) ||
    (typeof output.content === 'string' && output.content) ||
    (typeof output.summary === 'string' && output.summary) ||
    ''
  const ok = routeLooksSuccessful(routePayload)
  const label = mode === 'dry_run' ? 'Dry-run' : 'Réel'
  const bits = [`${label} · ${ok ? 'ok' : 'à vérifier'}`]
  if (result.routed_to) bits.push(String(result.routed_to))
  if (outcome === 'dry_run') bits.push('dry_run')
  else if (decision) bits.push(decision)
  if (outcome === 'approval_denied' || /Approval token/i.test(String(output.error || ''))) {
    bits.push('Jeton incorrect ou manquant (doit matcher LBG_DESKTOP_APPROVAL_TOKEN sur .10)')
  } else if (reply) {
    bits.push(String(reply).slice(0, 280))
  } else if (output.error) {
    bits.push(String(output.error).slice(0, 200))
  }
  return bits.join(' — ')
}
