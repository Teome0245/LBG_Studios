@echo off
REM Agent_IA — mode console (debug). Pour prod / auto : start_agent.ps1 (sans fenêtre).
cd /d C:\Agent_IA
set LBG_DESKTOP_ENV_PATH=C:\Agent_IA\desktop.env
set PYEXE=python
if exist "C:\Agent_IA\.venv\Scripts\python.exe" set PYEXE="C:\Agent_IA\.venv\Scripts\python.exe"
echo [INFO] Mode console — pour arriere-plan : powershell -WindowStyle Hidden -File C:\Agent_IA\start_agent.ps1
%PYEXE% -m uvicorn main:app --host 0.0.0.0 --port 5005
