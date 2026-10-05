/**
 * Agir — proposer → dry-run → réel via Cortex Pilot (.140).
 * Miroir de pilot_assistant.js (assistantPropose / assistantRunRouteFromProposal).
 */

const ACTOR = 'ui:compagnon'
const TOKEN_KEY = 'lbg_orch_desktop_approval_token'
/** Même clé que Pilot Desktop — reprise auto si déjà saisi côté ops */
const PILOT_TOKEN_KEY = 'lbg_pilot_desktop_approval_v1'
/** LAB soft-confirm — agents acceptent cette sentinelle */
export const SOFT_CONFIRM_SENTINEL = 'confirmed'

/** @type {'token'|'confirm'|''} */
let _approvalMode = ''

export function getApprovalMode() {
  return _approvalMode || 'token'
}

export function isSoftConfirmMode() {
  return getApprovalMode() === 'confirm'
}

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
 * Récupère le mode approval (+ jeton si mode token) depuis :5174.
 * @param {{ force?: boolean }} [opts]
 * @returns {Promise<string>} token ou sentinelle soft-confirm
 */
export async function bootstrapApprovalToken(opts = {}) {
  const force = Boolean(opts.force)
  if (!force) {
    const existing = loadApprovalToken().trim()
    void existing
  }
  try {
    const res = await fetch('/api/desktop-approval', {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    })
    if (!res.ok) return loadApprovalToken()
    const json = await res.json()
    const mode = String(json?.mode || 'token').toLowerCase()
    _approvalMode = mode === 'confirm' || mode === 'soft' || mode === 'lab' ? 'confirm' : 'token'
    if (_approvalMode === 'confirm') {
      return SOFT_CONFIRM_SENTINEL
    }
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
 * Contre-pouvoir — revue avant dry-run→réel (Prométhée-gate, pas Lyra).
 * @param {Record<string, unknown>|null} proposal
 * @param {{ sourceText?: string, forceLlm?: boolean }} [opts]
 * @returns {Promise<{
 *   pass: boolean,
 *   block_real: boolean,
 *   auto_dry_run: boolean,
 *   auto_real: boolean,
 *   summary: string,
 *   risks: string[],
 *   alternatives: string[],
 *   confidence: number,
 *   source: string,
 *   raw: object|null,
 * }>}
 */
export async function reviewProposal(proposal, opts = {}) {
  const out = await postPilot('/companion/review-proposal', {
    actor_id: ACTOR,
    source_text: String(opts.sourceText || '').trim(),
    proposal: proposal && typeof proposal === 'object' ? proposal : null,
    force_llm: Boolean(opts.forceLlm),
  })
  if (out.status !== 200 || !out.json || out.json.ok === false) {
    // Fail-open soft : dry-run auto, réel non bloqué (jeton reste requis)
    return {
      pass: true,
      block_real: false,
      auto_dry_run: true,
      auto_real: false,
      summary: out.json?.error || `Revue indisponible (HTTP ${out.status})`,
      risks: ['Contre-pouvoir offline — prudence humaine'],
      alternatives: [],
      confidence: 0,
      source: 'fallback',
      raw: out.json,
    }
  }
  const r = out.json.review && typeof out.json.review === 'object' ? out.json.review : {}
  return {
    pass: r.pass !== false,
    block_real: Boolean(r.block_real),
    auto_dry_run: Boolean(r.auto_dry_run),
    auto_real: Boolean(r.auto_real),
    summary: String(r.summary || ''),
    risks: Array.isArray(r.risks) ? r.risks.map(String) : [],
    alternatives: Array.isArray(r.alternatives) ? r.alternatives.map(String) : [],
    confidence: typeof r.confidence === 'number' ? r.confidence : 0,
    source: String(r.source || 'unknown'),
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
    const soft = isSoftConfirmMode() || token === SOFT_CONFIRM_SENTINEL
    if (soft) {
      ctx.desktop_confirm = true
      const sentinel = SOFT_CONFIRM_SENTINEL
      if (capability === 'desktop_control') ctx.desktop_approval = sentinel
      else if (capability === 'devops_probe') ctx.devops_approval = sentinel
      else if (capability === 'prototype_game') ctx.opengame_approval = sentinel
      else ctx.desktop_approval = sentinel
    } else if (token) {
      if (capability === 'desktop_control') ctx.desktop_approval = token
      else if (capability === 'devops_probe') ctx.devops_approval = token
      else if (capability === 'prototype_game') ctx.opengame_approval = token
    }
  }
  return ctx
}

export function routeLooksSuccessful(routePayload) {
  if (!routePayload || routePayload.ok === false) return false
  const out =
    (routePayload.result && routePayload.result.output) ||
    routePayload.output ||
    null
  if (!out) return false
  // Dry-run agent réussi même si certaines couches mettent ok=false ailleurs
  if (out.outcome === 'dry_run') return true
  if (out.ok === false) return false
  const pol = out.policy
  if (pol && pol.allowed === false) return false
  // Erreurs métier agent (filtres mail, allowlist…) malgré policy approved
  if (typeof out.error === 'string' && out.error.trim()) return false
  if (out.outcome && ['bad_request', 'approval_denied', 'allowlist_denied', 'error', 'feature_disabled', 'configuration_error', 'missing_dependency'].includes(String(out.outcome))) {
    return false
  }
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

/** Output agent depuis une réponse /route (Pilot). */
export function extractRouteOutput(routePayload) {
  if (!routePayload || typeof routePayload !== 'object') return null
  const result = routePayload.result || routePayload
  const output = result?.output || routePayload.output || null
  return output && typeof output === 'object' ? output : null
}

/**
 * Liste mails IMAP (champ `messages` de mail_imap_preview).
 * @returns {Array<{ uid?: string, from?: string, subject?: string, date?: string, body_preview?: string }>}
 */
export function extractMailPreviewMessages(routePayload) {
  const output = extractRouteOutput(routePayload)
  if (!output) return []
  const msgs = output.messages
  if (!Array.isArray(msgs)) return []
  return msgs.filter((m) => m && typeof m === 'object')
}

/** Une ligne compacte par message pour résumé texte. */
export function formatMailPreviewLines(messages, { max = 5, bodyChars = 120 } = {}) {
  const list = Array.isArray(messages) ? messages : []
  return list.slice(0, Math.max(0, max)).map((m, i) => {
    const from = String(m.from || '—').slice(0, 80)
    const subject = String(m.subject || '(sans objet)').slice(0, 120)
    const date = String(m.date || '').slice(0, 40)
    const body = String(m.body_preview || '')
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, Math.max(0, bodyChars))
    const head = `${i + 1}. ${from} — ${subject}`
    const mid = date ? `${head} (${date})` : head
    return body ? `${mid}\n   ${body}` : mid
  })
}

/** Résumé court pour le chat après route. */
export function summarizeRouteResult(routePayload, mode) {
  if (!routePayload) return 'Pas de réponse'
  if (routePayload.ok === false) {
    return `Échec : ${routePayload.error || routePayload.detail || 'route KO'}`
  }
  const result = routePayload.result || routePayload
  const output = result.output || routePayload.output || {}
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
  const bits = [`${label} · ${ok ? 'ok' : 'échec'}`]
  if (result.routed_to || routePayload.routed_to) {
    bits.push(String(result.routed_to || routePayload.routed_to))
  }
  // Préférer l'outcome agent (réel) à la seule decision policy (approved_action trompeur).
  if (outcome) bits.push(outcome)
  else if (decision) bits.push(decision)
  if (outcome === 'approval_denied' || /Approval token/i.test(String(output.error || ''))) {
    bits.push(
      isSoftConfirmMode()
        ? 'Confirmation requise (coche « Je confirme »)'
        : 'Jeton incorrect ou manquant (doit matcher LBG_DESKTOP_APPROVAL_TOKEN sur .10)',
    )
  } else if (output.error) {
    bits.push(String(output.error).slice(0, 200))
  } else if (reply) {
    bits.push(String(reply).slice(0, 280))
  }
  if (output.app) bits.push(`app=${output.app}`)
  if (output.desktop_target_host) bits.push(`host=${output.desktop_target_host}`)

  const mailMsgs = extractMailPreviewMessages(routePayload)
  if (mailMsgs.length) {
    const n =
      typeof output.matched_count === 'number' ? output.matched_count : mailMsgs.length
    bits.push(`aperçu IMAP · ${n} message${n > 1 ? 's' : ''}`)
    if (outcome === 'dry_run') {
      bits.push('(simulation — cliquer Réel pour lire l’INBOX)')
    }
  }

  return bits.join(' — ')
}
