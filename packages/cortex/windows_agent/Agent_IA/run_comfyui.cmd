@echo off
REM ComfyUI - mode console (debug). Pour prod : start_comfyui.ps1 (sans fenetre).
cd /d C:\Users\sdesh\ComfyUI
if exist "venv\Scripts\activate.bat" call "venv\Scripts\activate.bat"
echo [INFO] Mode console - pour arriere-plan : powershell -WindowStyle Hidden -File C:\Agent_IA\start_comfyui.ps1
python main.py --listen 0.0.0.0 --port 8188 --lowvram
