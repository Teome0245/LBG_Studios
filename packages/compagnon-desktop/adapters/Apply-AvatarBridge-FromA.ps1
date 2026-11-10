#Requires -Version 5.1
# ASCII-only (SMB A: + Windows PowerShell 5.1 without UTF-8 BOM).
# Sync compagnon-desktop (bridge D8) from A: (.143) -> C:\Agent_IA then smoke.
param(
  [string]$Source = "A:\LBG_Studios\packages\compagnon-desktop",
  [string]$Dest = "C:\Agent_IA\compagnon-desktop",
  [switch]$Start,
  [switch]$NoStart
)

$ErrorActionPreference = "Stop"

function Write-Ok([string]$m) { Write-Host "OK  $m" }
function Write-Step([string]$m) { Write-Host "==> $m" }

if (-not (Test-Path -LiteralPath (Join-Path $Source "main.js"))) {
  throw "Source introuvable: $Source (A: = \\192.168.0.143\projects ?)"
}
if (-not (Test-Path -LiteralPath (Join-Path $Source "avatar_bridge.js"))) {
  throw "avatar_bridge.js manquant dans $Source - sync Omarchy d'abord."
}

Write-Step "Sync $Source -> $Dest"
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
& robocopy.exe $Source $Dest /E /NFL /NDL /NJH /NJS /nc /ns /np `
  /XD node_modules dist .git `
  /XF "*.log" | Out-Null
$code = $LASTEXITCODE
if ($code -ge 8) { throw "robocopy failed code=$code" }
Write-Ok "files synced (robocopy=$code)"

$bridge = Join-Path $Dest "avatar_bridge.js"
$watch = Join-Path $Dest "adapters\Watch-AvatarBridge.ps1"
if (-not (Test-Path -LiteralPath $bridge)) { throw "missing $bridge" }
if (-not (Test-Path -LiteralPath $watch)) { throw "missing $watch" }
Write-Ok "bridge + Watch-AvatarBridge present"

# Sample VRM (gitignored) - telecharger si absent cote A: et Dest
$vrmSrc = Join-Path $Source "overlay\vrm\default.vrm"
$vrmDst = Join-Path $Dest "overlay\vrm\default.vrm"
$vrmUrl = "https://pixiv.github.io/three-vrm/packages/three-vrm/examples/models/VRM1_Constraint_Twist_Sample.vrm"
New-Item -ItemType Directory -Force -Path (Split-Path $vrmDst) | Out-Null
if (-not (Test-Path -LiteralPath $vrmSrc)) {
  Write-Step "Download sample VRM -> A:"
  try {
    Invoke-WebRequest -Uri $vrmUrl -OutFile $vrmSrc -UseBasicParsing
  } catch {
    Write-Host "WARN VRM download A: $($_.Exception.Message)"
  }
}
if ((Test-Path -LiteralPath $vrmSrc) -and -not (Test-Path -LiteralPath $vrmDst)) {
  Copy-Item -LiteralPath $vrmSrc -Destination $vrmDst -Force
}
if (Test-Path -LiteralPath $vrmDst) {
  Write-Ok ("vrm present size={0}" -f (Get-Item $vrmDst).Length)
} else {
  Write-Host "WARN default.vrm absent - overlay VRM affichera une erreur de chargement"
}

# Toujours reprendre config.json source (evite corruption ConvertTo-Json PowerShell)
$cfgSrc = Join-Path $Source "config.json"
$cfgPath = Join-Path $Dest "config.json"
if (Test-Path -LiteralPath $cfgSrc) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding $false
  $raw = [System.IO.File]::ReadAllText($cfgSrc)
  if ($raw.Length -gt 0 -and [int][char]$raw[0] -eq 0xFEFF) { $raw = $raw.Substring(1) }
  [System.IO.File]::WriteAllText($cfgPath, $raw, $utf8NoBom)
  Write-Ok "config.json copied from A: (no BOM)"
}

$doStart = $Start -or (-not $NoStart)
if ($doStart) {
  Write-Step "Launch Install-CompagnonDesktop.ps1 -NoStart then Electron"
  $install = Join-Path $Dest "Install-CompagnonDesktop.ps1"
  if (Test-Path -LiteralPath $install) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $install -NoStart
  }
  $electronExe = Join-Path $Dest "node_modules\electron\dist\electron.exe"
  if (-not (Test-Path -LiteralPath $electronExe)) {
    Write-Host "WARN electron.exe absent - lance Install-CompagnonDesktop.ps1 une fois"
  } else {
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
      Where-Object {
        $_.Name -match 'electron|Compagnon' -and
        $_.CommandLine -and
        $_.CommandLine -match 'compagnon-desktop'
      } |
      ForEach-Object {
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
      }
    Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
    $p = Start-Process -FilePath $electronExe -ArgumentList "`"$Dest`"" -WorkingDirectory $Dest -PassThru
    Write-Ok "Electron pid=$($p.Id)"
    Start-Sleep -Seconds 3
  }
}

try {
  $st = Invoke-RestMethod -Uri "http://127.0.0.1:8765/avatar/state" -TimeoutSec 4
  Write-Ok ("avatar/state event={0} mood={1}" -f $st.state.event, $st.state.mood)
} catch {
  Write-Host "WARN bridge pas encore joignable: $($_.Exception.Message)"
}

Write-Ok "Apply-AvatarBridge-FromA done"
