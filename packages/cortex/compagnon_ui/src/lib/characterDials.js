/**
 * Dials de caractère Compagnon (lab) — 7 curseurs style MC, bornés LBG.
 * Sync localStorage + API `/character/dials` (best-effort).
 */

export const STORAGE_KEY = 'lbg_compagnon_character_dials_v1'
export const PANEL_KEY = 'lbg_compagnon_character_panel_v1'

/** @typedef {{ piquant: number, densite: number, ego: number, familiarite: number, politesse: number, humour: number, enthousiasme: number }} CharacterDials */

/** @type {{ id: keyof CharacterDials, label: string, low: string, high: string }[]} */
export const DIAL_DEFS = [
  { id: 'piquant', label: 'Piquant', low: 'Doux', high: 'Mordant' },
  { id: 'densite', label: 'Densité', low: 'Court', high: 'Long' },
  { id: 'ego', label: 'Ego', low: 'Modeste', high: 'Fier' },
  { id: 'familiarite', label: 'Familiarité', low: 'Formel', high: 'Familier' },
  { id: 'politesse', label: 'Politesse', low: 'Brut', high: 'Poli' },
  { id: 'humour', label: 'Humour', low: 'Sérieux', high: 'Blagueur' },
  { id: 'enthousiasme', label: 'Énergie', low: 'Blasé', high: 'Enthousiaste' },
]

function characterApiUrl(path) {
  const p = path.startsWith('/') ? path : `/${path}`
  try {
    const fromEnv = String(
      (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) || '',
    )
      .trim()
      .replace(/\/$/, '')
    if (fromEnv) return `${fromEnv}${p}`
    if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.PROD) {
      return `/api${p}`
    }
  } catch {
    /* node:test without vite */
  }
  return p
}

/** @returns {CharacterDials} */
export function defaultDials() {
  return {
    piquant: 0.35,
    densite: 0.35,
    ego: 0.45,
    familiarite: 0.4,
    politesse: 0.7,
    humour: 0.3,
    enthousiasme: 0.45,
  }
}

/**
 * @param {unknown} raw
 * @returns {CharacterDials}
 */
export function clampDials(raw) {
  const base = defaultDials()
  if (!raw || typeof raw !== 'object') return base
  /** @type {CharacterDials} */
  const out = { ...base }
  for (const def of DIAL_DEFS) {
    const v = /** @type {Record<string, unknown>} */ (raw)[def.id]
    const n = typeof v === 'number' ? v : Number(v)
    if (Number.isFinite(n)) out[def.id] = Math.max(0, Math.min(1, n))
  }
  return out
}

let _mem = null

/** @returns {CharacterDials} */
export function getDials() {
  try {
    if (typeof localStorage === 'undefined') {
      if (!_mem) _mem = defaultDials()
      return { ..._mem }
    }
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaultDials()
    return clampDials(JSON.parse(raw))
  } catch {
    return defaultDials()
  }
}

/** @param {Partial<CharacterDials>} patch */
export function setDials(patch) {
  const next = clampDials({ ...getDials(), ...(patch || {}) })
  try {
    if (typeof localStorage === 'undefined') {
      _mem = next
    } else {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    }
  } catch {
    _mem = next
  }
  return next
}

export function resetDials() {
  const d = defaultDials()
  try {
    if (typeof localStorage !== 'undefined') localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* ignore */
  }
  _mem = d
  return d
}

export function isPanelOpen() {
  try {
    if (typeof localStorage === 'undefined') return false
    return localStorage.getItem(PANEL_KEY) === '1'
  } catch {
    return false
  }
}

/** @param {boolean} open */
export function setPanelOpen(open) {
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(PANEL_KEY, open ? '1' : '0')
    }
  } catch {
    /* ignore */
  }
}

/** Sync dials vers le backend Orch (best-effort). */
export async function syncDialsToServer(dials, { lab = true } = {}) {
  const body = { dials: clampDials(dials), lab: !!lab }
  try {
    const res = await fetch(characterApiUrl('/character/dials'), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) return { ok: false, status: res.status }
    const data = await res.json()
    if (data?.dials) setDials(data.dials)
    return { ok: true, dials: data?.dials || body.dials }
  } catch (err) {
    return { ok: false, error: String(err?.message || err) }
  }
}

/** Charge dials serveur si dispo, sinon local. */
export async function hydrateDialsFromServer() {
  try {
    const res = await fetch(characterApiUrl('/character/dials'), {
      headers: { Accept: 'application/json' },
    })
    if (!res.ok) return getDials()
    const data = await res.json()
    if (data?.dials) return setDials(data.dials)
  } catch {
    /* ignore */
  }
  return getDials()
}
