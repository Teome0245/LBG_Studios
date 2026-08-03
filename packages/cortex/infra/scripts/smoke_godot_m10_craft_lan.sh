#!/usr/bin/env bash
# Smoke M10 — talents/craft B2B sidecar :8791 (catalog skills + schematics).
#
# Critères P2 minimal (PLAN_MMO_O2) :
#   healthz OK ; GET /v1/catalog/skills → skills[] et schematics[] non vides ; fallback≠true
#
# Usage :
#   bash infra/scripts/smoke_godot_m10_craft_lan.sh
#   LBG_SIDECAR_HTTP=http://192.168.0.246:8791 bash …
set -euo pipefail

SIDECAR="${LBG_SIDECAR_HTTP:-http://192.168.0.246:8791}"
SIDECAR="${SIDECAR%/}"
MIN_SKILLS="${LBG_M10_MIN_SKILLS:-1}"
MIN_SCHEM="${LBG_M10_MIN_SCHEMATICS:-1}"

echo "=== Smoke M10 craft catalog (sidecar) ==="
echo "sidecar: ${SIDECAR}"

health="$(curl -sfS --max-time 8 "${SIDECAR}/healthz" || true)"
if [[ -z "${health}" ]]; then
  echo "FAIL: /healthz injoignable sur ${SIDECAR}" >&2
  exit 1
fi
echo "health: ${health}"

tmp="$(mktemp)"
trap 'rm -f "${tmp}"' EXIT
if ! curl -sfS --max-time 10 "${SIDECAR}/v1/catalog/skills" -o "${tmp}"; then
  echo "FAIL: GET /v1/catalog/skills" >&2
  exit 2
fi

LBG_M10_MIN_SKILLS="${MIN_SKILLS}" LBG_M10_MIN_SCHEMATICS="${MIN_SCHEM}" \
python3 - "${tmp}" <<'PY'
import json, os, sys

path = sys.argv[1]
with open(path, encoding="utf-8") as fh:
    d = json.load(fh)
skills = d.get("skills") or []
schematics = d.get("schematics") or []
if not isinstance(skills, list) or not isinstance(schematics, list):
    print("FAIL: skills/schematics non-list", file=sys.stderr)
    sys.exit(3)
min_sk = int(os.environ.get("LBG_M10_MIN_SKILLS", "1"))
min_sc = int(os.environ.get("LBG_M10_MIN_SCHEMATICS", "1"))
if len(skills) < min_sk:
    print(f"FAIL: skills vides ({len(skills)} < {min_sk})", file=sys.stderr)
    sys.exit(4)
if len(schematics) < min_sc:
    print(f"FAIL: schematics vides ({len(schematics)} < {min_sc})", file=sys.stderr)
    sys.exit(5)
if d.get("fallback") is True:
    print("FAIL: catalog en fallback=true (mock serveur)", file=sys.stderr)
    sys.exit(6)

def _label(row):
    if isinstance(row, dict):
        return str(row.get("name") or row.get("id") or "")
    return str(row)

if any(not _label(r) for r in skills[:20]):
    print("FAIL: skill sans name/id", file=sys.stderr)
    sys.exit(7)
print(
    f"OK M10 — skills={len(skills)} schematics={len(schematics)} "
    f"fallback={d.get('fallback')} track={d.get('track')} "
    f"sample={_label(skills[0])!r} / {_label(schematics[0])!r}"
)
PY

if ! curl -sfS --max-time 10 "${SIDECAR}/v1/catalog/schematics" -o /dev/null; then
  echo "FAIL: GET /v1/catalog/schematics" >&2
  exit 8
fi
echo "OK M10 — /v1/catalog/schematics joignable"
