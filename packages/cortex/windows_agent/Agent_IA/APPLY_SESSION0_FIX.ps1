#Requires -RunAsAdministrator
# Applique le correctif Session 0 (scripts + main.py) puis bascule Agent_IA en session bureau.
#
# Usage (PowerShell Admin, session interactive sdesh sur .10) :
#   irm http://192.168.0.100:8765/APPLY_SESSION0_FIX.ps1 | iex
# ou:
#   powershell -NoProfile -ExecutionPolicy Bypass -File C:\Temp\APPLY_SESSION0_FIX.ps1

$ErrorActionPreference = "Stop"
$Base = "http://192.168.0.100:8765"
$Dst = "C:\Agent_IA"
$Tmp = "C:\Temp\Agent_IA_fix_session0"
New-Item -ItemType Directory -Force -Path $Dst, $Tmp | Out-Null

$files = @(
  "main.py",
  "executor.py",
  "repair_vghd_deps.ps1",
  "backup_vghd_deps.ps1",
  "fix_session0_admin.ps1",
  "install_fix_session0_task.ps1",
  "fix_agent_to_user_session.ps1",
  "install_agent_ia_scheduled_tasks.ps1",
  "start_agent.ps1",
  "restart_agent.ps1",
  "agent_ia_process.ps1"
)
foreach ($f in $files) {
  $url = "$Base/$f"
  $out = Join-Path $Tmp $f
  Write-Host "GET $url"
  try {
    Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing
    Copy-Item $out (Join-Path $Dst $f) -Force
    Write-Host "OK -> $Dst\$f"
  } catch {
    Write-Host "WARN skip $f : $_"
  }
}

Write-Host "== reinstall task LBG-AgentIA-fix-session0 (AtLogOn + Compagnon) =="
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Dst "install_fix_session0_task.ps1")

$logonInstall = Join-Path $Dst "install_agent_ia_scheduled_tasks.ps1"
if (Test-Path $logonInstall) {
  Write-Host "== reinstall LBG-AgentIA-logon (session interactive) =="
  try {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $logonInstall
  } catch {
    Write-Host "WARN logon tasks: $_"
  }
}

Write-Host "== bascule session utilisateur =="
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Dst "fix_agent_to_user_session.ps1")
$code = $LASTEXITCODE
if ($code -ne 0) {
  Write-Host "WARN fix_agent exit=$code — tente fix_session0_admin"
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Dst "fix_session0_admin.ps1")
  $code = $LASTEXITCODE
}

Start-Sleep 3
try {
  $h = Invoke-RestMethod http://127.0.0.1:5005/healthz
  Write-Host ("healthz ok service={0}" -f $h.service)
} catch {
  Write-Host "WARN healthz: $_"
}

Write-Host ""
Write-Host "Si OK: Compagnon ouvre vghd sans action manuelle le matin (AtLogOn + auto open_app)."
Write-Host "Sinon voir C:\Agent_IA\logs\fix_session0.log"
exit $code
