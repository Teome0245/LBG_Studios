/**
 * Pilotage Compagnon — actions de commande (comme un agent Cursor),
 * pas de décoration : chaque entrée mène à Agir, ask, ou Pilot.
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

/** @type {PilotageAction[]} */
export const PILOTAGE_BAR = [
  {
    id: 'probe_ad',
    label: 'Sonde AD',
    hint: 'devops · dry-run',
    kind: 'agir',
    sourceText: 'fais un diagnostic infra selfcheck de l agent AD sur le LAN',
  },
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
    id: 'open_desktop',
    label: 'Pilot Desktop',
    hint: 'cockpit',
    kind: 'link',
    href: PILOT_LINKS.desktop,
  },
  {
    id: 'team_status',
    label: 'Team status',
    hint: 'ask',
    kind: 'ask',
    prompt: 'team: status orchestrateur et file Campus',
  },
  {
    id: 'approvals',
    label: 'Approbations L2',
    hint: 'ask',
    kind: 'ask',
    prompt: 'liste les jobs / approbations L2 en attente et propose quoi faire',
  },
  {
    id: 'open_vghd',
    label: 'Ouvrir VGHD',
    hint: 'desktop',
    kind: 'agir',
    sourceText: 'ouvre vghd sur mon pc',
  },
  {
    id: 'notepad',
    label: 'Notepad++',
    hint: 'desktop',
    kind: 'agir',
    sourceText: 'ouvre notepadpp sur mon pc',
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
  return out.slice(0, 4)
}
