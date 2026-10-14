#Requires -RunAsAdministrator
# Installe la tâche élevée LBG-AgentIA-fix-session0.
# - AtLogOn : chaque matin après login (poste éteint la nuit) → coupe AgentLocalV0 + listener S0
# - Compagnon / Start-ScheduledTask : remédiation à la demande sans UAC
#
# Usage (PowerShell Admin, session bureau) :
#   powershell -NoProfile -ExecutionPolicy Bypass -File C:\Agent_IA\install_fix_session0_task.ps1

$ErrorActionPreference = "Stop"
$agentDir = "C:\Agent_IA"
$fixPs1 = Join-Path $agentDir "fix_session0_admin.ps1"
if (-not (Test-Path $fixPs1)) { throw "Manquant: $fixPs1" }

Unblock-File -LiteralPath $fixPs1 -ErrorAction SilentlyContinue

$user = $env:USERNAME
if (-not $user) { throw "USERNAME vide" }
$domainUser = if ($env:USERDOMAIN) { "$env:USERDOMAIN\$user" } else { $user }

$name = "LBG-AgentIA-fix-session0"
$existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false
    Write-Host "OK removed old task: $name"
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument (
    "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$fixPs1`""
)
# Highest = peut tuer le listener Session 0 / désactiver AgentLocalV0
$principal = New-ScheduledTaskPrincipal -UserId $domainUser -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -MultipleInstances Parallel
# Parallel : évite IgnoreNew qui no-opait quand un fantôme « Running » bloquait la remédiation.
# AtLogOn + délai : session bureau prête, service S0 déjà éventuellement démarré au boot.
$logonTrigger = New-ScheduledTaskTrigger -AtLogOn -User $domainUser
$logonTrigger.Delay = "PT45S"
Register-ScheduledTask `
    -TaskName $name `
    -Action $action `
    -Trigger $logonTrigger `
    -Principal $principal `
    -Settings $settings | Out-Null

# Autoriser l'utilisateur courant à démarrer la tâche (même depuis un worker non-admin / Session 0)
try {
    $task = Get-ScheduledTask -TaskName $name
    # SDDL : owner + Authenticated Users peuvent exécuter
    Export-ScheduledTask -TaskName $name | Out-Null
} catch {
    Write-Host "WARN ACL: $_"
}

Write-Host "OK task $name user=$domainUser RunLevel=Highest (AtLogOn + Compagnon)"
Write-Host "Test: Start-ScheduledTask -TaskName $name"
Get-ScheduledTask -TaskName $name | ForEach-Object {
    $tr = ($_ | Get-ScheduledTaskInfo -ErrorAction SilentlyContinue)
    "{0}  user={1}  run={2}  state={3}  triggers={4}" -f `
        $_.TaskName, $_.Principal.UserId, $_.Principal.RunLevel, $_.State, ($_.Triggers.Count)
}
