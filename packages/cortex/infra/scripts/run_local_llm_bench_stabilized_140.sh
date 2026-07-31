#!/usr/bin/env bash
# Bench stabilise 110 — deux lots separes (e2b puis 26b) depuis la VM 140.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
set -a
# shellcheck disable=SC1091
source /etc/lbg-ia-mmo.env 2>/dev/null || true
set +a

BASE="${LBG_BENCH_OLLAMA_URL:-http://192.168.0.110:11434}"
PY="${LBG_BENCH_PYTHON:-/opt/LBG_IA_MMO/.venv/bin/python}"
OUT_DIR="${LBG_BENCH_OUT_DIR:-tmp/local_llm_bench}"
mkdir -p "$OUT_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"

echo "BENCH_STABILIZED_START $STAMP base=$BASE"

"$PY" infra/scripts/atlas_bench_watchdog.py \
  --base-url "$BASE" \
  --out-dir "$OUT_DIR" \
  --min-oks "${LBG_ATLAS_BENCH_MIN_OKS:-3}" \
  --no-alert

echo "BENCH_STABILIZED_DONE $STAMP"
