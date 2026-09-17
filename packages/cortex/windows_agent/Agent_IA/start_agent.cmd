@echo off
REM Demarre Agent_IA sans laisser de terminal ouvert (delegue a VBS fenetre 0).
cd /d C:\Agent_IA
wscript.exe //nologo "C:\Agent_IA\start_agent.vbs"
exit /b 0
