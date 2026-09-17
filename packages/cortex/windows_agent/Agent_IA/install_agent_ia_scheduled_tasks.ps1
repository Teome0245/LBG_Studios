# Installe demarrage + redemarrage Agent_IA (:5005) pour l'utilisateur courant (session interactive).
# - Pas de compte SYSTEM / Session 0
# - Lanceurs PowerShell -WindowStyle Hidden (pas de fenetre cmd)
#
# Usage (depuis ta session sdesh, PowerShell) :
#   powershell -NoProfile -ExecutionPolicy Bypass -File C:\Agent_IA\install_agent_ia_scheduled_tasks.ps1

$ErrorActionPreference = "Stop"
$agentDir = "C:\Agent_IA"
$startPs1 = Join-Path $agentDir "start_agent.ps1"
$restartPs1 = Join-Path $agentDir "restart_agent.ps1"

foreach ($p in @($startPs1, $restartPs1, (Join-Path $agentDir "agent_ia_process.ps1"))) {
    if (-not (Test-Path $p)) { throw "Fichier manquant: $p" }
}

$sid = [int]([System.Diagnostics.Process]::GetCurrentProcess().SessionId)
if ($sid -le 0) {
    throw "Refuse installation depuis Session 0. Ouvre PowerShell dans ta session bureau et relance."
}

$user = $env:USERNAME
if (-not $user) { throw "USERNAME vide" }
$domainUser = if ($env:USERDOMAIN) { "$env:USERDOMAIN\$user" } else { $user }

Get-ChildItem -Path $agentDir -Include *.cmd,*.ps1 -Recurse -ErrorAction SilentlyContinue |
    ForEach-Object { Unblock-File -LiteralPath $_.FullName -ErrorAction SilentlyContinue }

$psHidden = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$startPs1`""
$startup = [Environment]::GetFolderPath("Startup")
$lnkPath = Join-Path $startup "LBG Agent_IA.lnk"
$wsh = New-Object -ComObject WScript.Shell
$lnk = $wsh.CreateShortcut($lnkPath)
$lnk.TargetPath = "powershell.exe"
$lnk.Arguments = $psHidden
$lnk.WorkingDirectory = $agentDir
$lnk.WindowStyle = 7
$lnk.Description = "Demarre Agent_IA :5005 (session utilisateur, sans fenetre)"
$lnk.Save()
Write-Host "OK raccourci Demarrage: $lnkPath"

function Remove-LbgTask([string]$name) {
    $existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "OK removed old task: $name"
    }
}

function Register-LbgUserTask {
    param(
        [string]$Name,
        [string]$ScriptPath,
        [object]$Trigger
    )
    Remove-LbgTask $Name
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument (
        "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`""
    )
    $principal = New-ScheduledTaskPrincipal -UserId $domainUser -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit ([TimeSpan]::Zero) `
        -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $Trigger -Principal $principal -Settings $settings | Out-Null
    Write-Host "OK task $Name user=$domainUser Interactive Limited"
}

$logonTrigger = New-ScheduledTaskTrigger -AtLogOn -User $domainUser
$morningTrigger = New-ScheduledTaskTrigger -Daily -At 08:00
$eveningTrigger = New-ScheduledTaskTrigger -Daily -At 20:00

Register-LbgUserTask -Name "LBG-AgentIA-logon" -ScriptPath $startPs1 -Trigger $logonTrigger
Register-LbgUserTask -Name "LBG-AgentIA-restart-morning" -ScriptPath $restartPs1 -Trigger $morningTrigger
Register-LbgUserTask -Name "LBG-AgentIA-restart-evening" -ScriptPath $restartPs1 -Trigger $eveningTrigger

Write-Host ""
Write-Host "Verification:"
Get-ScheduledTask -TaskName "LBG-AgentIA-*" | ForEach-Object {
    "{0}  user={1}  logon={2}  run={3}  state={4}" -f $_.TaskName, $_.Principal.UserId, $_.Principal.LogonType, $_.Principal.RunLevel, $_.State
}
