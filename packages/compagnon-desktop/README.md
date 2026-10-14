# LBG Compagnon Desktop (Electron) — D2 / D3

App bureau Windows : **tray** + fenêtre chat (`:5174`) + **overlay avatar** FaceRig
+ **notifications d’initiative** (quota strict, jamais d’auto-exec).

Cadrage : [`docs/FOCUS_COMPAGNON.md`](../../docs/FOCUS_COMPAGNON.md).

## Prérequis

- Node 20+ sur le poste **`.10`** (Windows)
- Compagnon UI joignable : http://192.168.0.100:5174/

## Lancer (dev)

Depuis Windows PowerShell (**Node LTS requis** sur `.10`) :

Sur le poste **`.10`**, le repo Omarchy est monté en **`A:`**
(`\\192.168.0.143\projects`) :

```powershell
# Bridge D8 + sync (préféré)
powershell -ExecutionPolicy Bypass -File A:\LBG_Studios\packages\compagnon-desktop\adapters\Apply-AvatarBridge-FromA.ps1 -Start

# Ou install complète Electron
cd A:\LBG_Studios\packages\compagnon-desktop
powershell -ExecutionPolicy Bypass -File .\Install-CompagnonDesktop.ps1
```

Le script **copie** le package vers `C:\Agent_IA\compagnon-desktop` (évite les
UNC/`\\wsl$` pour `npm`), installe Electron **Windows**, puis démarre.

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

Modes (`config.json` → `overlay.mode`) :

| mode | Rendu |
|------|--------|
| `vrm` (défaut) | Perso 3D three-vrm — `overlay/vrm/` |
| `face` | FaceRig 2D (Lyra) |

Tray : **Avatar mode: VRM 3D** / **FaceRig 2D**. Remplacer `overlay/vrm/default.vrm` par ton modèle VRoid.

## Initiatives (D3)

Poll `proactive/status` via le proxy `:5174`. Si nouvelle initiative et quota OK :
notif Windows + bulle overlay avec **intent Agir-ready**. Clic notif / Agir →
chat avec proposal préremplie. Aucune action poste auto.

## Présence Agents (D7)

Bandeau session + Allow/Deny (ADR 0027). Opt-in dans `config.json` :

```json
"sessionIsland": {
  "enabled": true,
  "streamUrl": "http://192.168.0.143:5005/session/stream",
  "decisionUrl": "http://192.168.0.143:5005/session/decision"
}
```

Le process Electron s’abonne au SSE et forward vers l’overlay (pas de CSP réseau dans le renderer).
Runbook : `packages/cortex/docs/runbook_session_island_d7.md`.

## Avatar bridge (VRM / Mate Engine)

Bus local loopback pour piloter un rendu externe **sans** remplacer le cerveau `:5174`.

Contrat : [`packages/cortex/docs/avatar_presence_events_v1.md`](../cortex/docs/avatar_presence_events_v1.md)  
Adaptateurs : [`adapters/README.md`](adapters/README.md)

```json
"avatarBridge": {
  "enabled": true,
  "host": "127.0.0.1",
  "port": 8765
}
```

- `GET http://127.0.0.1:8765/avatar/state` — snapshot  
- `GET http://127.0.0.1:8765/avatar/stream` — SSE (`avatar.mood` · `talking` · `initiative`)  
- TTS du chat Electron → `notifyPresence` → bridge + FaceRig overlay  

Smoke : `powershell -ExecutionPolicy Bypass -File .\adapters\Watch-AvatarBridge.ps1`
