# Runbook — `nas-lun-backup` (Synology iSCSI / NFS)

## Architecture cible

| Nœud | Rôle | Montage de `/mnt/pve/nas-lun-backup` |
|------|------|--------------------------------------|
| **`.201` (R720)** | propriétaire du LUN | iSCSI Synology `192.168.0.51` → `/dev/sdc1` (ext4) |
| **`.200` (NUC)** | client backup CT 111/142 | **NFS** depuis `.201` (même chemin) |

Target iSCSI : `iqn.2000-01.com.synology:NAS-LBG.Target-1.998d838e300`.

Storage PVE (cluster) :

```
dir: nas-lun-backup
	path /mnt/pve/nas-lun-backup
	content backup
```

**Ne jamais** monter le même LUN iSCSI ext4 en RW sur les deux nœuds (corruption).

## Bug corrigé (2026-08-20)

Sur `.200`, le chemin existait comme **dossier local sur `pve-root`**. Les `vzdump` nocturnes ont rempli le root (~96 %) et laissé des locks `snapshot-delete`.

Correctif :

1. NFS export sur `.201` : `/mnt/pve/nas-lun-backup 192.168.0.200(rw,…)`
2. fstab `.200` : `192.168.0.201:/mnt/pve/nas-lun-backup /mnt/pve/nas-lun-backup nfs …`
3. Migration des dumps locaux vers le LUN, suppression du dossier local

## Vérification

```bash
# .200
findmnt -T /mnt/pve/nas-lun-backup   # doit être nfs4 → 192.168.0.201:...
df -h / /mnt/pve/nas-lun-backup
pvesm status | grep nas-lun

# .201
findmnt -T /mnt/pve/nas-lun-backup   # doit être /dev/sdc1
exportfs -v
```

Sonde Team : `proxmox_storage` alerte **critical** si `nas-lun-backup` retombe sur le root local.
