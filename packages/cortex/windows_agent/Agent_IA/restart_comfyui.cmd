@echo off
REM Wrapper - delegue au lanceur PowerShell sans fenetre.
powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Agent_IA\restart_comfyui.ps1"
exit /b %ERRORLEVEL%
