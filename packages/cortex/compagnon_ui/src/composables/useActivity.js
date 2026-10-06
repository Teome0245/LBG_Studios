/**
 * Encart d’activité live (style Cursor) — impression d’action.
 * Pas d’auto-exec : pure UI de progression.
 */

import { ref, computed } from 'vue'

/** @typedef {{ ts: number, text: string, level?: 'info'|'ok'|'warn'|'err' }} ActivityLine */
/** @typedef {{
 *   id: string,
 *   title: string,
 *   tools: string[],
 *   lines: ActivityLine[],
 *   phase: 'running'|'planning'|'done'|'error',
 *   phaseLabel: string,
 *   open: boolean,
 *   startedAt: number,
 *   endedAt?: number,
 * }} Activity */

const current = ref(/** @type {Activity | null} */ (null))
const history = ref(/** @type {Activity[]} */ ([]))

function nowId() {
  return `act-${Date.now().toString(36)}`
}

const PHASE_LABELS = {
  running: 'En cours…',
  planning: 'Prépare la suite…',
  done: 'Terminé',
  error: 'Échec',
}

/**
 * @param {string} title
 * @param {string[]} [tools]
 */
export function startActivity(title, tools = []) {
  if (current.value && current.value.phase === 'running') {
    endActivity('done')
  }
  const titleStr = String(title || 'Action').slice(0, 120)
  const toolsList = (tools || []).map(String).slice(0, 6)
  // D6.3 : encart replié pour ask/réponse ; ouvert pour Agir / Team / palette
  const quietAsk =
    toolsList.includes('ask') ||
    /compagnon\s*[·•]\s*réponse/i.test(titleStr) ||
    /causerie/i.test(titleStr)
  current.value = {
    id: nowId(),
    title: titleStr,
    tools: toolsList,
    lines: [],
    phase: 'running',
    phaseLabel: PHASE_LABELS.running,
    open: !quietAsk,
    startedAt: Date.now(),
  }
  return current.value.id
}

/**
 * @param {string} text
 * @param {'info'|'ok'|'warn'|'err'} [level]
 */
export function activityLog(text, level = 'info') {
  if (!current.value) return
  const line = String(text || '').trim()
  if (!line) return
  current.value.lines.push({
    ts: Date.now(),
    text: line.slice(0, 400),
    level,
  })
  // Garde les ~40 dernières lignes visibles
  if (current.value.lines.length > 40) {
    current.value.lines = current.value.lines.slice(-40)
  }
}

/**
 * @param {'running'|'planning'|'done'|'error'} phase
 * @param {string} [label]
 */
export function activityPhase(phase, label) {
  if (!current.value) return
  current.value.phase = phase
  current.value.phaseLabel = label || PHASE_LABELS[phase] || phase
}

/**
 * @param {'done'|'error'} [phase]
 * @param {string} [finalLine]
 */
export function endActivity(phase = 'done', finalLine) {
  if (!current.value) return
  if (finalLine) activityLog(finalLine, phase === 'error' ? 'err' : 'ok')
  current.value.phase = phase
  current.value.phaseLabel = PHASE_LABELS[phase] || phase
  current.value.endedAt = Date.now()
  history.value = [current.value, ...history.value].slice(0, 8)
  // Garde l’encart visible 1,2s en “done” puis on peut laisser current
  const snap = current.value
  setTimeout(() => {
    if (current.value?.id === snap.id && current.value.phase !== 'running') {
      // reste affiché jusqu’à la prochaine activité
    }
  }, 0)
}

export function clearActivity() {
  current.value = null
}

export function toggleActivityOpen() {
  if (current.value) current.value.open = !current.value.open
}

export function useActivity() {
  return {
    current,
    history,
    active: computed(() => current.value?.phase === 'running' || current.value?.phase === 'planning'),
    startActivity,
    activityLog,
    activityPhase,
    endActivity,
    clearActivity,
    toggleActivityOpen,
  }
}
