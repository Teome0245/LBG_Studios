#!/usr/bin/env bash
# Pont Cloud ↔ LAN — exécuteur WSL (pull Team).
#
# Poll l'orchestrateur .140 pour des tâches context.executor=wsl, exécute
# les skills allowlistés localement, renvoie le résultat à l'API Team.
#
# Usage :
#   cd ~/projects/LBG_Studios/packages/cortex
#   export LBG_WSL_EXECUTOR_TOKEN=...   # même valeur que sur .140 (si configuré)
#   bash infra/scripts/lbg_wsl_executor.sh --once
#   bash infra/scripts/lbg_wsl_executor.sh --loop
#   bash infra/scripts/lbg_wsl_executor.sh --enqueue diag_godot_supervisor "Diag post-smoke O2"
#
# Variables :
#   LBG_ORCHESTRATOR_URL        défaut http://192.168.0.140:8010
#   LBG_WSL_EXECUTOR_TOKEN      header X-LBG-WSL-TOKEN (optionnel si absent sur .140)
#   LBG_WSL_EXECUTOR_ID         défaut $(hostname)
#   LBG_WSL_POLL_INTERVAL_S     défaut 30 (mode --loop)
#   LBG_SSH_IDENTITY            transmis aux scripts enfants (diag, etc.)

set -euo pipefail

CORTEX_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MONO_ROOT="$(cd "${CORTEX_ROOT}/../.." && pwd)"
ORCH_URL="${LBG_ORCHESTRATOR_URL:-http://192.168.0.140:8010}"
ORCH_URL="${ORCH_URL%/}"
EXECUTOR_ID="${LBG_WSL_EXECUTOR_ID:-$(hostname -s 2>/dev/null || hostname)}"
POLL_INTERVAL="${LBG_WSL_POLL_INTERVAL_S:-30}"
MODE="once"
ENQUEUE_SKILL=""
ENQUEUE_OBJECTIVE=""

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --once) MODE="once"; shift ;;
    --loop) MODE="loop"; shift ;;
    --enqueue)
      ENQUEUE_SKILL="${2:?--enqueue requiert skill + objectif}"
      ENQUEUE_OBJECTIVE="${3:?--enqueue requiert skill + objectif}"
      shift 3
      ;;
    *)
      echo "Option inconnue : $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

curl_json() {
  local method="$1" url="$2" data="${3:-}"
  local -a hdr=(-H "Content-Type: application/json")
  [[ -n "${LBG_WSL_EXECUTOR_TOKEN:-}" ]] && hdr+=(-H "X-LBG-WSL-TOKEN: ${LBG_WSL_EXECUTOR_TOKEN}")
  if [[ -n "$data" ]]; then
    curl -sS -X "$method" "${hdr[@]}" -d "$data" "$url"
  else
    curl -sS -X "$method" "${hdr[@]}" "$url"
  fi
}

run_wsl_skill() {
  local skill="$1"
  shift
  local script="" cwd_mode="cortex"

  case "$skill" in
    diag_godot_supervisor) script="infra/scripts/diag_godot_supervisor_wsl.sh" ;;
    smoke_godot_m11_login) script="infra/scripts/smoke_godot_m11_login_lan.sh" ;;
    smoke_godot_m12_ws) script="infra/scripts/smoke_godot_m12_ws_lan.sh" ;;
    smoke_godot_owners) script="infra/scripts/smoke_godot_owners.sh" ;;
    smoke_lan_surfaces) script="tools/smoke_lan_surfaces.sh"; cwd_mode="monorepo" ;;
    smoke_cursor_agent) script="infra/scripts/smoke_cursor_agent_lan.sh" ;;
    *)
      echo "skill inconnu : ${skill}" >&2
      return 127
      ;;
  esac

  local path workdir="$CORTEX_ROOT"
  if [[ "$cwd_mode" == "monorepo" ]]; then
    path="${MONO_ROOT}/${script}"
    workdir="$MONO_ROOT"
  else
    path="${CORTEX_ROOT}/${script}"
  fi
  [[ -f "$path" ]] || { echo "script absent : ${path}" >&2; return 127; }

  (
    cd "$workdir"
    export LBG_SSH_IDENTITY="${LBG_SSH_IDENTITY:-}"
    bash "$path" "$@"
  )
}

process_one_task() {
  export ORCH_URL EXECUTOR_ID CORTEX_ROOT MONO_ROOT
  python3 <<'PY'
import json
import os
import subprocess
import sys

orch = os.environ["ORCH_URL"].rstrip("/")
executor_id = os.environ["EXECUTOR_ID"]
token = os.environ.get("LBG_WSL_EXECUTOR_TOKEN", "")

def curl_json(method: str, url: str, data: dict | None = None) -> dict:
    cmd = ["curl", "-sS", "-X", method, "-H", "Content-Type: application/json"]
    if token:
        cmd += ["-H", f"X-LBG-WSL-TOKEN: {token}"]
    if data is not None:
        cmd += ["-d", json.dumps(data)]
    cmd.append(url)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"curl failed: {proc.stderr[:300]}")
    return json.loads(proc.stdout)

poll = curl_json("POST", f"{orch}/v1/team/wsl/poll", {"executor_id": executor_id})
task = poll.get("task")
if not task:
    print("IDLE")
    sys.exit(2)

ctx = task.get("context") or {}
skill = str(ctx.get("wsl_skill") or "")
args = ctx.get("wsl_args") or []
if not isinstance(args, list):
    args = []
task_id = task["id"]
print(f"RUN {task_id[:8]} skill={skill}")

skills = {
    "diag_godot_supervisor": ("cortex", "infra/scripts/diag_godot_supervisor_wsl.sh"),
    "smoke_godot_m11_login": ("cortex", "infra/scripts/smoke_godot_m11_login_lan.sh"),
    "smoke_godot_m12_ws": ("cortex", "infra/scripts/smoke_godot_m12_ws_lan.sh"),
    "smoke_godot_owners": ("cortex", "infra/scripts/smoke_godot_owners.sh"),
    "smoke_lan_surfaces": ("mono", "tools/smoke_lan_surfaces.sh"),
    "smoke_cursor_agent": ("cortex", "infra/scripts/smoke_cursor_agent_lan.sh"),
}
if skill not in skills:
    complete = curl_json(
        "POST",
        f"{orch}/v1/team/wsl/tasks/{task_id}/complete",
        {
            "ok": False,
            "exit_code": 127,
            "stderr_tail": f"skill inconnu: {skill}",
            "executor_id": executor_id,
            "result": {"wsl_skill": skill},
        },
    )
    print("FAIL unknown skill")
    sys.exit(1)

mode, rel = skills[skill]
cortex = os.environ["CORTEX_ROOT"]
mono = os.environ["MONO_ROOT"]
workdir = mono if mode == "mono" else cortex
path = os.path.join(workdir, rel)
env = {**os.environ}
if os.environ.get("LBG_SSH_IDENTITY"):
    env["LBG_SSH_IDENTITY"] = os.environ["LBG_SSH_IDENTITY"]

proc = subprocess.run(
    ["bash", path, *[str(a) for a in args]],
    cwd=workdir,
    capture_output=True,
    text=True,
    env=env,
)
ok = proc.returncode == 0
if skill == "diag_godot_supervisor" and proc.returncode == 3:
    ok = True  # runtime OK, advisory seulement (cf. diag_godot_supervisor_wsl.sh)
curl_json(
    "POST",
    f"{orch}/v1/team/wsl/tasks/{task_id}/complete",
    {
        "ok": ok,
        "exit_code": proc.returncode,
        "stdout_tail": (proc.stdout or "")[-4000:],
        "stderr_tail": (proc.stderr or "")[-2000:],
        "executor_id": executor_id,
        "result": {"wsl_skill": skill},
    },
)
print(proc.stdout or "")
if not ok:
    print((proc.stderr or "")[-1000:], file=sys.stderr)
    sys.exit(1)
print(f"DONE {task_id[:8]} exit={proc.returncode}")
PY
}

if [[ -n "$ENQUEUE_SKILL" ]]; then
  payload="$(python3 -c "import json,sys; print(json.dumps({'wsl_skill':sys.argv[1],'objective':sys.argv[2],'actor_id':'wsl:cli'}))" "$ENQUEUE_SKILL" "$ENQUEUE_OBJECTIVE")"
  echo "=== Enqueue WSL ${ENQUEUE_SKILL} → ${ORCH_URL} ==="
  curl_json POST "${ORCH_URL}/v1/team/wsl/tasks" "$payload" | python3 -m json.tool
  exit 0
fi

echo "=== LBG WSL executor (${MODE}) → ${ORCH_URL} id=${EXECUTOR_ID} ===" >&2

if [[ "$MODE" == "loop" ]]; then
  while true; do
    if process_one_task; then
      :
    else
      rc=$?
      [[ "$rc" -eq 2 ]] && sleep "$POLL_INTERVAL"
      [[ "$rc" -ne 2 ]] && sleep 5
    fi
  done
else
  if process_one_task; then
    exit 0
  fi
  rc=$?
  if [[ "$rc" -eq 2 ]]; then
    echo "Aucune tâche WSL en file." >&2
    exit 0
  fi
  exit "$rc"
fi
