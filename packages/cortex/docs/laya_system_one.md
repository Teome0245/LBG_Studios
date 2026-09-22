# Laya — System One (décisions typées) pour Cortex

**Date** : 2026-09-22  
**Statut** : intégration optionnelle (feature flag OFF par défaut)  
**Code** :
- client HTTP : `orchestrator/services/laya_client.py`
- intents : `orchestrator/introspection/laya_intent_classifier.py`
- cascade : `hybrid_classify()` dans `llm_intent_classifier.py`

## Pourquoi

Laya (Convai Innovations, Apache 2.0) est un modèle **System 1** : `state` + questions typées (`choice` / `score` / `noul`) → décisions + probabilités, **sans générer de texte**.

Chez LBG : accélérer / fiabiliser le **routage d'intention** avant les LLM (Qwen 2B / gemma), pas remplacer le dialogue PNJ.

Alternative cloud fermée : **TypeSafe Jev** — non retenue en priorité (local-first).

## Architecture

```
Pilot / Compagnon
    → POST /v1/route
        → déterministe (regex / status)
        → [option] Laya HTTP  POST {LAYA}/v1/systemone
        → [option] LLM intent (OpenAI-compat)
        → dispatch agent
```

L'orchestrateur **n'importe pas** `laya`/`torch`. Il parle à un process séparé :

| Process | Rôle | Hôte suggéré |
|---------|------|--------------|
| `laya-serve` (PyPI) | API compatible Jev | `.111` light (NUC) **:8097** |
| orchestrateur | client HTTP | `.100` / LAN |

Checkpoint recommandé FR / multi : `convaiinnovations/laya-multilingual` (322M).  
Fine-tune ultérieur : `laya-typed-decisions` sur corpus d'intents LBG.

## Activation

Dans `lbg.env` / EnvironmentFile systemd :

```bash
LBG_ORCHESTRATOR_INTENT_LAYA=1
LBG_ORCHESTRATOR_INTENT_LAYA_BASE_URL=http://192.168.0.111:8097
LBG_ORCHESTRATOR_INTENT_LAYA_MODEL=laya-latest
LBG_ORCHESTRATOR_INTENT_LAYA_TIMEOUT_S=2
LBG_ORCHESTRATOR_INTENT_LAYA_ACCEPT_CONF=0.30
LBG_ORCHESTRATOR_INTENT_LAYA_OVERRIDE_CONF=0.85
LBG_ORCHESTRATOR_INTENT_LAYA_NEEDS_LLM_THRESH=0.70
LBG_ORCHESTRATOR_INTENT_LAYA_TIMEOUT_S=30
# LBG_ORCHESTRATOR_INTENT_LAYA_API_KEY=
```

> **Note LAB** : checkpoint EN + 12 intents FR → P(top) souvent ~0.3 ; le score d’acceptation prend `max(confidence_entropie, P(top))` (défaut seuil 0.30). Affiner plus tard via fine-tune ou schéma hiérarchique.

Surcharge requête : `context._intent_classify` = `laya` | `llm` | `deterministic`.

## Lancer laya-serve (LAB)

Sur **`.111`** (port **8097** — 8095=web-enrich, 8096=petri) :

```bash
# Depuis le monorepo (SSH root@111)
bash packages/cortex/infra/scripts/install_laya_serve_111.sh
# Smoke API sans poids HF :
bash packages/cortex/infra/scripts/install_laya_serve_111.sh 192.168.0.111 --fake
# + activer les flags sur l'orchestrateur .140 :
bash packages/cortex/infra/scripts/install_laya_serve_111.sh 192.168.0.111 --enable-orch
```

Unit : `infra/systemd/lbg-laya-serve.service`  
Env runtime : `/etc/lbg-laya-serve.env` (`LAYA_SERVE_BACKEND=laya|fake`, `LAYA_SERVE_PRELOAD`, `LAYA_SERVE_DEVICE=cpu`).

Manuel (équivalent) :

```bash
pip install "laya-serve[inference]==0.1.0"
export USE_TF=0 LAYA_SERVE_BACKEND=laya LAYA_SERVE_PRELOAD=true LAYA_SERVE_DEVICE=cpu
uvicorn laya_serve.app:create_app --factory --host 0.0.0.0 --port 8097
# health : GET http://192.168.0.111:8097/healthz
```

Checkpoint recommandé FR / multi : le `Router` Laya préchargé par `laya-serve` bascule EN↔multilingual ; `LAYA_SERVE_SERVING_MODEL` n'est que l'id echo Jev (`laya-english` par défaut).

Smoke côté orchestrateur (venv Cortex) :

```bash
cd packages/cortex
source .venv/bin/activate
export LBG_ORCHESTRATOR_INTENT_LAYA_BASE_URL=http://192.168.0.111:8097
python -c "
from services.laya_client import systemone_predict
from introspection.laya_intent_classifier import intent_questions
r = systemone_predict(state={'text': 'vérifie healthz'}, questions=intent_questions())
print(r)
"
```

Orchestrateur :

```bash
LBG_ORCHESTRATOR_INTENT_LAYA=1
LBG_ORCHESTRATOR_INTENT_LAYA_BASE_URL=http://192.168.0.111:8097
LBG_ORCHESTRATOR_INTENT_LAYA_MODEL=laya-latest
```

## Règles produit

- **≤15 options** `choice` (ici 12 intents) — Laya faible au-delà de ~20 labels.
- Intents `*_status` factuels : le déterministe gagne toujours (anti-hallucination).
- Si Laya `needs_llm` ≥ seuil → cascade vers le classifieur LLM existant.
- Erreur / timeout Laya → dégradation silencieuse vers det puis LLM.

## Tests

```bash
cd packages/cortex/orchestrator
python -m pytest tests/test_laya_intent.py tests/test_llm_intent_classifier.py -q
```

(Mocks HTTP — pas de poids modèle requis.)

## Suite (hors scope v0)

1. Endpoint Pilot `GET /v1/pilot/...` affichant `intent_source=laya` dans la meta route.
2. Fine-tune sur logs `/v1/route` (det vs humain).
3. Deuxième usage : guardrails tools / maturité dialogue (autre schéma de questions).
4. Bench A/B vs Qwen 2B router sur corpus FR Studio.
