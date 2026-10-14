/**
 * Préférences rapports monde (B1) — filtre greeting / stream / toasts.
 * Sync serveur via /world/notif-prefs pour short_social.
 */

export const WORLD_NOTIF_CATEGORIES = [
  {
    id: 'world_marking',
    label: 'Monde',
    hint: 'boss · événements · ferraille',
  },
  {
    id: 'companion_social',
    label: 'Social hub',
    hint: 'escortes · greets',
  },
  {
    id: 'ops_jobs',
    label: 'Ops / Jobs',
    hint: 'mandat · sondes (initiatives)',
  },
]

const STORAGE_KEY = 'lbg_world_notif_prefs_v1'

/** @returns {Record<string, boolean>} */
export function defaultWorldNotifPrefs() {
  return {
    world_marking: true,
    companion_social: true,
    ops_jobs: true,
  }
}

/** @returns {Record<string, boolean>} */
export function loadWorldNotifPrefs() {
  const base = defaultWorldNotifPrefs()
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return base
    const p = JSON.parse(raw)
    if (!p || typeof p !== 'object') return base
    for (const c of WORLD_NOTIF_CATEGORIES) {
      if (c.id in p) base[c.id] = Boolean(p[c.id])
    }
  } catch {
    /* ignore */
  }
  return base
}

/**
 * @param {Partial<Record<string, boolean>>} patch
 * @returns {Record<string, boolean>}
 */
export function saveWorldNotifPrefs(patch) {
  const next = { ...loadWorldNotifPrefs(), ...(patch || {}) }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  } catch {
    /* ignore */
  }
  return next
}

/**
 * @param {string} kind
 * @param {Record<string, boolean>} [prefs]
 */
export function categoryForEventKind(kind) {
  const k = String(kind || '').toLowerCase()
  if (k.includes('companion') || k.includes('escort')) return 'companion_social'
  return 'world_marking'
}

/**
 * @param {Array<Record<string, unknown>>} events
 * @param {Record<string, boolean>} [prefs]
 */
export function filterWorldEvents(events, prefs) {
  const p = prefs || loadWorldNotifPrefs()
  return (Array.isArray(events) ? events : []).filter((ev) => {
    if (!ev || typeof ev !== 'object') return false
    const cat = categoryForEventKind(ev.kind)
    return p[cat] !== false
  })
}

/** Push prefs to Orch (greeting monde respecte le filtre). */
export async function syncWorldNotifPrefs(prefs) {
  const body = prefs || loadWorldNotifPrefs()
  try {
    const { apiUrl } = await import('@/api/http')
    const res = await fetch(apiUrl('/world/notif-prefs'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) return { ok: false, prefs: body }
    const json = await res.json().catch(() => ({}))
    return { ok: true, prefs: json.prefs || body }
  } catch {
    return { ok: false, prefs: body }
  }
}
