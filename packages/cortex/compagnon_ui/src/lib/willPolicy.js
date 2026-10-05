/**
 * Politique envies Self (pending_will) — intents par kind + auto-validate L1.
 * Jamais d'auto-Réel desktop / L2.
 */

/**
 * @param {Record<string, unknown>|null|undefined} will
 */
export function isSmokeWill(will) {
  const id = String(will?.id || '').toLowerCase()
  const title = String(will?.title || '').toLowerCase()
  if (!id && !title) return false
  return id.includes('smoke') || title.includes('smoke')
}

/**
 * Opt-in auto-validate. Défaut ON ; localStorage `lbg_will_auto_validate=0` pour couper.
 */
export function willAutoValidateEnabled() {
  try {
    const v = String(localStorage.getItem('lbg_will_auto_validate') || '').trim().toLowerCase()
    if (v === '0' || v === 'false' || v === 'off' || v === 'no') return false
    if (v === '1' || v === 'true' || v === 'on' || v === 'yes') return true
  } catch {
    /* ignore */
  }
  return true
}

/**
 * @param {Record<string, unknown>|null|undefined} will
 * @returns {'brief'|'team_l1'|null}
 */
export function autoValidateMode(will) {
  if (!will || typeof will !== 'object') return null
  const kind = String(will.kind || '').toLowerCase()
  if (kind === 'morning_brief') return 'brief'
  if (isSmokeWill(will)) return 'team_l1'
  return null
}

/**
 * Intents toast groundés sur le kind de l'envie.
 * @param {Record<string, unknown>} will
 */
export function intentsForWill(will) {
  const title = String(will?.title || will?.summary || will?.kind || 'envie interne').slice(0, 120)
  const kind = String(will?.kind || 'evolution').toLowerCase()
  const willId = String(will?.id || '').slice(0, 80)

  if (kind === 'morning_brief') {
    return [
      {
        id: 'agir_brief',
        label: 'Brief du matin',
        sourceText: 'fais mon brief du matin',
        hint: 'lecture seule',
      },
      {
        id: 'team_l1_will',
        label: 'Team L1',
        sourceText: `team: ${title}`,
        hint: 'qa · lecture seule',
        teamSpawn: true,
        teamObjective:
          'Compiler un brief studio Self / proactive / infra (5–10 lignes, lecture seule).',
      },
    ]
  }

  if (isSmokeWill(will) || kind === 'evolution') {
    const intents = [
      {
        id: 'team_l1_evo',
        label: 'Team L1',
        sourceText: `team: ${title}`,
        hint: 'qa · lecture seule',
        teamSpawn: true,
        teamObjective: isSmokeWill(will)
          ? 'Smoke maturité studio : healthz Compagnon + GET Self status (lecture seule). Rapporter OK/KO en 5 lignes.'
          : `Explorer cette idée d'évolution Compagnon (5 lignes, pas de merge) : ${title}`,
      },
      {
        id: 'discuss_evo',
        label: 'En parler',
        sourceText: `parle-moi de cette idée d'évolution : ${title}`,
        hint: 'discuss',
      },
    ]
    void willId
    return intents
  }

  return [
    {
      id: 'team_l1_will',
      label: 'Team L1',
      sourceText: `team: ${title}`,
      hint: 'crée une tâche qa lecture seule',
      teamSpawn: true,
      teamObjective: `Traiter l'envie studio « ${title} » en lecture seule (5 lignes).`,
    },
    {
      id: 'open_team',
      label: 'Voir Pilot Team',
      sourceText: 'ouvre http://192.168.0.140:8080/#/team dans le navigateur',
      hint: 'navigateur',
    },
  ]
}

/**
 * Consomme / ignore une envie via proxy Pilot.
 * @param {string} willId
 * @param {'complete'|'dismiss'} action
 * @param {string} [reason]
 */
export async function consumePendingWill(willId, action = 'complete', reason = 'done') {
  const id = String(willId || '').trim()
  if (!id) return { ok: false, error: 'will_id vide' }
  const path =
    action === 'dismiss'
      ? '/api/pilot/orchestrator/self/will/dismiss'
      : '/api/pilot/orchestrator/self/will/complete'
  try {
    const res = await fetch(path, {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify({ will_id: id, reason: String(reason || action).slice(0, 48) }),
    })
    const json = await res.json().catch(() => ({}))
    if (!res.ok || json?.ok === false) {
      return { ok: false, error: json?.error || `HTTP ${res.status}` }
    }
    return { ok: true, state: json?.state || null }
  } catch (e) {
    return { ok: false, error: e?.message || String(e) }
  }
}
