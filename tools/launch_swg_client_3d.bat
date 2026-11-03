@echo off
rem Lance le Client SWG Pre-CU 3D sous Windows
echo [LBG] Lancement du Client SWG Pre-CU 3D (Lost Heaven)...

set GODOT_EXE="J:\mmmorpg\Godot_v4.6.1-stable_win64\Godot_v4.6.1-stable_win64.exe"
if not exist %GODOT_EXE% (
    set GODOT_EXE="godot.exe"
)

%GODOT_EXE% --path "%~dp0..\packages\swg-client" %*

