@echo off
REM Relance Agent_IA sans laisser de terminal ouvert (delegue a VBS fenetre 0).
REM Ne pas utiliser run_agent.cmd pour ca : c'est le mode console debug.
cd /d C:\Agent_IA
wscript.exe //nologo "C:\Agent_IA\restart_agent.vbs"
exit /b 0
