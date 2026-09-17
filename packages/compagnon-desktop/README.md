# LBG Compagnon Desktop (Electron) — D2 / D3

App bureau Windows : **tray** + fenêtre chat (`:5174`) + **overlay avatar** FaceRig
+ **notifications d’initiative** (quota strict, jamais d’auto-exec).

Cadrage : [`docs/FOCUS_COMPAGNON.md`](../../docs/FOCUS_COMPAGNON.md).

## Prérequis

- Node 20+ sur le poste **`.10`** (Windows)
- Compagnon UI joignable : http://192.168.0.100:5174/

## Lancer (dev)

Depuis Windows PowerShell (**Node LTS requis** sur `.10`) :

```powershell
cd \\wsl$\Ubuntu\home\sdesh\projects\LBG_Studios\packages\compagnon-desktop
powershell -ExecutionPolicy Bypass -File .\Install-CompagnonDesktop.ps1
```

Le script **copie** le package vers `C:\Agent_IA\compagnon-desktop` (les chemins UNC
`\\wsl$` ne sont pas supportes par `cmd`/`npm`), installe Electron **Windows**
(telecharge le binaire meme si npm bloque les postinstall), puis demarre.

Si Electron casse : `Install-CompagnonDesktop.ps1 -ForceElectron`

Raccourci Bureau :

```powershell
powershell -ExecutionPolicy Bypass -File .\Create-DesktopShortcut.ps1
```

## Build portable

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-CompagnonDesktop.ps1 -Build
```

Sortie : `dist/` (portable Electron Builder).

## Config

`config.json` (à côté de l’exe une fois packagé) :

| Clé | Défaut |
|-----|--------|
| `compagnonUrl` | `http://192.168.0.100:5174/` |
| `overlay.enabled` | `true` |
| `initiative.enabled` | `true` |
| `initiative.maxPerHour` | `3` |
| `initiative.minIntervalSec` | `600` |
| Env `LBG_COMPAGNON_URL` | surcharge l’URL |

## Tray

- Clic / double-clic : chat  
- Menu : ouvrir, overlay, navigateur, quitter  
- Fermer la fenêtre = **masquer** (reste dans le tray)

## Avatar (Desktop Pet)

Petite fenêtre transparente bas-droite (`overlay/`) — bulle « Je vois » + **Agir**
(deep-link `?agir=` → carte Dry-run/Réel). Clic avatar → chat. Jamais d’auto-exec.

## Initiatives (D3)

Poll `proactive/status` via le proxy `:5174`. Si nouvelle initiative et quota OK :
notif Windows + bulle overlay avec **intent Agir-ready**. Clic notif / Agir →
chat avec proposal préremplie. Aucune action poste auto.
