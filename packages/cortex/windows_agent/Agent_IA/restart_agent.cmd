@echo off
REM Wrapper — delegue au lanceur PowerShell sans fenetre.
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Agent_IA\restart_agent.ps1"
exit /b %ERRORLEVEL%
