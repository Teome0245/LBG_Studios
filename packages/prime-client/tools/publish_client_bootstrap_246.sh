#!/usr/bin/env bash
# Publie bootstrap install + installer-manifest + (optionnel) Launchpad zip sur 246:8080
#
# Usage :
#   bash tools/publish_client_bootstrap_246.sh
#   INCLUDE_LAUNCHPAD_ZIP=1 bash tools/publish_client_bootstrap_246.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${ROOT}/../.." && pwd)"
LP_ROOT="${REPO_ROOT}/packages/launchpad"
VM_HOST="${VM_HOST:-192.168.0.246}"
VM_USER="${VM_USER:-lbg}"
REMOTE_ROOT="${REMOTE_ROOT:-/home/lbg/lbg-client-patches}"
PORT="${LBG_CLIENT_PATCH_PORT:-8080}"
STAGE="${STAGE:-${ROOT}/dist/bootstrap-publish}"
INCLUDE_LAUNCHPAD_ZIP="${INCLUDE_LAUNCHPAD_ZIP:-1}"

echo "==> Staging bootstrap"
rm -rf "${STAGE}"
mkdir -p "${STAGE}/bootstrap" "${STAGE}/releases/launchpad" "${STAGE}/releases/godot"

cp "${ROOT}/tools/install_lbg_prime_client.ps1" "${STAGE}/bootstrap/"
cat >"${STAGE}/bootstrap/install.cmd" <<'CMD'
@echo off
setlocal
set URL=http://192.168.0.246:8080/bootstrap/install_lbg_prime_client.ps1
set TARGET=%~1
if "%TARGET%"=="" set TARGET=D:\LBG
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Invoke-WebRequest -Uri '%URL%' -OutFile $env:TEMP\install_lbg_prime_client.ps1 -UseBasicParsing; ^
   & $env:TEMP\install_lbg_prime_client.ps1 -TargetRoot '%TARGET%'"
CMD

# installer-manifest.json (lu par le script PS1)
BUILD_INFO="${ROOT}/assets/build_info.json"
SYNCED_AT="$(python3 -c "import json; print(json.load(open('${BUILD_INFO}')).get('synced_at','') if __import__('pathlib').Path('${BUILD_INFO}').is_file() else '')" 2>/dev/null || echo "")"
if [[ -z "${SYNCED_AT}" ]]; then
  SYNCED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
fi
LP_VER="$(python3 -c "import json; print(json.load(open('${LP_ROOT}/launchpad.config.json')).get('launchpadVersion','2.1.1'))" 2>/dev/null || echo "2.1.1")"

export STAGE VM_HOST PORT SYNCED_AT LP_VER
python3 - <<'PY'
import json
import os
from pathlib import Path

stage = os.environ["STAGE"]
vm_host = os.environ["VM_HOST"]
port = os.environ["PORT"]
synced_at = os.environ["SYNCED_AT"]
lp_ver = os.environ["LP_VER"]

out = Path(stage) / "releases" / "installer-manifest.json"
install_hint = (
    f"irm http://{vm_host}:{port}/bootstrap/install_lbg_prime_client.ps1 "
    r"-OutFile $env:TEMP\install_lbg_prime_client.ps1; "
    r"powershell -ExecutionPolicy Bypass -File $env:TEMP\install_lbg_prime_client.ps1 -TargetRoot D:\LBG"
)
data = {
    "schema": 1,
    "generated_at": synced_at,
    "launchpad_version": lp_ver,
    "godot_version": "4.6.1",
    "patch_server": f"http://{vm_host}:{port}",
    "prime_client_channel": "prime",
    "urls": {
        "bootstrap_ps1": "/bootstrap/install_lbg_prime_client.ps1",
        "bootstrap_cmd": "/bootstrap/install.cmd",
        "launchpad_zip": "/releases/launchpad/LBG-Launchpad-win.zip",
        "launchpad_asar": "/releases/launchpad/app.asar",
        "godot_zip": "/releases/godot/Godot_v4.6.1-stable_win64.zip",
        "prime_manifest": "/patches/prime/manifest.json",
        "prime_build_info": "/patches/prime/build_info.json",
    },
    "smoke": {
        "patch_manifest": f"http://{vm_host}:{port}/patches/prime/manifest.json",
        "sidecar_healthz": f"http://{vm_host}:8791/healthz",
        "gateway_http": f"http://{vm_host}:8765",
        "gateway_ws_port": 50000,
        "status_api": f"http://{vm_host}:8792/api/servers",
    },
    "install_hint": install_hint,
}
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("OK", out)

lp_version_file = Path(stage) / "releases" / "launchpad" / "version.json"
lp_version_file.parent.mkdir(parents=True, exist_ok=True)
lp_version_data = {
    "version": lp_ver,
    "synced_at": synced_at,
    "asar_path": "/releases/launchpad/app.asar",
    "zip_path": "/releases/launchpad/LBG-Launchpad-win.zip",
}
lp_version_file.write_text(json.dumps(lp_version_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("OK", lp_version_file)
PY

echo "==> Build app.asar pour auto-update Launchpad"
node "${LP_ROOT}/scripts/pack_asar.js" "${STAGE}/releases/launchpad"
node "${LP_ROOT}/scripts/pack_asar.js" "${LP_ROOT}/dist/win-unpacked/resources"

if [[ "${INCLUDE_LAUNCHPAD_ZIP}" == "1" && -d "${LP_ROOT}/dist/win-unpacked" ]]; then
  echo "==> Zip Launchpad dist/win-unpacked"
  export LP_ROOT
  python3 - <<'PY'
import os
import zipfile
from pathlib import Path

src = Path(os.environ["LP_ROOT"]) / "dist" / "win-unpacked"
out = Path(os.environ["STAGE"]) / "releases" / "launchpad" / "LBG-Launchpad-win.zip"
out.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    for p in src.rglob("*"):
        if p.is_file():
            zf.write(p, p.relative_to(src.parent))
print("OK", out, "bytes", out.stat().st_size)
PY
else
  echo "SKIP Launchpad zip (build: cd packages/launchpad && npm ci && npm run build:win)"
  cat >"${STAGE}/releases/launchpad/README.txt" <<EOF
Build Launchpad puis republier :
  cd packages/launchpad && npm ci && npm run build:win
  INCLUDE_LAUNCHPAD_ZIP=1 bash packages/prime-client/tools/publish_client_bootstrap_246.sh
EOF
fi

if [[ -f "${STAGE}/releases/godot/Godot_v4.6.1-stable_win64.zip" ]]; then
  echo "OK godot zip déjà présent dans staging"
else
  cat >"${STAGE}/releases/godot/README.txt" <<'EOF'
Placez Godot_v4.6.1-stable_win64.zip ici (miroir LAN) puis republiez :
  releases/godot/Godot_v4.6.1-stable_win64.zip

Sinon l'installateur accepte -GodotExe sur un Godot déjà installé.
EOF
fi

echo "==> rsync bootstrap → ${VM_USER}@${VM_HOST}:${REMOTE_ROOT}/"
rsync -av \
  "${STAGE}/bootstrap/" \
  "${VM_USER}@${VM_HOST}:${REMOTE_ROOT}/bootstrap/"
rsync -av \
  "${STAGE}/releases/" \
  "${VM_USER}@${VM_HOST}:${REMOTE_ROOT}/releases/"

echo "==> Vérification HTTP"
BASE="http://${VM_HOST}:${PORT}"
for path in \
  "/bootstrap/install_lbg_prime_client.ps1" \
  "/releases/installer-manifest.json" \
  "/patches/prime/manifest.json"
do
  code="$(curl -sS -o /dev/null -w '%{http_code}' -m 8 "${BASE}${path}" || echo fail)"
  echo "  ${code}  ${BASE}${path}"
done

echo ""
echo "Nouveau PC Windows (PowerShell) :"
echo "  irm ${BASE}/bootstrap/install_lbg_prime_client.ps1 -OutFile \$env:TEMP\\install_lbg_prime_client.ps1"
echo "  powershell -ExecutionPolicy Bypass -File \$env:TEMP\\install_lbg_prime_client.ps1 -TargetRoot D:\\LBG"
