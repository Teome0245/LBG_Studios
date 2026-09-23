/**
 * Quota strict + intents Agir-ready pour initiatives (D3+).
 * Jamais d'auto-exécution — toast / pet portent une action concrète.
 * Boucle autonomie : objectif Studio + feedback Agir/Ignorer.
 */

import {
  feedbackGate,
  getStudioGoal,
  goalRelevance,
  messageWithGoal,
  recordGoalFeedback,
} from './studioGoal.js'
import { idleUsefulAgirIntents } from './usefulAgirActions.js'

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
  defaultSnoozeHours: 4,
}

let _memoryFallback = null

function loadState() {
  try {
    if (typeof localStorage === 'undefined') {
      if (!_memoryFallback) _memoryFallback = { shown: [], snoozed: {} }
      return _memoryFallback
    }
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { shown: /** @type {ShownLog} */ ([]), snoozed: /** @type {Record<string, number>} */ ({}) }
    const parsed = JSON.parse(raw)
    return {
      shown: Array.isArray(parsed?.shown) ? parsed.shown : [],
      snoozed: parsed?.snoozed && typeof parsed.snoozed === 'object' ? parsed.snoozed : {},
    }
  } catch {
    return { shown: [], snoozed: {} }
  }
}

function saveState(state) {
  try {
    if (typeof localStorage === 'undefined') {
      _memoryFallback = state
      return
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {
    /* ignore */
  }
}

function prune(shown, now = Date.now(), snoozed = {}) {
  const hourAgo = now - 60 * 60 * 1000
  const cleanShown = (shown || []).filter((x) => x && typeof x.ts === 'number' && x.ts >= hourAgo)
  const cleanSnoozed = {}
  if (snoozed && typeof snoozed === 'object') {
    for (const [k, exp] of Object.entries(snoozed)) {
      if (typeof exp === 'number' && exp > now) {
        cleanSnoozed[k] = exp
      }
    }
  }
  return { shown: cleanShown, snoozed: cleanSnoozed }
}

/**
 * Fingerprint stable pour le signal utilisateur affiché.
 * Priorité absolue aux alertes infra / messages spécifiques pour éviter
 * qu'un last_job_id volatile ne change l'ID à chaque tick.
 */
export function fingerprintFromStatus(status) {
  if (!status || typeof status !== 'object') return ''

  // 1. Alertes infra critiques prioritaires (stables, match avec messageFromStatus)
  const infra = status.infra_signals && typeof status.infra_signals === 'object' ? status.infra_signals : null
  if (infra?.disk_critical || (typeof infra?.disk_root_used_pct === 'number' && infra.disk_root_used_pct >= 90)) {
    return 'disk:critical'
  }
  if (infra?.disk_high || (typeof infra?.disk_root_used_pct === 'number' && infra.disk_root_used_pct >= 80)) {
    return 'disk:high'
  }
  if (infra?.ad_agent_down) return 'infra:ad_agent_down'
  if (infra?.orchestrator_reachable === false) return 'infra:orch_down'
  if (infra?.mmo_sidecar_reachable === false) return 'infra:mmo_down'

  // Causes explicites du moteur (après recalibrage)
  const causes = Array.isArray(status.tension_causes) ? status.tension_causes : []
  for (const c of causes) {
    const s = String(c)
    if (s.startsWith('disk_critical')) return 'disk:critical'
    if (s.startsWith('disk_high')) return 'disk:high'
    if (s === 'ad_agent_down') return 'infra:ad_agent_down'
    if (s.startsWith('jobs_l2')) return `jobs:l2:${s.split(':')[1] || 'n'}`
  }

  // 2. Tension élevée UNIQUEMENT si cause réelle (plus le silence synthétique seul)
  const tension = Number(status.tension)
  const realCause = causes.some((c) => !String(c).includes('silence'))
  if (Number.isFinite(tension) && tension >= 0.85 && realCause) return 'tension:high'

  const act = status.last_action && typeof status.last_action === 'object' ? status.last_action : null
  const silenceOnly =
    causes.length > 0 && causes.every((c) => String(c).includes('silence'))
  const silencePlan =
    silenceOnly ||
    (act && String(act.cause || '').includes('silence')) ||
    (act && /silence prolong/i.test(String(act.message || '')))

  // 3. Silence prolongé → id stable aligné objectif Studio (évite off_goal sur act:…)
  if (silencePlan) return 'jobs:idle'

  // 4. Action spécifique proactive (hors silence)
  if (act && act.message) {
    const kind = String(act.kind || 'action')
    const msg = String(act.message || '').slice(0, 60)
    return `act:${kind}|${msg}`
  }

  // 5. Job L2 uniquement en dernier ressort
  const job = typeof status.last_job_id === 'string' ? status.last_job_id.trim() : ''
  if (job) return `job:${job}`

  return ''
}

/**
 * Snooze explicite d'un fingerprint (ex. après Ignorer ou Agir réussi).
 * @param {string} id
 * @param {number} [durationHours=4]
 */
export function snoozeInitiative(id, durationHours = 4) {
  if (!id) return
  const now = Date.now()
  const state = loadState()
  const { shown, snoozed } = prune(state.shown, now, state.snoozed)
  snoozed[id] = now + durationHours * 3600 * 1000
  saveState({ shown, snoozed })
}

/**
 * Vérifie si un fingerprint d'initiative est actuellement snoozé.
 * @param {string} id
 * @returns {boolean}
 */
export function isInitiativeSnoozed(id) {
  if (!id) return false
  const now = Date.now()
  const state = loadState()
  return typeof state.snoozed?.[id] === 'number' && state.snoozed[id] > now
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

  if (infra.disk_critical || (typeof infra.disk_root_used_pct === 'number' && infra.disk_root_used_pct >= 90)) {
    out.push({
      id: 'disk_l2_jobs',
      label: 'Approuver remédiation L2',
      sourceText: 'ouvre http://192.168.0.140:8080/#/jobs dans le navigateur',
      hint: `root ${infra.disk_root_used_pct}% · Pilot Jobs`,
    })
    out.push({
      id: 'disk_selfcheck',
      label: 'Selfcheck disque (L1)',
      sourceText: 'fais un diagnostic infra selfcheck stockage disque LAN dry-run',
      hint: 'lecture seule',
    })
  } else if (infra.disk_high || (typeof infra.disk_root_used_pct === 'number' && infra.disk_root_used_pct >= 80)) {
    out.push({
      id: 'disk_l2_jobs',
      label: 'Voir Jobs L2',
      sourceText: 'ouvre http://192.168.0.140:8080/#/jobs dans le navigateur',
      hint: `root ${infra.disk_root_used_pct}%`,
    })
  }
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
  if (Number.isFinite(tension) && tension >= 0.85 && !out.some((x) => x.id === 'open_jobs')) {
    out.push({
      id: 'open_jobs',
      label: 'Ouvrir Pilot Jobs',
      sourceText: 'ouvre http://192.168.0.140:8080/#/jobs dans le navigateur',
      hint: 'navigateur par défaut · .10',
    })
  }
  if (job && !out.some((x) => x.id === 'open_jobs')) {
    out.push({
      id: 'open_jobs_job',
      label: 'Revue job L2',
      sourceText: 'ouvre http://192.168.0.140:8080/#/jobs dans le navigateur',
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
    out.push(...idleUsefulAgirIntents(3))
  }
  return out.slice(0, 3)
}

export function messageFromStatus(status) {
  const infra = status?.infra_signals
  const pct = infra?.disk_root_used_pct
  if (infra?.disk_critical || (typeof pct === 'number' && pct >= 90)) {
    return `Disque root à ${pct}% — selfcheck L1 + job remédiation en attente L2 (Pilot Jobs). Pas de purge auto.`
  }
  if (infra?.disk_high || (typeof pct === 'number' && pct >= 80)) {
    return `Disque root à ${pct}% — je propose selfcheck puis approbation L2 pour remédier.`
  }
  if (infra?.ad_agent_down) {
    return 'Je vois l’agent AD injoignable — je peux lancer une sonde (dry-run).'
  }
  if (infra?.orchestrator_reachable === false) {
    return 'Orchestrateur injoignable — je propose une sonde health.'
  }
  const causes = Array.isArray(status?.tension_causes) ? status.tension_causes : []
  if (causes.some((c) => String(c).startsWith('jobs_l2'))) {
    return 'Jobs L2 en attente — je propose d’ouvrir Pilot Jobs pour revue.'
  }
  if (typeof status?.tension === 'number' && status.tension >= 0.85) {
    return 'Tension orch élevée (signal réel) — je propose d’ouvrir Pilot Jobs.'
  }
  const act = status?.last_action
  if (act && typeof act === 'object' && act.message) {
    const msg = String(act.message)
    // Ancien wording « veille légère » → reformuler avec une piste concrète.
    if (/silence prolong|veille l[eé]g[eè]re/i.test(msg)) {
      return (
        'Silence prolongé (aucune alerte infra) — ' +
        'je propose une action concrète : mails récents, selfcheck LAN ou revue Pilot Jobs L2.'
      )
    }
    return msg
  }
  const intents = agirIntentsFromStatus(status)
  if (intents.length) {
    const top = intents[0]
    return `Initiative — je propose « ${top.label} »${top.hint ? ` (${top.hint})` : ''}.`
  }
  return 'Initiative — une action concrète est proposée ci-dessous (Agir).'
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
  if (isInitiativeSnoozed(id)) return { ok: false, reason: 'snoozed' }

  const maxPerHour = opts.maxPerHour ?? INITIATIVE_DEFAULTS.maxPerHour
  const minIntervalSec = opts.minIntervalSec ?? INITIATIVE_DEFAULTS.minIntervalSec
  const now = Date.now()
  const state = loadState()
  const { shown } = prune(state.shown, now, state.snoozed)

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
  const { shown, snoozed } = prune(state.shown, now, state.snoozed)
  shown.push({ ts: now, id })
  saveState({ shown, snoozed })
}

/**
 * Enregistre le feedback utilisateur pour l’apprentissage local.
 * @param {string} id
 * @param {'accept'|'dismiss'} kind
 */
export function recordInitiativeFeedback(id, kind) {
  recordGoalFeedback(id, kind)
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

  const learned = feedbackGate(id)
  if (learned.suppress) {
    return { offer: false, reason: learned.reason || 'learned_dismiss', id }
  }

  // Objectif actif : signaux peu alignés (hors infra / idle Studio) → attendre
  const studio = getStudioGoal()
  const rel = goalRelevance(id)
  const allowIdle =
    id === 'jobs:idle' ||
    (Number(status.curiosite) >= 0.7 && Number(status.silence_seconds_est) >= 600)
  if (
    studio.enabled &&
    rel < 0.4 &&
    !id.startsWith('infra:') &&
    !allowIdle
  ) {
    return { offer: false, reason: 'off_goal', id, relevance: rel }
  }

  const gate = canShowInitiative(id, opts)
  if (!gate.ok) return { offer: false, reason: gate.reason, id }

  const intents = agirIntentsFromStatus(status)
  const goal = studio.goal
  return {
    offer: true,
    id,
    message: messageWithGoal(messageFromStatus(status), id),
    kind: (status.last_action && status.last_action.kind) || 'initiative',
    intents,
    primary: intents[0] || null,
    goal: goal ? { id: goal.id, title: goal.title } : null,
    relevance: rel,
    weight: learned.weight,
  }
}
