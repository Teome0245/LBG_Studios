# Compagnon sur le poste `.10` (D1)

Objectif : une **icône Bureau / barre des tâches** qui ouvre le Compagnon comme une mini-app, sans attendre Electron (D2).

## Recommandé — mode app navigateur

Sur Windows (poste **192.168.0.10**) :

```powershell
cd \\wsl$\Ubuntu\home\sdesh\projects\LBG_Studios\packages\cortex\compagnon_ui\desktop
powershell -ExecutionPolicy Bypass -File .\Install-CompagnonShortcut.ps1
```

Le script est en **UTF-8 BOM** (ASCII) pour éviter les erreurs de parsing via `\\wsl$`.

Ça crée **LBG Compagnon** sur le Bureau + menu Démarrer : Edge/Chrome avec `--app=http://192.168.0.100:5174/`.

Alternative immédiate : double-clic `Open-Compagnon.bat`.

Puis : clic droit sur l’icône de la fenêtre → **Épingler à la barre des tâches**.

## PWA (manifest)

Le site `:5174` expose `manifest.webmanifest` + service worker.  
Sur **HTTP LAN**, Chrome n’installe souvent pas l’app (HTTPS requis) — d’où le raccourci `--app=` ci-dessus.

## Suite D2

App Electron (tray + avatar FaceRig) : réutiliser le pattern `packages/launchpad`.
