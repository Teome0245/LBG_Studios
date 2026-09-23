# Install / vérif alternative Cursor (VS Code + Cline + Continue) — poste Windows
# Usage (PowerShell) :
#   powershell -NoProfile -ExecutionPolicy Bypass -File packages\cortex\infra\scripts\install_editor_alt_windows.ps1

$ErrorActionPreference = "Stop"
$vs = Join-Path $env:LOCALAPPDATA "Programs\Microsoft VS Code\bin\code.cmd"
if (-not (Test-Path $vs)) {
  Write-Host "ERR: VS Code introuvable ($vs). Installe VS Code puis relance."
  exit 1
}

Write-Host "==> Extensions"
& $vs --install-extension continue.continue --force
& $vs --install-extension saoudrizwan.claude-dev --force

Write-Host "==> Continue config (matrice LBG)"
$cont = Join-Path $env:USERPROFILE ".continue"
New-Item -ItemType Directory -Force -Path $cont | Out-Null
# Ne pas écraser si déjà LBG Local
$cfg = Join-Path $cont "config.yaml"
$srcHint = "Voir repo LBG_Studios\packages\cortex\docs\sans_cursor.md"
if (-not (Test-Path $cfg) -or -not (Select-String -Path $cfg -Pattern "LBG Local" -Quiet -ErrorAction SilentlyContinue)) {
  Write-Host "INFO: config.yaml déjà géré ou à coller depuis docs (Continue)."
  Write-Host $srcHint
} else {
  Write-Host "OK Continue config présente (LBG Local)"
}

Write-Host "==> Ollama LAN"
try {
  $t110 = Invoke-RestMethod -Uri "http://192.168.0.110:11434/api/tags" -TimeoutSec 5
  $t111 = Invoke-RestMethod -Uri "http://192.168.0.111:11434/api/tags" -TimeoutSec 5
  Write-Host ("110: " + (($t110.models | ForEach-Object { $_.name }) -join ", "))
  Write-Host ("111: " + (($t111.models | ForEach-Object { $_.name }) -join ", "))
} catch {
  Write-Host "WARN Ollama: $_"
}

Write-Host "==> Agent desktop Session0 tasks"
Get-ScheduledTask -TaskName "LBG-AgentIA-*" -ErrorAction SilentlyContinue |
  ForEach-Object { "{0}  {1}" -f $_.TaskName, $_.State }

Write-Host ""
Write-Host "OK  Ouvre VS Code → Cline : Act=110 gemma-4:12b · Plan=110 qwen:9b (triage=111 0.8B/2B)"
Write-Host "    Doc: packages/cortex/docs/sans_cursor.md · docs/cline/providers.plan-110-9b.json"
