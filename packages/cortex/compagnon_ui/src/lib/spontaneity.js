/**
 * Client Spontanéité — enrichit une offre d'initiative via LLM light (.100).
 * Fallback silencieux → offre heuristique.
 */

/**
 * @typedef {{
 *   id?: string,
 *   label?: string,
 *   sourceText?: string,
 *   hint?: string,
 *   teamSpawn?: boolean,
 *   teamObjective?: string,
 *   teamRole?: string,
 * }} SpontIntent
 */

/**
 * @typedef {{
 *   offer: boolean,
 *   id?: string,
 *   message?: string,
 *   kind?: string,
 *   offerType?: string,
 *   intents?: SpontIntent[],
 *   primary?: SpontIntent|null,
 *   goal?: { id?: string, title?: string }|null,
 *   fromSelf?: boolean,
 *   themes?: string[],
 *   evolution_seed?: string|null,
 *   spontaneous?: boolean,
 *   spice_mode?: string,
 * }} InitiativeOffer
 */

const PROPOSE_TIMEOUT_MS = 10_000

function spontaneityApiUrl(path) {
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

/**
 * @param {InitiativeOffer} offer
 * @param {{ selfLine?: string, goalTitle?: string }} [ctx]
 * @returns {Promise<InitiativeOffer>}
 */
export async function spiceInitiative(offer, ctx = {}) {
  if (!offer?.offer || !offer.message) return offer
  const ctrl = typeof AbortController !== 'undefined' ? new AbortController() : null
  const timer = ctrl ? setTimeout(() => ctrl.abort(), PROPOSE_TIMEOUT_MS) : null
  try {
    const res = await fetch(spontaneityApiUrl('/spontaneity/propose'), {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: offer.id || '',
        message: offer.message || '',
        kind: offer.kind || '',
        offerType: offer.offerType || '',
        intents: offer.intents || [],
        primary: offer.primary || null,
        goal: offer.goal || null,
        fromSelf: Boolean(offer.fromSelf),
        offer: true,
        context: {
          self_line: ctx.selfLine || '',
          goal_title: ctx.goalTitle || offer.goal?.title || '',
        },
      }),
      signal: ctrl?.signal,
      cache: 'no-store',
    })
    if (timer) clearTimeout(timer)
    if (!res.ok) return offer
    const data = await res.json()
    if (!data?.ok || !data.spontaneous || !data.message) return offer
    const intents = Array.isArray(data.intents) && data.intents.length ? data.intents : offer.intents
    return {
      ...offer,
      message: String(data.message),
      intents,
      primary: data.primary || intents?.[0] || offer.primary,
      themes: Array.isArray(data.themes) ? data.themes : [],
      evolution_seed: data.evolution_seed || null,
      spontaneous: true,
      spice_mode: data.spice_mode || '',
      spiceSource: data.source || 'ollama_light',
    }
  } catch {
    if (timer) clearTimeout(timer)
    return offer
  }
}

/**
 * @param {{
 *   id?: string,
 *   kind?: 'accept'|'dismiss',
 *   themes?: string[],
 *   message?: string,
 *   evolution_seed?: string|null,
 * }} payload
 */
export async function sendSpontaneityFeedback(payload) {
  try {
    await fetch(spontaneityApiUrl('/spontaneity/feedback'), {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: payload.id || '',
        kind: payload.kind === 'accept' ? 'accept' : 'dismiss',
        themes: payload.themes || [],
        message: payload.message || '',
        evolution_seed: payload.evolution_seed || null,
      }),
      cache: 'no-store',
    })
  } catch {
    /* ignore — feedback best-effort */
  }
}

/**
 * Merge résultat spice dans l'objet toast courant.
 * @param {InitiativeOffer} offer
 * @param {Record<string, unknown>} [extra]
 */
export function toToastPayload(offer, extra = {}) {
  return {
    id: offer.id,
    message: offer.message,
    kind: offer.kind,
    offerType: offer.offerType || offer.kind || 'initiative',
    intents: offer.intents || [],
    primary: offer.primary || offer.intents?.[0] || null,
    goal: offer.goal || null,
    at: Date.now(),
    fromSelf: Boolean(offer.fromSelf),
    spontaneous: Boolean(offer.spontaneous),
    themes: offer.themes || [],
    evolution_seed: offer.evolution_seed || null,
    spice_mode: offer.spice_mode || '',
    willId: offer.willId || null,
    willKind: offer.willKind || null,
    autoValidate: offer.autoValidate || null,
    ...extra,
  }
}

export { spontaneityApiUrl }

/**
 * Snapshot évolution (seeds scorées).
 * @returns {Promise<{ ok?: boolean, evolution_seeds?: Array<Record<string, unknown>> }|null>}
 */
export async function fetchEvolution() {
  try {
    const res = await fetch(spontaneityApiUrl('/spontaneity/evolution'), {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

/**
 * Meilleure seed non encore trop vieille pour toast local.
 * @param {{ evolution_seeds?: Array<Record<string, unknown>> }|null|undefined} snap
 */
export function topEvolutionSeed(snap) {
  const seeds = Array.isArray(snap?.evolution_seeds) ? snap.evolution_seeds : []
  const ranked = seeds
    .filter((s) => s && typeof s === 'object' && String(s.text || '').length >= 12)
    .map((s) => ({ ...s, score: Number(s.score) || 0 }))
    .sort((a, b) => b.score - a.score)
  return ranked[0] || null
}
