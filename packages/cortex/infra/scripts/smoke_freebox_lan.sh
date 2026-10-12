#!/usr/bin/env bash
# Smoke Freebox OS API — baux DHCP + audit vs plan lab (read-only).
#
# Usage :
#   bash packages/cortex/infra/scripts/smoke_freebox_lan.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export ROOT_DIR
export PYTHONPATH="${ROOT_DIR}/agents/src:${PYTHONPATH:-}"

PY=python3
if [[ -x "${ROOT_DIR}/agents/.venv/bin/python" ]]; then
  PY="${ROOT_DIR}/agents/.venv/bin/python"
fi

for f in "${ROOT_DIR}/infra/secrets/lbg.env" "${ROOT_DIR}/infra/secrets/freebox.env.local"; do
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

mod_path = Path(os.environ.get("LBG_FREEBOX_CLIENT", "")).resolve() if os.environ.get("LBG_FREEBOX_CLIENT") else (
    Path(__file__)  # unused
)
# Locate client relative to script via env set by bash
root = Path(os.environ["ROOT_DIR"])
mod_path = root / "agents" / "src" / "lbg_agents" / "freebox_client.py"
spec = importlib.util.spec_from_file_location("freebox_client", mod_path)
fb = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(fb)

if not fb.freebox_configured():
    print("FAIL: LBG_FREEBOX_APP_TOKEN absent — lancer authorize_freebox_app.sh", file=sys.stderr)
    sys.exit(2)

out = fb.probe_freebox(include_lan=True)
print(fb.format_audit_text(out))
print("---")
summary = {
    "ok": out.get("ok"),
    "configured": out.get("configured"),
    "box_model": out.get("box_model"),
    "api_version": out.get("api_version"),
    "n_leases": out.get("n_leases"),
    "n_lan_hosts": out.get("n_lan_hosts"),
    "audit": {
        k: out.get("audit", {}).get(k)
        for k in ("ok", "n_ok", "n_missing", "n_mac_mismatch", "n_extra", "missing", "mac_mismatch")
    },
    "error": out.get("error"),
}
print(json.dumps(summary, indent=2, ensure_ascii=False))
sys.exit(0 if out.get("ok") else 1)
PY
