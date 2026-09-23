/**
 * Self-State (Agency B) — présence studio pour Compagnon.
 * Source : GET /api/pilot/orchestrator/self/status (slim, ensure_goals=0).
 */

/**
 * @typedef {{
 *   enabled?: boolean,
 *   ok?: boolean,
 *   state?: {
 *     drives?: Record<string, number>,
 *     intent?: { primary?: string, narrative?: string, horizon?: string },
 *     pending_will?: Array<Record<string, unknown>>,
 *     goals?: Array<Record<string, unknown>>,
 *     goals_active_count?: number,
 *     goals_total?: number,
 *     last_tick?: { kind?: string, summary?: string, ok?: boolean },
 *     identity?: { display_name?: string, mode?: string },
 *   },
 * }} SelfStatus
 */

/**
 * @returns {Promise<SelfStatus|null>}
 */
export async function fetchSelfStatus() {
  try {
    const res = await fetch('/api/pilot/orchestrator/self/status?ensure_goals=0', {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    })
    if (!res.ok) return null
    const json = await res.json()
    if (!json || json.ok === false) return null
    return json
  } catch {
    return null
  }
}

/**
 * Ligne compacte pour UI (pas de jargon ops).
 * @param {SelfStatus|null|undefined} status
 */
export function formatSelfLine(status) {
  if (!status?.enabled && !status?.state) return ''
  const st = status.state || {}
  const d = st.drives || {}
  const intent = st.intent || {}
  const name = st.identity?.display_name || 'Cortex'
  const cur = Number(d.curiosity)
  const ten = Number(d.tension)
  const soc = Number(d.social_hunger)
  const parts = [name]
  if (intent.primary) parts.push(String(intent.primary))
  const gauges = []
  if (Number.isFinite(cur)) gauges.push(`curiosité ${Math.round(cur * 100)}%`)
  if (Number.isFinite(ten)) gauges.push(`tension ${Math.round(ten * 100)}%`)
  if (Number.isFinite(soc) && soc >= 0.5) gauges.push(`social ${Math.round(soc * 100)}%`)
  if (gauges.length) parts.push(gauges.join(' · '))
  const will = Array.isArray(st.pending_will) ? st.pending_will.length : 0
  if (will > 0) parts.push(`${will} envie${will > 1 ? 's' : ''}`)
  const gActive = Number(st.goals_active_count)
  if (Number.isFinite(gActive) && gActive > 0) parts.push(`${gActive} but${gActive > 1 ? 's' : ''}`)
  return parts.join(' — ')
}

/**
 * Offre d'initiative depuis Self (si proactive n'offre rien de prioritaire).
 * @param {SelfStatus|null|undefined} status
 * @returns {{ offer: boolean, id?: string, message?: string, kind?: string, intents?: object[], reason?: string }}
 */
export function offerFromSelf(status) {
  if (!status?.enabled) return { offer: false, reason: 'self_disabled' }
  const st = status.state || {}
  const will = Array.isArray(st.pending_will) ? st.pending_will : []
  if (will.length) {
    const w = will[0] || {}
    const title = String(w.title || w.summary || w.kind || 'envie interne').slice(0, 120)
    const id = `self:will:${String(w.id || title).slice(0, 40)}`
    return {
      offer: true,
      id,
      kind: 'self_will',
      message: `Je sens une envie studio : « ${title} ». On en parle, Agir, ou on passe à la Team L1 ?`,
      intents: [
        {
          id: 'team_l1_will',
          label: 'Team L1',
          sourceText: `team: ${title}`,
          hint: 'crée une tâche qa lecture seule',
          teamSpawn: true,
        },
        {
          id: 'open_team',
          label: 'Voir Pilot Team',
          sourceText: 'ouvre http://192.168.0.140:8080/#/team dans le navigateur',
          hint: 'navigateur',
        },
      ],
    }
  }

  const d = st.drives || {}
  const cur = Number(d.curiosity)
  const ten = Number(d.tension)
  const soc = Number(d.social_hunger)

  if (Number.isFinite(cur) && cur >= 0.85) {
    return {
      offer: true,
      id: 'self:curiosity',
      kind: 'self_drive',
      message:
        'Curiosité haute — je propose une revue Team L1 (smoke lecture seule) ou d’ouvrir VS Code sur Omarchy.',
      intents: [
        {
          id: 'team_l1_smoke',
          label: 'Team L1 smoke',
          sourceText: 'team smoke self companion',
          hint: 'qa · lecture seule',
          teamSpawn: true,
          teamObjective:
            'Smoke maturité studio : healthz Compagnon :5174 + GET Self status (lecture seule). Rapporter OK/KO en 5 lignes.',
        },
        {
          id: 'omarchy_vscode',
          label: 'VS Code .143',
          sourceText: 'ouvre code sur omarchy',
          hint: 'Cline / éditeur',
        },
      ],
    }
  }

  if (Number.isFinite(soc) && soc >= 0.85) {
    return {
      offer: true,
      id: 'self:social',
      kind: 'self_drive',
      message: 'Faim sociale haute — un passage Team ou un check mail léger ?',
      intents: [
        {
          id: 'team_l1_social',
          label: 'Team L1',
          sourceText: 'team check présence',
          hint: 'pm · synthèse courte',
          teamSpawn: true,
          teamRole: 'pm',
          teamObjective:
            'Synthèse présence studio (Self + proactive) en 5 lignes pour le Compagnon — pas d’action destructive.',
        },
        {
          id: 'mail',
          label: 'Mails récents',
          sourceText: 'regarde mes mails récents',
          hint: 'IMAP',
        },
      ],
    }
  }

  if (Number.isFinite(ten) && ten >= 0.75) {
    return {
      offer: true,
      id: 'self:tension',
      kind: 'self_drive',
      message: 'Tension Self élevée — je propose Pilot Jobs ou une tâche Team L1 de revue.',
      intents: [
        {
          id: 'jobs',
          label: 'Pilot Jobs',
          sourceText: 'ouvre http://192.168.0.140:8080/#/jobs dans le navigateur',
          hint: 'L2',
        },
        {
          id: 'team_l1_tension',
          label: 'Team L1',
          sourceText: 'team revue tension',
          hint: 'qa',
          teamSpawn: true,
          teamObjective:
            'Diagnostiquer la tension Self/proactive (lecture seule) et proposer 1 action L1 sûre.',
        },
      ],
    }
  }

  return { offer: false, reason: 'no_self_signal' }
}
