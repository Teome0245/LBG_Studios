#!/usr/bin/env bash
# Pull Ollama model sur un hôte LAN (API HTTP, pas SSH obligatoire).
#
# Usage :
#   bash infra/scripts/pull_ollama_model_lan.sh gemma4:e2b
#   bash infra/scripts/pull_ollama_model_lan.sh gemma4:e2b http://192.168.0.111:11434
#
set -euo pipefail

MODEL="${1:?modèle requis (ex. gemma4:e2b)}"
BASE="${2:-${LBG_OLLAMA_PULL_URL:-http://192.168.0.111:11434}}"
BASE="${BASE%/}"

echo "=== ollama pull ${MODEL} @ ${BASE} ==="
curl -sS -X POST "${BASE}/api/pull" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"${MODEL}\"}" \
  | python3 -c "
import json,sys
for line in sys.stdin:
    line=line.strip()
    if not line: continue
    try:
        d=json.loads(line)
        st=d.get('status') or ''
        if st: print(st)
    except json.JSONDecodeError:
        print(line[:200])
"

echo "=== tags ==="
curl -sS "${BASE}/api/tags" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for m in d.get('models') or []:
    print(' -', m.get('name'))
"
