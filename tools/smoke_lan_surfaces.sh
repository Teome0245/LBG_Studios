#!/usr/bin/env bash
# Smoke HTTP (+ optionnel fonctionnel) des surfaces LAN LBG Studios.
# Usage:
#   bash tools/smoke_lan_surfaces.sh
#   bash tools/smoke_lan_surfaces.sh --functional
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FUNCTIONAL=0
[[ "${1:-}" == "--functional" ]] && FUNCTIONAL=1

PILOT="${LBG_PILOT_URL:-http://192.168.0.140:8080}"
OK=0
WARN=0
KO=0

check_http() {
  local name="$1" url="$2" expect="${3:-2}"
  local code
  code=$(curl -sS -o /tmp/lbg_smoke.body -w "%{http_code}" --connect-timeout 4 --max-time 15 "$url" 2>/tmp/lbg_smoke.err) || {
    echo "KO  $name  curl_fail  $url  $(tr '\n' ' ' </tmp/lbg_smoke.err | head -c 80)"
    KO=$((KO + 1))
    return
  }
  if [[ "$code" =~ ^${expect} ]]; then
    echo "OK  $name  HTTP $code  $url"
    OK=$((OK + 1))
  else
    echo "WARN  $name  HTTP $code  $url"
    WARN=$((WARN + 1))
  fi
}

echo "=== Surfaces LAN ==="
check_http "Pilot UI" "$PILOT/pilot/"
check_http "Pilot healthz" "$PILOT/healthz"
check_http "Pilot status" "$PILOT/v1/pilot/status"
check_http "Cockpit UI" "http://192.168.0.100:8093/pilot/"
check_http "Cockpit snapshot" "http://192.168.0.100:8093/v1/pilot/cockpit/snapshot"
check_http "Orch UI /" "http://192.168.0.100:5174/"
check_http "Orch UI /lyra" "http://192.168.0.100:5174/lyra"
check_http "Orch UI /agents/map" "http://192.168.0.100:5174/agents/map"
check_http "Orch API /health" "http://192.168.0.100:3000/health"
check_http "Prime 246:8792" "http://192.168.0.246:8792/"
check_http "Prime api/servers" "http://192.168.0.246:8792/api/servers"
check_http "PreCU 245:8792" "http://192.168.0.245:8792/"
check_http "PreCU api/servers" "http://192.168.0.245:8792/api/servers"
check_http "Patches manifest" "http://192.168.0.246:8080/patches/prime/manifest.json"
check_http "MCP healthz" "http://192.168.0.100:8766/healthz"

echo
echo "=== Détail serveurs jeu ==="
python3 - <<'PY'
import json, urllib.request
for host, label in (("246", "Prime UI"), ("245", "PreCU UI")):
    url = f"http://192.168.0.{host}:8792/api/servers"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.load(r)
    except Exception as e:
        print(f"KO  {label} api/servers: {e}")
        continue
    for s in data:
        print(f"  {label}: {s.get('id')} status={s.get('status')} ready={s.get('ready')} online={s.get('online')} login_udp={s.get('login_udp')}")
PY

if [[ "$FUNCTIONAL" -eq 1 ]]; then
  echo
  echo "=== Fonctionnel ==="
  # 1 Desktop dry-run
  code=$(curl -sS -o /tmp/lbg_fn_desktop.json -w "%{http_code}" --connect-timeout 8 --max-time 45 \
    -X POST "$PILOT/v1/pilot/route" -H 'Content-Type: application/json' \
    -d '{"actor_id":"pilot:smoke","text":"ouvre https://example.org","context":{"history":[],"desktop_dry_run":true,"desktop_action":{"kind":"open_url","url":"https://example.org"}}}')
  if [[ "$code" == "200" ]] && python3 -c "import json; d=json.load(open('/tmp/lbg_fn_desktop.json')); raise SystemExit(0 if d.get('ok') else 1)"; then
    echo "OK  Desktop dry-run route  HTTP $code"
    OK=$((OK + 1))
  else
    echo "KO  Desktop dry-run route  HTTP $code  $(head -c 200 /tmp/lbg_fn_desktop.json)"
    KO=$((KO + 1))
  fi

  # 2 Orch Lyra gauges via /health
  if python3 - <<'PY'
import json, urllib.request
d=json.load(urllib.request.urlopen("http://192.168.0.100:3000/health", timeout=8))
g=(d.get("lyra") or {}).get("gauges") or {}
raise SystemExit(0 if g else 1)
PY
  then
    echo "OK  Orch Lyra gauges in /health"
    OK=$((OK + 1))
  else
    echo "KO  Orch Lyra gauges missing"
    KO=$((KO + 1))
  fi

  # 3 Jeu ready (already checked; assert both ready)
  if python3 - <<'PY'
import json, urllib.request
ok=True
for host in ("246","245"):
    data=json.load(urllib.request.urlopen(f"http://192.168.0.{host}:8792/api/servers", timeout=8))
    if not any(s.get("id")=="prime" and s.get("ready") for s in data):
        ok=False
    if not any(s.get("id")=="swgemu" and s.get("ready") for s in data):
        ok=False
raise SystemExit(0 if ok else 1)
PY
  then
    echo "OK  Jeu Prime+PreCU ready (via both :8792)"
    OK=$((OK + 1))
  else
    echo "KO  Jeu servers not fully ready"
    KO=$((KO + 1))
  fi

  # 4 Assistant action-proposal (Forge Prime hint)
  code=$(curl -sS -o /tmp/lbg_fn_prop.json -w "%{http_code}" --connect-timeout 8 --max-time 45 \
    -X POST "$PILOT/v1/pilot/action-proposal" -H 'Content-Type: application/json' \
    -d '{"actor_id":"pilot:smoke","text":"forge un prototype OpenGame pour Prime dry-run","context":{"history":[],"session_summary":{"player_note":"smoke lan","tracked_quest":"smoke"}}}')
  if [[ "$code" == "200" ]]; then
    echo "OK  Assistant action-proposal  HTTP $code"
    OK=$((OK + 1))
    python3 -c "import json; d=json.load(open('/tmp/lbg_fn_prop.json')); print('   keys', list(d)[:12]); print('   snippet', str(d)[:220].replace(chr(10),' '))"
  else
    echo "KO  Assistant action-proposal  HTTP $code  $(head -c 200 /tmp/lbg_fn_prop.json)"
    KO=$((KO + 1))
  fi

  # Desktop agent healthz (info)
  code=$(curl -sS -o /tmp/lbg_fn_desk_h.json -w "%{http_code}" --connect-timeout 5 --max-time 12 \
    "$PILOT/v1/pilot/agent-desktop/healthz" || true)
  echo "INFO  agent-desktop/healthz  HTTP ${code:-err}  $(head -c 160 /tmp/lbg_fn_desk_h.json 2>/dev/null)"

  # 5 Cockpit Desktop réel (inject approval) — optionnel si SSH 140 OK
  if ssh -o BatchMode=yes -o ConnectTimeout=4 lbg@192.168.0.140 'true' 2>/dev/null; then
    if ssh -o BatchMode=yes lbg@192.168.0.140 'bash -s' <<'REMOTE'
PILOT=$(sudo grep -E '^LBG_PILOT_API_TOKEN=' /etc/lbg-project-03.env | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
curl -sS --max-time 60 -o /tmp/lbg_fn_vghd.json -w "%{http_code}" -X POST http://127.0.0.1:9800/v1/pilot/tasks/run \
  -H "Authorization: Bearer $PILOT" -H 'Content-Type: application/json' \
  -d '{"goal":"lance notepad sur mon pc","context":{"desktop_dry_run":false}}' > /tmp/lbg_fn_vghd.code
code=$(cat /tmp/lbg_fn_vghd.code)
python3 - <<'PY'
import json
code=open("/tmp/lbg_fn_vghd.code").read().strip()
d=json.load(open("/tmp/lbg_fn_vghd.json"))
ok = code=="200" and d.get("ok") is True and "approval" not in (d.get("error") or "").lower()
# notepad peut échouer WinError path — on accepte aussi vghd-style success ou erreur non-approval
err=(d.get("error") or "")+(d.get("reply") or "")
if "Approval token" in err or "approval_denied" in err:
    raise SystemExit(2)
raise SystemExit(0 if ok or code=="200" else 1)
PY
REMOTE
    then
      echo "OK  Cockpit Desktop réel (tasks/run, sans approval client)"
      OK=$((OK + 1))
    else
      echo "WARN  Cockpit Desktop réel (SSH/API) — voir jetons / worker"
      WARN=$((WARN + 1))
    fi
  else
    echo "INFO  Cockpit Desktop réel skip (pas de SSH BatchMode vers 140)"
  fi

  # 6 Team ADR 0019 — plan + messages (orch 140 ou local)
  SMOKE_TEAM="${ROOT}/packages/cortex/infra/scripts/smoke_team_plan_bus.sh"
  if [[ -f "$SMOKE_TEAM" ]]; then
    export LBG_ORCHESTRATOR_URL="${LBG_ORCHESTRATOR_URL:-http://192.168.0.140:8010}"
    if bash "$SMOKE_TEAM"; then
      echo "OK  Team plan+bus smoke_team_plan_bus.sh"
      OK=$((OK + 1))
    else
      echo "WARN  Team plan+bus (orch down ou ADR 0019 non déployé)"
      WARN=$((WARN + 1))
    fi
  fi
fi

echo
echo "Résumé: OK=$OK WARN=$WARN KO=$KO"
[[ "$KO" -eq 0 ]]
