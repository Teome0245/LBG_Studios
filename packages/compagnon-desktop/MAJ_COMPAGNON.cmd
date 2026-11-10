@echo off
chcp 65001 >nul
echo ============================================================
echo   Mise a jour & Synchronisation LBG Compagnon Desktop (.10)
echo ============================================================
echo.

echo 1. Fermeture d'Electron en cours...
taskkill /F /IM electron.exe /T >nul 2>&1
timeout /t 1 /nobreak >nul

echo 2. Synchronisation des fichiers VRM, bundle et animations depuis A: vers C:...
:: Sauvegarde prealable de securite de TOUS les modeles VRM perso de C: vers A: (sans ecraser)
if exist "C:\Agent_IA\compagnon-desktop\overlay\vrm\*.vrm" (
    robocopy "C:\Agent_IA\compagnon-desktop\overlay\vrm" "A:\LBG_Studios\packages\compagnon-desktop\overlay\vrm" *.vrm /XC /XN /XO /NFL /NDL /NJH /NJS /nc /ns /np
)
:: Copie des fichiers sans /MIR (utilisation stricte de /E pour ne jamais supprimer de modeles perso)
robocopy "A:\LBG_Studios\packages\compagnon-desktop\overlay" "C:\Agent_IA\compagnon-desktop\overlay" /E /NFL /NDL /NJH /NJS /nc /ns /np
robocopy "A:\LBG_Studios\packages\compagnon-desktop" "C:\Agent_IA\compagnon-desktop" main.js preload.js config.json Lancer_Compagnon.cmd MAJ_COMPAGNON.cmd /NFL /NDL /NJH /NJS /nc /ns /np

echo 3. Relance de l'agent local Agent_IA (:5005)...
if exist "C:\Agent_IA\start_agent.cmd" (
    start "" /b cmd /c "C:\Agent_IA\start_agent.cmd" >nul 2>&1
)

echo 4. Relance de LBG Compagnon Desktop...
start "" "C:\Agent_IA\compagnon-desktop\node_modules\electron\dist\electron.exe" "C:\Agent_IA\compagnon-desktop"

echo.
echo ============================================================
echo   Mise a jour terminee avec succes !
echo ============================================================
timeout /t 3
