/**
 * Mandat Compagnon — ce que l'utilisateur autorise à surveiller / proposer (D5).
 * Stockage local ; TTL frais ; aligne studioGoal.
 */

import { patchStudioGoal, STUDIO_GOALS } from './studioGoal.js'

const STORAGE_KEY = 'lbg_compagnon_mandate_v1'

/** @typedef {'jobs_l2'|'lan'|'mail'|'studio'|'morning'} MandateScope */

/** @type {{ id: MandateScope, label: string, hint: string, goalId: string }[]} */
export const MANDATE_SCOPES = [
  {
    id: 'jobs_l2',
    label: 'Jobs L2',
    hint: 'approbations Pilot',
    goalId: 'jobs_l2',
  },
  {
    id: 'lan',
    label: 'LAN / infra',
    hint: 'selfcheck · sondes',
    goalId: 'lan_watch',
  },
  {
    id: 'mail',
    label: 'Mails',
    hint: 'aperçu IMAP',
    goalId: 'mail_watch',
  },
  {
    id: 'studio',
    label: 'Studio',
    hint: 'conception · veille',
    goalId: 'studio_craft',
  },
  {
    id: 'morning',
    label: 'Brief matin',
    hint: 'point Self / infra',
    goalId: 'morning_brief',
  },
]

export const MANDATE_TTL_MS = 4 * 3600 * 1000
export const MANDATE_ASK_MIN_SILENCE_S = 7200

let _mem = null

/**
 * @typedef {{
 *   watch: MandateScope[],
 *   updatedAt: number,
 *   until: number,
 * }} MandateState
 */

function defaultState() {
  return {
    watch: /** @type {MandateScope[]} */ (['jobs_l2']),
    updatedAt: 0,
    until: 0,
  }
}

function load() {
  try {
    if (typeof localStorage === 'undefined') {
      if (!_mem) _mem = defaultState()
      return {
        ..._mem,
        watch: Array.isArray(_mem.watch) ? [..._mem.watch] : ['jobs_l2'],
      }
    }
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaultState()
    const p = JSON.parse(raw)
    const watch = Array.isArray(p?.watch)
      ? p.watch.filter((x) => MANDATE_SCOPES.some((s) => s.id === x))
      : []
    return {
      watch: watch.length ? watch : ['jobs_l2'],
      updatedAt: typeof p?.updatedAt === 'number' ? p.updatedAt : 0,
      until: typeof p?.until === 'number' ? p.until : 0,
    }
  } catch {
    return defaultState()
  }
}

function save(state) {
  const next = { ...state }
  try {
    if (typeof localStorage === 'undefined') {
      _mem = next
      return
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  } catch {
    /* ignore */
  }
}

/** @returns {MandateState & { fresh: boolean, scopes: typeof MANDATE_SCOPES }} */
export function getMandate() {
  const st = load()
  const now = Date.now()
  const fresh = st.updatedAt > 0 && st.until > now
  return { ...st, fresh, scopes: MANDATE_SCOPES }
}

/** Mandat jamais confirmé ou TTL dépassé. */
export function mandateNeedsAsk(now = Date.now()) {
  const st = load()
  if (!st.updatedAt) return true
  if (st.until <= now) return true
  return false
}

/**
 * @param {MandateScope[]} watch
 * @param {number} [ttlMs]
 */
export function setMandate(watch, ttlMs = MANDATE_TTL_MS) {
  const allowed = (watch || []).filter((x) => MANDATE_SCOPES.some((s) => s.id === x))
  const nextWatch = /** @type {MandateScope[]} */ (
    allowed.length ? allowed : ['jobs_l2']
  )
  const now = Date.now()
  save({
    watch: nextWatch,
    updatedAt: now,
    until: now + ttlMs,
  })
  // Aligne l'objectif affiché sur le 1er scope
  const primary = MANDATE_SCOPES.find((s) => s.id === nextWatch[0])
  const goalId =
    (primary && STUDIO_GOALS.some((g) => g.id === primary.goalId) && primary.goalId) ||
    'jobs_l2'
  patchStudioGoal({ goalId, enabled: true })
  return getMandate()
}

/** @param {MandateScope} scope */
export function mandateAllows(scope) {
  const st = load()
  if (!st.updatedAt) {
    // défaut soft : jobs_l2 seulement jusqu'à confirmation
    return scope === 'jobs_l2'
  }
  return st.watch.includes(scope)
}

/**
 * Filtre intents Agir selon mandat (Garde passe toujours).
 * @param {Array<{ id?: string, kind?: string, label?: string, sourceText?: string, hint?: string }>} intents
 * @param {{ isGuard?: boolean }} [opts]
 */
export function filterIntentsByMandate(intents, opts = {}) {
  if (opts.isGuard) return intents
  const list = Array.isArray(intents) ? intents : []
  const out = list.filter((it) => {
    const id = String(it.id || it.kind || '')
    if (id.includes('disk') || id.includes('probe') || id.includes('orch')) {
      return mandateAllows('lan') || opts.isGuard
    }
    if (id === 'mail' || id.includes('mail')) return mandateAllows('mail')
    if (id === 'morning_brief' || id.includes('morning')) {
      return mandateAllows('morning') || mandateAllows('studio') || mandateAllows('lan')
    }
    if (id === 'jobs' || id.includes('jobs') || id.includes('open_jobs')) {
      return mandateAllows('jobs_l2')
    }
    if (id.startsWith('studio') || id.includes('team') || id.includes('veille')) {
      return mandateAllows('studio')
    }
    if (id === 'selfcheck' || id === 'inventory' || id.includes('session')) {
      return mandateAllows('lan')
    }
    // desktop apps : opportunité soft si au moins un scope
    return true
  })
  return out.length ? out : list.slice(0, 1)
}

/** Intents toast Mandat (chips → setMandate). */
export function mandateAskIntents() {
  return MANDATE_SCOPES.map((s) => ({
    id: `mandate_${s.id}`,
    label: s.label,
    hint: s.hint,
    sourceText: '',
    mandateScope: s.id,
    mandatePick: true,
  }))
}

export function mandateAskMessage() {
  return (
    'Je peux veiller Jobs L2, le LAN, les mails, le Studio, ou le brief du matin. ' +
    'Quelle priorité pour les prochaines heures ?'
  )
}

/** Reset tests. */
export function resetMandate() {
  save(defaultState())
}
