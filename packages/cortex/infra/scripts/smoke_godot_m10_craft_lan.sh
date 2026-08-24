#!/usr/bin/env bash
# Smoke M10 — talents/craft B2B sidecar :8791 (catalog + craft_combine optionnel).
#
# Critères P2 minimal (PLAN_MMO_O2) :
#   healthz OK ; GET /v1/catalog/skills → skills[] et schematics[] non vides ; fallback≠true
#   Si LBG_M10_SMOKE_CRAFT=1 (défaut auto si /v1/craft/combine existe) :
#     reset inventaire → POST craft ration_compacte → inventaire contient output
#
# Usage :
#   bash infra/scripts/smoke_godot_m10_craft_lan.sh
#   LBG_SIDECAR_HTTP=http://127.0.0.1:8791 bash …   # stub local
#   LBG_SIDECAR_HTTP=http://192.168.0.246:8791 bash …
set -euo pipefail

SIDECAR="${LBG_SIDECAR_HTTP:-http://192.168.0.246:8791}"
SIDECAR="${SIDECAR%/}"
MIN_SKILLS="${LBG_M10_MIN_SKILLS:-1}"
MIN_SCHEM="${LBG_M10_MIN_SCHEMATICS:-1}"
PLAYER="${LBG_M10_STUB_PLAYER:-local}"
SCHEMATIC="${LBG_M10_SMOKE_SCHEMATIC:-ration_compacte}"
SMOKE_CRAFT="${LBG_M10_SMOKE_CRAFT:-auto}"

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

inv_tmp="$(mktemp)"
if curl -sfS --max-time 10 "${SIDECAR}/v1/inventory?player=${PLAYER}" -o "${inv_tmp}"; then
  python3 - "${inv_tmp}" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
inv = d.get("inventory") if isinstance(d, dict) else None
src = d.get("source") if isinstance(d, dict) else None
live = d.get("core3_live") if isinstance(d, dict) else None
n = len(inv) if isinstance(inv, list) else -1
print(f"OK M10 inventory — stacks={n} source={src} core3_live={live}")
if not isinstance(d, dict) or not d.get("ok"):
    raise SystemExit("FAIL: GET /v1/inventory ok≠true")
PY
else
  echo "FAIL: GET /v1/inventory" >&2
  rm -f "${inv_tmp}"
  exit 8
fi
rm -f "${inv_tmp}"

# --- craft_combine (stub local ou sidecar étendu) ---
craft_probe="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 \
  -X POST "${SIDECAR}/v1/craft/combine" \
  -H 'Content-Type: application/json' \
  -d '{"player":"__probe__","schematic_id":"__none__"}' || true)"

do_craft=0
if [[ "${SMOKE_CRAFT}" == "1" || "${SMOKE_CRAFT}" == "true" ]]; then
  do_craft=1
elif [[ "${SMOKE_CRAFT}" == "auto" ]]; then
  if [[ "${craft_probe}" == "400" || "${craft_probe}" == "200" ]]; then
    do_craft=1
  fi
fi

if [[ "${do_craft}" != "1" ]]; then
  echo "SKIP M10 craft_combine (endpoint absent ou LBG_M10_SMOKE_CRAFT=0) probe_http=${craft_probe}"
  echo "OK M10 smoke (catalog only)"
  exit 0
fi

echo "=== Smoke M10 craft_combine ==="
curl -sfS --max-time 10 -X POST "${SIDECAR}/v1/inventory/reset" \
  -H 'Content-Type: application/json' \
  -d "{\"player\":\"${PLAYER}\"}" >/dev/null || {
  echo "FAIL: POST /v1/inventory/reset" >&2
  exit 9
}

craft_out="$(mktemp)"
trap 'rm -f "${tmp}" "${craft_out}"' EXIT
http_c="$(curl -sS -o "${craft_out}" -w '%{http_code}' --max-time 10 \
  -X POST "${SIDECAR}/v1/craft/combine" \
  -H 'Content-Type: application/json' \
  -d "{\"player\":\"${PLAYER}\",\"schematic_id\":\"${SCHEMATIC}\"}" || true)"

PLAYER="${PLAYER}" SCHEMATIC="${SCHEMATIC}" HTTP_C="${http_c}" \
python3 - "${craft_out}" <<'PY'
import json, os, sys

path = sys.argv[1]
http_c = os.environ.get("HTTP_C", "")
schem = os.environ.get("SCHEMATIC", "ration_compacte")
with open(path, encoding="utf-8") as fh:
    try:
        d = json.load(fh)
    except Exception as exc:
        print(f"FAIL: craft JSON {exc}", file=sys.stderr)
        sys.exit(10)
if not isinstance(d, dict) or not d.get("ok"):
    print(f"FAIL: craft ok≠true http={http_c} body={d!r}", file=sys.stderr)
    sys.exit(11)
crafted = d.get("crafted") or {}
cid = str(crafted.get("id") or "")
inv = d.get("inventory") or []
ids = {str(x.get("id")) for x in inv if isinstance(x, dict)}
if schem not in ids and cid not in ids:
    print(f"FAIL: output {schem!r} absent inventaire ids={sorted(ids)}", file=sys.stderr)
    sys.exit(13)
print(f"OK M10 craft_combine — {schem} → inventaire (http={http_c})")
PY

echo "OK M10 smoke (catalog + craft)"
