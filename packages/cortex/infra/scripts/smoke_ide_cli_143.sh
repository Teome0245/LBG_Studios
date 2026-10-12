#!/usr/bin/env bash
# Smoke reproductible — mains code headless Omarchy (.143) ADR 0025.
#
# Dry-run par défaut. Live opt-in : LBG_SMOKE_IDE_CLI_LIVE=1
# Usage (depuis LBG_Studios) :
#   bash packages/cortex/infra/scripts/smoke_ide_cli_143.sh
#
set -euo pipefail

HOST="${LBG_OMARCHY_HOST:-192.168.0.143}"
PORT="${LBG_OMARCHY_AGENT_PORT:-5005}"
ORCH="${LBG_ORCH_URL:-http://192.168.0.140:8010}"
COMPAGNON="${LBG_COMPAGNON_URL:-http://192.168.0.100:5174}"
CWD="${LBG_OMARCHY_STUDIO_WORKSPACE:-/home/lbg/projects/LBG_Studios}"
PROMPT="${LBG_SMOKE_IDE_CLI_PROMPT:-Réponds uniquement: OK smoke_ide_cli_143}"
APP="${LBG_SMOKE_IDE_CLI_APP:-opencode}"
LIVE="${LBG_SMOKE_IDE_CLI_LIVE:-0}"
TEXT="lance ${APP} sur omarchy pour ${PROMPT}"

echo "==> Agent .143 healthz"
curl -fsS -m 8 "http://${HOST}:${PORT}/healthz" >/dev/null
echo "OK  http://${HOST}:${PORT}/healthz"

echo "==> Agent dry-run run_cli_agent app=${APP}"
curl -fsS -m 60 -X POST "http://${HOST}:${PORT}/invoke" \
  -H 'Content-Type: application/json' \
  -d "{\"actor_id\":\"ui:smoke\",\"text\":\"dry\",\"context\":{\"desktop_dry_run\":true,\"desktop_action\":{\"kind\":\"run_cli_agent\",\"app\":\"${APP}\",\"prompt\":\"${PROMPT}\",\"cwd\":\"${CWD}\"}}}" \
  | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d.get("ok") is True, d
assert d.get("outcome") == "dry_run", d
assert d.get("kind") == "run_cli_agent", d
assert d.get("app") == "'"${APP}"'", d
argv = d.get("argv") or []
joined = " ".join(str(x) for x in argv)
assert "'"${APP}"'" in joined or (d.get("bin_missing") and d.get("ok")), d
print("OK  dry_run", d.get("app"), "cwd=", d.get("cwd"), "argv=", joined[:120])
'

echo "==> Orch action-proposal (:8010)"
curl -fsS -m 30 -X POST "${ORCH}/v1/action-proposal" \
  -H 'Content-Type: application/json' \
  -d "$(python3 -c "import json; print(json.dumps({'actor_id':'ui:smoke','text':'''${TEXT}''','context':{}}))")" \
  | python3 -c '
import json,sys
d=json.load(sys.stdin)
p=d.get("proposal")
assert p is not None, d.get("reason") or d
act=p.get("action") or {}
assert act.get("kind")=="run_cli_agent", p
assert act.get("app") in ("opencode","claude","cline"), act
assert (p.get("context_patch") or {}).get("desktop_target")=="omarchy", p
assert (p.get("context_patch") or {}).get("ide_cli") is True, p
print("OK  proposal run_cli_agent app=", act.get("app"), "→ omarchy")
'

echo "==> Compagnon proxy Agir (optionnel)"
if curl -fsS -m 8 "${COMPAGNON}/" >/dev/null 2>&1; then
  if ! curl -fsS -m 30 -X POST "${COMPAGNON}/api/pilot/action-proposal" \
    -H 'Content-Type: application/json' \
    -d "$(python3 -c "import json; print(json.dumps({'actor_id':'ui:smoke','text':'''${TEXT}''','context':{}}))")" \
    | python3 -c '
import json,sys
d=json.load(sys.stdin)
p=d.get("proposal")
if p is None and isinstance(d.get("body"), dict):
    p=(d.get("body") or {}).get("proposal")
if p is None:
    print("WARN  Compagnon pas encore branché:", (d.get("reason") or str(d))[:160])
    raise SystemExit(0)
assert (p.get("action") or {}).get("kind")=="run_cli_agent", p
print("OK  Compagnon Agir → run_cli_agent")
'; then
    echo "WARN  Compagnon proxy fail — orch direct OK suffit"
  fi
else
  echo "WARN  Compagnon :5174 injoignable — skip proxy"
fi

if [[ "${LIVE}" == "1" || "${LIVE}" == "true" ]]; then
  echo "==> LIVE run_cli_agent (LBG_SMOKE_IDE_CLI_LIVE=1) — soft-confirm LAB attendu si policy confirm"
  curl -fsS -m 360 -X POST "http://${HOST}:${PORT}/invoke" \
    -H 'Content-Type: application/json' \
    -d "{\"actor_id\":\"ui:smoke\",\"text\":\"live\",\"context\":{\"desktop_dry_run\":false,\"desktop_approval\":\"LAB\",\"desktop_action\":{\"kind\":\"run_cli_agent\",\"app\":\"${APP}\",\"prompt\":\"${PROMPT}\",\"cwd\":\"${CWD}\",\"timeout_s\":120}}}" \
    | python3 -c '
import json,sys
d=json.load(sys.stdin)
print("LIVE outcome=", d.get("outcome"), "ok=", d.get("ok"), "reply=", str(d.get("reply") or d.get("error") or "")[:200])
assert d.get("kind") == "run_cli_agent", d
if d.get("outcome") in ("feature_disabled", "approval_denied", "not_installed"):
    print("WARN  live bloqué (flags/approval/bin) — dry-run OK suffit pour checklist")
    raise SystemExit(0)
assert d.get("ok") is True, d
'
else
  echo "==> LIVE skip (export LBG_SMOKE_IDE_CLI_LIVE=1 pour micro-test réel)"
fi

echo
echo "OK  smoke ide_cli / run_cli_agent (dry-run)"
echo "    Agir : « lance opencode sur omarchy pour … » (défaut) · « lance claude … » (expérimental)"
echo "    Cline CLI : hors scope .143 — UI Cline via open_app uniquement"
echo "    Flags : LBG_LINUX_CLI_AGENT_ENABLED=1 · LBG_TEAM_IDE_CLI_ENABLED=1 · modèle opencode/big-pickle"
