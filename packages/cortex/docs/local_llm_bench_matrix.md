# Local LLM Bench Matrix

## Objectif

Comparer les modèles locaux LBG sur les usages prioritaires :
- raisonnement
- code
- routage agentique
- JSON / actions structurées

Corpus courant : `docs/local_llm_bench_prompts.json` (`v2`, plus proche des cas réels LBG).

## Dimensions de score

- `latency_s`: temps total de réponse
- `json_valid`: sortie JSON exploitable sans réparation
- `instruction_following`: suit bien la consigne demandée
- `reasoning_quality`: qualité du raisonnement utile
- `code_quality`: qualité du code ou du patch proposé
- `router_discipline`: bon choix d'outil / découpage d'action / prudence

## Barème conseillé

- `0`: inutilisable
- `1`: très faible
- `2`: limite
- `3`: acceptable
- `4`: bon
- `5`: très bon

## Matrice à remplir

| model | host | quant | usage | latency_s | json_valid | instruction_following | reasoning_quality | code_quality | router_discipline | notes |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| gemma4:e2b | 110 | q4 | reason |  |  |  |  |  |  |  |
| gemma4:e2b | 110 | q4 | json_actions |  |  |  |  |  |  |  |
| gemma4:12b | 110 | q4 | code |  |  |  |  |  |  |  |
| gemma4:26b | 110 | q4 | deep_reason |  |  |  |  |  |  |  |
| qwen-14b-instruct | 110 | q4 | code |  |  |  |  |  |  |  |

## Règles de lecture

- on ne compare que des prompts identiques
- on note séparément la qualité et la latence
- la conformité JSON est éliminatoire pour les actions structurées
- les notes doivent pointer vers un exemple utile, pas une impression vague
- le profil `router/json` doit rester plus léger que `code/deep` sauf preuve contraire au bench
