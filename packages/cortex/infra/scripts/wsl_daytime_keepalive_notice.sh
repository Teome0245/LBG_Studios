#!/usr/bin/env bash
# Pousse l'avis « ne pas couper le WSL en journée » sur .10 (SSH :2222).
# Usage (core 140) :
#   bash infra/scripts/wsl_daytime_keepalive_notice.sh
# Timer recommandé : toutes les heures 7h–21h (hors fenêtre nuit 22h–7h).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/agents/src${PYTHONPATH:+:$PYTHONPATH}"
PY="${LBG_CORTEX_PYTHON:-${ROOT_DIR}/.venv/bin/python}"
if [[ ! -x "${PY}" ]]; then
  PY="$(command -v python3)"
fi

exec "${PY}" - <<'PY'
import json
from lbg_agents.wsl_schedule import push_daytime_keepalive_notice

print(json.dumps(push_daytime_keepalive_notice(), ensure_ascii=False, indent=2))
PY
