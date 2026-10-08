/**
 * Watch missions Campus → toast / chat quand traitées (D6.5 suivi).
 * Stockage local — pas d'Agir ; lecture seule Pilot `#/team`.
 */

const STORAGE_KEY = 'lbg_compagnon_mission_watch_v1'
const MAX_WATCHES = 8

/**
 * @typedef {{
 *   missionId: string,
 *   objective?: string,
 *   taskIds?: string[],
 *   createdAt: number,
 *   notify: boolean,
 *   notifiedAt?: number|null,
 *   lastStatus?: string,
 * }} MissionWatch
 */

function safeParse(raw) {
  try {
    const data = JSON.parse(raw || '[]')
    return Array.isArray(data) ? data : []
  } catch {
    return []
  }
}

/** @returns {MissionWatch[]} */
export function listWatches() {
  if (typeof localStorage === 'undefined') return []
  return safeParse(localStorage.getItem(STORAGE_KEY))
    .filter((w) => w && w.missionId)
    .slice(0, MAX_WATCHES)
}

/** @param {MissionWatch[]} watches */
function persist(watches) {
  if (typeof localStorage === 'undefined') return
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(watches.slice(0, MAX_WATCHES)))
  } catch {
    /* ignore quota */
  }
}

/**
 * @param {{ missionId: string, objective?: string, taskIds?: string[], notify?: boolean }} input
 * @returns {MissionWatch|null}
 */
export function watchMission(input) {
  const missionId = String(input?.missionId || '').trim()
  if (!missionId) return null
  const watches = listWatches().filter((w) => w.missionId !== missionId)
  /** @type {MissionWatch} */
  const entry = {
    missionId,
    objective: String(input.objective || '').slice(0, 240),
    taskIds: Array.isArray(input.taskIds) ? input.taskIds.map(String).slice(0, 20) : [],
    createdAt: Date.now(),
    notify: input.notify !== false,
    notifiedAt: null,
    lastStatus: 'watching',
  }
  watches.unshift(entry)
  persist(watches)
  return entry
}

/** Active le flag notify sur une mission (ou la dernière). */
export function requestNotify(missionId = '') {
  const watches = listWatches()
  if (!watches.length) return null
  const id = String(missionId || '').trim()
  let hit = id ? watches.find((w) => w.missionId === id) : watches[0]
  if (!hit) {
    hit = watches[0]
  }
  hit.notify = true
  hit.notifiedAt = null
  hit.lastStatus = 'watching'
  persist(watches)
  return hit
}

export function markNotified(missionId, status = 'done') {
  const watches = listWatches()
  const hit = watches.find((w) => w.missionId === missionId)
  if (!hit) return
  hit.notifiedAt = Date.now()
  hit.lastStatus = status
  hit.notify = false
  persist(watches)
}

/** Heuristique NL : l'humain demande un retour à la clôture. */
export function wantsMissionNotify(prompt) {
  const t = String(prompt || '')
  return (
    /\b(retour\s+quand|pr[ée]viens?[-\s]?moi|notifie[-\s]?moi|ping(?:ue)?[-\s]?moi)\b/i.test(
      t,
    ) ||
    /\bquand\s+(?:la\s+)?team\s+(?:a\s+|aura\s+)?(?:trait|fini|clos|termin)/i.test(t) ||
    /\bdis[- ]?moi\s+quand\b/i.test(t) ||
    /\bsuivi\s+(?:de\s+la\s+)?mission\b/i.test(t)
  )
}

/**
 * Unwrap OkEnvelope Pilot si besoin.
 * @param {any} data
 */
export function unwrapPilot(data) {
  if (!data || typeof data !== 'object') return {}
  if (data.body && typeof data.body === 'object') return data.body
  if (data.payload && typeof data.payload === 'object') return data.payload
  return data
}

export async function fetchCampusSnapshot() {
  const [stRes, clRes] = await Promise.all([
    fetch('/api/pilot/team/campus/status', { headers: { Accept: 'application/json' } }),
    fetch('/api/pilot/team/campus/mission/closure', {
      headers: { Accept: 'application/json' },
    }),
  ])
  const status = unwrapPilot(stRes.ok ? await stRes.json() : {})
  const closure = unwrapPilot(clRes.ok ? await clRes.json() : {})
  return { status, closure, ok: stRes.ok }
}

/**
 * @param {{ status: any, closure: any }} snap
 * @param {MissionWatch} watch
 * @returns {{ ready: boolean, kind: 'closable'|'closed'|'replaced'|null, detail: string }}
 */
export function evaluateWatch(snap, watch) {
  const mission = snap?.status?.mission || {}
  const openId = String(mission.id || '')
  const closure = snap?.closure || snap?.status?.mission_closure || {}
  const closable = Boolean(closure.closable ?? snap?.status?.decision?.mission_closable)
  const closeOutcome = closure.outcome || snap?.status?.decision?.mission_close_outcome
  const stats = closure.task_stats || {}
  const obj = String(watch.objective || mission.objective || '').slice(0, 100)

  if (openId && openId === watch.missionId) {
    if (closable || closeOutcome === 'closed' || String(mission.status) === 'closed') {
      return {
        ready: true,
        kind: closable ? 'closable' : 'closed',
        detail: obj
          ? `Mission prête / close — ${obj}`
          : `Mission \`${watch.missionId.slice(0, 8)}…\` traitée (Team).`,
      }
    }
    const pending = Number(stats.pending ?? 0)
    const done = Number(stats.done ?? 0)
    return {
      ready: false,
      kind: null,
      detail: `Encore ouverte (${done} done / ${pending} pending).`,
    }
  }

  // Plus la mission ouverte courante → considérée traitée / remplacée
  if (watch.missionId && openId && openId !== watch.missionId) {
    return {
      ready: true,
      kind: 'replaced',
      detail: obj
        ? `La mission « ${obj} » n'est plus la mission Campus ouverte (traitée ou remplacée).`
        : `Mission \`${watch.missionId.slice(0, 8)}…\` plus ouverte sur le Campus.`,
    }
  }

  // Aucune mission ouverte
  if (!openId && watch.missionId) {
    return {
      ready: true,
      kind: 'closed',
      detail: obj
        ? `Plus de mission Campus ouverte — « ${obj} » est considérée traitée.`
        : `Plus de mission Campus ouverte (\`${watch.missionId.slice(0, 8)}…\`).`,
    }
  }

  return { ready: false, kind: null, detail: 'en cours' }
}

/**
 * @param {MissionWatch} watch
 * @param {{ kind: string, detail: string }} evalResult
 */
export function offerFromMissionDone(watch, evalResult) {
  const short = watch.missionId.slice(0, 8)
  const label =
    evalResult.kind === 'closable'
      ? 'prête à clôturer'
      : evalResult.kind === 'replaced'
        ? 'plus ouverte (traitée / remplacée)'
        : 'traitée'
  return {
    offer: true,
    id: `mission:done:${watch.missionId}`,
    offerType: 'studio',
    kind: 'mission_watch',
    message: `Team — mission \`${short}…\` ${label}. ${evalResult.detail} Suivi : Pilot #/team/office.`,
    intents: [
      {
        id: 'mission_pilot',
        label: 'Ouvrir Pilot Team',
        hint: 'bureau',
        sourceText: 'ouvre http://192.168.0.140:8080/pilot/#/team/office dans le navigateur',
      },
      {
        id: 'mission_status',
        label: 'Status campus',
        hint: 'lecture',
        sourceText: 'team: status campus',
      },
    ],
    primary: null,
    goal: {
      id: `mission:${watch.missionId}`,
      title: String(watch.objective || `Mission ${short}`).slice(0, 80),
    },
  }
}

/**
 * Parcourt les watches notify — premier prêt gagne.
 * @param {{ status: any, closure: any }} snap
 */
export function nextMissionOffer(snap) {
  for (const w of listWatches()) {
    if (!w.notify || w.notifiedAt) continue
    const ev = evaluateWatch(snap, w)
    if (ev.ready) {
      return { watch: w, eval: ev, offer: offerFromMissionDone(w, ev) }
    }
  }
  return null
}

/** Accusé de réception chat (sans Agir / dry-run). */
export function ackNotifyMessage(watch) {
  if (!watch?.missionId) {
    return (
      "C'est noté — dès qu'une mission Campus est en watch, je te préviens à la clôture "
      + "(toast + message). Pas besoin d'Agir : tu es déjà l'humain qui demande le suivi."
    )
  }
  const short = watch.missionId.slice(0, 8)
  const obj = watch.objective ? ` (« ${String(watch.objective).slice(0, 80)} »)` : ''
  return (
    `OK — je surveille la mission \`${short}…\`${obj}. `
    + "Je te ferai un retour (toast + message) quand la Team l'aura traitée / clôturée. "
    + "C'est un suivi lecture seule (pas une action Agir) — Pilot `#/team/office`."
  )
}
