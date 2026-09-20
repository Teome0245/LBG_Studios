# Cloud uncensored (hors Groq)

**Date** : 2026-09-20  
**Statut** : actif si `LBG_DIALOGUE_UNCENSORED_CLOUD_ENABLED=1`

Groq (`LBG_DIALOGUE_FAST_*`) reste **filtré** (vitesse).  
Le palier **`uncensored`** pointe un provider OpenAI-compat distinct — canon : [OpenRouter Venice / Dolphin](https://openrouter.ai/cognitivecomputations/dolphin-mistral-24b-venice-edition).

## Variables

| Env | Défaut |
|-----|--------|
| `LBG_DIALOGUE_UNCENSORED_CLOUD_ENABLED` | `0` |
| `LBG_DIALOGUE_UNCENSORED_CLOUD_BASE_URL` | `https://openrouter.ai/api/v1` |
| `LBG_DIALOGUE_UNCENSORED_CLOUD_MODEL` | `cognitivecomputations/dolphin-mistral-24b-venice-edition` |
| `LBG_DIALOGUE_UNCENSORED_CLOUD_API_KEY` | `${OPENROUTER_API_KEY}` |

REASON / Prométhée : même endpoint via `reason_cloud_uncensored_route()` si profil `uncensored` (réutilise les vars dialogue si `LBG_REASON_CLOUD_UNCENSORED_*` absentes).

## Usage

```json
{ "dialogue_target": "uncensored" }
```

Aliases : `venice`, `cloud_uncensored`.

Auto / failover recommandé :

```bash
LBG_DIALOGUE_AUTO_ORDER="local,uncensored,fast,remote"
LBG_DIALOGUE_FAILOVER_ORDER="local,uncensored,fast,remote"
```

Maturité C / `force_uncensored` : la chaîne auto **saute Groq fast** et préfère `local` puis `uncensored`.

## Smoke

```bash
curl -sS https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "HTTP-Referer: https://github.com/lbg-ia-mmo" \
  -H "X-Title: LBG-smoke" \
  -H "Content-Type: application/json" \
  -d '{"model":"cognitivecomputations/dolphin-mistral-24b-venice-edition","messages":[{"role":"user","content":"ping: OK"}],"max_tokens":8}'
```
