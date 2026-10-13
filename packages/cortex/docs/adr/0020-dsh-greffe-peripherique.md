# ADR 0020 — DeepSeek Harness en greffe périphérique

**Statut** : **clos par ADR 0028** (NO-GO pour dsh_headless dans Team / Cortex ; poste .10 uniquement)  
**Date** : 2026-08-24 (clos 2026-10-13)

## Contexte

[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (`dsh`) est un harness agentique
open-source (MIT, 189 k★) basé sur **Cordis** — « everything is a plugin ».
Il fournit boucle agent/tool, session log, shell/FS, subagents, skills et UI web.

Il supporte Ollama en provider local (API OpenAI-compatible `host:11434/v1`)
et dispose d'une intégration first-party (`ollama launch dsh`).

Le Studio LBG dispose déjà d'un **OS agentique LAN** :
orchestrateur 140, Team SQLite, Lyra Conductor, `reason_llm` (matrice 110/111),
Pilot UI, rôles métier, garde-fous L1/L2, Cursor Cloud Agent (ADR 0019, `plan_cursor_cloud_agent.md`).

La politique produit (`lbg_agentic_os.md` § 6.1) est claire :
**greffer des capacités externes en périphérie — ne pas substituer le bus interne.**

## Décision

1. **Ne pas remplacer** Cortex / Team / Pilot / Conductor par DSH.
2. **Autoriser l'usage sur le poste dev (.10)** comme outil coding exploratoire,
   pointé vers Ollama **110** (`huihui_ai/Qwen3.8-abliterated:27b`, `gemma4:e2b`).
3. **Évaluer** une capability Team `dsh_headless` (L2, allowlist repos) sur le modèle
   Cursor Cloud Agent — si le test .10 s'avère utile.
4. **S'inspirer** des patterns Cordis (capability seams, session log durable, waterfall events)
   pour l'évolution de l'orchestrateur Python, sans dépendance npm sur 140.

## Config poste .10 — spike

```bash
# Option A : intégration Ollama native
ollama launch dsh --model huihui_ai/Qwen3.8-abliterated:27b

# Option B : provider custom dans DSH settings
#   Provider ID : ollama-lan
#   API Protocol : openai-completions
#   Base URL : http://192.168.0.110:11434/v1
#   Models : huihui_ai/Qwen3.8-abliterated:27b, gemma4:e2b
```

Pas de clé API requise (Ollama local).
DSH reste sur .10, pas de déploiement sur 140/141.

## Capability Team `dsh_headless` (si P2 validé)

```
Pilot / Lyra / Team (dev_game | dev_infra)
  → intent code_patch | refactor
  → capability dsh_headless (OFF par défaut, LBG_DSH_AGENT_ENABLED=0)
  → dsh --profile headless "task" (110:11434)
  → rapport stdout → Team trace + SQLite
```

| Garde-fou | Valeur |
|-----------|--------|
| Opt-in | `LBG_DSH_AGENT_ENABLED=0` par défaut |
| Approbation | L2 + `LBG_TEAM_APPROVAL_TOKEN` |
| Repos | `LBG_DSH_AGENT_REPOS` (allowlist CSV) |
| Timeout | `LBG_DSH_AGENT_TIMEOUT_S=300` |
| Audit | Trace JSONL `agents.team.trace` |

## Alternatives rejetées

| Alternative | Raison du rejet |
|-------------|-----------------|
| DSH comme orchestrateur principal sur 140 | Perte intégrations Core3/Godot/smokes LAN, nouvelle stack Node.js ops, preview instable |
| UI DSH web en remplacement de Pilot | Doublon fonctionnel, perte du fil Team/présence/campus |
| Import Cordis en dépendance Python | Cordis = TypeScript ; pas de binding Python officiel |
| Ignorer DSH entièrement | Harness le plus populaire du moment, patterns utiles, support Ollama natif |

## Risques

| Risque | Mitigation |
|--------|------------|
| Breaking changes DSH (developer preview) | Spike isolé sur .10, pas d'infra critique |
| Doublon Cursor Cloud Agent vs DSH headless | Un seul actif à la fois par rôle ; décision après test |
| Dérive scope (DSH « grossit » sur le LAN) | Pas de Node.js sur 140 ; L2 + allowlist obligatoires |

## Conséquences

- Aucun changement sur 140 / orchestrateur / Pilot.
- Spike `ollama launch dsh` documenté sur .10 (résultat attendu dans `docs/`).
- Si P2 validé : nouveau module `orchestrator/integrations/dsh_agent.py` + workflow Team,
  sur le modèle de `cursor_agent.py` / `cursor_agent_workflow.py`.

## Références

- `docs/lbg_agentic_os.md` § 6.1 (greffe vs substitution)
- `docs/plan_cursor_cloud_agent.md` (pattern capability externe L2)
- `docs/adr/0014-equipe-virtuelle-orchestrateur.md` (rôles + garde-fous)
- `docs/adr/0015-tri-backend-hybride.md` (matrice LLM)
- `docs/local_llm_route_matrix.md`
- https://github.com/deepseek-ai/deepseek-harness
