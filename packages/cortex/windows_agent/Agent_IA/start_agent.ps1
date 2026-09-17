# Demarre Agent_IA :5005 en arriere-plan (sans fenetre), session utilisateur courante.
# Usage : powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\Agent_IA\start_agent.ps1

. "$PSScriptRoot\agent_ia_process.ps1"

$sid = Get-CurrentInteractiveSessionId
if ($sid -le 0) {
    Write-Error "Refuse de demarrer Agent_IA depuis Session 0 / service. Lancer depuis une session interactive."
    exit 3
}

if (Test-AgentInCurrentUserSession) {
    Write-Output "Agent_IA already listening on 5005 (session $sid)"
    exit 0
}

if (Test-AgentListening) {
    $listeners = Get-AgentListeners
    $desc = ($listeners | ForEach-Object { "pid=$($_.Pid)/s$($_.SessionId)/$($_.Owner)" }) -join "; "
    Write-Output "Agent_IA on 5005 hors session courante - stop + relance. listeners=$desc"
    $stop = Stop-AgentProcess
    if (-not $stop.ok) {
        Write-Error ("Impossible de liberer :5005 (pids={0}). Relancer ce script en admin une fois." -f ($stop.still -join ","))
        exit 2
    }
}

$result = Start-AgentHidden
if (-not (Wait-AgentUp -TimeoutSec 20)) {
    Write-Error "Agent_IA started (pid $($result.pid)) but :5005 not in session $sid - voir C:\Agent_IA\logs\agent_ia.log"
    exit 1
}

# Best-effort : restaure Qt5Sql.dll VGHD si backup present (updater le casse souvent au reboot)
$repair = "C:\Agent_IA\repair_vghd_deps.ps1"
if (Test-Path $repair) {
    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $repair 2>&1 | Out-Null
    } catch {}
}

Write-Output "Agent_IA started hidden pid=$($result.pid) session=$sid"
exit 0
