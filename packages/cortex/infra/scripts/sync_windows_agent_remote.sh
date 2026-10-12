#!/usr/bin/env bash
# Pousse Agent_IA vers un PC Windows distant via SMB (C$\Agent_IA_deploy.zip).
#
# Usage:
#   WIN_USER=Teome WIN_PASS='…' bash packages/cortex/infra/scripts/sync_windows_agent_remote.sh
#   WIN_HOST=192.168.0.77 WIN_USER=… WIN_PASS=… bash …
#
# Prérequis: smbclient + zip, compte Windows avec accès //HOST/C$
# Après push: en session bureau sur le PC —
#   Expand-Archive C:\Agent_IA_deploy.zip C:\Temp\Agent_IA_deploy -Force
#   powershell -ExecutionPolicy Bypass -File C:\Temp\Agent_IA_deploy\Agent_IA\INSTALL_ONCE.ps1

set -euo pipefail

HOST="${WIN_HOST:-192.168.0.77}"
USER="${WIN_USER:?definir WIN_USER}"
PASS="${WIN_PASS:?definir WIN_PASS}"
DOMAIN="${WIN_DOMAIN:-}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="${ROOT}/windows_agent/Agent_IA"
STAGE="$(mktemp -d /tmp/agent_ia_remote.XXXXXX)"
ZIP="${STAGE}/Agent_IA_deploy.zip"
trap 'rm -rf "$STAGE"' EXIT

if [ ! -d "$SRC" ]; then
  echo "ERREUR: source introuvable: $SRC" >&2
  exit 1
fi

mkdir -p "${STAGE}/Agent_IA"
rsync -a --exclude='__pycache__' --exclude='tests' --exclude='*.pyc' \
  --exclude='desktop.env' \
  "$SRC/" "${STAGE}/Agent_IA/"
cp -f "$SRC/desktop.env.example" "${STAGE}/Agent_IA/desktop.env.example"

cat > "${STAGE}/Agent_IA/INSTALL_ONCE.ps1" <<'PSEOF'
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Dst = "C:\Agent_IA"
New-Item -ItemType Directory -Force -Path $Dst | Out-Null
Get-ChildItem $Root -Force | Where-Object { $_.Name -ne 'INSTALL_ONCE.ps1' } | ForEach-Object {
  Copy-Item $_.FullName -Destination (Join-Path $Dst $_.Name) -Recurse -Force
}
if (-not (Test-Path (Join-Path $Dst "desktop.env"))) {
  Copy-Item (Join-Path $Dst "desktop.env.example") (Join-Path $Dst "desktop.env") -Force
}
$py = $null
foreach ($c in @("C:\Python\Python314\python.exe","C:\Python\Python313\python.exe","python","py")) {
  try { $v = & $c -c "import sys; print(sys.executable)" 2>$null; if ($LASTEXITCODE -eq 0 -and $v) { $py = $v.Trim(); break } } catch {}
}
if (-not $py) { throw "Python introuvable - installez Python 3.x puis relancez." }
& $py -m pip install -r (Join-Path $Dst "requirements.txt")
try {
  New-NetFirewallRule -DisplayName "LBG Agent_IA 5005" -Direction Inbound -Protocol TCP -LocalPort 5005 -Action Allow -ErrorAction SilentlyContinue | Out-Null
} catch {}
powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File (Join-Path $Dst "start_agent.ps1")
Start-Sleep -Seconds 2
try { Invoke-RestMethod http://127.0.0.1:5005/healthz | ConvertTo-Json -Compress } catch { Write-Host "WARN healthz: $_" }
Write-Host "OK. Optionnel auto-start: powershell -File C:\Agent_IA\install_agent_ia_scheduled_tasks.ps1"
PSEOF

(cd "$STAGE" && zip -qr "$ZIP" Agent_IA)

AUTH_USER="${DOMAIN:+${DOMAIN}/}${USER}"
echo "==> Push $ZIP -> //${HOST}/C\$/Agent_IA_deploy.zip"
smbclient "//${HOST}/C$" -U "${AUTH_USER}%${PASS}" -c "put ${ZIP} Agent_IA_deploy.zip"

echo "OK."
echo
echo "Sur PORTABLE-SDS (RDP / session bureau) :"
echo "  Expand-Archive C:\\Agent_IA_deploy.zip C:\\Temp\\Agent_IA_deploy -Force"
echo "  powershell -NoProfile -ExecutionPolicy Bypass -File C:\\Temp\\Agent_IA_deploy\\Agent_IA\\INSTALL_ONCE.ps1"
echo
echo "Vérif LAN : curl -sf http://${HOST}:5005/healthz"
echo "Orch : desktop_target=portable"
