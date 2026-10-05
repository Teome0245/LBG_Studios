# Runbook — inventaire réseau LAN (P3)

**Date** : 2026-10-05  
**Statut** : live sur `.140` (timer 30 min)  
**Personas** : Héphaïstos (`ops`) · Atlas (`admin_infra`)

## Objectif

Cartographier le LAN (PC, box, switch, IoT, VMs…) ; détecter **apparus** / **disparus** ; alimenter Compagnon Agir + Team.

## Chaîne

```
Timer lbg-network-inventory-job (30 min)
  → run_network_inventory (scan TCP + Freebox LAN + Cast Eureka)
  → state.json (/var/lib/lbg/network_inventory/)
  → si +/− : spawn tâche Héphaïstos (ops_kind=network_inventory)
  → Atlas lit state.json (network_lan) sans rescanner
```

Compagnon : intent inventaire → `network_inventory` · `auto_real` (lecture seule).

## Install / smoke

```bash
bash packages/cortex/infra/scripts/install_network_inventory_job_vm.sh
ssh lbg@192.168.0.140 'systemctl list-timers lbg-network-inventory-job.timer --no-pager'
ssh lbg@192.168.0.140 'sudo systemctl start lbg-network-inventory-job.service && journalctl -u lbg-network-inventory-job -n 5 --no-pager -q'
```

État : `/var/lib/lbg/network_inventory/state.json`

## Env (exemple)

Voir `infra/secrets/lbg.env.example` :

| Variable | Rôle |
|----------|------|
| `LBG_NETWORK_INVENTORY_JOB_ENABLED` | Timer (défaut 1) |
| `LBG_NETWORK_INVENTORY_SPAWN_OPS` | Spawn Héphaïstos si changement |
| `LBG_NETWORK_INVENTORY_NOTIFY` | Slack/Element si +/− |
| `LBG_FREEBOX_*` | LAN browser Freebox |
| `LBG_NEST_MINI_HOST` / `LBG_CAST_*` | Nest Mini Cast (`.75`) |

## Nest Mini `.75` (« Séjour »)

| Rôle | Possible ? |
|------|------------|
| **Bouche** (annonces TTS via Cast) | Oui — sonde Eureka OK ; annonce = `pychromecast` + flux audio (Piper préféré) |
| **Oreilles** (STT / wake-word LBG) | Non — micro verrouillé Google Assistant cloud |

Sonde : `cast_speaker_client.probe_cast_speaker("192.168.0.75")` → rôle inventaire `cast`.

## Héphaïstos / Atlas

| Agent | Accroche |
|-------|----------|
| Héphaïstos | `ops_kind=network_inventory` dans `team/roles.py` ; plan NL « inventaire réseau / apparus » |
| Atlas | `load_network_lan_context()` dans `admin_infra_workflow` → champ `network_lan` + reco si diff |

## Vague Compagnon Agir

| # | Livrable | Statut |
|---|----------|--------|
| **P1** | IMAP + `auto_real` soft (mail) | OK |
| **P2** | Selfcheck LAN + soft-confirm DevOps | OK |
| **P3** | Inventaire LAN + timer + diff + Nest Cast + Team | OK |
| **P4** | Brief du matin (Self + Jobs L2 + LAN + 1–2 Agir) | OK — [`morning_brief.md`](morning_brief.md) |
| **P5** | Mémoire → seed d’évolution STUDIO | OK — [`memory_evolution_seed.md`](memory_evolution_seed.md) |

## Fichiers clés

| Couche | Chemin |
|--------|--------|
| Scan + diff | `agents/src/lbg_agents/network_inventory.py` |
| Timer | `agents/src/lbg_agents/spawn_network_inventory_job.py` |
| Freebox | `agents/src/lbg_agents/freebox_client.py` |
| Cast / Nest | `agents/src/lbg_agents/cast_speaker_client.py` |
| Atlas contexte | `orchestrator/team/network_lan_context.py` |
| Systemd | `infra/systemd/lbg-network-inventory-job.{service,timer}` |
