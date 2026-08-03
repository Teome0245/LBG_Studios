# Smoke Jeu Prime (O2) — depuis LBG_Studios

## Prérequis

- Serveur Prime **246** up (gateway / login selon config Launchpad)
- Client sur PC Windows : `J:\swgemu\clients\prime-client` (sync depuis ce package)
- Launchpad : `J:\swgemu\dist\win-unpacked\LBG Launchpad.exe` (profil **prime**)

## Checks LAN

```bash
# Surfaces projet (Pilot, Cockpit, Orch, Core3 :8792, patches)
bash ../../tools/smoke_lan_surfaces.sh --functional

# Manifeste patches seul
curl -sf -o /dev/null -w "%{http_code}\n" http://192.168.0.246:8080/patches/prime/manifest.json
# Attendu : 200

# État serveurs (pastilles Launchpad)
curl -s http://192.168.0.246:8792/api/servers | jq .
curl -s http://192.168.0.245:8792/api/servers | jq .
```

UI comptes / état : http://192.168.0.246:8792/ (Prime) · http://192.168.0.245:8792/ (PreCU).  
Doc globale : [`docs/SMOKE_LAN.md`](../../docs/SMOKE_LAN.md).

## Sync client → J:

```bash
bash packages/prime-client/tools/sync_prime_client_to_j.sh
# ou depuis le package :
# bash tools/sync_prime_client_to_j.sh
```

## Lancement

1. Pilot Accueil → **Launchpad** / **Godot** (Desktop hybride), ou Launchpad Windows profil Prime
2. Connexion compte test (ex. Teome) → perso → **Entrer en zone**
3. Attendu : statut LoginPanel `WS connexion…` → `login_result` → monde ; logs `[LbgWs] state=`
4. Si figé >28s : fermer Godot, relancer Launchpad (cache `.godot` régénéré par `sync_prime_client_to_j.sh`)

Smoke HTTP / WS (sans Godot) :

```bash
bash packages/cortex/infra/scripts/smoke_godot_m11_login_lan.sh
# M12 durci : login → WS → zone_state → move (±1.5 m)
bash packages/cortex/infra/scripts/smoke_godot_m12_ws_lan.sh
# M10 craft : catalog skills/schematics sidecar :8791
bash packages/cortex/infra/scripts/smoke_godot_m10_craft_lan.sh
# Bundle owners M11+M12 (+ M9/M10 si godot_client)
bash packages/cortex/infra/scripts/smoke_godot_owners.sh
```

## Doc

- `packages/launchpad/README.md`
- Legacy détaillé : `../new_mmo/launchpad/README.md` (si présent)
