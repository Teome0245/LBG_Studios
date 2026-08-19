# Démarre Agent_IA :5005 en arrière-plan (sans fenêtre).
# Usage : powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\Agent_IA\start_agent.ps1

. "$PSScriptRoot\agent_ia_process.ps1"

if (Test-AgentListening) {
    Write-Output "Agent_IA already listening on 5005"
    exit 0
}

$result = Start-AgentHidden
if (-not (Wait-AgentUp -TimeoutSec 20)) {
    Write-Error "Agent_IA started (pid $($result.pid)) but :5005 not listening yet - voir C:\Agent_IA\logs\agent_ia.log"
    exit 1
}
Write-Output "Agent_IA started hidden pid=$($result.pid)"
exit 0
