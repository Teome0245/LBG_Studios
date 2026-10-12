#!/usr/bin/env bash
# Smoke reproductible — MAJ VS Code Omarchy (.143) via l’écosystème LBG.
#
# Ne lance JAMAIS le Réel (yay) : dry-run agent + proposition Agir seulement.
# Usage (depuis LBG_Studios) :
#   bash packages/cortex/infra/scripts/smoke_update_vscode_143.sh
#
set -euo pipefail

HOST="${LBG_OMARCHY_HOST:-192.168.0.143}"
PORT="${LBG_OMARCHY_AGENT_PORT:-5005}"
ORCH="${LBG_ORCH_URL:-http://192.168.0.140:8010}"
COMPAGNON="${LBG_COMPAGNON_URL:-http://192.168.0.100:5174}"
TEXT='mets à jour vscode sur omarchy'

echo "==> Agent .143 healthz"
curl -fsS -m 8 "http://${HOST}:${PORT}/healthz" >/dev/null
echo "OK  http://${HOST}:${PORT}/healthz"

echo "==> Agent dry-run update_vscode"
curl -fsS -m 150 -X POST "http://${HOST}:${PORT}/invoke" \
  -H 'Content-Type: application/json' \
  -d '{"actor_id":"ui:compagnon","text":"dry","context":{"desktop_dry_run":true,"desktop_action":{"kind":"update_vscode"}}}' \
  | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d.get("ok") is True, d
assert d.get("outcome") == "dry_run", d
assert d.get("kind") == "update_vscode", d
st = d.get("status") or {}
print("OK  dry_run", st.get("current"), "→", st.get("available"), "update_available=", st.get("update_available"))
'

echo "==> Orch action-proposal (:8010)"
curl -fsS -m 30 -X POST "${ORCH}/v1/action-proposal" \
  -H 'Content-Type: application/json' \
  -d "{\"actor_id\":\"ui:compagnon\",\"text\":\"${TEXT}\",\"context\":{}}" \
  | python3 -c '
import json,sys
d=json.load(sys.stdin)
p=d.get("proposal")
assert p is not None, d.get("reason") or d
assert p.get("action",{}).get("kind")=="update_vscode", p
assert (p.get("context_patch") or {}).get("desktop_target")=="omarchy", p
assert p.get("requires_review") is True, p
print("OK  proposal update_vscode → omarchy (review required)")
'

echo "==> Compagnon proxy Agir (optionnel)"
if curl -fsS -m 8 "${COMPAGNON}/" >/dev/null 2>&1; then
  if ! curl -fsS -m 30 -X POST "${COMPAGNON}/api/pilot/action-proposal" \
    -H 'Content-Type: application/json' \
    -d "{\"actor_id\":\"ui:compagnon\",\"text\":\"${TEXT}\",\"context\":{}}" \
    | python3 -c '
import json,sys
d=json.load(sys.stdin)
p=d.get("proposal")
if p is None and isinstance(d.get("body"), dict):
    p=(d.get("body") or {}).get("proposal")
if p is None:
    print("WARN  Compagnon pas encore branché:", (d.get("reason") or str(d))[:160])
    raise SystemExit(0)
assert p.get("action",{}).get("kind")=="update_vscode", p
print("OK  Compagnon Agir → update_vscode")
'; then
    echo "WARN  Compagnon proxy fail — orch direct OK suffit tant que nginx→.140 est à jour"
  fi
else
  echo "WARN  Compagnon :5174 injoignable — skip proxy"
fi

echo
echo "OK  smoke update_vscode (dry-run only)"
echo "    Réel : Compagnon Agir « ${TEXT} » → confirm L2, hors session Cline critique"
echo "    Deploy : bash packages/cortex/infra/scripts/deploy_update_vscode_ecosystem.sh"
