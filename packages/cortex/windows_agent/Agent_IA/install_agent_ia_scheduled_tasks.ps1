# Installe demarrage + redemarrage Agent_IA (:5005) pour l'utilisateur courant.
# Lance en arriere-plan (sans fenetre cmd) via start_agent.ps1 / restart_agent.ps1
#
# Usage :
#   powershell -NoProfile -ExecutionPolicy Bypass -File C:\Agent_IA\install_agent_ia_scheduled_tasks.ps1

$ErrorActionPreference = "Stop"
$agentDir = "C:\Agent_IA"
$startPs1 = Join-Path $agentDir "start_agent.ps1"
$restartPs1 = Join-Path $agentDir "restart_agent.ps1"
$startCmd = Join-Path $agentDir "start_agent.cmd"
$restartCmd = Join-Path $agentDir "restart_agent.cmd"

foreach ($p in @($startPs1, $restartPs1, (Join-Path $agentDir "agent_ia_process.ps1"), (Join-Path $agentDir "run_agent.cmd"))) {
    if (-not (Test-Path $p)) { throw "Fichier manquant: $p" }
}

# Retirer le marqueur "telecharge depuis Internet" (evite l'avertissement sur .cmd au demarrage)
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
$lnk.Description = "Demarre Agent_IA :5005 (sans fenetre)"
$lnk.Save()
Write-Host "OK raccourci Demarrage: $lnkPath -> powershell hidden start_agent.ps1"

function Install-SchTask([string]$name, [string[]]$extra) {
    $cmd = @("/Create", "/F", "/TN", $name) + $extra
    & schtasks.exe @cmd | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "schtasks $name exit=$LASTEXITCODE"
    }
}

$failed = @()
try {
    Install-SchTask "LBG-AgentIA-logon" @("/SC", "ONLOGON", "/TR", $startCmd)
} catch {
    $failed += "logon: $_"
}
try {
    Install-SchTask "LBG-AgentIA-restart-morning" @("/SC", "DAILY", "/ST", "08:00", "/TR", $restartCmd)
} catch {
    $failed += "morning: $_"
}
try {
    Install-SchTask "LBG-AgentIA-restart-evening" @("/SC", "DAILY", "/ST", "20:00", "/TR", $restartCmd)
} catch {
    $failed += "evening: $_"
}

if ($failed.Count -gt 0) {
    Write-Host "WARN schtasks (relancer ce script depuis PowerShell Windows si besoin) :"
    $failed | ForEach-Object { Write-Host " - $_" }
} else {
    Write-Host "OK taches Agent_IA :"
    foreach ($n in @("LBG-AgentIA-logon", "LBG-AgentIA-restart-morning", "LBG-AgentIA-restart-evening")) {
        schtasks.exe /Query /TN $n /FO LIST | Select-String -Pattern "TaskName|Status|Next"
    }
}
