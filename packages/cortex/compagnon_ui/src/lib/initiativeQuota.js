/**
 * Quota strict pour notifications d'initiative (D3).
 * Jamais d'auto-exécution — affichage seul.
 */

const STORAGE_KEY = 'lbg_compagnon_initiative_quota_v1'

/** @typedef {{ ts: number, id: string }[]} ShownLog */

export const INITIATIVE_DEFAULTS = {
  /** Max toasts affichés / fenêtre glissante */
  maxPerHour: 3,
  /** Secondes mini entre deux toasts */
  minIntervalSec: 600,
  /** Poll proactive status */
  pollIntervalMs: 60_000,
  /** Silence estimé mini (API) avant de proposer une initiative */
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
  return ''
}

export function messageFromStatus(status) {
  const act = status?.last_action
  if (act && typeof act === 'object' && act.message) return String(act.message)
  const infra = status?.infra_signals
  if (infra?.ad_agent_down) {
    return 'Agent AD injoignable — je peux proposer un diagnostic (sans exécuter).'
  }
  if (typeof status?.tension === 'number' && status.tension >= 0.85) {
    return 'Tension orchestration élevée — une initiative est disponible (validation L2).'
  }
  return 'Initiative Compagnon disponible.'
}

/**
 * Propositions concrètes L2 (texte seul — jamais d'exec).
 * @param {Record<string, unknown>} status
 * @returns {string[]}
 */
export function concreteProposalsFromStatus(status) {
  const out = []
  const infra = status?.infra_signals && typeof status.infra_signals === 'object' ? status.infra_signals : {}
  const tension = Number(status?.tension)
  const curiosite = Number(status?.curiosite)
  const job = typeof status?.last_job_id === 'string' ? status.last_job_id : ''

  if (infra.ad_agent_down) {
    out.push('Vérifier l’agent AD (`.111` / devops) — sonde read-only via Pilot Desktop ou Agir dry-run.')
  }
  if (infra.orchestrator_reachable === false) {
    out.push('Orchestrateur injoignable — contrôler `.100` / `.140` avant toute action.')
  }
  if (infra.mmo_sidecar_reachable === false) {
    out.push('Sidecar MMO down — hors scope Compagnon immédiat ; noter pour ops Core3.')
  }
  if (Number.isFinite(tension) && tension >= 0.85) {
    out.push(
      'Tension haute : passer en mode conversation (pas d’auto-job), relire le dernier job Team, puis Agir seulement si une action claire.'
    )
  }
  if (Number.isFinite(curiosite) && curiosite >= 0.85 && out.length < 3) {
    out.push('Curiosité haute : me demander un résumé d’infra (Pilot status) plutôt qu’une action poste.')
  }
  if (job) {
    out.push(`Dernier job proactif : \`${job.slice(0, 12)}…\` — ouvrir Pilot → Jobs pour revue L2.`)
  }
  if (!out.length) {
    out.push('Rien d’urgent détecté : on peut ignorer, ou me demander l’état Studio (sans lancer d’app).')
  }
  return out.slice(0, 4)
}

/** Réponse locale pour le bouton Discuter (évite le routeur desktop Orch). */
export function formatDiscussReply(status) {
  const headline = messageFromStatus(status)
  const proposals = concreteProposalsFromStatus(status)
  const lines = [
    `Initiative (proposition seule, rien n’est exécuté) :`,
    `« ${headline} »`,
    '',
    'Concrètement, je te propose :',
    ...proposals.map((p, i) => `${i + 1}. ${p}`),
    '',
    'Pour une action poste : bouton Agir → Dry-run → Réel (jeton). Sinon on continue à parler.',
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
  return {
    offer: true,
    id,
    message: messageFromStatus(status),
    kind: (status.last_action && status.last_action.kind) || 'initiative',
    proposals: concreteProposalsFromStatus(status),
  }
}
