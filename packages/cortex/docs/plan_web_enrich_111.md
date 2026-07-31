# Plan — Enrichissement web LLM (111 → 140)

**Date** : 2026-07-29  
**Statut** : teaser déployé sur **111** ; branchement Team sur **140** dès que l’infra remonte  
**Complète** : `plan_team_petri_peau.md`, dual LLM Fast/Clean

---

## Décision actée

| Nœud | Rôle |
|------|------|
| **110** | Référence heavy (code / pm / forge) |
| **111** | Light : délestage petites tâches + secours si 110 crash |

Sur **111** uniquement 2 modèles :
- **Fast** → `llama3.2:3b`
- **Clean** → `qwen2.5:3b` (router + json)

---

## Ce qui est déjà sur 111 (sans attendre 140)

Service **`lbg-light-web-enrich`** :

- URL : **http://192.168.0.111:8095**
- `GET /healthz`
- `POST /v1/enrich` — Wikipedia (EN/FR) + DDG Instant Answer + fetch allowlisté
- `POST /v1/chat` — enrichit le prompt puis appelle Ollama local (défaut **Clean** = Qwen)

Principe : le LLM ne surfe pas ; le sidecar récupère le web, injecte le contexte, puis génère.

### Smoke teaser

```bash
curl -s http://192.168.0.111:8095/healthz

curl -s -X POST http://192.168.0.111:8095/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"web":true,"model":"qwen2.5:3b","messages":[{"role":"user","content":"Qu est-ce qu un LXC Proxmox ?"}]}'
```

---

## Quand 140 remonte

1. Appliquer env Fast/Clean sur 140 (`LBG_REASON_MODEL_*`)
2. Brancher Team/MCP sur `111:8095/v1/enrich`
3. Optionnel : écrire les learnings dans Fable5 `cortex/web`
4. Teaser Petri `#/team/office` consommant `presence` + enrich

---

## Hors scope v1

- Fine-tune / LoRA
- Crawl web ouvert sans allowlist
- Remplacer 110 pour le code profond
