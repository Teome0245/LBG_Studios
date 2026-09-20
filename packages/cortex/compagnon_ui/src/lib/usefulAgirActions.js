/**
 * Catalogue d'actions Agir « utiles » (ops / poste / LAN).
 * Utilisé : suite post-succès ActionCard, défauts initiative, palette.
 */

/**
 * @typedef {{
 *   id: string,
 *   label: string,
 *   hint?: string,
 *   sourceText: string,
 *   kind?: string,
 * }} UsefulAgirAction
 */

/** @type {UsefulAgirAction[]} */
export const USEFUL_AGIR_ACTIONS = [
  {
    id: 'selfcheck',
    label: 'Selfcheck LAN',
    hint: 'devops · lecture seule',
    sourceText: 'fais un diagnostic infra selfcheck LAN',
    kind: 'selfcheck',
  },
  {
    id: 'inventory',
    label: 'Inventaire réseau',
    hint: 'sondes read-only',
    sourceText: 'fais un inventaire réseau LAN cartographie des appareils',
    kind: 'network_inventory',
  },
  {
    id: 'mail',
    label: 'Mails récents',
    hint: 'IMAP preview',
    sourceText: 'regarde mes mails récents',
    kind: 'mail_imap_preview',
  },
  {
    id: 'search',
    label: 'Recherche web',
    hint: 'navigateur',
    sourceText: 'cherche sur internet LBG Studios Cursor agent desktop',
    kind: 'search_web_open',
  },
  {
    id: 'vghd',
    label: 'Ouvrir VGHD',
    hint: 'desktop',
    sourceText: 'ouvre vghd sur mon pc',
    kind: 'open_app',
  },
  {
    id: 'notepad',
    label: 'Notepad++',
    hint: 'desktop',
    sourceText: 'ouvre notepadpp sur mon pc',
    kind: 'open_app',
  },
  {
    id: 'jobs',
    label: 'Pilot Jobs L2',
    hint: 'approbations',
    sourceText: 'ouvre http://192.168.0.140:8080/#/jobs dans le navigateur',
    kind: 'open_url',
  },
  {
    id: 'cockpit',
    label: 'Cockpit P03',
    hint: 'mur infra',
    sourceText: 'ouvre http://192.168.0.100:8093/pilot/#/cockpit dans le navigateur',
    kind: 'open_url',
  },
  {
    id: 'orch_ui',
    label: 'Orch Compagnon',
    hint: 'chat .100',
    sourceText: 'ouvre http://192.168.0.100:5174/ dans le navigateur',
    kind: 'open_url',
  },
  {
    id: 'browser_info',
    label: 'Navigateur par défaut',
    hint: 'lecture seule',
    sourceText: 'quel est mon navigateur par défaut',
    kind: 'default_browser_info',
  },
]

/**
 * Suggestions de suite après une action réussie (exclut l'action courante).
 * @param {{ kind?: string, url?: string, capability?: string }} [done]
 * @param {number} [limit]
 * @returns {UsefulAgirAction[]}
 */
export function nextUsefulAgirSuggestions(done = {}, limit = 4) {
  const kind = String(done.kind || '').toLowerCase()
  const url = String(done.url || '').toLowerCase()
  const cap = String(done.capability || '').toLowerCase()

  const skip = new Set()
  if (kind) skip.add(kind)
  if (cap === 'devops_probe') skip.add('selfcheck')
  if (cap === 'network_inventory') skip.add('network_inventory')
  if (url.includes('#/jobs') || url.includes('/jobs')) skip.add('jobs')
  if (url.includes('8093') || url.includes('cockpit')) skip.add('cockpit')
  if (url.includes(':5174')) skip.add('orch_ui')
  // Ouvrir Pilot racine .140:8080 ≈ déjà « navigué » — proposer autre chose qu'un 2e open_url
  if (kind === 'open_url' && (url.includes('192.168.0.140:8080') || url.includes('140:8080'))) {
    skip.add('jobs')
    skip.add('orch_ui')
  }

  return USEFUL_AGIR_ACTIONS.filter((a) => !skip.has(a.kind) && !skip.has(a.id)).slice(
    0,
    Math.max(1, limit),
  )
}

/** Défauts initiative quand aucun signal infra critique. */
export function idleUsefulAgirIntents(limit = 3) {
  return USEFUL_AGIR_ACTIONS.filter((a) =>
    ['selfcheck', 'mail', 'vghd', 'inventory', 'jobs'].includes(a.id),
  )
    .slice(0, limit)
    .map((a) => ({
      id: a.id,
      label: a.label,
      sourceText: a.sourceText,
      hint: a.hint,
    }))
}
