@echo off
REM Agent_IA — MODE CONSOLE DEBUG uniquement (fenetre qui reste ouverte).
REM Pour relancer en prod SANS terminal :
REM   C:\Agent_IA\restart_agent.cmd
REM   ou: wscript //nologo C:\Agent_IA\restart_agent.vbs
cd /d C:\Agent_IA
set LBG_DESKTOP_ENV_PATH=C:\Agent_IA\desktop.env
set PYEXE=python
if exist "C:\Agent_IA\.venv\Scripts\python.exe" set PYEXE="C:\Agent_IA\.venv\Scripts\python.exe"
echo [INFO] Mode console DEBUG — la fenetre restera ouverte.
echo [INFO] Prod sans fenetre : C:\Agent_IA\restart_agent.cmd
%PYEXE% -m uvicorn main:app --host 0.0.0.0 --port 5005
