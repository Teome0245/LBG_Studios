@echo off
chcp 65001 >nul
title LBG Compagnon - Lancement & Synchronisation

set "SRC_DIR=A:\LBG_Studios\packages\compagnon-desktop"
if not exist "%SRC_DIR%\main.js" (
    set "SRC_DIR=\\192.168.0.143\projects\LBG_Studios\packages\compagnon-desktop"
)

:: 1. Synchronisation rapide automatique au lancement (SANS /MIR pour ne jamais effacer les modèles perso)
if exist "%SRC_DIR%\main.js" (
    echo [LBG Compagnon] Verification des mises a jour depuis %SRC_DIR%...
    :: Copie des mises a jour sans suppression (/E copie recursive sans /PURGE)
    robocopy "%SRC_DIR%\overlay" "C:\Agent_IA\compagnon-desktop\overlay" /E /NFL /NDL /NJH /NJS /nc /ns /np
    robocopy "%SRC_DIR%" "C:\Agent_IA\compagnon-desktop" main.js preload.js config.json /NFL /NDL /NJH /NJS /nc /ns /np
    :: Sauvegarde securisee des modeles VRM perso vers le depot s'ils n'y sont pas deja
    if exist "C:\Agent_IA\compagnon-desktop\overlay\vrm\*.vrm" (
        robocopy "C:\Agent_IA\compagnon-desktop\overlay\vrm" "%SRC_DIR%\overlay\vrm" *.vrm /XC /XN /XO /NFL /NDL /NJH /NJS /nc /ns /np
    )
    echo [LBG Compagnon] Synchronisation terminee.
) else (
    echo [LBG Compagnon] Mode local (repo source non detecte).
)

:: 2. Demarrage de l'agent IA local si present
if exist "C:\Agent_IA\start_agent.cmd" (
    start "" /b cmd /c "C:\Agent_IA\start_agent.cmd" >nul 2>&1
)

:: 3. Lancement d'Electron
start "" "C:\Agent_IA\compagnon-desktop\node_modules\electron\dist\electron.exe" "C:\Agent_IA\compagnon-desktop"
exit

