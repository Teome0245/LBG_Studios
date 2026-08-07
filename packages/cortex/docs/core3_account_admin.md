# UI web — gestion des comptes Core3

Module : `packages/cortex/tools/core3_account_admin/`

## Surfaces (après split)

| UI | Rôle | Pastille `/api/servers` | Comptes MariaDB |
|----|------|-------------------------|-----------------|
| **http://192.168.0.245:8792/** | PreCU / nostalgie SWG | **swgemu** (`core3-swgemu`) seul | PreCU local |
| **http://192.168.0.246:8792/** | Prime / produit LBG | **prime** (`core3-clean`) seul | Prime local |

Plus de bandeau croisé (245 ne sonde plus clean/Prime ; 246 ne sonde plus swgemu). Override ops : `CORE3_STATUS_SHOW_ALL=1` ou JSON `CORE3_STATUS_INSTANCES`.

## Accès (VM LAN 245 — PreCU)

```bash
bash packages/cortex/infra/scripts/start_core3_account_admin_vm.sh
```

- Token par défaut du script : `lbg-core3-admin-change-me` (surcharge : `CORE3_ADMIN_TOKEN=…`)
- **État serveur** : `GET /api/servers` — pastille PreCU uniquement.

## Accès (VM LAN 246 — Prime)

```bash
bash packages/cortex/infra/scripts/start_core3_account_admin_prime_vm.sh
```

## Démarrage automatique au reboot (systemd)

```bash
ssh lbg@192.168.0.245 'systemctl status lbg-core3-account-admin.service --no-pager'
ssh lbg@192.168.0.246 'systemctl status lbg-core3-account-admin.service --no-pager'
```

À retenir :

- Le port `:8792` peut être occupé si l’UI a été lancée en `nohup`. Dans ce cas, tuer l’ancien process (`pkill -f core3_account_admin.py`) puis redémarrer le service systemd.
- Secrets : `/etc/lbg-core3-account-admin.env` (`CORE3_DB_PASS`, `CORE3_ADMIN_TOKEN`). Sans token, l’écoute `0.0.0.0:8792` est refusée.
- `CORE3_LOCAL_SERVER_ID=precu` (245) ou `prime` (246) pilote pastilles + bases exposées.

## Alignement Core3

Les mots de passe créés ou modifiés utilisent le même algorithme que le serveur :

`SHA256(DBSecret + password + salt)` avec sel hex 32 caractères.

`DBSecret` doit correspondre à `DBSecret` dans `config.lua` de l'instance Core3.

## Complément SQL

Pour suppressions en CLI : `infra/snippets/core3-delete-account.sql`
