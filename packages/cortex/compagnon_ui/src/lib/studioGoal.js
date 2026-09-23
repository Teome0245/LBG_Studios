/**
 * Objectif Studio persistant — autonomie émergente pilotée (1 but à la fois).
 * Stockage local ; feedback Agir / Ignorer biaise les prochaines initiatives.
 */

const STORAGE_KEY = 'lbg_compagnon_studio_goal_v1'

/**
 * @typedef {{
 *   id: string,
 *   title: string,
 *   description: string,
 *   signalPrefixes: string[],
 * }} StudioGoalDef
 */

/** Catalogue minimal — un seul objectif actif pour l’instant. */
/** @type {StudioGoalDef[]} */
export const STUDIO_GOALS = [
  {
    id: 'jobs_l2',
    title: 'Veiller Jobs L2',
    description: 'Proposer une revue quand tension orch élevée, silence proactif, ou job en attente.',
    // jobs:idle = silence prolongé (orch proactif) — rendu « vivant » sans alerte infra
    signalPrefixes: ['tension:high', 'job:', 'jobs:', 'infra:', 'disk:', 'act:'],
  },
]

/**
 * @typedef {{
 *   goalId: string,
 *   enabled: boolean,
 *   feedback: Record<string, { accept: number, dismiss: number }>,
 *   updatedAt: number,
 * }} StudioGoalState
 */

let _mem = null

function defaultState() {
  return {
    goalId: 'jobs_l2',
    enabled: true,
    feedback: {},
    updatedAt: Date.now(),
  }
}

function load() {
  try {
    if (typeof localStorage === 'undefined') {
      if (!_mem) _mem = defaultState()
      return { ..._mem, feedback: { ...(_mem.feedback || {}) } }
    }
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaultState()
    const p = JSON.parse(raw)
    return {
      goalId: typeof p?.goalId === 'string' ? p.goalId : 'jobs_l2',
      enabled: p?.enabled !== false,
      feedback: p?.feedback && typeof p.feedback === 'object' ? p.feedback : {},
      updatedAt: typeof p?.updatedAt === 'number' ? p.updatedAt : Date.now(),
    }
  } catch {
    return defaultState()
  }
}

function save(state) {
  const next = { ...state, updatedAt: Date.now() }
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

/** @returns {StudioGoalDef} */
export function activeGoalDef() {
  const st = load()
  return STUDIO_GOALS.find((g) => g.id === st.goalId) || STUDIO_GOALS[0]
}

/** @returns {StudioGoalState & { goal: StudioGoalDef }} */
export function getStudioGoal() {
  const st = load()
  const goal = STUDIO_GOALS.find((g) => g.id === st.goalId) || STUDIO_GOALS[0]
  return { ...st, goal }
}

/**
 * Alignement fingerprint ↔ objectif actif (0..1).
 * @param {string} fingerprint
 * @param {StudioGoalDef} [goal]
 */
export function goalRelevance(fingerprint, goal = activeGoalDef()) {
  const id = String(fingerprint || '')
  if (!id || !goal?.signalPrefixes?.length) return 0
  for (const pref of goal.signalPrefixes) {
    if (id === pref || id.startsWith(pref)) {
      if (pref.startsWith('infra:')) return 1
      if (pref === 'tension:high') return 0.85
      if (pref === 'job:') return 0.9
      return 0.7
    }
  }
  return 0.15
}

/**
 * @param {string} fingerprint
 * @param {'accept'|'dismiss'} kind
 */
export function recordGoalFeedback(fingerprint, kind) {
  if (!fingerprint || (kind !== 'accept' && kind !== 'dismiss')) return
  const st = load()
  const prev = st.feedback[fingerprint] || { accept: 0, dismiss: 0 }
  const next = {
    accept: prev.accept + (kind === 'accept' ? 1 : 0),
    dismiss: prev.dismiss + (kind === 'dismiss' ? 1 : 0),
  }
  st.feedback[fingerprint] = next
  save(st)
}

/**
 * Si l’utilisateur ignore souvent un signal sans jamais accepter → freiner.
 * @param {string} fingerprint
 * @returns {{ suppress: boolean, reason?: string, weight: number }}
 */
export function feedbackGate(fingerprint) {
  if (!fingerprint) return { suppress: false, weight: 1 }
  const st = load()
  if (!st.enabled) return { suppress: false, weight: 1 }
  const fb = st.feedback[fingerprint] || { accept: 0, dismiss: 0 }
  const weight = Math.max(0.2, 1 + fb.accept * 0.25 - fb.dismiss * 0.35)
  // 2+ ignores sans accept → ne plus proposer ce signal seul
  if (fb.dismiss >= 2 && fb.accept === 0) {
    return { suppress: true, reason: 'learned_dismiss', weight: 0 }
  }
  return { suppress: false, weight }
}

/**
 * Message teinté par l’objectif (sans jargon).
 * @param {string} base
 * @param {string} fingerprint
 */
export function messageWithGoal(base, fingerprint) {
  const st = load()
  if (!st.enabled) return base
  const rel = goalRelevance(fingerprint)
  if (rel < 0.5) return base
  const g = activeGoalDef()
  return `${base} (objectif · ${g.title})`
}

/** Remise à zéro feedback (tests / debug). */
export function resetStudioGoalFeedback() {
  const st = load()
  st.feedback = {}
  save(st)
}

/** @param {Partial<StudioGoalState>} patch */
export function patchStudioGoal(patch) {
  const st = load()
  save({ ...st, ...patch, feedback: patch.feedback ?? st.feedback })
}
