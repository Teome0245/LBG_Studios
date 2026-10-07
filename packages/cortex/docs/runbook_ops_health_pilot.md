# Runbook — Ops Health Pilot + Fleet

**Plan** : [`plan_combler_gaps_agentiques.md`](plan_combler_gaps_agentiques.md)  
**Code** : `team/fleet.py` · `team/ops_health_pilot.py` · `lbg_agents.spawn_ops_health_pilot_job` · Pilot `#/team/fleet`

## Endpoints

| Méthode | Orch | Pilot proxy |
|---------|------|-------------|
| GET | `/v1/team/fleet` | `/v1/pilot/team/fleet` |
| POST | `/v1/team/ops_health_pilot` | `/v1/pilot/team/ops_health_pilot` |

### Body ops_health_pilot

```json
{
  "dry_run": true,
  "notify": null,
  "spawn_l2_remediation": true,
  "include_smoke": false,
  "actor_id": "pilot:ops_health"
}
```

| Champ | Défaut | Effet |
|-------|--------|--------|
| `dry_run` | `true` | Pas de Slack / pas de tâche L2 |
| `notify` | `null` (= auto) | Auto : off en dry-run, **on** en live si KO |
| `spawn_l2_remediation` | `true` | Crée (ou déduplique) tâche `ops` en `review` |
| `include_smoke` | `false` | Smoke QA lourd (optionnel) |

Live KO : `send_text` + `send_l2_pending` (HITL Slack) + lesson + état `/var/lib/lbg/ops_health_pilot/state.json`.

## Pilot UI

1. `#/team/fleet` — agents, L2 HITL (token → Approuver / Exécuter), flags agentiques, dernier run.
2. **Ops health dry-run** — safe.
3. **Ops health live** — confirmation ; notify auto + L2 si KO.

## Timer systemd (B6)

Fichiers : `infra/systemd/lbg-ops-health-pilot-job.{service,timer}`  
Install : `bash infra/scripts/install_ops_health_pilot_job_vm.sh`

| Env | Défaut | Sens |
|-----|--------|------|
| `LBG_OPS_HEALTH_PILOT_DRY_RUN` | `1` | Timer safe |
| `LBG_OPS_HEALTH_PILOT_NOTIFY` | `0` (dry) / `1` (si dry=0) | Slack |
| `LBG_OPS_HEALTH_PILOT_JOB_COOLDOWN_S` | `10800` (3 h) | Anti-spam |

Passer en live sur 140 :

```bash
# dans /etc/lbg-ia-mmo.env
LBG_OPS_HEALTH_PILOT_DRY_RUN=0
LBG_OPS_HEALTH_PILOT_NOTIFY=1
sudo systemctl daemon-reload
sudo systemctl start lbg-ops-health-pilot-job.service
journalctl -u lbg-ops-health-pilot-job -n 40 --no-pager
```

## Phase C — chat agentique opt-in

```bash
# Toujours off global, OU :
LBG_CHAT_AGENTIC=1
LBG_CHAT_AGENTIC_INTENTS=devops_probe,project_pm,desktop_control   # C + F1 + F2
LBG_JOBS_RUNNER_ENABLED=1
```

Sans allowlist, tous les intents `AGENTIC_INTENTS` s'élèvent.  
`context.prefer_agentic=true` force l'élévation même si global off (UI).

## Phase F1 — PM agentique

Intent NL `project_pm` (roadmap / point d’avancement / chef de projet) + `prefer_agentic`
ou allowlist → job fond (pas le payload structuré `project_pm: {…}` console).

```bash
curl -s -X POST http://192.168.0.140:8010/v1/route \
  -H 'Content-Type: application/json' \
  -d '{"actor_id":"pilot:pm","text":"point d'\''avancement et plan de route",
       "context":{"prefer_agentic":true,"pm_focus":true}}'
```

## Phase F2 — Pygmalion assets → L2

Playbook : sonde Comfy → **auto-ensure si down** → tâche Team `dev_game` (approval) + HITL.  
Pas de queue Comfy sans approve.

**Ensure** (si `LBG_PYGMALION_COMFY_AUTO_ENSURE=1`, défaut) via agent Windows `.10:5005` :

```text
cd C:\Users\sdesh\ComfyUI
.\venv\Scripts\python.exe main.py --listen 0.0.0.0 --port 8188 --lowvram
```

(équivalent de l’activation venv + `python main.py …` — géré par `comfyui_lifecycle` / `start_comfyui.ps1`)

Prérequis worker : `LBG_DESKTOP_COMFYUI_ENABLED=1` dans `C:\Agent_IA\desktop.env`.  
Sync agent : `bash infra/scripts/sync_windows_agent.sh`.

```bash
curl -s -X POST http://192.168.0.140:8010/v1/team/pygmalion_assets_pilot \
  -H 'Content-Type: application/json' \
  -d '{"brief":"Prépare ComfyUI pour sprite PNJ","dry_run":true}'
curl -s -X POST http://192.168.0.140:8010/v1/team/pygmalion_assets_pilot \
  -H 'Content-Type: application/json' \
  -d '{"brief":"Prépare ComfyUI pour sprite PNJ","dry_run":false,"notify":true}'
```

NL + `prefer_agentic` : mots-clés `pygmalion` / `comfyui` / `brief assets` → `desktop_control` (dry-run injecté).  
Pilot Fleet : boutons **Pygmalion dry / live**.

## Phase E — HITL jobs + mission L3 bornée

```bash
LBG_JOBS_L2_NOTIFY=1          # push Slack quand job → waiting_approval
# HITL texte : approve <job_id_court>  (résout Team puis Jobs)
```

Mission L3 (deadline / budget retries / escalade puis stop) :

```bash
curl -s -X POST http://192.168.0.140:8010/v1/team/smoke_lan_mission \
  -H 'Content-Type: application/json' \
  -d '{"days":3,"budget_retries":5,"escalate_after_red":2}'
curl -s -X POST http://192.168.0.140:8010/v1/team/smoke_lan_mission/tick \
  -H 'Content-Type: application/json' -d '{"dry_run":true}'
curl -s http://192.168.0.140:8010/v1/team/smoke_lan_mission
# Pilot Fleet : #/team/fleet — panneau Mission L3 + boutons
```

État : `/var/lib/lbg/smoke_lan_mission/state.json` (surcharge `LBG_SMOKE_LAN_MISSION_STATE`).

Le timer `lbg-ops-health-pilot-job` appelle aussi `POST /v1/team/smoke_lan_mission/tick`
après chaque run (`LBG_SMOKE_LAN_MISSION_TICK_ON_OPS_HEALTH=1` par défaut).  
`days_ok` n’incrémente qu’**une fois par jour UTC** (même si le timer tourne toutes les 3 h).  
Sans mission active → skip soft (`no_mission`).

**Périmètre** : PreCU **245** est **optionnel** (`required=False`) — OFF ≠ remediate.  
246 Prime requis via **`http://192.168.0.246:8787/healthz`** (Godot G5+ unifié ; plus `:8765` / sidecar `:8791`).

## Curl

```bash
curl -s http://192.168.0.140:8010/v1/team/fleet | head -c 800
curl -s -X POST http://192.168.0.140:8010/v1/team/ops_health_pilot \
  -H 'Content-Type: application/json' -d '{"dry_run":true}'
curl -s -X POST http://192.168.0.140:8010/v1/team/ops_health_pilot \
  -H 'Content-Type: application/json' -d '{"dry_run":false}'
```

## Live (activé 2026-10-05 sur 140)

```bash
# /etc/lbg-ia-mmo.env
LBG_OPS_HEALTH_PILOT_DRY_RUN=0
LBG_OPS_HEALTH_PILOT_NOTIFY=1
```

Unit systemd : plus de DRY_RUN hardcodé — lit l’env.  
Healthy → pas de Slack. KO hôte **requis** → notify + L2.

Revenir en dry-run :
```bash
sudo sed -i 's/^LBG_OPS_HEALTH_PILOT_DRY_RUN=.*/LBG_OPS_HEALTH_PILOT_DRY_RUN=1/' /etc/lbg-ia-mmo.env
sudo sed -i 's/^LBG_OPS_HEALTH_PILOT_NOTIFY=.*/LBG_OPS_HEALTH_PILOT_NOTIFY=0/' /etc/lbg-ia-mmo.env
```
