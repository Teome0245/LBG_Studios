/**
 * Pilotage Compagnon — actions de commande (comme un agent Cursor).
 * Barre visible = peu d’entrées ; le reste vit dans Ctrl+K (PILOTAGE_CATALOG).
 */

import { PILOT_LINKS } from '@/lib/pilotLinks'

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
  {
    id: 'probe_lan',
    label: 'Selfcheck LAN',
    hint: 'lecture seule',
    kind: 'agir',
    sourceText: 'fais un diagnostic infra selfcheck LAN',
  },
  {
    id: 'open_jobs',
    label: 'Jobs L2',
    hint: 'desktop',
    kind: 'agir',
    sourceText: 'ouvre firefox sur mon pc avec l url http://192.168.0.140:8080/#/jobs',
  },
  {
    id: 'team_status',
    label: 'Team status',
    hint: 'ask',
    kind: 'ask',
    prompt: 'team: status orchestrateur et file Campus',
  },
  {
    id: 'notepad',
    label: 'Notepad++',
    hint: 'desktop',
    kind: 'agir',
    sourceText: 'ouvre notepadpp sur mon pc',
  },
  {
    id: 'open_vghd',
    label: 'Ouvrir VGHD',
    hint: 'desktop',
    kind: 'agir',
    sourceText: 'ouvre vghd sur mon pc',
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

/** Barre sous l’input — max 4 + palette (évite le mur de boutons). */
/** @type {PilotageAction[]} */
export const PILOTAGE_BAR = PILOTAGE_CATALOG.filter((a) =>
  ['probe_lan', 'open_jobs', 'team_status', 'notepad'].includes(a.id)
)

/**
 * Suite de pilotage après un Agir (réel/dry-run) — impression « next moves ».
 * @param {{ capability?: string, ok?: boolean, mode?: string }} ctx
 * @returns {PilotageAction[]}
 */
export function nextPilotageAfterAgir(ctx = {}) {
  const cap = String(ctx.capability || '')
  const ok = ctx.ok !== false
  /** @type {PilotageAction[]} */
  const out = []

  if (cap.includes('devops') || cap.includes('probe')) {
    out.push({
      id: 'next_jobs',
      label: 'Voir Jobs L2',
      kind: 'agir',
      sourceText: 'ouvre firefox sur mon pc avec l url http://192.168.0.140:8080/#/jobs',
      hint: 'revue',
    })
    out.push({
      id: 'next_team',
      label: 'Status Team',
      kind: 'ask',
      prompt: 'team: status',
      hint: 'campus',
    })
  }
  if (cap.includes('desktop')) {
    out.push({
      id: 'next_desktop_ui',
      label: 'Ouvrir Pilot Desktop',
      kind: 'link',
      href: PILOT_LINKS.desktop,
      hint: 'cockpit',
    })
    if (ok) {
      out.push({
        id: 'next_note',
        label: 'Noter dans Notepad++',
        kind: 'agir',
        sourceText: 'ouvre notepadpp sur mon pc',
        hint: 'desktop',
      })
    }
  }
  if (!out.length) {
    out.push(
      {
        id: 'next_probe',
        label: 'Selfcheck LAN',
        kind: 'agir',
        sourceText: 'fais un diagnostic infra selfcheck LAN',
        hint: 'lecture',
      },
      {
        id: 'next_jobs2',
        label: 'Jobs',
        kind: 'link',
        href: PILOT_LINKS.jobs,
        hint: 'pilot',
      }
    )
  }
  return out.slice(0, 3)
}
