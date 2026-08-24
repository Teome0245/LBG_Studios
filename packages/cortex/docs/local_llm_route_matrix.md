# Matrice de routage LLM locale (source de vérité)

**Date** : 2026-08-16  
**Statut** : canonique — inventaire validé 110 / 111  
**Code** : `orchestrator/team/reason_llm.py` → `reason_route_matrix()`  
**Audit** : `orchestrator/team/ollama_audit.py` (Atlas / admin_infra)

---

## Principe

Une seule matrice pour **Cursor**, **Team (Atlas, Thémis, …)** et **Pilot** :

1. Le code (`reason_route_matrix`) est la source exécutable.
2. Ce document est la source lisible humaine / agents.
3. L’env prod (`/etc/lbg-ia-mmo.env`) doit coller à la matrice.
4. Atlas alerte si un modèle configuré est **absent** sur l’hôte attendu.

**Ne pas réintroduire `gemma3:4b` sur 111** — écarté après validation (moins adapté que le duo Fast/Clean).

**Heavy code/PM/dialogue** : `qwen3.8:27b` (bench août 2026 sur `.110`, `think: false`) remplace `gemma4:26b`.

---

## Inventaire validé

| Hôte | Rôle | Modèles installés |
|------|------|-------------------|
| **110** heavy | code / PM / forge / dialogue | `gemma4:e2b`, `qwen3.8:27b` (+ `gemma4:26b` legacy optionnel) |
| **111** light (NUC) | délestage latence | **`qwen2.5:3b`** (Clean), **`llama3.2:3b`** (Fast) |

## Profils REASON

| Profil | Env | Défaut | Hôte |
|--------|-----|--------|------|
| `router` / Clean | `LBG_REASON_MODEL_ROUTER` | `qwen2.5:3b` | 111 |
| `json` / Clean | `LBG_REASON_MODEL_JSON` | `qwen2.5:3b` | 111 |
| `fast` | `LBG_REASON_MODEL_FAST` | `llama3.2:3b` | 111 |
| `forge` | `LBG_REASON_MODEL_FORGE` | `gemma4:e2b` | 110 |
| `default` | `LBG_REASON_LOCAL_MODEL` | `gemma4:e2b` | 110 |
| `code` | `LBG_REASON_MODEL_CODE` | `qwen3.8:27b` | 110 |
| `pm` | `LBG_REASON_MODEL_PM` | `qwen3.8:27b` | 110 |
| `dialogue` | `LBG_REASON_MODEL_DIALOGUE` | `qwen3.8:27b` | 110 |

Failover light → heavy : `LBG_REASON_LIGHT_FAILOVER_HEAVY=1` + `LBG_REASON_LIGHT_FAILOVER_MODEL=gemma4:e2b`.

Ollama thinking (Qwen) : `LBG_REASON_OLLAMA_THINK=false` (défaut) et `LBG_DIALOGUE_LLM_OLLAMA_THINK=false`.

---

## Diffusion

| Canal | Mécanisme |
|-------|-----------|
| Cursor | règle `.cursor/rules/local-llm-route-matrix.mdc` (`alwaysApply`) si présente |
| Team / Atlas | run `admin_infra` → champ `route_matrix` + mémoire `team/atlas` |
| Env exemple | `infra/secrets/lbg.env.example` |
| Audit LAN | `bash infra/scripts/audit_ollama_110_lan.sh` |
| Dialogue fast Groq | Atlas `admin_infra` → `dialogue_fast_groq` ; sonde `/v1/llm/probe` (priorité `LBG_DIALOGUE_FAST_MODEL`) |

Toute évolution de modèles **doit** mettre à jour : `reason_route_matrix()`, ce fichier, `lbg.env.example`, **`LBG_DIALOGUE_FAST_MODEL`** (+ `GROQ_MODEL_*` si Groq), et l’env prod 140 via `push_secrets_vm.sh`.
