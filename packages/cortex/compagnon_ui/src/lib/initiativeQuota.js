/**
 * Quota strict + intents Agir-ready pour initiatives (D3+).
 * Jamais d'auto-exécution — toast / pet portent une action concrète.
 */

const STORAGE_KEY = 'lbg_compagnon_initiative_quota_v1'

/** @typedef {{ ts: number, id: string }[]} ShownLog */

/**
 * @typedef {{
 *   id: string,
 *   label: string,
 *   sourceText: string,
 *   hint?: string,
 * }} AgirIntent
 */

export const INITIATIVE_DEFAULTS = {
  maxPerHour: 3,
  minIntervalSec: 600,
  pollIntervalMs: 60_000,
  minSilenceSec: 90,
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { shown: /** @type {ShownLog} */ ([]) }
    const parsed = JSON.parse(raw)
    return {
      shown: Array.isArray(parsed?.shown) ? parsed.shown : [],
    }
  } catch {
    return { shown: [] }
  }
}

function saveState(state) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {
    /* ignore */
  }
}

function prune(shown, now = Date.now()) {
  const hourAgo = now - 60 * 60 * 1000
  return shown.filter((x) => x && typeof x.ts === 'number' && x.ts >= hourAgo)
}

export function fingerprintFromStatus(status) {
  if (!status || typeof status !== 'object') return ''
  const job = typeof status.last_job_id === 'string' ? status.last_job_id.trim() : ''
  if (job) return `job:${job}`
  const act = status.last_action && typeof status.last_action === 'object' ? status.last_action : null
  if (act) {
    const kind = String(act.kind || '')
    const msg = String(act.message || '').slice(0, 120)
    if (kind || msg) return `act:${kind}|${msg}`
  }
  const infra = status.infra_signals && typeof status.infra_signals === 'object' ? status.infra_signals : null
  if (infra?.ad_agent_down) return 'infra:ad_agent_down'
  if (infra?.orchestrator_reachable === false) return 'infra:orch_down'
  return ''
}

/**
 * Intents Agir concrets (texte → action-proposal).
 * @param {Record<string, unknown>} status
 * @returns {AgirIntent[]}
 */
export function agirIntentsFromStatus(status) {
  /** @type {AgirIntent[]} */
  const out = []
  const infra = status?.infra_signals && typeof status.infra_signals === 'object' ? status.infra_signals : {}
  const tension = Number(status?.tension)
  const job = typeof status?.last_job_id === 'string' ? status.last_job_id : ''

  if (infra.ad_agent_down) {
    out.push({
      id: 'probe_ad',
      label: 'Sonde AD (dry-run)',
      sourceText: 'fais un diagnostic infra selfcheck de l agent AD sur le LAN',
      hint: 'devops_probe · lecture seule',
    })
  }
  if (infra.orchestrator_reachable === false) {
    out.push({
      id: 'probe_orch',
      label: 'Sonde orchestrateur',
      sourceText: 'fais un diagnostic HTTP health de l orchestrateur Cortex',
      hint: 'devops_probe',
    })
  }
  if (Number.isFinite(tension) && tension >= 0.85) {
    out.push({
      id: 'open_jobs',
      label: 'Ouvrir Pilot Jobs',
      sourceText: 'ouvre firefox sur mon pc avec l url http://192.168.0.140:8080/#/jobs',
      hint: 'desktop · .10',
    })
  }
  if (job && !out.some((x) => x.id === 'open_jobs')) {
    out.push({
      id: 'open_jobs_job',
      label: 'Revue job L2',
      sourceText: 'ouvre firefox sur mon pc avec l url http://192.168.0.140:8080/#/jobs',
      hint: `job ${job.slice(0, 8)}…`,
    })
  }
  if (infra.mmo_sidecar_reachable === false) {
    out.push({
      id: 'note_mmo',
      label: 'Ouvrir notes sidecar',
      sourceText: 'ouvre notepadpp sur mon pc',
      hint: 'desktop · noter l alerte MMO',
    })
  }
  if (!out.length) {
    out.push({
      id: 'status_check',
      label: 'État Studio (dry-run)',
      sourceText: 'fais un diagnostic infra selfcheck LAN',
      hint: 'lecture seule',
    })
  }
  return out.slice(0, 3)
}

export function messageFromStatus(status) {
  const infra = status?.infra_signals
  if (infra?.ad_agent_down) {
    return 'Je vois l’agent AD injoignable — je peux lancer une sonde (dry-run).'
  }
  if (infra?.orchestrator_reachable === false) {
    return 'Orchestrateur injoignable — je propose une sonde health.'
  }
  if (typeof status?.tension === 'number' && status.tension >= 0.85) {
    return 'Tension orch élevée — je propose d’ouvrir Pilot Jobs pour revue L2.'
  }
  const act = status?.last_action
  if (act && typeof act === 'object' && act.message) {
    return `Signal : ${String(act.message)} — action concrète ci-dessous.`
  }
  return 'Petite initiative — une action possible ci-dessous.'
}

/** @deprecated texte ; préférer agirIntentsFromStatus */
export function concreteProposalsFromStatus(status) {
  return agirIntentsFromStatus(status).map((i) => `${i.label}${i.hint ? ` (${i.hint})` : ''}`)
}

export function formatDiscussReply(status) {
  const headline = messageFromStatus(status)
  const intents = agirIntentsFromStatus(status)
  const lines = [
    `Je vois ça : « ${headline} »`,
    '',
    'Actions concrètes (pas encore exécutées) :',
    ...intents.map((p, i) => `${i + 1}. ${p.label}${p.hint ? ` — ${p.hint}` : ''}`),
    '',
    'Clique Agir sur le toast, ou le bouton Agir avec le texte de l’action → Dry-run → Réel.',
  ]
  return lines.join('\n')
}

/**
 * @param {string} id
 * @param {Partial<typeof INITIATIVE_DEFAULTS>} [opts]
 */
export function canShowInitiative(id, opts = {}) {
  if (!id) return { ok: false, reason: 'empty' }
  const maxPerHour = opts.maxPerHour ?? INITIATIVE_DEFAULTS.maxPerHour
  const minIntervalSec = opts.minIntervalSec ?? INITIATIVE_DEFAULTS.minIntervalSec
  const now = Date.now()
  const state = loadState()
  const shown = prune(state.shown, now)
  if (shown.some((x) => x.id === id)) return { ok: false, reason: 'already_shown' }
  if (shown.length >= maxPerHour) return { ok: false, reason: 'quota_hour' }
  const last = shown.reduce((a, b) => (a.ts > b.ts ? a : b), { ts: 0, id: '' })
  if (last.ts && now - last.ts < minIntervalSec * 1000) {
    return { ok: false, reason: 'interval' }
  }
  return { ok: true, shown }
}

/** @param {string} id */
export function markInitiativeShown(id) {
  if (!id) return
  const now = Date.now()
  const state = loadState()
  const shown = prune(state.shown, now)
  shown.push({ ts: now, id })
  saveState({ shown })
}

/** @param {Record<string, unknown>} status */
export function shouldOfferFromStatus(status, opts = {}) {
  if (!status || status.enabled === false || status.ok === false) {
    return { offer: false, reason: 'disabled' }
  }
  const minSilence = opts.minSilenceSec ?? INITIATIVE_DEFAULTS.minSilenceSec
  const silence = Number(status.silence_seconds_est)
  if (Number.isFinite(silence) && silence < minSilence) {
    return { offer: false, reason: 'user_active' }
  }
  const id = fingerprintFromStatus(status)
  if (!id) return { offer: false, reason: 'no_signal' }
  const gate = canShowInitiative(id, opts)
  if (!gate.ok) return { offer: false, reason: gate.reason, id }
  const intents = agirIntentsFromStatus(status)
  return {
    offer: true,
    id,
    message: messageFromStatus(status),
    kind: (status.last_action && status.last_action.kind) || 'initiative',
    intents,
    primary: intents[0] || null,
  }
}
