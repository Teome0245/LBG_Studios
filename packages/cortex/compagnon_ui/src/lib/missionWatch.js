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

/** Tokens significatifs pour détecter un respawn « même sujet ». */
const SUBJECT_KEEP = new Set([
  'zone',
  'entrainement',
  'entraînement',
  'presence',
  'présence',
  'nix',
  'lia',
  'mmorpg',
  'dials',
  'dial',
  'smoke',
  'brief',
  'chaleur',
  'humeur',
  'compagnon',
  'hub',
  'lost',
  'heaven',
  'incarnation',
  'joueur',
  'joueurs',
])

/**
 * Empreinte sujet (ignore blabla Hermès / Dry-run).
 * @param {string} objective
 * @returns {Set<string>}
 */
export function objectiveSubjectTokens(objective) {
  const raw = String(objective || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/\p{M}/gu, '')
  const cleaned = raw
    .replace(/herm[eè]s[^:]*:/gi, ' ')
    .replace(/dry[\s-]?run[^.]*/gi, ' ')
    .replace(/owners?\s+typiques[^.]*/gi, ' ')
    .replace(/---[\s\S]*$/g, ' ')
  const words = cleaned.match(/[a-z0-9àâäéèêëïîôùûüç]+/gi) || []
  const out = new Set()
  for (const w of words) {
    const n = w
      .normalize('NFD')
      .replace(/\p{M}/gu, '')
      .toLowerCase()
    if (n.length < 3) continue
    if (SUBJECT_KEEP.has(n) || SUBJECT_KEEP.has(w.toLowerCase())) out.add(n)
    // bi-grammes utiles
    if (n.includes('entrain')) out.add('entrainement')
    if (n.includes('presen')) out.add('presence')
  }
  return out
}

/**
 * Même sujet si ≥2 tokens partagés, ou 1 token fort (nix/mmorpg/…) + overlap.
 * @param {string} a
 * @param {string} b
 */
export function sameSubjectObjective(a, b) {
  const ta = objectiveSubjectTokens(a)
  const tb = objectiveSubjectTokens(b)
  if (!ta.size || !tb.size) return false
  let shared = 0
  for (const t of ta) {
    if (tb.has(t)) shared += 1
  }
  if (shared >= 2) return true
  const strong = ['nix', 'lia', 'mmorpg', 'entrainement', 'presence']
  if (shared >= 1 && strong.some((s) => ta.has(s) && tb.has(s))) return true
  return false
}

/**
 * Ré-attache le watch sur un nouvel id (respawn même sujet).
 * @param {string} oldMissionId
 * @param {{ missionId: string, objective?: string, taskIds?: string[] }} next
 */
export function retargetWatch(oldMissionId, next) {
  const watches = listWatches()
  const hit = watches.find((w) => w.missionId === oldMissionId)
  const newId = String(next?.missionId || '').trim()
  if (!hit || !newId) return null
  // Évite doublon sur le nouvel id
  const others = watches.filter((w) => w.missionId !== oldMissionId && w.missionId !== newId)
  hit.missionId = newId
  if (next.objective) hit.objective = String(next.objective).slice(0, 240)
  if (Array.isArray(next.taskIds)) hit.taskIds = next.taskIds.map(String).slice(0, 20)
  hit.notify = true
  hit.notifiedAt = null
  hit.lastStatus = 'retargeted'
  hit.createdAt = Date.now()
  others.unshift(hit)
  persist(others)
  return hit
}

/**
 * @param {{ status: any, closure: any }} snap
 * @param {MissionWatch} watch
 * @returns {{
 *   ready: boolean,
 *   kind: 'closable'|'closed'|'replaced'|'continued'|null,
 *   detail: string,
 *   retarget?: { missionId: string, objective?: string, taskIds?: string[] },
 * }}
 */
export function evaluateWatch(snap, watch) {
  const mission = snap?.status?.mission || {}
  const openId = String(mission.id || '')
  const openObj = String(mission.objective || '')
  const closure = snap?.closure || snap?.status?.mission_closure || {}
  const closable = Boolean(closure.closable ?? snap?.status?.decision?.mission_closable)
  const closeOutcome = closure.outcome || snap?.status?.decision?.mission_close_outcome
  const stats = closure.task_stats || {}
  const obj = String(watch.objective || openObj || '').slice(0, 100)

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

  // Respawn même sujet → continuer le watch (pas de faux « traité »)
  if (watch.missionId && openId && openId !== watch.missionId) {
    if (sameSubjectObjective(watch.objective || '', openObj)) {
      return {
        ready: false,
        kind: 'continued',
        detail: `Même sujet — watch basculé vers \`${openId.slice(0, 8)}…\`.`,
        retarget: {
          missionId: openId,
          objective: openObj.slice(0, 240),
          taskIds: Array.isArray(mission.task_ids) ? mission.task_ids : [],
        },
      }
    }
    return {
      ready: true,
      kind: 'replaced',
      detail: obj
        ? `La mission « ${obj} » n'est plus la mission Campus ouverte (autre sujet).`
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
 * Parcourt les watches notify — retarget même sujet silencieux ; premier prêt gagne.
 * @param {{ status: any, closure: any }} snap
 */
export function nextMissionOffer(snap) {
  for (const w of listWatches()) {
    if (!w.notify || w.notifiedAt) continue
    const ev = evaluateWatch(snap, w)
    if (ev.kind === 'continued' && ev.retarget?.missionId) {
      retargetWatch(w.missionId, ev.retarget)
      continue
    }
    if (ev.ready) {
      return { watch: w, eval: ev, offer: offerFromMissionDone(w, ev) }
    }
  }
  return null
}

/**
 * Ré-arme explicitement sur la mission Campus ouverte (après faux « replaced »).
 * @returns {Promise<MissionWatch|null>}
 */
export async function rearmOnOpenCampusMission() {
  const snap = await fetchCampusSnapshot().catch(() => null)
  const mission = snap?.status?.mission || {}
  const mid = String(mission.id || '').trim()
  if (!mid) return null
  return watchMission({
    missionId: mid,
    objective: String(mission.objective || '').slice(0, 240),
    taskIds: Array.isArray(mission.task_ids) ? mission.task_ids : [],
    notify: true,
  })
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
