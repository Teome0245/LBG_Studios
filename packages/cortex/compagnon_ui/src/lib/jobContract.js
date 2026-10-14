/**
 * Contrat de job Agir — Tâche / Entrée / Sortie / Format (style Cowork).
 * Affiché sur ActionCard ; injecté dans le context Pilot (pas d’auto-exec).
 */

/**
 * @typedef {{
 *   objective: string,
 *   input: string,
 *   output: string,
 *   format: string,
 *   recipeId?: string,
 *   kind?: string,
 *   sourceText?: string,
 *   gates?: string[],
 * }} JobContract
 */

/**
 * @param {Partial<JobContract> & { objective: string }} fields
 * @returns {JobContract}
 */
export function buildJobContract(fields) {
  const objective = String(fields?.objective || '').trim()
  if (!objective) throw new Error('job_contract: objective requis')
  return {
    objective: objective.slice(0, 240),
    input: String(fields.input || 'contexte live studio / LAN').trim().slice(0, 240),
    output: String(fields.output || 'livrable actionnable').trim().slice(0, 240),
    format: String(fields.format || '5–10 lignes, faits mesurés').trim().slice(0, 160),
    recipeId: fields.recipeId ? String(fields.recipeId).slice(0, 48) : undefined,
    kind: fields.kind ? String(fields.kind).slice(0, 48) : undefined,
    sourceText: fields.sourceText ? String(fields.sourceText).trim().slice(0, 400) : undefined,
    gates: Array.isArray(fields.gates)
      ? fields.gates.map((g) => String(g).slice(0, 48)).filter(Boolean).slice(0, 6)
      : ['L2', 'dry-run→réel'],
  }
}

/**
 * Texte compact pour chat / ask (brief Cowork).
 * @param {JobContract|null|undefined} contract
 */
export function formatJobBrief(contract) {
  if (!contract || typeof contract !== 'object') return ''
  const lines = [
    `Tâche : ${contract.objective}`,
    `Entrée : ${contract.input}`,
    `Sortie : ${contract.output}`,
    `Format : ${contract.format}`,
  ]
  if (contract.gates?.length) {
    lines.push(`Gardes : ${contract.gates.join(' · ')}`)
  }
  return lines.join('\n')
}

/**
 * Context Pilot — le backend peut ignorer ; utile revue / logs.
 * @param {JobContract|null|undefined} contract
 * @returns {Record<string, unknown>}
 */
export function jobContractToPilotContext(contract) {
  if (!contract || typeof contract !== 'object') return {}
  return {
    job_contract: {
      objective: contract.objective,
      input: contract.input,
      output: contract.output,
      format: contract.format,
      recipe_id: contract.recipeId || null,
      kind: contract.kind || null,
      gates: contract.gates || [],
    },
  }
}

/**
 * Inférence soft depuis une demande libre (Agir free-text).
 * @param {string} text
 * @returns {JobContract}
 */
export function inferJobContractFromText(text) {
  const t = String(text || '').trim().replace(/\s+/g, ' ')
  const lower = t.toLowerCase()
  let input = 'demande utilisateur + état live si mesurable'
  let output = 'carte Agir (dry-run puis réel si OK)'
  let format = 'résumé court + outcome'
  let kind = 'free_text'
  const gates = ['L2', 'dry-run→réel']

  if (/selfcheck|diagnostic|sonde|inventaire|réseau|lan/.test(lower)) {
    input = 'sondes LAN / agent desktop (lecture seule)'
    output = 'diagnostic OK/KO + 3 points max'
    format = 'faits mesurés, pas d’invention'
    kind = 'probe'
    gates.push('lecture seule')
  } else if (/mail|imap|inbox/.test(lower)) {
    input = 'INBOX IMAP (aperçu)'
    output = 'liste messages récents'
    format = 'from · subject · date'
    kind = 'mail'
    gates.push('lecture seule')
  } else if (/brief|matin/.test(lower)) {
    input = 'Self / proactive / infra'
    output = 'brief du matin'
    format = '5–10 lignes'
    kind = 'morning_brief'
    gates.push('lecture seule')
  } else if (/ouvre|open|lance|démarre/.test(lower)) {
    input = 'poste cible (.10 / .143) + allowlist'
    output = 'app ouverte ou URL'
    format = 'outcome + host'
    kind = 'desktop'
  } else if (/mémoire|reten/.test(lower)) {
    input = 'mémoire agent Self'
    output = 'ce qui est retenu'
    format = 'liste courte'
    kind = 'memory'
    gates.push('lecture seule')
  }

  return buildJobContract({
    objective: t.slice(0, 200) || 'Action Compagnon',
    input,
    output,
    format,
    kind,
    sourceText: t,
    gates,
  })
}
