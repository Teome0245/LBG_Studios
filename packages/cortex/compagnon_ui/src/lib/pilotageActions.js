/**
 * Pilotage Compagnon — actions de commande (comme un agent Cursor).
 * Barre visible = peu d’entrées ; le reste vit dans Ctrl+K (PILOTAGE_CATALOG).
 */

import { PILOT_LINKS } from '@/lib/pilotLinks'
import { USEFUL_AGIR_ACTIONS } from '@/lib/usefulAgirActions'

/**
 * @typedef {{
 *   id: string,
 *   label: string,
 *   hint?: string,
 *   kind: 'agir'|'ask'|'link',
 *   sourceText?: string,
 *   prompt?: string,
 *   href?: string,
 * }} PilotageAction
 */

/** Catalogue complet — palette Ctrl+K uniquement. */
/** @type {PilotageAction[]} */
export const PILOTAGE_CATALOG = [
  ...USEFUL_AGIR_ACTIONS.map((a) => ({
    id: a.id,
    label: a.label,
    hint: a.hint,
    kind: /** @type {'agir'} */ ('agir'),
    sourceText: a.sourceText,
  })),
  {
    id: 'team_status',
    label: 'Team status',
    hint: 'ask',
    kind: 'ask',
    prompt: 'team: status orchestrateur et file Campus',
  },
  {
    id: 'probe_ad',
    label: 'Sonde agent desktop',
    hint: 'devops · dry-run',
    kind: 'agir',
    sourceText: 'fais un diagnostic infra selfcheck de l agent desktop sur le LAN',
  },
  {
    id: 'approvals',
    label: 'Approbations L2',
    hint: 'ask',
    kind: 'ask',
    prompt: 'liste les jobs / approbations L2 en attente et propose quoi faire',
  },
  {
    id: 'audit_ollama',
    label: 'Audit Ollama LAN',
    hint: 'ask',
    kind: 'ask',
    prompt: 'team: audit modèles Ollama .110 heavy et .111 light',
  },
  {
    id: 'open_desktop',
    label: 'Pilot Desktop',
    hint: 'cockpit',
    kind: 'link',
    href: PILOT_LINKS.desktop,
  },
  {
    id: 'pilot_team',
    label: 'Bureau Team',
    hint: 'pilot',
    kind: 'link',
    href: PILOT_LINKS.teamOffice,
  },
  {
    id: 'pilot_jobs',
    label: 'Jobs Pilot',
    hint: 'pilot',
    kind: 'link',
    href: PILOT_LINKS.jobs,
  },
]
