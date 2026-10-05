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
    id: 'morning_brief',
    label: 'Brief du matin',
    hint: 'Self · proactive · infra',
    sourceText: 'fais mon brief du matin',
    kind: 'morning_brief',
  },
  {
    id: 'memory_recall',
    label: 'Ma mémoire',
    hint: 'Self + leçons (≠ RAM VM)',
    sourceText: 'montre ce que tu retiens (mémoire agent)',
    kind: 'memory_recall',
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
    id: 'session0',
    label: 'Réparer Session 0',
    hint: 'agent .10 · Admin task',
    sourceText: 'répare session 0 de l agent desktop',
    kind: 'fix_session0',
  },
  {
    id: 'session_status',
    label: 'Session agent',
    hint: 'lecture seule',
    sourceText: 'vérifie la session de l agent desktop',
    kind: 'agent_session_status',
  },
  {
    id: 'omarchy_chromium',
    label: 'Chromium sur Omarchy',
    hint: 'poste .143',
    sourceText: 'ouvre chromium sur omarchy',
    kind: 'open_app',
  },
  {
    id: 'omarchy_vscode',
    label: 'VS Code + Cline (.143)',
    hint: 'workspace → Plan→Act',
    sourceText: 'ouvre code sur omarchy',
    kind: 'open_app',
  },
  {
    id: 'omarchy_cli_agent',
    label: 'Mains code Claude (.143)',
    hint: 'CLI headless · ADR 0025',
    sourceText: 'lance claude sur omarchy pour un smoke dry-run du monorepo',
    kind: 'run_cli_agent',
  },
  {
    id: 'omarchy_second_avis',
    label: 'Second avis Claude Code',
    hint: 'ADR 0023 · concurrent Cline',
    sourceText: 'second avis claude code sur omarchy',
    kind: 'open_app',
  },
  {
    id: 'omarchy_vscode_update',
    label: 'MAJ VS Code (.143)',
    hint: 'yay · hors session critique',
    sourceText: 'mets à jour vscode sur omarchy',
    kind: 'update_vscode',
  },
  {
    id: 'team_pilot',
    label: 'Pilot Team',
    hint: 'équipe virtuelle',
    sourceText: 'ouvre http://192.168.0.140:8080/#/team dans le navigateur',
    kind: 'open_url',
  },
  {
    id: 'omarchy_heal',
    label: 'Heal agent Omarchy',
    hint: '.143 · systemd user',
    sourceText: 'répare session 0 sur omarchy',
    kind: 'fix_session0',
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
 * @param {{ kind?: string, url?: string, capability?: string, app?: string, sourceText?: string }} [done]
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

  // Après ouverture IDE (.143) : prioriser second avis (ADR 0023)
  const preferSecondAvis =
    kind === 'open_app' &&
    (String(done.app || '').toLowerCase() === 'code' ||
      String(done.sourceText || '').toLowerCase().includes('code'))

  const filtered = USEFUL_AGIR_ACTIONS.filter((a) => !skip.has(a.kind) && !skip.has(a.id))
  if (preferSecondAvis) {
    const second = filtered.find((a) => a.id === 'omarchy_second_avis')
    const rest = filtered.filter((a) => a.id !== 'omarchy_second_avis')
    const ordered = second ? [second, ...rest] : rest
    return ordered.slice(0, Math.max(1, limit))
  }

  return filtered.slice(0, Math.max(1, limit))
}

/** Défauts initiative quand aucun signal infra critique (rotation horaire). */
export function idleUsefulAgirIntents(limit = 3) {
  const pool = USEFUL_AGIR_ACTIONS.filter((a) =>
    [
      'selfcheck',
      'morning_brief',
      'memory_recall',
      'mail',
      'vghd',
      'inventory',
      'jobs',
      'session0',
      'cockpit',
      'omarchy_vscode',
      'team_pilot',
    ].includes(a.id),
  )
  const hour = new Date().getHours()
  // Matin (7–10) : prioriser le brief en tête de rotation
  if (hour >= 7 && hour < 10) {
    const brief = pool.find((a) => a.id === 'morning_brief')
    const rest = pool.filter((a) => a.id !== 'morning_brief')
    const rotatedRest = (() => {
      const h = Math.floor(Date.now() / 3_600_000)
      const start = rest.length ? h % rest.length : 0
      return [...rest.slice(start), ...rest.slice(0, start)]
    })()
    const ordered = brief ? [brief, ...rotatedRest] : rotatedRest
    return ordered.slice(0, Math.max(1, limit)).map((a) => ({
      id: a.id,
      label: a.label,
      sourceText: a.sourceText,
      hint: a.hint || 'initiative',
    }))
  }
  const hourBucket = Math.floor(Date.now() / 3_600_000)
  const start = pool.length ? hourBucket % pool.length : 0
  const rotated = [...pool.slice(start), ...pool.slice(0, start)]
  return rotated.slice(0, Math.max(1, limit)).map((a) => ({
    id: a.id,
    label: a.label,
    sourceText: a.sourceText,
    hint: a.hint || 'initiative',
  }))
}
