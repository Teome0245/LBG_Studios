/**
 * Affichage tier light/heavy à partir du modèle ou des méta route_*.
 */

const HEAVY_RE = /(:9b|:12b|12b-qat|:e4b|27b)/i
const LIGHT_RE = /(0\.8[Bb]|:2[Bb]|:e2b|llama3\.2:3b|qwen2\.5:3b)/i

/**
 * @param {{ model?: string, route_tier?: string, route_profile?: string }} msg
 * @returns {'heavy'|'light'|''}
 */
export function resolveRouteTier(msg) {
  const explicit = String(msg?.route_tier || '').toLowerCase()
  if (explicit === 'heavy' || explicit === 'light') return explicit
  const model = String(msg?.model || msg?.route_preferred || '')
  if (HEAVY_RE.test(model)) return 'heavy'
  if (LIGHT_RE.test(model)) return 'light'
  return ''
}

/**
 * @param {{ route_profile?: string, route_tier?: string }} msg
 */
export function routeTierLabel(msg) {
  const tier = resolveRouteTier(msg)
  if (tier === 'heavy') return 'L2 heavy'
  if (tier === 'light') {
    const p = String(msg?.route_profile || '')
    if (p === 'fast') return 'L1 fast'
    if (p === 'dialogue') return 'L1 chat'
    return 'L1 light'
  }
  return ''
}
