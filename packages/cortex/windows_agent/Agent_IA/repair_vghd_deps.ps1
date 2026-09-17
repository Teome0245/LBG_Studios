# Restaure Qt5Sql.dll (et sqldrivers) depuis C:\Agent_IA\app_deps\vghd si manquants.
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File C:\Agent_IA\repair_vghd_deps.ps1

$ErrorActionPreference = "Stop"
$bin = "C:\Users\sdesh\AppData\Local\vghd\bin"
$srcRoot = "C:\Agent_IA\app_deps\vghd"
$sqlSrc = Join-Path $srcRoot "Qt5Sql.dll"
$sqlDst = Join-Path $bin "Qt5Sql.dll"

if (-not (Test-Path $bin)) {
    throw "Dossier VGHD introuvable: $bin"
}

if (Test-Path $sqlDst) {
    Write-Host "OK Qt5Sql.dll deja present"
} elseif (Test-Path $sqlSrc) {
    Copy-Item -Force $sqlSrc $sqlDst
    Write-Host "OK restore Qt5Sql.dll depuis backup"
} else {
    throw "Pas de backup ($sqlSrc). Reinstalle VGHD puis lance backup_vghd_deps.ps1"
}

$pluginsSrc = Join-Path $srcRoot "sqldrivers"
$pluginsDst = Join-Path $bin "sqldrivers"
if ((Test-Path $pluginsSrc) -and -not (Test-Path $pluginsDst)) {
    Copy-Item -Recurse -Force $pluginsSrc $pluginsDst
    Write-Host "OK restore sqldrivers\"
}

$updater = Join-Path $bin "updater.exe"
$disabled = Join-Path $bin "updater.exe.disabled_by_lbg"
if ((Test-Path $updater) -and -not (Test-Path $disabled)) {
    Rename-Item -LiteralPath $updater -NewName "updater.exe.disabled_by_lbg"
    Write-Host "OK updater.exe desactive"
}

Write-Host "Done."
