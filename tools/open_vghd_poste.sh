#!/usr/bin/env bash
set -euo pipefail

# Ouvre vghd sur le poste Windows via la chaîne Pilot → orchestrateur → agent desktop.
#
# Usage (depuis WSL ou une machine du LAN 192.168.0.x) :
#   bash tools/open_vghd_poste.sh
#   LBG_DESKTOP_APPROVAL=SECRET bash tools/open_vghd_poste.sh
#   bash tools/open_vghd_poste.sh --dry-run
#
# Variables :
#   LBG_PILOT_URL              défaut http://192.168.0.140:8080
#   LBG_PILOT_API_TOKEN        Bearer (Cockpit / Réglages) — optionnel si inject serveur
#   LBG_PILOT_INTERNAL_TOKEN   header X-LBG-Service-Token — optionnel
#   LBG_DESKTOP_APPROVAL       jeton desktop (aligné C:\Agent_IA\desktop.env)
#   LBG_OPEN_VGHD_GOAL         défaut « ouvre vghd sur mon poste »

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PILOT_URL="${LBG_PILOT_URL:-http://192.168.0.140:8080}"
GOAL="${LBG_OPEN_VGHD_GOAL:-ouvre vghd sur mon poste}"
DRY_RUN=0

for arg in "$@"; do
  case "${arg}" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      sed -n '2,18p' "$0"
      exit 0
      ;;
    *)
      echo "Argument inconnu: ${arg} (essayez --help)" >&2
      exit 2
      ;;
  esac
done

SEC_FILE="${ROOT}/packages/cortex/infra/secrets/lbg.env"

read_env_var() {
  local key="$1"
  python3 - <<'PY' "$SEC_FILE" "$key"
import re, sys, pathlib
p = pathlib.Path(sys.argv[1])
key = sys.argv[2]
if not p.exists():
    print("")
    raise SystemExit(0)
escaped = re.escape(key)
pat = re.compile(rf"^\s*{escaped}\s*=\s*\"?(.*?)\"?\s*$")
for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
    m = pat.match(line)
    if m:
        print(m.group(1).strip())
        raise SystemExit(0)
print("")
PY
}

PILOT_TOKEN="${LBG_PILOT_API_TOKEN:-$(read_env_var LBG_PILOT_API_TOKEN)}"
INTERNAL_TOKEN="${LBG_PILOT_INTERNAL_TOKEN:-$(read_env_var LBG_PILOT_INTERNAL_TOKEN)}"
APPROVAL="${LBG_DESKTOP_APPROVAL:-$(read_env_var LBG_DESKTOP_APPROVAL_TOKEN)}"

hdr=(-H "Content-Type: application/json")
if [[ -n "${PILOT_TOKEN}" ]]; then
  hdr+=(-H "Authorization: Bearer ${PILOT_TOKEN}")
fi
if [[ -n "${INTERNAL_TOKEN}" ]]; then
  hdr+=(-H "X-LBG-Service-Token: ${INTERNAL_TOKEN}")
fi

tmp_body="$(mktemp)"
tmp_payload="$(mktemp)"
trap 'rm -f "${tmp_body}" "${tmp_payload}"' EXIT

export GOAL DRY_RUN APPROVAL ROOT="${ROOT}"
python3 - <<'PY' >"${tmp_payload}"
import json, os, sys

root = os.environ.get("ROOT", ".")
sys.path.insert(0, os.path.join(root, "packages", "cortex", "agents", "src"))
from lbg_agents.desktop_apps import open_app_action_from_goal

goal = os.environ.get("GOAL", "ouvre vghd sur mon poste")
dry = os.environ.get("DRY_RUN", "0") == "1"
approval = (os.environ.get("APPROVAL") or "").strip()
action = open_app_action_from_goal(goal)
if action is None:
    raise SystemExit("Impossible d'inférer desktop_action depuis le goal")
ctx: dict = {"desktop_dry_run": dry, "desktop_action": action}
if not dry and approval:
    ctx["desktop_approval"] = approval
print(json.dumps({"actor_id": "ops:open_vghd", "text": goal, "context": ctx}, ensure_ascii=False))
PY

echo "== open_vghd_poste =="
echo "pilot=${PILOT_URL} dry_run=${DRY_RUN} goal=${GOAL@Q}"
echo ""

http_code="$(
  curl -sS --connect-timeout 5 --max-time 90 \
    "${hdr[@]}" \
    -X POST "${PILOT_URL%/}/v1/pilot/route" \
    -d @"${tmp_payload}" \
    -o "${tmp_body}" \
    -w "%{http_code}" || echo "000"
)"

echo "HTTP ${http_code}"
HTTP_CODE="${http_code}" python3 - <<'PY' "${tmp_body}"
import json, os, sys

raw = open(sys.argv[1], encoding="utf-8").read()
http_code = os.environ.get("HTTP_CODE", "000")
try:
    d = json.loads(raw)
except json.JSONDecodeError:
    print(raw[:2000])
    raise SystemExit(1)

print(json.dumps(d, ensure_ascii=False, indent=2)[:4000])
if http_code != "200":
    raise SystemExit(1)

intent = d.get("intent")
out = d.get("output") if isinstance(d.get("output"), dict) else {}
if intent != "desktop_control":
    print(f"\n→ Mauvais routage : intent={intent!r} (attendu desktop_control)", file=sys.stderr)
    raise SystemExit(3)

err = " ".join(str(out.get(k) or d.get(k) or "") for k in ("error", "reply", "detail")).lower()
if "approval" in err and "token" in err:
    print(
        "\n→ Jeton desktop manquant : export LBG_DESKTOP_APPROVAL=… "
        "(même valeur que C:\\Agent_IA\\desktop.env)",
        file=sys.stderr,
    )
    raise SystemExit(2)

policy = out.get("policy") if isinstance(out.get("policy"), dict) else {}
decision = policy.get("decision")
outcome = out.get("outcome")
ok = out.get("ok") is True
if ok or outcome in ("ok", "dry_run") or decision in ("dry_run", "approved_action"):
    raise SystemExit(0)
if decision == "approval_required":
    raise SystemExit(2)
raise SystemExit(1)
PY

echo ""
echo "OK — vghd demandé sur le poste (vérifiez la fenêtre sur Windows)."
