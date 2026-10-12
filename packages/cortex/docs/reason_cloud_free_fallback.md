# Secours API free (Groq / OpenRouter / HF)

**Date** : 2026-09-20  
**Statut** : runbook — voie de secours si Ollama LAN down  
**Comparatif** : [`llm_cloud_free_vs_local.md`](llm_cloud_free_vs_local.md)  
**Code REASON** : `orchestrator/team/reason_llm.py` → `reason_cloud_*` / `reason_routes()`  
**Dialogue fast** : `LBG_DIALOGUE_FAST_*` + Atlas `dialogue_fast_groq`  
**Env** : `infra/secrets/lbg.env.example`

---

## Principe

Ordre nominal :

```
Ollama local → (failover heavy) → ephemeral GPU? → cloud API?
```

Le **cloud API** est le secours **stable** (pas H24 local, mais sans notebook flaky).  
Priorité LBG : **Groq** (déjà sondé / audité). OpenRouter et HF = alternatives OpenAI-compat.

Les modèles free tier **ne remplacent pas** les tags abliterated locaux. Pour du « uncensored », rester sur `.110` ou `LBG_REASON_EPHEMERAL_*`.

---

## 1. Groq (recommandé)

### Variables REASON

```bash
export LBG_REASON_FAILOVER=1
export LBG_REASON_CLOUD_BASE_URL="https://api.groq.com/openai/v1"
export LBG_REASON_CLOUD_MODEL="qwen/qwen3.8-27b"   # aligner GROQ_MODEL_*
export LBG_REASON_CLOUD_API_KEY="<GROQ_API_KEY>"
# optionnel : forcer cloud en premier
# export LBG_REASON_PREFER_CLOUD=1
```

### Variables dialogue fast (souvent déjà posées)

```bash
export LBG_DIALOGUE_FAST_ENABLED=1
export LBG_DIALOGUE_FAST_BASE_URL="https://api.groq.com/openai/v1"
export LBG_DIALOGUE_FAST_MODEL="qwen/qwen3.8-27b"
export LBG_DIALOGUE_FAST_API_KEY="<GROQ_API_KEY>"
# ou GROQ_API_KEY=… (résolu par le probe)
```

### Contrôles

| Outil | Action |
|-------|--------|
| Atlas | run `admin_infra` → champ `dialogue_fast_groq` |
| Sonde | `GET /v1/llm/probe` (orchestrateur) |
| Code | `team/llm_model_probe.py` → `audit_dialogue_fast_cloud()` |

Canon Groq fast : `qwen/qwen3.8-27b` (éviter legacy `llama-3.1-8b-instant` signalé par le probe).

### Smoke manuel

```bash
curl -sS https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" | head
```

Compte : [console.groq.com](https://console.groq.com).

---

## 2. OpenRouter (optionnel)

Compatible OpenAI. Utile pour modèles `:free` ou GLM.

### Via dialogue GLM (déjà prévu)

```bash
export LBG_DIALOGUE_GLM_ENABLED=1
export LBG_DIALOGUE_GLM_BASE_URL="https://openrouter.ai/api/v1"
export LBG_DIALOGUE_GLM_MODEL="z-ai/glm-5.2"   # ou un id :free
export LBG_DIALOGUE_GLM_API_KEY="<OPENROUTER_KEY>"
```

### Via REASON cloud (si Groq indispo)

```bash
export LBG_REASON_CLOUD_BASE_URL="https://openrouter.ai/api/v1"
export LBG_REASON_CLOUD_MODEL="<provider/model:free>"
export LBG_REASON_CLOUD_API_KEY="<OPENROUTER_KEY>"
```

Compte : [openrouter.ai](https://openrouter.ai). Filtrer le catalogue sur **price = free**.

---

## 3. Hugging Face Inference (expérimental)

```bash
export LBG_REASON_CLOUD_BASE_URL="https://router.huggingface.co/v1"  # ou endpoint Inference dédié
export LBG_REASON_CLOUD_MODEL="<org/model>"
export LBG_REASON_CLOUD_API_KEY="<HF_TOKEN>"
```

À valider modèle par modèle (cold start, 503). Pas d’audit Atlas dédié — usage perso / lab uniquement.

---

## Matrice « quel secours pour quel profil »

| Profil REASON | Local | Secours free réaliste |
|---------------|-------|------------------------|
| `router` / `json` / `fast` | `.111` 0.8B–2B | Groq petit / instant (qualité ≠ JSON local) |
| `forge` / `default` | gemma e2b abliterated | Groq `qwen/qwen3.8-27b` |
| `code` / `pm` / `dialogue` | qwen3.5 9b abliterated | Groq (filtré) ou ephemeral Colab 8b |
| `uncensored` / Prométhée | même 9b + prompts | **ephemeral** ou attendre `.110` — pas Groq free |

---

## Prod `.140`

- Clés Groq : secrets via `infra/secrets` + `push_secrets_vm.sh` si déjà en usage dialogue.  
- **Ne pas** pousser d’URL tunnel Colab / Kaggle.  
- Après changement de modèle Groq : aligner `LBG_DIALOGUE_FAST_MODEL` **et** `GROQ_MODEL_*`.

---

## Checklist incident « Ollama down »

1. Confirmer : `curl -sS http://192.168.0.110:11434/api/tags`  
2. Activer / vérifier `LBG_REASON_CLOUD_*` + clé Groq  
3. Sonde `complete_reason` ou Pilot chat court  
4. Si besoin abliterated immédiat → notebook Colab ([`reason_ephemeral_colab.md`](reason_ephemeral_colab.md))  
5. Remettre `LBG_REASON_PREFER_CLOUD=0` dès que `.110` revient
