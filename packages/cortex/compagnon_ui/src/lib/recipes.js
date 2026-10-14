/**
 * 10 recettes Compagnon — jobs prêts à lancer (empty state + Ctrl+K).
 * Chaque recette porte un contrat Tâche/Entrée/Sortie/Format.
 */

import { buildJobContract, formatJobBrief } from './jobContract.js'

/**
 * @typedef {'agir'|'ask'} RecipeKind
 * @typedef {{
 *   id: string,
 *   label: string,
 *   hint: string,
 *   kind: RecipeKind,
 *   sourceText?: string,
 *   prompt?: string,
 *   contract: import('./jobContract.js').JobContract,
 *   emptyState?: boolean,
 * }} CompagnonRecipe
 */

/** @type {Omit<CompagnonRecipe, 'contract'> & { contract: Parameters<typeof buildJobContract>[0] }[]} */
const RAW = [
  {
    id: 'recipe_selfcheck',
    label: 'Selfcheck LAN',
    hint: 'ops · lecture seule',
    kind: 'agir',
    sourceText: 'fais un diagnostic infra selfcheck LAN',
    emptyState: true,
    contract: {
      objective: 'Diagnostiquer l’infra LAN (selfcheck)',
      input: 'sondes devops / agent desktop (lecture seule)',
      output: 'diagnostic OK/KO + points bloquants',
      format: '3–6 lignes, faits mesurés',
      kind: 'selfcheck',
      gates: ['L2', 'dry-run→réel', 'lecture seule'],
    },
  },
  {
    id: 'recipe_morning',
    label: 'Brief du matin',
    hint: 'Self · infra',
    kind: 'agir',
    sourceText: 'fais mon brief du matin',
    emptyState: true,
    contract: {
      objective: 'Compiler le brief du matin studio',
      input: 'Self status + proactive + infra',
      output: 'brief actionnable',
      format: '5–10 lignes',
      kind: 'morning_brief',
      gates: ['L2', 'lecture seule'],
    },
  },
  {
    id: 'recipe_mail',
    label: 'Mails récents',
    hint: 'IMAP preview',
    kind: 'agir',
    sourceText: 'regarde mes mails récents',
    emptyState: true,
    contract: {
      objective: 'Aperçu INBOX (mails récents)',
      input: 'IMAP preview',
      output: 'liste from · subject · date',
      format: 'max 5 messages',
      kind: 'mail_imap_preview',
      gates: ['L2', 'lecture seule'],
    },
  },
  {
    id: 'recipe_jobs',
    label: 'Jobs L2 en attente',
    hint: 'ask · Pilot',
    kind: 'ask',
    emptyState: true,
    contract: {
      objective: 'Lister les jobs / approbations L2 en attente',
      input: 'état Pilot Jobs (si mesurable) + mémoire récente',
      output: 'liste priorisée + 1 proposition Agir',
      format: '5 lignes max',
      kind: 'jobs_l2',
      gates: ['pas d’auto-exec'],
    },
  },
  {
    id: 'recipe_memory',
    label: 'Ma mémoire',
    hint: 'Self',
    kind: 'agir',
    sourceText: 'montre ce que tu retiens (mémoire agent)',
    emptyState: true,
    contract: {
      objective: 'Restituer la mémoire agent Self',
      input: 'memory_recall',
      output: 'ce qui est retenu + seed éventuelle',
      format: 'liste courte',
      kind: 'memory_recall',
      gates: ['L2', 'lecture seule'],
    },
  },
  {
    id: 'recipe_world',
    label: 'Pulse Lost Heaven',
    hint: 'monde · relations',
    kind: 'ask',
    emptyState: true,
    contract: {
      objective: 'Résumer le pulse monde + liens relationnels Teome',
      input: 'world stream + relation memory (si dispo)',
      output: 'faits marquants + liens utiles',
      format: '6 lignes, zéro invention',
      kind: 'world_pulse',
      gates: ['faits seulement'],
    },
  },
  {
    id: 'recipe_deploy',
    label: 'Smoke Compagnon',
    hint: 'ask · Team',
    kind: 'ask',
    emptyState: false,
    contract: {
      objective: 'Smoke Compagnon : healthz :5174 + Self status',
      input: 'endpoints live LAN',
      output: 'rapport OK/KO',
      format: '5 lignes, team: si besoin',
      kind: 'smoke',
      gates: ['lecture seule', 'pas de merge'],
    },
  },
  {
    id: 'recipe_vghd',
    label: 'Ouvrir VGHD',
    hint: 'desktop .10',
    kind: 'agir',
    sourceText: 'ouvre vghd sur mon pc',
    emptyState: false,
    contract: {
      objective: 'Ouvrir VGHD sur le poste .10',
      input: 'agent desktop .10 allowlist',
      output: 'app ouverte',
      format: 'outcome + host',
      kind: 'open_app',
      gates: ['L2', 'dry-run→réel'],
    },
  },
  {
    id: 'recipe_omarchy',
    label: 'Smoke OpenCode (.143)',
    hint: 'CLI · dry-run',
    kind: 'agir',
    sourceText: 'lance opencode sur omarchy pour un smoke dry-run du monorepo',
    emptyState: false,
    contract: {
      objective: 'Smoke CLI OpenCode sur Omarchy (.143)',
      input: 'worker .143 + monorepo',
      output: 'dry-run CLI outcome',
      format: 'outcome + logs courts',
      kind: 'run_cli_agent',
      gates: ['L2', 'dry-run'],
    },
  },
  {
    id: 'recipe_studio',
    label: 'Piste conception',
    hint: 'studio · 5 lignes',
    kind: 'ask',
    emptyState: true,
    contract: {
      objective: 'Proposer 1 micro-amélioration Compagnon (copy ou toast)',
      input: 'FOCUS_COMPAGNON + état empty-state actuel',
      output: '1 piste concrète + critère de done',
      format: '5 lignes, pas de refonte',
      kind: 'studio_craft',
      gates: ['pas de merge', 'validation humaine'],
    },
  },
]

/** @type {CompagnonRecipe[]} */
export const COMPAGNON_RECIPES = RAW.map((r) => {
  const contract = buildJobContract({
    ...r.contract,
    recipeId: r.id,
    sourceText: r.sourceText,
  })
  const brief = formatJobBrief(contract)
  return {
    id: r.id,
    label: r.label,
    hint: r.hint,
    kind: r.kind,
    sourceText: r.sourceText,
    prompt:
      r.kind === 'ask'
        ? `${brief}\n\nExécute ce brief (faits mesurés, pas d’invention).`
        : undefined,
    contract,
    emptyState: r.emptyState !== false,
  }
})

/** Recettes visibles sur empty state (max ~7). */
export function recipesForEmptyState(limit = 7) {
  return COMPAGNON_RECIPES.filter((r) => r.emptyState).slice(0, Math.max(1, limit))
}

/**
 * @param {string} id
 * @returns {CompagnonRecipe|null}
 */
export function getRecipe(id) {
  const key = String(id || '').trim()
  return COMPAGNON_RECIPES.find((r) => r.id === key) || null
}

/** Entrées Ctrl+K (agir | ask). */
export function recipesAsPilotageActions() {
  return COMPAGNON_RECIPES.map((r) => ({
    id: r.id,
    label: `Recette · ${r.label}`,
    hint: r.hint,
    kind: r.kind,
    sourceText: r.sourceText,
    prompt: r.prompt,
    jobContract: r.contract,
  }))
}

/** Event bus empty state → ChatInput (ask). */
export const RECIPE_ASK_EVENT = 'lbg:compagnon-recipe-ask'

/**
 * @param {CompagnonRecipe} recipe
 */
export function dispatchRecipeAsk(recipe) {
  if (typeof window === 'undefined' || !recipe?.prompt) return
  window.dispatchEvent(
    new CustomEvent(RECIPE_ASK_EVENT, {
      detail: { prompt: recipe.prompt, recipeId: recipe.id, label: recipe.label },
    }),
  )
}
