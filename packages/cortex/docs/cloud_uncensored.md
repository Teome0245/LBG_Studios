# Cloud uncensored (hors Groq)

**Date** : 2026-09-21  
**Statut** : actif si `LBG_DIALOGUE_UNCENSORED_CLOUD_ENABLED=1`

Groq (`LBG_DIALOGUE_FAST_*`) reste **filtré** (vitesse).  
Le palier **`uncensored`** pointe un provider OpenAI-compat distinct — canon actuel : **DeepInfra** Dolphin 70B (`cognitivecomputations/dolphin-2.9.1-llama-3-70b`).

## Variables

| Env | Défaut |
|-----|--------|
| `LBG_DIALOGUE_UNCENSORED_CLOUD_ENABLED` | `0` |
| `LBG_DIALOGUE_UNCENSORED_CLOUD_BASE_URL` | `https://api.deepinfra.com/v1/openai` |
| `LBG_DIALOGUE_UNCENSORED_CLOUD_MODEL` | `cognitivecomputations/dolphin-2.9.1-llama-3-70b` |
| `LBG_DIALOGUE_UNCENSORED_CLOUD_API_KEY` | `${DEEPINFRA_API_KEY}` |

> DeepInfra exige un **solde > 0** (sinon HTTP 402). Recharger sur le dashboard DeepInfra.

REASON / Prométhée : même endpoint via `reason_cloud_uncensored_route()` si profil `uncensored`.

## Usage

```json
{ "dialogue_target": "uncensored" }
```

Aliases : `venice`, `cloud_uncensored`.

```bash
LBG_DIALOGUE_AUTO_ORDER="local,uncensored,fast,remote"
```

## Smoke

```bash
curl -sS https://api.deepinfra.com/v1/openai/chat/completions \
  -H "Authorization: Bearer $DEEPINFRA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"cognitivecomputations/dolphin-2.9.1-llama-3-70b","messages":[{"role":"user","content":"ping: OK"}],"max_tokens":8}'
```
