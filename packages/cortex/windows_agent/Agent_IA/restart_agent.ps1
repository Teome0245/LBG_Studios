# Stop + relance Agent_IA :5005 en arrière-plan (sans fenêtre).
# Usage : powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\Agent_IA\restart_agent.ps1

. "$PSScriptRoot\agent_ia_process.ps1"

$log = Join-Path $LogDir "restart_agent.log"
Add-Content -Path $log -Value ("[{0}] restart begin" -f (Get-Date -Format "s"))

$stop = Stop-AgentProcess -LogPath $log
if (-not $stop.ok) {
    Add-Content -Path $log -Value ("[{0}] ABORT port 5005 still in use pids={1}" -f (Get-Date -Format "s"), ($stop.still -join ","))
    exit 2
}

$result = Start-AgentHidden
if (-not (Wait-AgentUp -TimeoutSec 25)) {
    Add-Content -Path $log -Value ("[{0}] WARN started pid={1} but :5005 not up" -f (Get-Date -Format "s"), $result.pid)
    exit 1
}
Add-Content -Path $log -Value ("[{0}] ok listening on 5005 pid={1}" -f (Get-Date -Format "s"), $result.pid)
Write-Output "ok listening on 5005"
exit 0
