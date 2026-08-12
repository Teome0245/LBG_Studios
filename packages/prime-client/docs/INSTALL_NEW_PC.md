# Installation Prime — nouveau PC Windows

Installation **idempotente** depuis le LAN (246) : prime-client + cache `.godot` + Launchpad + smoke.

## Prérequis

- Windows 10/11, PowerShell 5.1+
- Accès LAN **`192.168.0.246`** (VPN ou même réseau)
- ~8 Go libres (Godot + client)
- Compte LBG sur Prime (ex. Gally, Teome)

## Installation en une commande

```powershell
irm http://192.168.0.246:8080/bootstrap/install_lbg_prime_client.ps1 -OutFile $env:TEMP\install_lbg_prime_client.ps1
powershell -ExecutionPolicy Bypass -File $env:TEMP\install_lbg_prime_client.ps1 -TargetRoot D:\LBG
```

Ou double-clic sur `install.cmd` (après copie depuis `http://192.168.0.246:8080/bootstrap/install.cmd`).

## Ce que fait l’installateur

1. Télécharge **tous les fichiers** du canal `patches/prime` (manifeste MD5)
2. Installe **Godot 4.6.1** depuis `releases/godot/` (si zip présent) ou `-GodotExe`
3. Génère **`.godot`** (`godot --headless --import`) — obligatoire pour entrer en zone
4. Installe **Launchpad** depuis `releases/launchpad/LBG-Launchpad-win.zip`
5. Écrit **`launchpad.config.json`** avec les chemins **de ce PC**
6. Smoke : ports 8765 / 50000 / 8080, `build_info` local = serveur

## Lancement

```
D:\LBG\dist\win-unpacked\LBG Launchpad.exe
```

Profil **Prime** → **Vérifier MAJ** → **Jouer** → login → **Entrer en zone**.

Attendu : bandeau **CONNECTED** (pas seulement WS OK).

## Options utiles

```powershell
# Godot déjà installé
.\install_lbg_prime_client.ps1 -TargetRoot D:\LBG -GodotExe "C:\Godot\Godot_v4.6.1-stable_win64.exe" -SkipGodot

# MAJ client seulement (Launchpad déjà là)
.\install_lbg_prime_client.ps1 -TargetRoot D:\LBG -SkipLaunchpad -SkipGodot

# Launchpad depuis un dossier local (dev)
.\install_lbg_prime_client.ps1 -LaunchpadSource "J:\swgemu\dist\win-unpacked"
```

## Publier / mettre à jour le bootstrap (dev)

```bash
# Patches prime-client
bash packages/prime-client/tools/deploy_prime_client_patch_246.sh

# Bootstrap + installer-manifest (+ zip Launchpad si dist buildée)
cd packages/launchpad && npm ci && npm run build:win
INCLUDE_LAUNCHPAD_ZIP=1 bash packages/prime-client/tools/publish_client_bootstrap_246.sh
```

### Miroir Godot sur 246 (recommandé)

Copier une fois sur la VM :

```
/home/lbg/lbg-client-patches/releases/godot/Godot_v4.6.1-stable_win64.zip
```

Puis republier le bootstrap (rsync `releases/`).

URLs publiques :

| Ressource | URL |
|-----------|-----|
| Script install | `http://192.168.0.246:8080/bootstrap/install_lbg_prime_client.ps1` |
| Manifest install | `http://192.168.0.246:8080/releases/installer-manifest.json` |
| Patches jeu | `http://192.168.0.246:8080/patches/prime/manifest.json` |

## Dépannage

| Symptôme | Action |
|----------|--------|
| WS OK mais pas CONNECTED | Relancer install (cache `.godot`) ; pas de copie USB manuelle |
| Godot zip 404 | `-GodotExe` ou déposer zip sur 246 `releases/godot/` |
| Launchpad zip 404 | `npm run build:win` + `publish_client_bootstrap_246.sh` |
| build_info différent | Relancer install ou Launchpad « Vérifier MAJ » |

Vérif locale : `packages/prime-client/tools/verify_launchpad_prime.ps1`
