# Demarre ComfyUI en arriere-plan (sans fenetre).
# Usage : powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\Agent_IA\start_comfyui.ps1

. "$PSScriptRoot\comfyui_process.ps1"

$conf = Get-ComfyuiConfig
if (Test-ComfyuiListening -Port $conf.port) {
    Write-Output "ComfyUI already listening on $($conf.port)"
    exit 0
}

$result = Start-ComfyuiHidden
if (-not (Wait-ComfyuiUp -Port $conf.port -TimeoutSec 90)) {
    Write-Error "ComfyUI started (pid $($result.pid)) but :$($conf.port) not listening yet - voir C:\Agent_IA\logs\comfyui_agent.log"
    exit 1
}
Write-Output "ComfyUI started hidden pid=$($result.pid) port=$($conf.port)"
exit 0
