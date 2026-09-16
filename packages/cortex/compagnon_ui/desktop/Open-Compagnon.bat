@echo off
REM Lance LBG Compagnon en mode app (Edge ou Chrome).
set URL=http://192.168.0.100:5174/
if defined LBG_COMPAGNON_URL set URL=%LBG_COMPAGNON_URL%

if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
  start "" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" --app=%URL%
  exit /b 0
)
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
  start "" "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" --app=%URL%
  exit /b 0
)
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
  start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" --app=%URL%
  exit /b 0
)
start "" "%URL%"
