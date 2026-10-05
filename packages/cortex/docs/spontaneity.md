# Spontanéité Compagnon — suggestions + moteur d'évolution

**Date** : 2026-09-29  
**Statut** : V1 (overlay + SPA)  
**Surface** : toast / « Je vois » + API Orch `.100`

## Intention

Les *gates* (quand proposer) restent heuristiques (Self, proactive, quota).  
Le **contenu** passe par une réflexion LLM light (« spontané ») :

| Mode | Quand | Effet |
|------|--------|--------|
| `full` | idle, Self drives, studio soft | message + intents réinventés (validés) |
| `message_only` | garde infra, brief matin, L2 | intents figés, message plus vivant |

Jamais d'auto-Réel — Agir / Team L1 / discuss uniquement.

## Évolution

Accept / dismiss → `/var/lib/lbg/spontaneity/state.json` :

- `theme_scores` — biais pour les prochaines propositions  
- `evolution_seeds` — idées produit (renforcées à l'accept)  
- anti-boucle via `shown` + thèmes dismissés  

**Promotion Self** (seuil `LBG_SPONTANEITY_PROMOTE_SCORE`, défaut `1.0`) :

1. Accept d'une spontanée avec `evolution_seed` → seed scorée  
2. `promote_ready_seeds` → `POST` orch `/v1/self/will` (ou Pilot `/v1/pilot/orchestrator/self/will`)  
3. Seed marquée `promoted_ts` + apparaît dans `pending_will` Self  
4. Toast Compagnon via `offerFromSelf` (ou fallback `offerFromEvolutionSeed`)  

`GET /spontaneity/evolution` · `POST /spontaneity/promote`  

SPA : biais léger `studioGoal` selon thèmes acceptés (`biasGoalFromThemes`).

## Fichiers

| Élément | Chemin |
|---------|--------|
| Moteur | `compagnon_ui/server_overlay/spontaneity.py` |
| API | `compagnon_ui/server_overlay/spontaneity_api.py` → `/spontaneity/*` |
| Client SPA | `compagnon_ui/src/lib/spontaneity.js` + `useInitiative.js` |
| Deploy | `infra/scripts/deploy_compagnon_100.sh` |

## API

- `POST /spontaneity/propose` — body = offre heuristique (+ context)  
- `POST /spontaneity/feedback` — `{ id, kind: accept|dismiss, themes, evolution_seed }`  
- `GET /spontaneity/evolution` — seeds + scores  

SPA prod : `/api/spontaneity/…` (nginx → backend `:3000`).

## Feature flag

`LBG_SPONTANEITY_ENABLED=0` → passe-plat heuristique.  
Cache TTL : `LBG_SPONTANEITY_CACHE_TTL_S` (défaut 1200).  
Modèle : `LBG_SPONTANEITY_MODEL` ou `LBG_REFLECTION_MODEL` (défaut `qwen2.5:3b` sur `.111`).

## Tests

```bash
python3 -m unittest packages/cortex/compagnon_ui/server_overlay/tests/test_spontaneity.py
node --test packages/cortex/compagnon_ui/src/lib/spontaneity.test.js
```

## Smoke post-deploy

```bash
curl -sS http://192.168.0.100:5174/api/spontaneity/ | jq .
curl -sS -X POST http://192.168.0.100:5174/api/spontaneity/propose \
  -H 'Content-Type: application/json' \
  -d '{"id":"jobs:idle","message":"Silence studio","kind":"studio","offerType":"opportunite","offer":true,"intents":[{"id":"mail","label":"Mails","sourceText":"regarde mes mails récents"}]}' | jq .
```
