#!/usr/bin/env bash
# Smoke Synology DSM WebAPI — stockage + FileStation + Download Station (read-only).
#
# Usage :
#   bash packages/cortex/infra/scripts/smoke_nas_51.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export ROOT_DIR
export PYTHONPATH="${ROOT_DIR}/agents/src:${PYTHONPATH:-}"

PY=python3
if [[ -x "${ROOT_DIR}/agents/.venv/bin/python" ]]; then
  PY="${ROOT_DIR}/agents/.venv/bin/python"
fi

for f in "${ROOT_DIR}/infra/secrets/lbg.env" "${ROOT_DIR}/infra/secrets/nas.env.local"; do
  if [[ -f "$f" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$f"
    set +a
  fi
done

"${PY}" - <<'PY'
import importlib.util
import json
import os
import sys
from pathlib import Path

root = Path(os.environ["ROOT_DIR"])
mod_path = root / "agents" / "src" / "lbg_agents" / "synology_client.py"
spec = importlib.util.spec_from_file_location("synology_client", mod_path)
nas = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(nas)

if not nas.nas_configured():
    print("FAIL: LBG_NAS_PASSWORD absent — renseigner nas.env.local", file=sys.stderr)
    sys.exit(2)

out = nas.probe_nas(include_downloads=True)
print(nas.format_nas_probe_text(out))
print("---")
summary = {
    "ok": out.get("ok"),
    "configured": out.get("configured"),
    "host": out.get("host"),
    "user": out.get("user"),
    "n_shares": out.get("n_shares"),
    "n_download_tasks": out.get("n_download_tasks"),
    "volume_warn": out.get("volume_warn"),
    "volumes": (out.get("storage") or {}).get("volumes"),
    "n_disks": len((out.get("storage") or {}).get("disks") or []),
    "share_names": [s.get("name") for s in (out.get("shares") or [])],
    "error": out.get("error"),
}
print(json.dumps(summary, indent=2, ensure_ascii=False))
sys.exit(0 if out.get("ok") else 1)
PY
