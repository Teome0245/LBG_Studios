# Plan — Capability Cursor Cloud Agent (exécutant code / PR)

## Failed Team — deux couches

| Couche | Rôle |
|--------|------|
| **TTL présence** (`LBG_TEAM_PRESENCE_FAILED_TTL_SEC=90`) | Libère l’UI (failed → idle café). **Ne corrige pas** le bug. |
| **Follow-up échec** (`failure_followup.py`, ON par défaut) | Crée une tâche **PM triage** (auto-run L1). Retry même rôle seulement si `LBG_TEAM_FAILURE_RETRY=1`. Les pipelines QA/Godot/M9 existants restent prioritaires. |

Donc : le failed n’est **pas ignoré** — il déclenche un triage ; le TTL évite juste de rester bloqué en rouge.
## Décision

| Oui | Non |
|-----|-----|
| Intent « ouvre une PR qui… », « corrige le bug X dans le repo » | Chaque message chat via Cursor |
| Clé `CURSOR_API_KEY` (User API Key) en env secrets | Clé en dur / dans le repo |
| Orchestrateur LBG reste le cerveau | Remplacer Groq/Mistral/Ollama |

## Flux

```
Pilot / Lyra / Team (dev_game|dev_godot)
  → intent code_pr / cursor_agent
  → capability cursor_cloud_agent (OFF par défaut)
  → cursor-sdk / Cloud Agent API
  → statut + URL PR → Team presence + job
```

## Garde-fous

- Opt-in : `LBG_CURSOR_AGENT_ENABLED=0` par défaut
- Approbation L2 pour écriture repo / PR
- Repos allowlist : `LBG_CURSOR_AGENT_REPOS` (ex. `Teome0245/new_mmo,Teome0245/LBG_IA_MMO`)
- Timeout + audit log

## Première brique

- `orchestrator/integrations/cursor_agent.py` — health + dry-run + `launch_cloud_agent` (SDK)
- `orchestrator/team/cursor_agent_workflow.py` — workflow Team
- API :
  - `GET /v1/team/cursor/health`
  - `POST /v1/team/cursor/launch` (`dry_run=true` par défaut)
- Tâche Team : `role=dev_game` + `context.cursor_cloud_agent=true`

```bash
curl -s http://192.168.0.140:8010/v1/team/cursor/health
curl -s -X POST http://192.168.0.140:8010/v1/team/cursor/launch \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Documenter X","repository":"Teome0245/new_mmo","dry_run":true}'
```

## Sync clé sur 140 (LAN)

Depuis le monorepo, sur le poste avec accès SSH à **192.168.0.140** :

```bash
# 1) User API Key Cursor (cursor.com → Settings → API Keys)
export CURSOR_API_KEY=cursor_...

# 2) Patch /etc/lbg-ia-mmo.env + pip cursor-sdk + restart orchestrateur + smoke
bash tools/push_cursor_secrets_140.sh
```

Alternative : ajouter `CURSOR_API_KEY=...` dans `packages/cortex/infra/secrets/lbg.env` (local, gitignoré) puis relancer le script.

Smoke seul (avant/après sync) :

```bash
bash packages/cortex/infra/scripts/smoke_cursor_agent_lan.sh
# ready=false attendu tant que la clé n'est pas sur 140 ; ready=true après push OK
```

Intégré dans `bash tools/smoke_lan_surfaces.sh --functional` (étape Cursor — WARN si `ready=false`).

Garde-fous : OFF par défaut, allowlist repos, `approval_required` sur lancement réel.