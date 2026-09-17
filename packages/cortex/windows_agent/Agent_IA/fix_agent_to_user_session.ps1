# Bascule Agent_IA hors SYSTEM/Session 0 vers session utilisateur courante (sans fenetre).
# Usage :
#   powershell -NoProfile -ExecutionPolicy Bypass -File C:\Agent_IA\fix_agent_to_user_session.ps1
# Si le kill Session 0 echoue : relancer ce script en PowerShell Admin une fois.

$ErrorActionPreference = "Stop"
Set-Location "C:\Agent_IA"

$sid = [int]([System.Diagnostics.Process]::GetCurrentProcess().SessionId)
Write-Host "session courante=$sid user=$env:USERNAME"
if ($sid -le 0) {
    throw "Ce script doit tourner dans ta session bureau (pas Session 0)."
}

Get-Process vghd -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "stop vghd pid=$($_.Id) session=$($_.SessionId)"
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Agent_IA\install_agent_ia_scheduled_tasks.ps1"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Agent_IA\restart_agent.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARN restart exit=$LASTEXITCODE - si Access Denied sur Session 0, relancer en Admin."
    exit $LASTEXITCODE
}

. "C:\Agent_IA\agent_ia_process.ps1"
$listeners = Get-AgentListeners
$listeners | Format-Table -AutoSize
foreach ($l in $listeners) {
    if ([int]$l.SessionId -eq $sid) {
        Write-Host "OK Agent_IA en session utilisateur pid=$($l.Pid) owner=$($l.Owner)"
        exit 0
    }
}
Write-Error "Agent_IA n ecoute toujours pas dans la session $sid"
exit 1
