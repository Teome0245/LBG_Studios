#Requires -Version 5.1
<#
.SYNOPSIS
  Installe LBG Prime (Godot prime-client + Launchpad) depuis le serveur LAN 246.

.DESCRIPTION
  Télécharge le manifeste patches/prime, applique les fichiers MD5, génère le cache .godot,
  installe/configure le Launchpad et exécute des smokes réseau.

  Source de vérité : http://192.168.0.246:8080/patches/prime/
  Bootstrap publié : http://192.168.0.246:8080/bootstrap/install_lbg_prime_client.ps1

.EXAMPLE
  # Nouveau PC (PowerShell admin ou utilisateur)
  irm http://192.168.0.246:8080/bootstrap/install_lbg_prime_client.ps1 -OutFile $env:TEMP\install_lbg_prime_client.ps1
  powershell -ExecutionPolicy Bypass -File $env:TEMP\install_lbg_prime_client.ps1 -TargetRoot D:\LBG

.EXAMPLE
  # Relance MAJ + import Godot seulement
  .\install_lbg_prime_client.ps1 -TargetRoot D:\LBG -SkipLaunchpad -SkipGodot
#>
[CmdletBinding()]
param(
    [string] $TargetRoot = 'D:\LBG',
    [string] $PatchServerUrl = 'http://192.168.0.246:8080',
    [string] $PrimeHost = '192.168.0.246',
    [string] $PrecuHost = '192.168.0.245',
    [string] $Channel = 'prime',
    [string] $GodotExe = '',
    [string] $LaunchpadZipUrl = '',
    [string] $GodotZipUrl = '',
    [string] $LaunchpadSource = '',
    [int] $MinFreeGb = 8,
    [switch] $SkipLaunchpad,
    [switch] $SkipGodot,
    [switch] $SkipImport,
    [switch] $SkipSmoke
)

$ErrorActionPreference = 'Stop'
$Script:PatchFailures = @()

function Write-Step([string]$Message) {
    Write-Host "[install] $Message" -ForegroundColor Cyan
}

function Write-Ok([string]$Message) {
    Write-Host "[install] OK $Message" -ForegroundColor Green
}

function Write-WarnStep([string]$Message) {
    Write-Host "[install] WARN $Message" -ForegroundColor Yellow
}

function Get-DriveFreeGb([string]$Path) {
    $root = [System.IO.Path]::GetPathRoot($Path)
    if (-not $root) { return $null }
    $di = New-Object System.IO.DriveInfo($root)
    if ($di.IsReady) { return [math]::Round($di.AvailableFreeSpace / 1GB, 1) }
    return $null
}

function Get-FileMd5([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return '' }
    return (Get-FileHash -LiteralPath $Path -Algorithm MD5).Hash.ToLowerInvariant()
}

function Invoke-Download {
    param(
        [string]$Url,
        [string]$Destination,
        [string]$Label
    )
    $dir = Split-Path -Parent $Destination
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    Write-Step "Téléchargement $Label"
    Write-Verbose $Url
    Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing -TimeoutSec 300
}

function Expand-ZipArchive {
    param(
        [string]$ZipPath,
        [string]$Destination
    )
    if (-not (Test-Path -LiteralPath $ZipPath)) {
        throw "Archive introuvable : $ZipPath"
    }
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $Destination -Force
}

function Get-InstallerManifest {
    param([string]$BaseUrl)
    $url = "$BaseUrl/releases/installer-manifest.json"
    try {
        return Invoke-RestMethod -Uri $url -TimeoutSec 12
    } catch {
        Write-WarnStep "installer-manifest.json absent ($url) — valeurs par défaut"
        return $null
    }
}

function Apply-PatchManifest {
    param(
        [string]$GameDir,
        [string]$BaseUrl,
        [string]$PatchChannel
    )
    $manifestUrl = "$BaseUrl/patches/$PatchChannel/manifest.json"
    Write-Step "Patches $PatchChannel depuis $manifestUrl"
    $manifest = Invoke-RestMethod -Uri $manifestUrl -TimeoutSec 30
    if (-not $manifest.files -or $manifest.files.Count -eq 0) {
        throw "Manifeste $PatchChannel vide"
    }
    New-Item -ItemType Directory -Force -Path $GameDir | Out-Null
    $updated = 0
    $skipped = 0
    foreach ($file in $manifest.files) {
        $rel = [string]$file.name
        if ($rel -match '(^|/)\.godot(/|$)') {
            continue
        }
        $dest = Join-Path $GameDir $rel
        $need = $true
        if (Test-Path -LiteralPath $dest) {
            $local = Get-FileMd5 $dest
            if ($local -eq [string]$file.hash) { $need = $false }
        }
        if (-not $need) {
            $skipped++
            continue
        }
        $parent = Split-Path -Parent $dest
        if ($parent -and -not (Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Force -Path $parent | Out-Null
        }
        $urls = @(
            "$BaseUrl/patches/$PatchChannel/$rel",
            "$BaseUrl/patches/$PatchChannel/$($rel -replace '\\','/')"
        )
        $ok = $false
        foreach ($url in $urls) {
            try {
                Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing -TimeoutSec 180
                $got = Get-FileMd5 $dest
                if ($got -ne [string]$file.hash) {
                    throw "Hash invalide après téléchargement ($got != $($file.hash))"
                }
                $ok = $true
                break
            } catch {
                Write-Verbose "Échec $url : $_"
            }
        }
        if (-not $ok) {
            $Script:PatchFailures += $rel
            Write-WarnStep "Impossible de patcher $rel"
            continue
        }
        $updated++
    }
    Write-Ok "prime-client : $updated fichier(s) mis à jour, $skipped déjà à jour"
    return $manifest
}

function Invoke-GodotImport {
    param(
        [string]$GodotPath,
        [string]$ProjectDir
    )
    if (-not (Test-Path -LiteralPath $GodotPath)) {
        throw "Godot introuvable : $GodotPath"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $ProjectDir 'project.godot'))) {
        throw "project.godot absent : $ProjectDir"
    }
    Write-Step "Import Godot (cache .godot) — peut prendre ~1 min"
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $GodotPath
    $psi.Arguments = "--headless --path `"$ProjectDir`" --import --quit-after 60"
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $p = [System.Diagnostics.Process]::Start($psi)
    if (-not $p.WaitForExit(120000)) {
        $p.Kill()
        throw "Import Godot timeout (120s)"
    }
    if ($p.ExitCode -ne 0) {
        $err = $p.StandardError.ReadToEnd()
        throw "Import Godot exit $($p.ExitCode) : $err"
    }
}

function Test-GodotCache {
    param([string]$ProjectDir)
    $cache = Join-Path $ProjectDir '.godot\global_script_class_cache.cfg'
    if (-not (Test-Path -LiteralPath $cache)) {
        return $false, 'global_script_class_cache.cfg absent'
    }
    $txt = Get-Content -LiteralPath $cache -Raw
    if ($txt -notmatch 'EntityManager') { return $false, 'EntityManager absent du cache' }
    if ($txt -notmatch 'LbgWsClient') { return $false, 'LbgWsClient absent du cache' }
    return $true, 'cache OK'
}

function Install-Launchpad {
    param(
        [string]$LaunchpadDir,
        [string]$BaseUrl,
        [string]$ZipUrl,
        [string]$LocalSource
    )
    New-Item -ItemType Directory -Force -Path $LaunchpadDir | Out-Null
    if ($LocalSource -and (Test-Path -LiteralPath $LocalSource)) {
        Write-Step "Copie Launchpad depuis $LocalSource"
        robocopy $LocalSource $LaunchpadDir /MIR /R:2 /W:3 /NFL /NDL /NP /XD node_modules | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "Robocopy Launchpad code $LASTEXITCODE" }
        return
    }
    if (-not $ZipUrl) {
        $ZipUrl = "$BaseUrl/releases/launchpad/LBG-Launchpad-win.zip"
    }
    $zipLocal = Join-Path $env:TEMP 'LBG-Launchpad-win.zip'
    try {
        Invoke-Download -Url $ZipUrl -Destination $zipLocal -Label 'Launchpad'
        $staging = Join-Path $env:TEMP 'LBG-Launchpad-extract'
        if (Test-Path $staging) { Remove-Item -Recurse -Force $staging }
        Expand-ZipArchive -ZipPath $zipLocal -Destination $staging
        $inner = Get-ChildItem -LiteralPath $staging -Directory | Select-Object -First 1
        $src = if ($inner -and (Test-Path (Join-Path $inner.FullName 'LBG Launchpad.exe'))) { $inner.FullName } else { $staging }
        robocopy $src $LaunchpadDir /E /R:2 /W:3 /NFL /NDL /NP | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "Robocopy Launchpad extract code $LASTEXITCODE" }
    } catch {
        throw "Launchpad indisponible sur $ZipUrl — fournis -LaunchpadSource ou copie dist\win-unpacked"
    }
}

function Install-GodotRuntime {
    param(
        [string]$ToolsDir,
        [string]$BaseUrl,
        [string]$ZipUrl,
        [string]$ExistingExe
    )
    if ($ExistingExe -and (Test-Path -LiteralPath $ExistingExe)) {
        return $ExistingExe
    }
    $defaultExe = Join-Path $ToolsDir 'Godot_v4.6.1-stable_win64\Godot_v4.6.1-stable_win64.exe'
    if (Test-Path -LiteralPath $defaultExe) {
        return $defaultExe
    }
    if ($SkipGodot) {
        throw "Godot requis (-GodotExe ou zip releases/godot)"
    }
    if (-not $ZipUrl) {
        $ZipUrl = "$BaseUrl/releases/godot/Godot_v4.6.1-stable_win64.zip"
    }
    $zipLocal = Join-Path $env:TEMP 'Godot_v4.6.1-stable_win64.zip'
    try {
        Invoke-Download -Url $ZipUrl -Destination $zipLocal -Label 'Godot 4.6.1'
        New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null
        Expand-ZipArchive -ZipPath $zipLocal -Destination $ToolsDir
    } catch {
        throw @"
Godot 4.6.1 introuvable sur le serveur ($ZipUrl).
Installe Godot manuellement puis relance avec :
  -GodotExe 'C:\chemin\Godot_v4.6.1-stable_win64.exe'
"@
    }
    if (Test-Path -LiteralPath $defaultExe) { return $defaultExe }
    $found = Get-ChildItem -LiteralPath $ToolsDir -Recurse -Filter 'Godot_v4.6.1-stable_win64.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { return $found.FullName }
    throw "Godot extrait mais exe introuvable sous $ToolsDir"
}

function Write-LaunchpadConfig {
    param(
        [string]$ConfigPath,
        [string]$LaunchpadVersion,
        [string]$PrimeClientDir,
        [string]$GodotExePath,
        [string]$BaseUrl,
        [string]$PrecuGameDir
    )
    $primeDirJson = $PrimeClientDir -replace '\\', '\\'
    $godotJson = $GodotExePath -replace '\\', '\\'
    $precuDirJson = $PrecuGameDir -replace '\\', '\\'
    $cfg = [ordered]@{
        launchpadVersion   = $LaunchpadVersion
        statusApiUrl       = "http://${PrecuHost}:8792/api/servers"
        patchServerUrl     = $BaseUrl
        patchServerUrlNas  = "http://${PrecuHost}:8080"
        diskSpaceWarningGb = 40
        defaultProfileId   = 'prime'
        profiles           = @(
            [ordered]@{
                id               = 'precu'
                label            = 'SWGEmu PreCu (original)'
                clientKind       = 'swgemu'
                gameDir          = $PrecuGameDir
                gameExe          = 'SWGEmu.exe'
                configFile       = 'swgemu.cfg'
                patchChannel     = 'precu'
                servers          = @(@{
                    id        = 'precu'
                    label     = 'LBG SWGEMU PreCu'
                    ip        = $PrecuHost
                    loginPort = 44453
                })
            },
            [ordered]@{
                id                 = 'prime'
                label              = 'LBG Prime (Godot)'
                clientKind         = 'godot'
                gameDir            = $PrimeClientDir
                gameExe            = $GodotExePath
                configFile         = ''
                patchChannel       = 'prime'
                skipPatch          = $true
                godotPatchEnabled  = $true
                godotFullscreen    = $false
                launchArgs         = @('--path', $PrimeClientDir)
                servers            = @(@{
                    id        = 'prime'
                    label     = 'LBG MMO Serveur Prime'
                    ip        = $PrimeHost
                    loginPort = 44553
                })
            }
        )
    }
    $json = ($cfg | ConvertTo-Json -Depth 8)
    Set-Content -LiteralPath $ConfigPath -Value $json -Encoding UTF8
    Write-Ok "launchpad.config.json → $ConfigPath"
}

function Invoke-SmokeTests {
    param(
        [string]$BaseUrl,
        [string]$PrimeClientDir,
        [string]$PrimeHost
    )
    Write-Step 'Smoke réseau + install'
    $fail = 0
    $checks = @(
        @{ name = 'patch manifest'; url = "$BaseUrl/patches/$Channel/manifest.json" },
        @{ name = 'build_info'; url = "$BaseUrl/patches/$Channel/build_info.json" },
        @{ name = 'sidecar'; url = "http://${PrimeHost}:8791/healthz" }
    )
    foreach ($c in $checks) {
        try {
            $r = Invoke-WebRequest -Uri $c.url -UseBasicParsing -TimeoutSec 8
            if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300) {
                Write-Ok $c.name
            } else {
                Write-WarnStep "$($c.name) HTTP $($r.StatusCode)"
                $fail++
            }
        } catch {
            Write-WarnStep "$($c.name) : $_"
            $fail++
        }
    }
    foreach ($port in @(8765, 50000, 8080)) {
        try {
            $t = Test-NetConnection -ComputerName $PrimeHost -Port $port -WarningAction SilentlyContinue
            if ($t.TcpTestSucceeded) {
                Write-Ok "TCP ${PrimeHost}:$port"
            } else {
                Write-WarnStep "TCP ${PrimeHost}:$port fermé"
                $fail++
            }
        } catch {
            Write-WarnStep "TCP ${PrimeHost}:$port : $_"
            $fail++
        }
    }
    $localBi = Join-Path $PrimeClientDir 'assets\build_info.json'
    if (Test-Path -LiteralPath $localBi) {
        try {
            $local = Get-Content -LiteralPath $localBi -Raw | ConvertFrom-Json
            $remote = Invoke-RestMethod -Uri "$BaseUrl/patches/$Channel/build_info.json" -TimeoutSec 8
            if ([string]$local.synced_at -eq [string]$remote.synced_at) {
                Write-Ok "build_info local = serveur ($($local.synced_at))"
            } else {
                Write-WarnStep "build_info différent local=$($local.synced_at) remote=$($remote.synced_at)"
                $fail++
            }
        } catch {
            Write-WarnStep "build_info compare : $_"
            $fail++
        }
    } else {
        Write-WarnStep 'assets/build_info.json local absent'
        $fail++
    }
    $cacheOk, $cacheMsg = Test-GodotCache -ProjectDir $PrimeClientDir
    if ($cacheOk) { Write-Ok $cacheMsg } else { Write-WarnStep $cacheMsg; $fail++ }
    return $fail
}

# --- Main ---
$PatchServerUrl = $PatchServerUrl.TrimEnd('/')
$TargetRoot = $TargetRoot.TrimEnd('\')
$manifestMeta = Get-InstallerManifest -BaseUrl $PatchServerUrl
if ($manifestMeta -and $manifestMeta.patch_server) {
    $PatchServerUrl = [string]$manifestMeta.patch_server.TrimEnd('/')
}
if ($manifestMeta -and $manifestMeta.urls) {
    if (-not $LaunchpadZipUrl -and $manifestMeta.urls.launchpad_zip) {
        $rel = [string]$manifestMeta.urls.launchpad_zip
        $LaunchpadZipUrl = if ($rel.StartsWith('http')) { $rel } else { "$PatchServerUrl$rel" }
    }
    if (-not $GodotZipUrl -and $manifestMeta.urls.godot_zip) {
        $rel = [string]$manifestMeta.urls.godot_zip
        $GodotZipUrl = if ($rel.StartsWith('http')) { $rel } else { "$PatchServerUrl$rel" }
    }
}

$LaunchpadDir = Join-Path $TargetRoot 'dist\win-unpacked'
$PrimeClientDir = Join-Path $TargetRoot 'clients\prime-client'
$ToolsDir = Join-Path $TargetRoot 'tools'
$PrecuDir = Join-Path $TargetRoot 'StarWarsGalaxies'

Write-Host ''
Write-Host '=== LBG Prime — installation bootstrap ===' -ForegroundColor White
Write-Host "  Cible       : $TargetRoot"
Write-Host "  Patch server: $PatchServerUrl"
Write-Host ''

$free = Get-DriveFreeGb $TargetRoot
if ($null -ne $free -and $free -lt $MinFreeGb) {
    Write-WarnStep "Espace libre ~${free} Go — ${MinFreeGb} Go recommandés"
}

New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null

# 1) prime-client via manifeste
$patchManifest = Apply-PatchManifest -GameDir $PrimeClientDir -BaseUrl $PatchServerUrl -PatchChannel $Channel
if ($Script:PatchFailures.Count -gt 0) {
    Write-WarnStep "$($Script:PatchFailures.Count) fichier(s) en échec — relance ou vérifie le réseau LAN"
}

# 2) Godot
$resolvedGodot = Install-GodotRuntime -ToolsDir $ToolsDir -BaseUrl $PatchServerUrl -ZipUrl $GodotZipUrl -ExistingExe $GodotExe
Write-Ok "Godot → $resolvedGodot"

# 3) Import .godot
if (-not $SkipImport) {
    Invoke-GodotImport -GodotPath $resolvedGodot -ProjectDir $PrimeClientDir
    $ok, $msg = Test-GodotCache -ProjectDir $PrimeClientDir
    if (-not $ok) { throw "Cache Godot invalide : $msg" }
    Write-Ok $msg
}

# 4) Launchpad
if (-not $SkipLaunchpad) {
    Install-Launchpad -LaunchpadDir $LaunchpadDir -BaseUrl $PatchServerUrl -ZipUrl $LaunchpadZipUrl -LocalSource $LaunchpadSource
    $lpVersion = '2.1.1'
    if ($manifestMeta -and $manifestMeta.launchpad_version) {
        $lpVersion = [string]$manifestMeta.launchpad_version
    }
    $cfgPath = Join-Path $LaunchpadDir 'launchpad.config.json'
    Write-LaunchpadConfig -ConfigPath $cfgPath -LaunchpadVersion $lpVersion `
        -PrimeClientDir $PrimeClientDir -GodotExePath $resolvedGodot `
        -BaseUrl $PatchServerUrl -PrecuGameDir $PrecuDir
}

# 5) Smoke
$smokeFails = 0
if (-not $SkipSmoke) {
    $smokeFails = Invoke-SmokeTests -BaseUrl $PatchServerUrl -PrimeClientDir $PrimeClientDir -PrimeHost $PrimeHost
}

Write-Host ''
Write-Host '=== Installation terminée ===' -ForegroundColor Green
$launchExe = Join-Path $LaunchpadDir 'LBG Launchpad.exe'
if (Test-Path -LiteralPath $launchExe) {
    Write-Host "  Lancer : $launchExe"
    Write-Host '  Profil Prime → Vérifier MAJ → Jouer → login → Entrer en zone'
} else {
    Write-Host "  Launchpad absent — ouvre Godot :"
    Write-Host "    `"$resolvedGodot`" --path `"$PrimeClientDir`""
}
Write-Host "  prime-client : $PrimeClientDir"
if ($patchManifest.version) {
    Write-Host "  Version patch: $($patchManifest.version)"
}
if ($smokeFails -gt 0) {
    Write-Host ''
    Write-WarnStep "$smokeFails test(s) smoke en échec — vérifie pare-feu / VPN LAN"
    exit 2
}
exit 0
