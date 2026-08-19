# Fonctions partagees - ComfyUI en arriere-plan (sans fenetre cmd).
# Usage interne : start_comfyui.ps1 / restart_comfyui.ps1

$ErrorActionPreference = "Stop"
$script:AgentDir = "C:\Agent_IA"
$script:LogDir = Join-Path $AgentDir "logs"
$script:ComfyLog = Join-Path $LogDir "comfyui_agent.log"
$script:EnvFile = Join-Path $AgentDir "desktop.env"

function Read-DesktopEnv {
    param([string]$Path = $script:EnvFile)
    $map = @{}
    if (-not (Test-Path $Path)) { return $map }
    Get-Content -LiteralPath $Path -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }
        $idx = $line.IndexOf("=")
        if ($idx -lt 1) { return }
        $k = $line.Substring(0, $idx).Trim()
        $v = $line.Substring($idx + 1).Trim()
        $map[$k] = $v
    }
    return $map
}

function Get-ComfyuiConfig {
    $cfg = Read-DesktopEnv
    $root = if ($cfg["LBG_COMFYUI_ROOT"]) { $cfg["LBG_COMFYUI_ROOT"] } else { "C:\Users\sdesh\ComfyUI" }
    $py = if ($cfg["LBG_COMFYUI_PYTHON"]) { $cfg["LBG_COMFYUI_PYTHON"] } else { Join-Path $root "venv\Scripts\python.exe" }
    $args = if ($cfg["LBG_COMFYUI_ARGS"]) { $cfg["LBG_COMFYUI_ARGS"] } else { "--listen 0.0.0.0 --port 8188 --lowvram" }
    $port = 8188
    if ($cfg["LBG_COMFYUI_PORT"] -match "^\d+$") {
        $port = [int]$cfg["LBG_COMFYUI_PORT"]
    } elseif ($args -match "--port\s+(\d+)") {
        $port = [int]$Matches[1]
    } elseif ($cfg["LBG_COMFYUI_BASE_URL"] -match ":(\d+)") {
        $port = [int]$Matches[1]
    }
    return @{
        root = $root
        python = $py
        args = $args
        port = $port
    }
}

function Test-ComfyuiListening {
    param([int]$Port = (Get-ComfyuiConfig).port)
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Get-ComfyuiPids {
    param([int]$Port = (Get-ComfyuiConfig).port)
    $pids = @(
        Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
            ForEach-Object { [int]$_.OwningProcess } |
            Where-Object { $_ -gt 0 }
    )
    return @($pids | Sort-Object -Unique)
}

function Stop-ComfyuiProcess {
    param(
        [int]$Port = (Get-ComfyuiConfig).port,
        [string]$LogPath = $script:ComfyLog
    )
    function W([string]$m) {
        Add-Content -Path $LogPath -Value ("[{0}] {1}" -f (Get-Date -Format "s"), $m)
    }
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    foreach ($comfyPid in Get-ComfyuiPids -Port $Port) {
        W "stop pid=$comfyPid port=$Port"
        Stop-Process -Id $comfyPid -Force -ErrorAction SilentlyContinue
        & taskkill.exe /F /PID $comfyPid /T 2>$null | Out-Null
    }
    $ErrorActionPreference = $prevEap
    Start-Sleep -Seconds 2
    $still = Get-ComfyuiPids -Port $Port
    return @{
        ok    = ($still.Count -eq 0)
        still = $still
        port  = $Port
    }
}

function Start-ComfyuiHidden {
    param([string]$LogPath = $script:ComfyLog)
    $conf = Get-ComfyuiConfig
    if (-not (Test-Path $conf.root)) {
        throw "LBG_COMFYUI_ROOT introuvable: $($conf.root)"
    }
    if (-not (Test-Path $conf.python)) {
        throw "Python ComfyUI introuvable: $($conf.python)"
    }
    if (-not (Test-Path $script:LogDir)) {
        New-Item -ItemType Directory -Path $script:LogDir -Force | Out-Null
    }
    $ts = Get-Date -Format "s"
    Add-Content -Path $LogPath -Value "[$ts] start hidden py=$($conf.python) root=$($conf.root) args=$($conf.args)"

    $pyArg = if ($conf.python -match '\s') { "`"$($conf.python)`"" } else { $conf.python }
    $cmdLine = "$pyArg main.py $($conf.args) >> `"$LogPath`" 2>&1"
    $proc = Start-Process -FilePath "cmd.exe" `
        -ArgumentList @("/c", $cmdLine) `
        -WorkingDirectory $conf.root `
        -WindowStyle Hidden `
        -PassThru

    Add-Content -Path $LogPath -Value ("[{0}] started pid={1}" -f (Get-Date -Format "s"), $proc.Id)
    return @{
        ok     = $true
        pid    = $proc.Id
        python = $conf.python
        root   = $conf.root
        port   = $conf.port
    }
}

function Wait-ComfyuiUp {
    param(
        [int]$Port = (Get-ComfyuiConfig).port,
        [int]$TimeoutSec = 90
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-ComfyuiListening -Port $Port) { return $true }
        Start-Sleep -Seconds 2
    }
    return $false
}
