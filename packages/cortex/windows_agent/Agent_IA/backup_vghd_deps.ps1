# Backup des DLL critiques VGHD vers C:\Agent_IA\app_deps\vghd
# A lancer UNE FOIS juste apres une reinstall qui marche (Qt5Sql.dll present).
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File C:\Agent_IA\backup_vghd_deps.ps1

$ErrorActionPreference = "Stop"
$bin = "C:\Users\sdesh\AppData\Local\vghd\bin"
$dest = "C:\Agent_IA\app_deps\vghd"
$sql = Join-Path $bin "Qt5Sql.dll"

if (-not (Test-Path $sql)) {
    throw "Qt5Sql.dll absent de $bin - reinstalle VGHD d'abord, puis relance ce script."
}

New-Item -ItemType Directory -Path $dest -Force | Out-Null
Copy-Item -Force $sql (Join-Path $dest "Qt5Sql.dll")
Write-Host "OK backup Qt5Sql.dll -> $dest"

$plugins = Join-Path $bin "sqldrivers"
if (Test-Path $plugins) {
    $destPlugins = Join-Path $dest "sqldrivers"
    if (Test-Path $destPlugins) { Remove-Item -Recurse -Force $destPlugins }
    Copy-Item -Recurse -Force $plugins $destPlugins
    Write-Host "OK backup sqldrivers\ -> $destPlugins"
} else {
    Write-Host "WARN sqldrivers\ absent (souvent fourni avec Qt Sql) - backup DLL seule."
}

# Neutralise l'updater qui re-casse l'install au reboot (renommage reversible)
$updater = Join-Path $bin "updater.exe"
$disabled = Join-Path $bin "updater.exe.disabled_by_lbg"
if (Test-Path $updater) {
    if (Test-Path $disabled) {
        Remove-Item -LiteralPath $updater -Force -ErrorAction SilentlyContinue
        Write-Host "OK updater.exe recree supprime (disabled_by_lbg deja present)"
    } else {
        Rename-Item -LiteralPath $updater -NewName "updater.exe.disabled_by_lbg" -Force
        Write-Host "OK updater.exe renomme en updater.exe.disabled_by_lbg (evite wipe post-reboot)"
    }
} elseif (Test-Path $disabled) {
    Write-Host "OK updater deja desactive"
} else {
    Write-Host "WARN updater.exe introuvable"
}

Write-Host "Done. Ensuite: C:\Agent_IA\restart_agent.cmd"
