# UI web — gestion des comptes Core3

Module : `packages/cortex/tools/core3_account_admin/`

## Accès (VM LAN)

Après déploiement :

```bash
# PreCU 245 — pastille swgemu seule
bash packages/cortex/infra/scripts/start_core3_account_admin_vm.sh

# Prime 246 — pastille prime (core3-clean) seule
bash packages/cortex/infra/scripts/start_core3_account_admin_prime_vm.sh
```

- URL PreCU : **http://192.168.0.245:8792/** · Prime : **http://192.168.0.246:8792/**
- Token par défaut des scripts : `lbg-core3-admin-change-me` (surcharge : `CORE3_ADMIN_TOKEN=…`)
- **État des serveurs Core3** (bandeau en haut, rafraîchi toutes les 15 s) : `GET /api/servers` — **une pastille par VM** (`CORE3_LOCAL_SERVER_ID`) : PreCU (`core3-swgemu`, 245) ou Prime (`core3-clean`, 246). Chaque pastille affiche **IP client** (`client_ip`), statut (*En ligne* / *Démarrage* / *Hors ligne*), port login et PID. La gestion comptes MariaDB distante reste optionnelle (`CORE3_PRIME_DB_*` / `CORE3_PRECU_DB_*`).

## Démarrage automatique au reboot (systemd)

Sur la VM, l’UI peut être gérée par systemd pour être relancée automatiquement après reboot :

```bash
ssh lbg@192.168.0.245 'systemctl status lbg-core3-account-admin.service --no-pager'
ssh lbg@192.168.0.245 'systemctl is-enabled lbg-core3-account-admin.service'
```

À retenir :

- Le port `:8792` peut être occupé si l’UI a été lancée en `nohup`. Dans ce cas, tuer l’ancien process (`pkill -f core3_account_admin.py`) puis redémarrer le service systemd.
- Secrets : `/etc/lbg-core3-account-admin.env` (`CORE3_DB_PASS`, `CORE3_ADMIN_TOKEN`). Sans token, l’écoute `0.0.0.0:8792` est refusée.
- Après split VM : PreCU sondé en `127.0.0.1` (client `192.168.0.245`), Prime via SSH `192.168.0.246` (client `192.168.0.246`). Clé SSH 245→246 installée par `start_core3_account_admin_vm.sh`.

## Alignement Core3

Les mots de passe créés ou modifiés utilisent le même algorithme que le serveur :

`SHA256(DBSecret + password + salt)` avec sel hex 32 caractères.

`DBSecret` doit correspondre à `DBSecret` dans `config.lua` de l'instance Core3.

## Complément SQL

Pour suppressions en CLI : `infra/snippets/core3-delete-account.sql`
