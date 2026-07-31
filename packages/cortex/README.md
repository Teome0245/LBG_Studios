# packages/cortex — Studio (O1)

Extrait chirurgical de `LBG_IA_MMORPG/LBG_IA_MMO` (sans `pilot_web/mmo`, sans sandbox MMO).

| Dossier | Rôle |
|---------|------|
| `orchestrator/` | Team, Campus, Cursor agent, jobs |
| `backend/` | API Pilot `/v1` |
| `agents/` | Capacités / dispatch |
| `pilot_web/` | UI Pilot (140:8080) |
| `infra/` | systemd, nginx, deploy |
| `windows_agent/` / `linux_agent/` | Desktop hybride |

Sync : `bash tools/sync_from_legacy.sh cortex`  
Deploy Pilot : `bash tools/deploy_cortex_140.sh`
