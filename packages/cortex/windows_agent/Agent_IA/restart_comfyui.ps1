# Stop + relance ComfyUI en arriere-plan (sans fenetre).
# Usage : powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\Agent_IA\restart_comfyui.ps1

. "$PSScriptRoot\comfyui_process.ps1"

$conf = Get-ComfyuiConfig
$log = Join-Path $LogDir "restart_comfyui.log"
Add-Content -Path $log -Value ("[{0}] restart begin port={1}" -f (Get-Date -Format "s"), $conf.port)

$stop = Stop-ComfyuiProcess -Port $conf.port -LogPath $log
if (-not $stop.ok) {
    Add-Content -Path $log -Value ("[{0}] ABORT port {1} still in use pids={2}" -f (Get-Date -Format "s"), $conf.port, ($stop.still -join ","))
    exit 2
}

$result = Start-ComfyuiHidden
if (-not (Wait-ComfyuiUp -Port $conf.port -TimeoutSec 90)) {
    Add-Content -Path $log -Value ("[{0}] WARN started pid={1} but :{2} not up" -f (Get-Date -Format "s"), $result.pid, $conf.port)
    exit 1
}
Add-Content -Path $log -Value ("[{0}] ok listening on {1} pid={2}" -f (Get-Date -Format "s"), $conf.port, $result.pid)
Write-Output "ok listening on $($conf.port)"
exit 0
