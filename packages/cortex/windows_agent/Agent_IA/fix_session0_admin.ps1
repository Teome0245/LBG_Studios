#Requires -RunAsAdministrator
# Tue le worker Session 0 (service AgentLocalV0) et relance Agent_IA en session interactive.
# Log: C:\Agent_IA\logs\fix_session0.log
$ErrorActionPreference = "Continue"
$log = "C:\Agent_IA\logs\fix_session0.log"
function W($m) {
  New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
  Add-Content $log ("[{0}] {1}" -f (Get-Date -Format s), $m)
  Write-Host $m
}

$selfSid = [Diagnostics.Process]::GetCurrentProcess().SessionId
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
  [Security.Principal.WindowsBuiltInRole]::Administrator
)
W "begin self_session=$selfSid user=$env:USERNAME elevated=$isAdmin"

# 1) Couper le service qui remet Agent_IA en Session 0
foreach ($svcName in @("AgentLocalV0", "Agent_IA", "LBG-AgentIA")) {
  try {
    $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
    if ($svc) {
      Stop-Service -Name $svcName -Force -ErrorAction SilentlyContinue
      Set-Service -Name $svcName -StartupType Disabled -ErrorAction SilentlyContinue
      W "service $svcName stopped+disabled (was $($svc.Status))"
    }
  } catch {
    W "service $svcName : $_"
  }
}

# 2) Tuer TOUT ce qui écoute :5005 (toutes sessions)
function Get-Listeners5005 {
  @(
    Get-NetTCPConnection -LocalPort 5005 -State Listen -ErrorAction SilentlyContinue |
      ForEach-Object { [int]$_.OwningProcess } |
      Where-Object { $_ -gt 0 } |
      Sort-Object -Unique
  )
}

$pids = Get-Listeners5005
W ("listeners_before={0}" -f (($pids | ForEach-Object { "$_" }) -join ","))
foreach ($p in $pids) {
  try {
    $pr = Get-Process -Id $p -ErrorAction SilentlyContinue
    W ("taskkill pid={0} name={1} session={2}" -f $p, $(if ($pr) { $pr.ProcessName } else { "?" }), $(if ($pr) { $pr.SessionId } else { "?" }))
  } catch {}
  & taskkill.exe /F /PID $p /T 2>$null | Out-Null
  Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 3

$still = Get-Listeners5005
if ($still.Count -gt 0) {
  W ("WARN still listening after kill: {0}" -f ($still -join ","))
  foreach ($p in $still) {
    & taskkill.exe /F /PID $p /T 2>$null | Out-Null
  }
  Start-Sleep -Seconds 2
}

# 3) Relancer en session utilisateur via tâche logon (Interactive)
$started = $false
foreach ($taskName in @("LBG-AgentIA-logon", "LBG-AgentIA-restart-morning")) {
  try {
    $t = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if (-not $t) {
      W "task missing: $taskName"
      continue
    }
    # Éviter IgnoreNew fantôme
    if ($t.State -eq "Running") {
      Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
      Start-Sleep -Seconds 1
    }
    Start-ScheduledTask -TaskName $taskName
    W "started $taskName"
    $started = $true
    break
  } catch {
    W "task $taskName : $_"
  }
}

if (-not $started) {
  # Fallback : start_agent.ps1 dans CETTE session (si on est déjà interactif > 0)
  if ([int]$selfSid -gt 0) {
    W "fallback start_agent.ps1 in session $selfSid"
    try {
      & powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\Agent_IA\start_agent.ps1"
      W "start_agent exit=$LASTEXITCODE"
    } catch {
      W "start_agent: $_"
    }
  } else {
    W "FAIL: pas de tâche logon et self encore Session 0 — impossible de démarrer un GUI agent ici."
    W "ACTION: depuis le bureau, Admin PowerShell: powershell -File C:\Agent_IA\fix_agent_to_user_session.ps1"
    exit 2
  }
}

# 4) Attendre un listener hors Session 0
$ok = $false
$info = "NO_LISTENER"
for ($i = 0; $i -lt 20; $i++) {
  Start-Sleep -Seconds 1
  $c = Get-NetTCPConnection -LocalPort 5005 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $c) { continue }
  try {
    $pr = Get-CimInstance Win32_Process -Filter "ProcessId=$($c.OwningProcess)" -ErrorAction Stop
    $sid = [int]$pr.SessionId
    $info = "listener pid=$($pr.ProcessId) session=$sid"
    W ("probe[$i] $info")
    if ($sid -gt 0) {
      $ok = $true
      break
    }
  } catch {
    W "probe[$i] err: $_"
  }
}

if ($ok) {
  W "OK $info"
  exit 0
}

W "FAIL still Session 0 or no listener — $info"
W "ACTION manuelle (bureau Admin): powershell -File C:\Agent_IA\fix_agent_to_user_session.ps1"
exit 1
