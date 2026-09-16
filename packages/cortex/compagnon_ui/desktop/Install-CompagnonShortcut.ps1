#Requires -Version 5.1
<#
.SYNOPSIS
  Installs "LBG Compagnon" shortcut on the Windows desktop (.10).

.DESCRIPTION
  Opens http://192.168.0.100:5174/ in app mode (no browser chrome)
  via Microsoft Edge or Chrome (--app=). D1 before Electron D2.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File Install-CompagnonShortcut.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File Install-CompagnonShortcut.ps1 -Url "http://192.168.0.100:5174/"
#>
param(
  [string]$Url = $(if ($env:LBG_COMPAGNON_URL) { $env:LBG_COMPAGNON_URL } else { "http://192.168.0.100:5174/" }),
  [string]$Name = "LBG Compagnon",
  [switch]$StartMenuOnly
)

$ErrorActionPreference = "Stop"
$Url = $Url.TrimEnd("/") + "/"

function Find-Browser {
  $candidates = @(
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
  )
  foreach ($p in $candidates) {
    if ($p -and (Test-Path -LiteralPath $p)) { return $p }
  }
  return $null
}

$browser = Find-Browser
if (-not $browser) {
  Write-Error "Neither Edge nor Chrome found. Open $Url manually, then Pin to taskbar."
}

$desktop = [Environment]::GetFolderPath("Desktop")
$startMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$targets = @()
if (-not $StartMenuOnly) { $targets += (Join-Path $desktop "$Name.lnk") }
$targets += (Join-Path $startMenu "$Name.lnk")

$wsh = New-Object -ComObject WScript.Shell
foreach ($lnkPath in $targets) {
  $dir = Split-Path -Parent $lnkPath
  if (-not (Test-Path -LiteralPath $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
  }
  $lnk = $wsh.CreateShortcut($lnkPath)
  $lnk.TargetPath = $browser
  $lnk.Arguments = "--app=$Url"
  $lnk.WorkingDirectory = Split-Path -Parent $browser
  $lnk.WindowStyle = 1
  $lnk.Description = "Compagnon LBG Studios - chat Studio (.100:5174)"
  $lnk.IconLocation = "$browser,0"
  $lnk.Save()
  Write-Host "OK  $lnkPath"
}

Write-Host ""
Write-Host "Compagnon : $Url"
Write-Host "Double-click the Desktop / Start Menu shortcut (app window, no URL bar)."
Write-Host "Pin: right-click the window icon -> Pin to taskbar."
