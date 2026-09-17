# Stop + relance Agent_IA :5005 en arriere-plan (sans fenetre), session utilisateur courante.
# Usage : powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\Agent_IA\restart_agent.ps1

. "$PSScriptRoot\agent_ia_process.ps1"

$log = Join-Path $LogDir "restart_agent.log"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}
Add-Content -Path $log -Value ("[{0}] restart begin session={1}" -f (Get-Date -Format "s"), (Get-CurrentInteractiveSessionId))

$sid = Get-CurrentInteractiveSessionId
if ($sid -le 0) {
    Add-Content -Path $log -Value ("[{0}] ABORT session 0 / non-interactive" -f (Get-Date -Format "s"))
    Write-Error "Refuse restart depuis Session 0. Lancer depuis la session utilisateur."
    exit 3
}

$stop = Stop-AgentProcess -LogPath $log
if (-not $stop.ok) {
    Add-Content -Path $log -Value ("[{0}] ABORT port 5005 still in use pids={1}" -f (Get-Date -Format "s"), ($stop.still -join ","))
    Write-Error ("Impossible de liberer :5005 (pids={0}). Admin une fois pour tuer Session 0." -f ($stop.still -join ","))
    exit 2
}

$result = Start-AgentHidden
if (-not (Wait-AgentUp -TimeoutSec 25)) {
    Add-Content -Path $log -Value ("[{0}] WARN started pid={1} but :5005 not in session {2}" -f (Get-Date -Format "s"), $result.pid, $sid)
    exit 1
}
Add-Content -Path $log -Value ("[{0}] ok listening on 5005 pid={1} session={2}" -f (Get-Date -Format "s"), $result.pid, $sid)
Write-Output "ok listening on 5005 session=$sid"
exit 0
