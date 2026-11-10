#Requires -Version 5.1
# Creates Desktop + Start Menu shortcut for LBG Compagnon Desktop (local Windows copy).
# Does NOT re-download Electron. Assumes C:\Agent_IA\compagnon-desktop is already installed.
param(
  [string]$Name = "LBG Compagnon Desktop",
  [string]$LocalRoot = $(if ($env:LBG_COMPAGNON_DESKTOP_DIR) { $env:LBG_COMPAGNON_DESKTOP_DIR } else { "C:\Agent_IA\compagnon-desktop" })
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath (Join-Path $LocalRoot "main.js"))) {
  Write-Error "Local app missing: $LocalRoot - run Install-CompagnonDesktop.ps1 first"
}

$node = (Get-Command node.exe -ErrorAction Stop).Source
$electronCli = Join-Path $LocalRoot "node_modules\electron\cli.js"
if (-not (Test-Path -LiteralPath $electronCli)) {
  Write-Error "Electron package missing in $LocalRoot - run: npm.cmd install electron@30 --save-dev"
}

# Resolve real electron.exe via Node (more reliable than path.txt parsing)
$resolveJs = @"
const p = require('electron');
process.stdout.write(String(p || ''));
"@
$tmp = Join-Path $env:TEMP "lbg-resolve-electron.js"
Set-Content -LiteralPath $tmp -Value $resolveJs -Encoding ASCII
$electronExe = & $node -e "process.chdir(process.argv[1]); process.stdout.write(require('electron'))" $LocalRoot
if (-not $electronExe -or -not (Test-Path -LiteralPath $electronExe)) {
  # Fallback: common layout
  $candidate = Join-Path $LocalRoot "node_modules\electron\dist\electron.exe"
  if (Test-Path -LiteralPath $candidate) { $electronExe = $candidate }
}
if (-not $electronExe -or -not (Test-Path -LiteralPath $electronExe)) {
  Write-Error "electron.exe not found. From $LocalRoot run: node .\node_modules\electron\install.js"
}

Write-Host "OK  electron=$electronExe"

$desktop = [Environment]::GetFolderPath("Desktop")
$startMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$targets = @(
  (Join-Path $desktop "$Name.lnk"),
  (Join-Path $startMenu "$Name.lnk")
)

# Shortcut targets Lancer_Compagnon.cmd (with auto-sync from A:) or electron.exe fallback
$launcherCmd = Join-Path $LocalRoot "Lancer_Compagnon.cmd"
$targetExe = if (Test-Path -LiteralPath $launcherCmd) { $launcherCmd } else { $electronExe }
$targetArgs = if ($targetExe -eq $launcherCmd) { "" } else { "`"$LocalRoot`"" }

$wsh = New-Object -ComObject WScript.Shell
foreach ($lnkPath in $targets) {
  $dir = Split-Path -Parent $lnkPath
  if (-not (Test-Path -LiteralPath $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
  }
  $lnk = $wsh.CreateShortcut($lnkPath)
  $lnk.TargetPath = $targetExe
  $lnk.Arguments = $targetArgs
  $lnk.WorkingDirectory = $LocalRoot
  $lnk.WindowStyle = 7 # Minimized window for seamless background sync
  $lnk.Description = "LBG Compagnon Desktop (Electron tray + avatar avec auto-update)"
  $icon = Join-Path $LocalRoot "assets\icon.png"
  if (Test-Path -LiteralPath $icon) { $lnk.IconLocation = $icon }
  else { $lnk.IconLocation = "$electronExe,0" }
  $lnk.Save()
  Write-Host "OK  $lnkPath"
}

Write-Host ""
Write-Host "Launch via shortcut: $Name"
Write-Host "App dir: $LocalRoot"
