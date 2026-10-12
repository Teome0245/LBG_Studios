#!/usr/bin/env bash
# Installe + active le timer Chœur L1 sur .140
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORTEX_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
HOST="${LBG_BACKEND_HOST:-192.168.0.140}"
REMOTE="lbg@${HOST}"
UNIT_S="${CORTEX_ROOT}/infra/systemd/lbg-team-choeur-l1-job.service"
UNIT_T="${CORTEX_ROOT}/infra/systemd/lbg-team-choeur-l1-job.timer"
JOB_PY="${CORTEX_ROOT}/agents/src/lbg_agents/spawn_team_choeur_l1_job.py"

[[ -f "$UNIT_S" && -f "$UNIT_T" && -f "$JOB_PY" ]] || { echo "ERR: units/job manquants" >&2; exit 1; }

echo "==> Sync job + units → ${HOST}"
scp -o BatchMode=yes -o ConnectTimeout=12 \
  "$JOB_PY" "${REMOTE}:/tmp/spawn_team_choeur_l1_job.py"
scp -o BatchMode=yes "$UNIT_S" "$UNIT_T" "${REMOTE}:/tmp/"

ssh -o BatchMode=yes "${REMOTE}" bash -s <<'REMOTE'
set -euo pipefail
sudo install -m 644 /tmp/spawn_team_choeur_l1_job.py \
  /opt/LBG_IA_MMO/agents/src/lbg_agents/spawn_team_choeur_l1_job.py
sudo install -m 644 /tmp/lbg-team-choeur-l1-job.service /etc/systemd/system/
sudo install -m 644 /tmp/lbg-team-choeur-l1-job.timer /etc/systemd/system/
sudo mkdir -p /var/lib/lbg/team_choeur_l1
sudo chown lbg:lbg /var/lib/lbg/team_choeur_l1
sudo systemctl daemon-reload
sudo systemctl enable --now lbg-team-choeur-l1-job.timer
systemctl is-enabled lbg-team-choeur-l1-job.timer
systemctl list-timers --all | grep choeur || true
# Dry-run oneshot (crée tâches si orch up) — ne bloque pas l'install
/opt/LBG_IA_MMO/.venv/bin/python -c '
from lbg_agents.spawn_team_choeur_l1_job import run_spawn
import json
print(json.dumps(run_spawn(persist=False, run_tasks=False), ensure_ascii=False)[:400])
' || echo "WARN: dry spawn (orch?) — timer quand même actif"
REMOTE

echo "OK — timer Chœur L1 actif sur ${HOST}"
