/**
 * Pilotage Compagnon — actions de commande (comme un agent Cursor).
 * Barre visible = peu d’entrées ; le reste vit dans Ctrl+K (PILOTAGE_CATALOG).
 */

import { PILOT_LINKS } from '@/lib/pilotLinks'
import { USEFUL_AGIR_ACTIONS } from '@/lib/usefulAgirActions'
import { recipesAsPilotageActions } from '@/lib/recipes'

/**
 * @typedef {{
 *   id: string,
 *   label: string,
 *   hint?: string,
 *   kind: 'agir'|'ask'|'link'|'breathe'|'new_thread',
 *   sourceText?: string,
 *   prompt?: string,
 *   href?: string,
 *   jobContract?: import('./jobContract.js').JobContract,
 * }} PilotageAction
 */

/** Catalogue complet — palette Ctrl+K uniquement. */
/** @type {PilotageAction[]} */
export const PILOTAGE_CATALOG = [
  ...recipesAsPilotageActions(),
  ...USEFUL_AGIR_ACTIONS.map((a) => ({
    id: a.id,
    label: a.label,
    hint: a.hint,
    kind: /** @type {'agir'} */ ('agir'),
    sourceText: a.sourceText,
  })),
  {
    id: 'breathe',
    label: 'Respire',
    hint: 'compacte le fil · garde mandat',
    kind: 'breathe',
  },
  {
    id: 'new_thread',
    label: 'Nouveau fil',
    hint: 'conversation fraîche',
    kind: 'new_thread',
  },
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
