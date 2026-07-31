# Smoke Jeu Prime (O2) — depuis LBG_Studios

## Prérequis

- Serveur Prime **246** up (gateway / login selon config Launchpad)
- Client sur PC Windows : `J:\swgemu\clients\prime-client` (sync depuis ce package)
- Launchpad : `J:\swgemu\dist\win-unpacked\LBG Launchpad.exe` (profil **prime**)

## Checks LAN

```bash
# Manifeste patches
curl -sf -o /dev/null -w "%{http_code}\n" http://192.168.0.246:8080/patches/prime/manifest.json
# Attendu : 200
```

## Sync client → J:

```bash
bash packages/prime-client/tools/sync_prime_client_to_j.sh
# ou depuis le package :
# bash tools/sync_prime_client_to_j.sh
```

## Lancement

1. Pilot Accueil → **Launchpad** / **Godot** (Desktop hybride), ou Launchpad Windows profil Prime
2. Connexion compte test → zone (Lost Heaven / Scrapaltai selon build)

## Doc

- `packages/launchpad/README.md`
- Legacy détaillé : `../new_mmo/launchpad/README.md` (si présent)
