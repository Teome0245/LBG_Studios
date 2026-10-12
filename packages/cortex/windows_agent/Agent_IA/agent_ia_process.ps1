# Fonctions partagees - Agent_IA :5005 en arriere-plan (sans fenetre cmd).
# Usage interne : start_agent.ps1 / restart_agent.ps1

$ErrorActionPreference = "Stop"
$script:AgentDir = "C:\Agent_IA"
$script:LogDir = Join-Path $AgentDir "logs"
$script:AgentLog = Join-Path $LogDir "agent_ia.log"
$script:AgentOutLog = Join-Path $LogDir "agent_ia.out.log"
$script:AgentErrLog = Join-Path $LogDir "agent_ia.err.log"
$script:EnvFile = Join-Path $AgentDir "desktop.env"
$script:AgentPort = 5005

function Get-AgentPython {
    $venvPy = Join-Path $AgentDir ".venv\Scripts\pythonw.exe"
    if (Test-Path $venvPy) { return $venvPy }
    $venvPy2 = Join-Path $AgentDir ".venv\Scripts\python.exe"
    if (Test-Path $venvPy2) { return $venvPy2 }
    # Installs silencieux typiques (éviter le stub Microsoft Store "python")
    foreach ($candidate in @(
            "C:\Python\Python314\python.exe",
            "C:\Python\Python313\python.exe",
            "C:\Python\Python312\python.exe",
            "C:\Python\Python311\python.exe"
        )) {
        if (Test-Path $candidate) { return $candidate }
    }
    $sysW = (Get-Command pythonw.exe -ErrorAction SilentlyContinue)
    if ($sysW -and $sysW.Source -and ($sysW.Source -notmatch 'WindowsApps')) { return $sysW.Source }
    $sys = (Get-Command python.exe -ErrorAction SilentlyContinue)
    if ($sys -and $sys.Source -and ($sys.Source -notmatch 'WindowsApps')) { return $sys.Source }
    return "python"
}

function Get-CurrentInteractiveSessionId {
    try {
        return [int]([System.Diagnostics.Process]::GetCurrentProcess().SessionId)
    } catch {
        return -1
    }
}

function Get-ProcessOwnerName {
    param([int]$ProcessId)
    try {
        $p = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop
        $o = Invoke-CimMethod -InputObject $p -MethodName GetOwner -ErrorAction Stop
        if ($o -and $o.ReturnValue -eq 0 -and $o.User) {
            return "$($o.Domain)\$($o.User)"
        }
    } catch {}
    return $null
}

function Test-AgentListening {
    return [bool](Get-NetTCPConnection -LocalPort $script:AgentPort -State Listen -ErrorAction SilentlyContinue)
}

function Get-AgentListeners {
    $rows = @()
    $conns = @(Get-NetTCPConnection -LocalPort $script:AgentPort -State Listen -ErrorAction SilentlyContinue)
    foreach ($c in $conns) {
        $procId = [int]$c.OwningProcess
        if ($procId -le 0) { continue }
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        $rows += [PSCustomObject]@{
            Pid       = $procId
            Name      = if ($proc) { $proc.ProcessName } else { "?" }
            SessionId = if ($proc) { [int]$proc.SessionId } else { -1 }
            Owner     = Get-ProcessOwnerName -ProcessId $procId
        }
    }
    return @($rows | Sort-Object Pid -Unique)
}

function Get-AgentPids {
    return @(Get-AgentListeners | ForEach-Object { [int]$_.Pid } | Where-Object { $_ -gt 0 } | Sort-Object -Unique)
}

function Test-AgentInCurrentUserSession {
    $want = Get-CurrentInteractiveSessionId
    if ($want -le 0) { return $false }
    foreach ($l in @(Get-AgentListeners)) {
        if ([int]$l.SessionId -eq $want) { return $true }
    }
    return $false
}

function Stop-AgentProcess {
    param([string]$LogPath = $script:AgentLog)
    function W([string]$m) {
        Add-Content -Path $LogPath -Value ("[{0}] {1}" -f (Get-Date -Format "s"), $m)
    }
    if (-not (Test-Path $script:LogDir)) {
        New-Item -ItemType Directory -Path $script:LogDir -Force | Out-Null
    }
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    foreach ($agentPid in Get-AgentPids) {
        $info = Get-AgentListeners | Where-Object { $_.Pid -eq $agentPid } | Select-Object -First 1
        W ("stop pid={0} session={1} owner={2}" -f $agentPid, $(if ($info) { $info.SessionId } else { "?" }), $(if ($info) { $info.Owner } else { "?" }))
        Stop-Process -Id $agentPid -Force -ErrorAction SilentlyContinue
        & taskkill.exe /F /PID $agentPid /T 2>$null | Out-Null
    }
    $ErrorActionPreference = $prevEap
    Start-Sleep -Seconds 2
    $still = Get-AgentPids
    return @{
        ok    = ($still.Count -eq 0)
        still = $still
    }
}

function Start-AgentHidden {
    param([string]$LogPath = $script:AgentLog)
    if (-not (Test-Path $script:LogDir)) {
        New-Item -ItemType Directory -Path $script:LogDir -Force | Out-Null
    }
    $py = Get-AgentPython
    $ts = Get-Date -Format "s"
    $sid = Get-CurrentInteractiveSessionId
    Add-Content -Path $LogPath -Value "[$ts] start hidden py=$py session=$sid (no cmd window)"

    $env:LBG_DESKTOP_ENV_PATH = $script:EnvFile

    $argList = @(
        "-m", "uvicorn", "main:app",
        "--host", "0.0.0.0",
        "--port", "$($script:AgentPort)"
    )
    $proc = Start-Process -FilePath $py `
        -ArgumentList $argList `
        -WorkingDirectory $script:AgentDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput $script:AgentOutLog `
        -RedirectStandardError $script:AgentErrLog `
        -PassThru

    Add-Content -Path $LogPath -Value ("[{0}] started pid={1} session={2}" -f (Get-Date -Format "s"), $proc.Id, $sid)
    return @{ ok = $true; pid = $proc.Id; python = $py; session = $sid }
}

function Wait-AgentUp {
    param([int]$TimeoutSec = 15)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-AgentInCurrentUserSession) { return $true }
        Start-Sleep -Seconds 1
    }
    return $false
}
