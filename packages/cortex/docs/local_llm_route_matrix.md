# Matrice de routage LLM locale (source de vérité)

**Date** : 2026-09-20  
**Statut** : canonique — inventaire ≤12B abliterated (filtre [HF Ollama trending ≤12B](https://huggingface.co/models?num_parameters=min:0,max:12B&apps=ollama&sort=trending))  
**Code** : `orchestrator/team/reason_llm.py` → `reason_route_matrix()`  
**Audit** : `orchestrator/team/ollama_audit.py` (Atlas / admin_infra)  
**Cline** : `docs/cline_local_llm.md`

---

## Principe

Une seule matrice pour **Cursor**, **Cline**, **Team (Atlas, Thémis, …)** et **Pilot** :

1. Le code (`reason_route_matrix`) est la source exécutable.
2. Ce document est la source lisible humaine / agents.
3. L’env prod (`/etc/lbg-ia-mmo.env`) doit coller à la matrice.
4. Atlas alerte si un modèle configuré est **absent** sur l’hôte attendu.

**Ne pas réintroduire `gemma3:4b` sur 111.**

**Heavy code/PM/dialogue** : `huihui_ai/gemma-4-abliterated:12b` (plafond ≤12B, qualité code).  
Garde-fous présentation = maturité **A/B/C** (prompts).  
Legacy disque OK : `huihui_ai/qwen3.5-abliterated:9b`, `huihui_ai/Qwen3.8-abliterated:27b`, `gemma4:e2b`, `qwen2.5:3b`, `llama3.2:3b` — **plus routés**.

Tags **Ollama natifs `huihui_ai/*`** préférés aux pulls `hf.co/HauhauCS/...` (erreurs load Qwen3.5 signalées sur HF).

---

## Remplacement 2026-09-20 (≤12B Uncensored)

| Avant | Après (Ollama) | Équiv. HF trending |
|-------|----------------|--------------------|
| `huihui_ai/Qwen3.8-abliterated:27b` → `:9b` | `huihui_ai/gemma-4-abliterated:12b` | [HauhauCS/Gemma4-12B-QAT-Uncensored…](https://huggingface.co/HauhauCS/Gemma4-12B-QAT-Uncensored-HauhauCS-Balanced) |
| `gemma4:e2b` | `huihui_ai/gemma-4-abliterated:e2b` | [HauhauCS/Gemma-4-E2B-Uncensored…](https://huggingface.co/HauhauCS/Gemma-4-E2B-Uncensored-HauhauCS-Aggressive) |
| `qwen2.5:3b` | `huihui_ai/qwen3.5-abliterated:2B` | HauhauCS/Qwen3.5-2B-Uncensored / MiniCPM5-2B abliterated |
| `llama3.2:3b` | `huihui_ai/qwen3.5-abliterated:0.8B` | petit fast uncensored (pas d’équivalent Llama3.2 fiable en lib Ollama) |

Pull :

```bash
# .110
ollama pull huihui_ai/gemma-4-abliterated:12b
ollama pull huihui_ai/gemma-4-abliterated:e2b
# .111
ollama pull huihui_ai/qwen3.5-abliterated:2B
ollama pull huihui_ai/qwen3.5-abliterated:0.8B
```

---

## Inventaire validé

| Hôte | Rôle | Modèles routés |
|------|------|----------------|
| **110** heavy | code / PM / forge / dialogue — **CPU only** (pas de GPU) | `huihui_ai/gemma-4-abliterated:12b`, `huihui_ai/gemma-4-abliterated:e2b` (+ `qwen3.5-abliterated:9b` disque) |
| **111** light (NUC) | délestage latence / **Compagnon LAB** | **`huihui_ai/qwen3.5-abliterated:2B`** (Clean), **`huihui_ai/qwen3.5-abliterated:0.8B`** (Fast) |

> `.110` sans GPU : préférer **2B/9b** pour l’interactif ; **12b** = batch / patient. Qualité type heavy en PoC → Colab T4 (`LBG_REASON_EPHEMERAL_*`, défaut `qwen3.5-abliterated:9b`).

## Profils REASON

| Profil | Env | Défaut | Hôte |
|--------|-----|--------|------|
| `router` / Clean | `LBG_REASON_MODEL_ROUTER` | `huihui_ai/qwen3.5-abliterated:2B` | 111 |
| `json` / Clean | `LBG_REASON_MODEL_JSON` | `huihui_ai/qwen3.5-abliterated:2B` | 111 |
| `fast` | `LBG_REASON_MODEL_FAST` | `huihui_ai/qwen3.5-abliterated:0.8B` | 111 |
| `forge` | `LBG_REASON_MODEL_FORGE` | `huihui_ai/gemma-4-abliterated:e2b` | 110 |
| `default` | `LBG_REASON_LOCAL_MODEL` | `huihui_ai/gemma-4-abliterated:e2b` | 110 |
| `code` | `LBG_REASON_MODEL_CODE` | `huihui_ai/gemma-4-abliterated:12b` | 110 |
| `pm` | `LBG_REASON_MODEL_PM` | `huihui_ai/gemma-4-abliterated:12b` | 110 |
| `dialogue` | `LBG_REASON_MODEL_DIALOGUE` | `huihui_ai/gemma-4-abliterated:12b` | 110 |
| `uncensored` | `LBG_REASON_MODEL_UNCENSORED` | même tag heavy | 110 |

### Dialogue maturité + Prométhée

| Cas | Mécanisme |
|-----|-----------|
| PNJ tous paliers | `LBG_DIALOGUE_LLM_MODEL` = gemma-4 abliterated 12b |
| Présentation soft | `maturity_cap` A/B → `format_maturity_guardrails` (pas de swap modèle) |
| Dual-modèle (legacy) | si `LBG_DIALOGUE_LLM_MODEL_UNCENSORED` posé → option B (C → 2e tag) |
| Agent Team **Prométhée** | rôle `contrarian` → profil REASON `uncensored` |

Failover light → heavy : `LBG_REASON_LIGHT_FAILOVER_HEAVY=1` + `LBG_REASON_LIGHT_FAILOVER_MODEL=huihui_ai/gemma-4-abliterated:e2b`.

Ollama thinking (Qwen) : `LBG_REASON_OLLAMA_THINK=false` (défaut) et `LBG_DIALOGUE_LLM_OLLAMA_THINK=false`.

> Avec ≤12B, 9b + e2b (~6.6 + 7.2 Go) peuvent coexister plus facilement qu’avec deux ~18 Go.  
> Garder `OLLAMA_MAX_LOADED_MODELS=1` sur 110 si RAM serrée.

---

## Diffusion

| Canal | Mécanisme |
|-------|-----------|
| Cursor | règle `.cursor/rules/local-llm-route-matrix.mdc` (`alwaysApply`) si présente |
| Cline (VS Code) | `docs/cline_local_llm.md` + snippets `docs/cline/providers.*.json` (**Plan=110:9b** / Act=110:12b ; triage 111) |
| Team / Atlas | run `admin_infra` → champ `route_matrix` + mémoire `team/atlas` |
| Env exemple | `infra/secrets/lbg.env.example` |
| Audit LAN | `bash infra/scripts/audit_ollama_110_lan.sh` |
| Dialogue fast Groq | Atlas `admin_infra` → `dialogue_fast_groq` ; sonde `/v1/llm/probe` (priorité `LBG_DIALOGUE_FAST_MODEL`) |
| Cloud uncensored | OpenRouter Venice/Dolphin — `docs/cloud_uncensored.md` ; `dialogue_target=uncensored` |
| Secours API free | Groq (canon) / OpenRouter / HF — `docs/reason_cloud_free_fallback.md` |
| Comparatif cloud free | Kaggle / Colab / Lightning / APIs vs LAN — `docs/llm_cloud_free_vs_local.md` |
| GPU éphémère (PoC) | `LBG_REASON_EPHEMERAL_*` — Colab T4, défaut `huihui_ai/qwen3.5-abliterated:9b` ; voir `docs/reason_ephemeral_colab.md` |

Toute évolution de modèles **doit** mettre à jour : `reason_route_matrix()`, ce fichier, `lbg.env.example`, **`LBG_DIALOGUE_FAST_MODEL`** (+ `GROQ_MODEL_*` si Groq), et l’env prod 140 via `push_secrets_vm.sh`.
