# Fonctions partagées — Agent_IA :5005 en arrière-plan (sans fenêtre cmd).
# Usage interne : start_agent.ps1 / restart_agent.ps1

$ErrorActionPreference = "Stop"
$script:AgentDir = "C:\Agent_IA"
$script:LogDir = Join-Path $AgentDir "logs"
$script:AgentLog = Join-Path $LogDir "agent_ia.log"
$script:EnvFile = Join-Path $AgentDir "desktop.env"

function Get-AgentPython {
    $venvPy = Join-Path $AgentDir ".venv\Scripts\python.exe"
    if (Test-Path $venvPy) { return $venvPy }
    return "python"
}

function Test-AgentListening {
    return [bool](Get-NetTCPConnection -LocalPort 5005 -State Listen -ErrorAction SilentlyContinue)
}

function Get-AgentPids {
    $pids = @(
        Get-NetTCPConnection -LocalPort 5005 -State Listen -ErrorAction SilentlyContinue |
            ForEach-Object { [int]$_.OwningProcess } |
            Where-Object { $_ -gt 0 }
    )
    return @($pids | Sort-Object -Unique)
}

function Stop-AgentProcess {
    param([string]$LogPath = $script:AgentLog)
    function W([string]$m) {
        Add-Content -Path $LogPath -Value ("[{0}] {1}" -f (Get-Date -Format "s"), $m)
    }
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    foreach ($agentPid in Get-AgentPids) {
        W "stop pid=$agentPid"
        Stop-Process -Id $agentPid -Force -ErrorAction SilentlyContinue
        & taskkill.exe /F /PID $agentPid /T 2>$null | Out-Null
    }
    $ErrorActionPreference = $prevEap
    Start-Sleep -Seconds 2
    $still = Get-AgentPids
    return @{
        ok     = ($still.Count -eq 0)
        still  = $still
    }
}

function Start-AgentHidden {
    param([string]$LogPath = $script:AgentLog)
    if (-not (Test-Path $script:LogDir)) {
        New-Item -ItemType Directory -Path $script:LogDir -Force | Out-Null
    }
    $py = Get-AgentPython
    $ts = Get-Date -Format "s"
    Add-Content -Path $LogPath -Value "[$ts] start hidden py=$py"

    $env:LBG_DESKTOP_ENV_PATH = $script:EnvFile
    $pyArg = if ($py -match '\s') { "`"$py`"" } else { $py }
    $cmdLine = "$pyArg -m uvicorn main:app --host 0.0.0.0 --port 5005 >> `"$LogPath`" 2>&1"
    $proc = Start-Process -FilePath "cmd.exe" `
        -ArgumentList @("/c", $cmdLine) `
        -WorkingDirectory $script:AgentDir `
        -WindowStyle Hidden `
        -PassThru

    Add-Content -Path $LogPath -Value ("[{0}] started pid={1}" -f (Get-Date -Format "s"), $proc.Id)
    return @{ ok = $true; pid = $proc.Id; python = $py }
}

function Wait-AgentUp {
    param([int]$TimeoutSec = 15)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-AgentListening) { return $true }
        Start-Sleep -Seconds 1
    }
    return $false
}
