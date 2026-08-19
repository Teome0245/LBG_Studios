@echo off
REM ComfyUI - arriere-plan via start_comfyui.ps1 (sans fenetre).
REM Mode console debug : run_comfyui.cmd
powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Agent_IA\start_comfyui.ps1"
exit /b %ERRORLEVEL%
