#!/usr/bin/env bash
# Audit Ollama VM 110 — inventaire vs config LBG (LAN).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://192.168.0.110:11434}"
# Défauts = matrice ≤12B (docs/local_llm_route_matrix.md) — plus de 26b/27b.
export LBG_DIALOGUE_LLM_MODEL="${LBG_DIALOGUE_LLM_MODEL:-huihui_ai/gemma-4-abliterated:12b}"
export LBG_REASON_MODEL_FORGE="${LBG_REASON_MODEL_FORGE:-huihui_ai/gemma-4-abliterated:e2b}"
export LBG_REASON_MODEL_CODE="${LBG_REASON_MODEL_CODE:-huihui_ai/gemma-4-abliterated:12b}"
export LBG_REASON_MODEL_PM="${LBG_REASON_MODEL_PM:-huihui_ai/gemma-4-abliterated:12b}"
export LBG_REASON_LOCAL_MODEL="${LBG_REASON_LOCAL_MODEL:-huihui_ai/gemma-4-abliterated:e2b}"
cd "${ROOT}/orchestrator"
PYTHONPATH=.:../agents/src ../orchestrator/.venv/bin/python -c "
from team.ollama_audit import audit_ollama_lan
import json
print(json.dumps(audit_ollama_lan(), ensure_ascii=False, indent=2))
"
