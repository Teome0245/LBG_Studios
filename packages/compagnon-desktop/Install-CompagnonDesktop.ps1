#Requires -Version 5.1
<#
.SYNOPSIS
  Sync + install + launch LBG Compagnon Desktop on Windows (.10).

.DESCRIPTION
  Copies the app to C:\Agent_IA\compagnon-desktop (UNC \\wsl$ is unsupported),
  approves Electron install scripts, downloads the Electron binary, then starts.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File Install-CompagnonDesktop.ps1
  powershell -ExecutionPolicy Bypass -File Install-CompagnonDesktop.ps1 -ForceElectron
#>
param(
  [switch]$Build,
  [switch]$NoStart,
  [switch]$ForceElectron,
  [string]$Url = $(if ($env:LBG_COMPAGNON_URL) { $env:LBG_COMPAGNON_URL } else { "" }),
  [string]$LocalRoot = $(if ($env:LBG_COMPAGNON_DESKTOP_DIR) { $env:LBG_COMPAGNON_DESKTOP_DIR } else { "C:\Agent_IA\compagnon-desktop" })
)

# Do NOT use Stop globally: npm writes warnings to stderr and PowerShell
# would abort NativeCommandError before Electron download finishes.
$ErrorActionPreference = "Continue"

function Resolve-SourceRoot {
  $candidates = @(
    $PSScriptRoot,
    "\\wsl$\Ubuntu\home\sdesh\projects\LBG_Studios\packages\compagnon-desktop",
    "\\wsl.localhost\Ubuntu\home\sdesh\projects\LBG_Studios\packages\compagnon-desktop"
  )
  foreach ($c in $candidates) {
    if (-not $c) { continue }
    $main = Join-Path $c "main.js"
    if (Test-Path -LiteralPath $main) {
      return (Resolve-Path -LiteralPath $c).ProviderPath
    }
  }
  throw "compagnon-desktop source not found (main.js)."
}

function Test-IsUnc([string]$Path) {
  return $Path -like "\\*"
}

function Sync-ToLocal([string]$Source, [string]$Dest) {
  Write-Host "==> Sync $Source -> $Dest"
  New-Item -ItemType Directory -Path $Dest -Force | Out-Null | Out-Null
  & robocopy.exe $Source $Dest /MIR /NFL /NDL /NJH /NJS /nc /ns /np `
    /XD node_modules dist .git `
    /XF "*.log" | Out-Null
  $code = $LASTEXITCODE
  if ($code -ge 8) { throw "robocopy failed with code $code" }
}

function Invoke-Npm {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$NpmArgs)
  $npm = (Get-Command npm.cmd -ErrorAction Stop).Source
  Write-Host ("==> npm " + ($NpmArgs -join " "))
  & cmd.exe /c "`"$npm`" $($NpmArgs -join ' ')"
  return $LASTEXITCODE
}

function Test-ElectronBinary([string]$Root) {
  # 1) Ask Node/require('electron') — canonical
  try {
    $node = (Get-Command node.exe -ErrorAction Stop).Source
    $exe = & $node -e "process.chdir(process.argv[1]); try { process.stdout.write(require('electron')||'') } catch(e) { process.stdout.write('') }" $Root 2>$null
    if ($exe -and (Test-Path -LiteralPath $exe)) {
      Write-Host "OK  electron exe=$exe"
      return $true
    }
  } catch {}

  # 2) path.txt (relative or absolute)
  $pathTxt = Join-Path $Root "node_modules\electron\path.txt"
  if (Test-Path -LiteralPath $pathTxt) {
    try {
      $rel = (Get-Content -LiteralPath $pathTxt -Raw).Trim().Trim('"')
      if ($rel) {
        $candidates = @()
        if ([System.IO.Path]::IsPathRooted($rel)) {
          $candidates += $rel
        } else {
          $base = Join-Path $Root "node_modules\electron"
          $candidates += (Join-Path $base ($rel -replace '/', '\'))
          $candidates += (Join-Path $base "dist\electron.exe")
        }
        foreach ($c in $candidates) {
          if ($c -and (Test-Path -LiteralPath $c)) {
            Write-Host "OK  electron exe=$c"
            return $true
          }
        }
      }
    } catch {}
  }

  # 3) Common Windows layout
  $fallback = Join-Path $Root "node_modules\electron\dist\electron.exe"
  if (Test-Path -LiteralPath $fallback) {
    Write-Host "OK  electron exe=$fallback"
    return $true
  }
  return $false
}

function Approve-ElectronScripts {
  # npm 11+ may require explicit allowScripts for electron postinstall
  $null = Invoke-Npm @("install-scripts", "approve", "electron")
  $null = Invoke-Npm @("install-scripts", "approve", "electron@30.5.1")
  # Also write package.json allowScripts if supported via .npmrc
  $rc = Join-Path (Get-Location) ".npmrc"
  $lines = @(
    "ignore-scripts=false",
    "foreground-scripts=true"
  )
  $lines -join "`r`n" | Set-Content -LiteralPath $rc -Encoding ASCII
}

function Ensure-ElectronBinary([string]$Root) {
  $node = (Get-Command node.exe -ErrorAction Stop).Source
  $cliJs = Join-Path $Root "node_modules\electron\cli.js"
  $installJs = Join-Path $Root "node_modules\electron\install.js"

  Approve-ElectronScripts

  if (-not (Test-Path -LiteralPath $cliJs) -or $ForceElectron) {
    if ($ForceElectron -and (Test-Path -LiteralPath (Join-Path $Root "node_modules\electron"))) {
      Write-Host "==> remove broken node_modules\electron"
      Remove-Item -LiteralPath (Join-Path $Root "node_modules\electron") -Recurse -Force -ErrorAction SilentlyContinue
    }
    $code = Invoke-Npm @("install", "--no-fund", "--no-audit")
    if ($code -ne 0) { throw "npm install failed ($code)" }
  }

  if (-not (Test-Path -LiteralPath $installJs)) {
    Write-Host "==> npm install electron@30 --save-dev"
    $code = Invoke-Npm @("install", "electron@30", "--save-dev", "--no-fund", "--no-audit")
    if ($code -ne 0) { throw "npm install electron failed ($code)" }
  }

  if (-not (Test-ElectronBinary $Root) -or $ForceElectron) {
    Write-Host "==> node node_modules\electron\install.js  (download binary)"
    if (-not (Test-Path -LiteralPath $installJs)) {
      throw "electron/install.js missing"
    }
    # Show full download logs
    & $node $installJs
    $dl = $LASTEXITCODE
    if ($dl -ne 0) {
      throw "electron install.js failed ($dl). Check network / firewall / proxy."
    }
  }

  if (-not (Test-ElectronBinary $Root)) {
    # Dump diagnostics
    $elecDir = Join-Path $Root "node_modules\electron"
    Write-Host "DIAG electron dir:"
    if (Test-Path $elecDir) {
      Get-ChildItem $elecDir | Select-Object -First 30 | ForEach-Object { Write-Host ("  " + $_.Name) }
    } else {
      Write-Host "  (missing)"
    }
    throw "Electron binary still missing after install.js"
  }
  Write-Host "OK  Electron binary ready"
}

$source = Resolve-SourceRoot
Write-Host "OK  source=$source"

$root = $source
if (Test-IsUnc $source) {
  Sync-ToLocal -Source $source -Dest $LocalRoot
  $root = $LocalRoot
} elseif ($env:LBG_COMPAGNON_FORCE_LOCAL -eq "1") {
  Sync-ToLocal -Source $source -Dest $LocalRoot
  $root = $LocalRoot
}

if (-not (Test-Path -LiteralPath (Join-Path $root "main.js"))) {
  throw "main.js missing in $root"
}

Set-Location -LiteralPath $root
Write-Host "OK  root=$root"

if ($Url) {
  $cfgPath = Join-Path $root "config.json"
  if (Test-Path -LiteralPath $cfgPath) {
    $cfg = Get-Content -LiteralPath $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $cfg.compagnonUrl = ($Url.TrimEnd("/") + "/")
    ($cfg | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath $cfgPath -Encoding UTF8
    Write-Host "OK  compagnonUrl=$($cfg.compagnonUrl)"
  }
}

Ensure-ElectronBinary -Root $root

if ($Build) {
  $code = Invoke-Npm @("run", "build:win:portable")
  if ($code -ne 0) { throw "build failed ($code)" }
  Write-Host "OK  dist\ (portable)"
  exit 0
}

if ($NoStart) {
  Write-Host "OK  install done (NoStart)"
  exit 0
}

Write-Host "==> start Electron"
$node = (Get-Command node.exe -ErrorAction Stop).Source
& $node (Join-Path $root "node_modules\electron\cli.js") $root
$code = $LASTEXITCODE
if ($code -ne 0) { throw "Electron exit $code" }
