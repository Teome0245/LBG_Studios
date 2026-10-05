# NAS Synology `.51` — droits & intégration LBG

**Date** : 2026-09-27  
**Hôte** : `NAS_LBG` · Synology **DS1815+** · DSM **7.1.1** (build 42962) · IP **`192.168.0.51`**  
**MAC** : `00:11:32:40:BE:2F` (bail Freebox OK)

## État accès (depuis lab / `.143`)

| Voie | État | Notes |
|------|------|-------|
| Ping / LAN | **OK** | |
| DSM UI | **OK** | `:5000` HTTP · `:5001` HTTPS |
| DSM WebAPI | **OK** | Auth SID via `LBG_NAS_USER` + `LBG_NAS_PASSWORD` (pas de PAT sur 7.1.1) |
| SSH `lbg@192.168.0.51` | **OK** (clé) | `uid=1027` · groupes **`users` + `administrators` + `http`** |
| `sudo` SSH | password requis | pas de NOPASSWD |
| SMB anonyme | KO | normal |
| NFS / iSCSI | **OK côté infra** | LUN backup → `.201` — [`runbook_nas_lun_backup.md`](../packages/cortex/docs/runbook_nas_lun_backup.md) |

### Disque

| Volume | FS | Taille | Utilisé |
|--------|-----|--------|---------|
| `/volume1` | btrfs | **~23 To** | ~89 % · avertissement DSM |

### Partages `/volume1` — droits compte `lbg` (probe 2026-09-27)

Tous **RW** pour `lbg` :

`Backup` · `LBG_GIT` · `NAS` · `NetBackup` · `Projet_MMO` · `Sources` · `Telechargements` · `docker` · `music` · `photo` · `video` · `web` · `surveillance` · `homes`

Windows poste `.10` : lecteur **`N:`** = raccourci SMB vers ce NAS (pas OneDrive).  
Rappel ops : uptime NAS **irrégulier** (~6 mois) — jamais seule source de vérité (voir [`hands_ct_142.md`](../packages/cortex/docs/hands_ct_142.md)).

## Écosystème LBG

| Couche | Capacité |
|--------|----------|
| Inventaire réseau | Hôte `synology-nas` · fingerprint 5000/5001 · **probe DSM** si `LBG_NAS_*` |
| Client DSM | [`synology_client.py`](../packages/cortex/agents/src/lbg_agents/synology_client.py) |
| Smoke | `bash packages/cortex/infra/scripts/smoke_nas_51.sh` |
| Sauvegardes Proxmox | iSCSI `nas-lun-backup` via `.201` |
| IMAP lab (optionnel) | Exemple `LBG_DESKTOP_MAIL_IMAP_HOST=192.168.0.51` |

## Auth — ce qu’il ne faut pas confondre

| UI DSM | Rôle |
|--------|------|
| **OAuth Service** | Apps tierces (redirect URI) — **pas** pour le client LBG |
| **Personal Access Token** | Dispo surtout DSM **7.2+** — absent / inutilisable ici en 7.1.1 |
| **Login WebAPI** `SYNO.API.Auth` | **Voie utilisée** : account + passwd → SID de session |

## Secrets (gitignorés)

```bash
# packages/cortex/infra/secrets/nas.env.local  (+ upsert lbg.env si besoin)
LBG_NAS_ENABLED=1
LBG_NAS_HOST=192.168.0.51
LBG_NAS_DSM_URL=https://192.168.0.51:5001
LBG_NAS_USER=lbg
LBG_NAS_PASSWORD=…          # MDP DSM — jamais en git
LBG_NAS_TOKEN=              # réserve PAT si upgrade DSM
LBG_NAS_VERIFY_SSL=0
```

**État** : MDP `lbg` en local + smoke stockage / FileStation / Download Station **OK**.

## API couvertes (lecture)

| Capacité | API |
|----------|-----|
| Login / logout | `SYNO.API.Auth` |
| Volumes / disques | `SYNO.Storage.CGI.Storage` `load_info` |
| CPU / RAM | `SYNO.Core.System.Utilization` |
| Partages | `SYNO.FileStation.List` `list_share` |
| Téléchargements | `SYNO.DownloadStation.Task` `list` |

Contacts / Photos : plus tard (packages dédiés).

## Vérif rapide

```bash
bash packages/cortex/infra/scripts/smoke_nas_51.sh
ssh -o BatchMode=yes lbg@192.168.0.51 'df -h /volume1'
```
