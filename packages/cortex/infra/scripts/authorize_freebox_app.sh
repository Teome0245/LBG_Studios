#!/usr/bin/env bash
# Enregistre l'app LBG Cortex sur la Freebox (lecture seule une fois autorisée).
# 1) Lance ce script
# 2) Sur l'écran Freebox (ou Freebox OS) → autoriser « LBG Cortex »
# 3) Le token est écrit dans infra/secrets/lbg.env + freebox.env.local
#
# Usage :
#   bash packages/cortex/infra/scripts/authorize_freebox_app.sh
#   LBG_FREEBOX_AUTH_TIMEOUT_S=300 bash .../authorize_freebox_app.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/agents/src:${PYTHONPATH:-}"
export LBG_FREEBOX_SECRETS_DIR="${ROOT_DIR}/infra/secrets"
export LBG_FREEBOX_AUTH_TIMEOUT_S="${LBG_FREEBOX_AUTH_TIMEOUT_S:-180}"

PY=python3
if [[ -x "${ROOT_DIR}/agents/.venv/bin/python" ]]; then
  PY="${ROOT_DIR}/agents/.venv/bin/python"
fi

if [[ -f "${LBG_FREEBOX_SECRETS_DIR}/lbg.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${LBG_FREEBOX_SECRETS_DIR}/lbg.env"
  set +a
fi

echo "=== Freebox authorize (timeout ${LBG_FREEBOX_AUTH_TIMEOUT_S}s) ==="
echo "Valide « LBG Cortex » sur l'écran Freebox / Freebox OS maintenant."
echo

"${PY}" - <<'PY'
import importlib.util
import json
import os
import sys
from pathlib import Path

mod_path = Path(os.environ["LBG_FREEBOX_SECRETS_DIR"]).parents[1] / "agents/src/lbg_agents/freebox_client.py"
# secrets_dir = .../infra/secrets → parents[1] = cortex root
mod_path = Path(os.environ.get("LBG_FREEBOX_CLIENT", ""))
if not mod_path.is_file():
    mod_path = Path(__file__).resolve() if False else Path(
        os.environ["LBG_FREEBOX_SECRETS_DIR"]
    ).resolve().parents[1] / "agents" / "src" / "lbg_agents" / "freebox_client.py"

spec = importlib.util.spec_from_file_location("freebox_client", mod_path)
fb = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(fb)

timeout = float(os.environ.get("LBG_FREEBOX_AUTH_TIMEOUT_S", "180"))
secrets_dir = Path(os.environ["LBG_FREEBOX_SECRETS_DIR"])
env_file = secrets_dir / "lbg.env"
local_file = secrets_dir / "freebox.env.local"

auth = fb.request_authorization()
print(
    f"Demande envoyée — track_id={auth.get('track_id')} app_id={auth.get('app_id')}",
    flush=True,
)
if not auth.get("app_token") or auth.get("track_id") is None:
    print("Échec authorize_failed", file=sys.stderr)
    sys.exit(2)

poll = fb.poll_authorization(auth["track_id"], api_meta=auth.get("api_meta"), timeout_s=timeout)
if not poll.get("ok"):
    print(f"Autorisation non accordée — status={poll.get('status') or poll.get('last_status')}", file=sys.stderr)
    sys.exit(1)

token = auth["app_token"]
app_id = auth.get("app_id") or "fr.lbg.cortex.freebox"
keys = {
    "LBG_FREEBOX_ENABLED": "1",
    "LBG_FREEBOX_HOST": "192.168.0.254",
    "LBG_FREEBOX_APP_ID": app_id,
    "LBG_FREEBOX_APP_TOKEN": token,
    "LBG_FREEBOX_VERIFY_SSL": "0",
}

secrets_dir.mkdir(parents=True, exist_ok=True)
local_file.write_text(
    "# Freebox OS app token — ne pas committer\n"
    + "\n".join(f'{k}="{v}"' for k, v in keys.items())
    + "\n",
    encoding="utf-8",
)
local_file.chmod(0o600)

text = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
lines = text.splitlines()
out: list[str] = []
seen: set[str] = set()
for line in lines:
    if not line or line.lstrip().startswith("#") or "=" not in line:
        out.append(line)
        continue
    k = line.split("=", 1)[0].strip()
    if k in keys:
        out.append(f'{k}="{keys[k]}"')
        seen.add(k)
    else:
        out.append(line)
for k, v in keys.items():
    if k not in seen:
        out.append(f'{k}="{v}"')
env_file.write_text("\n".join(out) + "\n", encoding="utf-8")
env_file.chmod(0o600)

print(json.dumps({"ok": True, "status": "granted", "app_id": app_id, "env_file": str(env_file), "local_file": str(local_file)}, ensure_ascii=False))
print("OK — token enregistré. Smoke : bash infra/scripts/smoke_freebox_lan.sh")
PY
