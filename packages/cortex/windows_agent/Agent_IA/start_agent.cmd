@echo off
REM Wrapper — delegue au lanceur PowerShell sans fenetre.
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Agent_IA\start_agent.ps1"
exit /b %ERRORLEVEL%
