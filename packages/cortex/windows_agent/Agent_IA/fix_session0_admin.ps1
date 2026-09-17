#Requires -RunAsAdministrator
# Tue le worker Session 0 (service AgentLocalV0) et relance Agent_IA en session interactive.
$ErrorActionPreference = "Continue"
$log = "C:\Agent_IA\logs\fix_session0.log"
function W($m) {
  New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
  Add-Content $log ("[{0}] {1}" -f (Get-Date -Format s), $m)
  Write-Host $m
}
W "begin session=$([Diagnostics.Process]::GetCurrentProcess().SessionId)"

try {
  Stop-Service AgentLocalV0 -Force -ErrorAction SilentlyContinue
  Set-Service AgentLocalV0 -StartupType Disabled -ErrorAction SilentlyContinue
  W "AgentLocalV0 stopped+disabled"
} catch {
  W "service: $_"
}

$pids = @(
  Get-NetTCPConnection -LocalPort 5005 -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { [int]$_.OwningProcess } | Sort-Object -Unique
)
foreach ($p in $pids) {
  W "taskkill $p"
  taskkill /F /PID $p /T 2>$null | Out-Null
  Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
}
Start-Sleep 2

try {
  Start-ScheduledTask -TaskName "LBG-AgentIA-logon"
  W "started LBG-AgentIA-logon"
} catch {
  W "task: $_"
  # fallback: start as current interactive user via start_agent in a user context is hard from SYSTEM
}

Start-Sleep 6
$c = Get-NetTCPConnection -LocalPort 5005 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($c) {
  $pr = Get-CimInstance Win32_Process -Filter "ProcessId=$($c.OwningProcess)"
  W "listener pid=$($pr.ProcessId) session=$($pr.SessionId)"
} else {
  W "NO_LISTENER — lance manuellement: powershell -File C:\Agent_IA\start_agent.ps1"
}
