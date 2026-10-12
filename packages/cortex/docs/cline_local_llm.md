# Cline → matrice LLM locale LBG (110 / 111)

**Date** : 2026-09-23  
**Statut** : guide éditeur (BYOK) — aligné sur `local_llm_route_matrix.md` (≤12B abliterated)  
**Source exécutable** : `orchestrator/team/reason_llm.py` → `reason_route_matrix()`  
**Snippets** : `docs/cline/`

---

## Mapping recommandé (Plan / Act)

| Mode Cline | Rôle matrice | Hôte | Base URL | Model ID |
|------------|--------------|------|----------|----------|
| **Act** (défaut code) | `code` / `pm` / `uncensored` | **110** heavy | `http://192.168.0.110:11434` | `huihui_ai/gemma-4-abliterated:12b-qat` (canon unique, plus d'alias `:12b`) |
| **Plan** (plans utiles) | raisonnement PM | **110** heavy | `http://192.168.0.110:11434` | `huihui_ai/qwen3.5-abliterated:9b` |
| Plan alt. (même qualité qu’Act) | `code` / `dialogue` | **110** | idem | `huihui_ai/gemma-4-abliterated:12b` |
| Plan triage (outline rapide) | `fast` / `router` | **111** light | `http://192.168.0.111:11434` | `0.8B` ou `2B` |
| Forge / failover | `forge` / `default` | **110** | `http://192.168.0.110:11434` | `huihui_ai/gemma-4-abliterated:e2b` |

> Le **2B n’est plus le défaut Plan** : trop faible pour archi / multi-fichiers. Snippet : `docs/cline/providers.plan-110-9b.json`.

**Anti-piège** : **`.143` = VM Omarchy éditeur** (VS Code + Cline + Continue + Claude Code) — **pas** le serveur Ollama.  
Ces trois extensions sont des **composants distincts** ; elles pointent toutes vers Ollama **`http://192.168.0.110:11434`** (heavy) ou **`.111:11434`** (triage) — **jamais** `http://192.168.0.143:11434`.

Voir `local_llm_route_matrix.md` pour les équivalents HF Uncensored.

---

## Config UI Cline (rapide)

### Act — code (110)

| Champ | Valeur |
|-------|--------|
| API Provider | `Ollama` |
| Base URL | `http://192.168.0.110:11434` |
| Model | `huihui_ai/gemma-4-abliterated:12b` |

### Plan — qualité (110)

| Champ | Valeur |
|-------|--------|
| API Provider | `Ollama` (ou OpenAI Compatible → `/v1`) |
| Base URL | `http://192.168.0.110:11434` |
| Model | `huihui_ai/qwen3.5-abliterated:9b` |

Features → **Use Compact Prompt** ON · **Plan/Act separate models** ON.

Profils JSON : `docs/cline/providers.*.json` + `SMOKE.md`.
