#!/usr/bin/env bash
# Install / vérif alternative Cursor (VS Code + Cline + Continue) — Omarchy .143
# Usage (depuis WSL / poste LAN) :
#   bash packages/cortex/infra/scripts/install_editor_alt_omarchy_143.sh
# Sur la VM (Hyprland) : code ~/projects/LBG_Studios
set -euo pipefail
HOST="${LBG_OMARCHY_HOST:-192.168.0.143}"
USER="${LBG_OMARCHY_USER:-lbg}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPO="$(cd "${ROOT}/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

echo "==> Packages + extensions sur ${HOST}"
ssh -o BatchMode=yes -o ConnectTimeout=8 "${USER}@${HOST}" 'set -euo pipefail
yay -S --noconfirm --needed visual-studio-code-bin
code --install-extension continue.continue --force
code --install-extension saoudrizwan.claude-dev --force
mkdir -p ~/.continue ~/.cline/data/settings ~/projects/LBG_Studios
'

echo "==> Continue config (matrice LBG)"
cat >"${TMP}/config.yaml" <<'YAML'
# Continue → matrice LLM LBG (sans Cursor) — Omarchy .143
# Doc: packages/cortex/docs/cline_local_llm.md · local_llm_route_matrix.md
name: LBG Local
version: 1.0.0
schema: v1

models:
  - name: LBG Act 12b
    provider: ollama
    model: huihui_ai/gemma-4-abliterated:12b
    apiBase: http://192.168.0.110:11434
    roles: [chat, edit, apply]
  - name: LBG Forge e2b
    provider: ollama
    model: huihui_ai/gemma-4-abliterated:e2b
    apiBase: http://192.168.0.110:11434
    roles: [chat, edit, apply]
  - name: LBG Plan 9b
    provider: ollama
    model: huihui_ai/qwen3.5-abliterated:9b
    apiBase: http://192.168.0.110:11434
    roles: [chat, edit]
  - name: LBG Plan triage 0.8B
    provider: ollama
    model: huihui_ai/qwen3.5-abliterated:0.8B
    apiBase: http://192.168.0.111:11434
    roles: [chat, autocomplete]
  - name: LBG Clean 2B
    provider: ollama
    model: huihui_ai/qwen3.5-abliterated:2B
    apiBase: http://192.168.0.111:11434
    roles: [chat]

tabAutocompleteModel:
  title: LBG Autocomplete
  provider: ollama
  model: huihui_ai/qwen3.5-abliterated:0.8B
  apiBase: http://192.168.0.111:11434
YAML
scp -o BatchMode=yes "${TMP}/config.yaml" "${USER}@${HOST}:~/.continue/config.yaml"

echo "==> Cline seed (Act 12b / Plan 9b · FR)"
cat >"${TMP}/globalState.json" <<'JSON'
{
  "welcomeViewCompleted": true,
  "planActSeparateModelsSetting": true,
  "preferredLanguage": "Français",
  "customInstructions": "Réponds toujours en français. Plans et explications en français. Code/idents en anglais si le projet l'exige.",
  "planModeApiProvider": "ollama",
  "actModeApiProvider": "ollama",
  "ollamaBaseUrl": "http://192.168.0.110:11434",
  "openAiBaseUrl": "http://192.168.0.110:11434/v1",
  "actModeOllamaModelId": "huihui_ai/gemma-4-abliterated:12b",
  "planModeOllamaModelId": "huihui_ai/qwen3.5-abliterated:9b",
  "planModeOpenAiModelId": "huihui_ai/qwen3.5-abliterated:9b"
}
JSON
cat >"${TMP}/providers.json" <<'JSON'
{
  "version": 1,
  "lastUsedProvider": "ollama",
  "modes": {},
  "providers": {
    "ollama": {
      "settings": {
        "provider": "ollama",
        "model": "huihui_ai/gemma-4-abliterated:12b",
        "baseUrl": "http://192.168.0.110:11434"
      },
      "tokenSource": "manual"
    },
    "openai-compatible": {
      "settings": {
        "provider": "openai-compatible",
        "apiKey": "ollama",
        "model": "huihui_ai/qwen3.5-abliterated:9b",
        "baseUrl": "http://192.168.0.110:11434/v1",
        "headers": {},
        "reasoning": { "enabled": false, "effort": "medium" }
      },
      "tokenSource": "manual"
    }
  }
}
JSON
scp -o BatchMode=yes "${TMP}/globalState.json" "${TMP}/providers.json" "${USER}@${HOST}:/tmp/"
ssh -o BatchMode=yes "${USER}@${HOST}" 'python3 - <<'"'"'PY'"'"'
from pathlib import Path
import json
home = Path.home()
gs = home / ".cline/data/globalState.json"
gs.parent.mkdir(parents=True, exist_ok=True)
seed = json.loads(Path("/tmp/globalState.json").read_text())
d = json.loads(gs.read_text()) if gs.exists() else {}
d.update(seed)
gs.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
prov = home / ".cline/data/settings/providers.json"
prov.parent.mkdir(parents=True, exist_ok=True)
prov.write_text(Path("/tmp/providers.json").read_text())
print("cline seed OK")
PY'

echo "==> Sync sources LBG_Studios (rsync)"
rsync -az --delete \
  --exclude '.venv' --exclude 'node_modules' --exclude '.git' \
  --exclude 'packages/cortex/.venv' \
  "${REPO}/" "${USER}@${HOST}:~/projects/LBG_Studios/"

echo "==> Smoke Ollama depuis .143"
ssh -o BatchMode=yes "${USER}@${HOST}" 'set -e
curl -fsS -m 5 http://192.168.0.110:11434/api/tags >/dev/null && echo OK_110
curl -fsS -m 5 http://192.168.0.111:11434/api/tags >/dev/null && echo OK_111
code --list-extensions | grep -E "continue|claude-dev"
echo "Lancer depuis Hyprland: code ~/projects/LBG_Studios"
'
echo "Done — docs/sans_cursor.md · docs/omarchy_vm_143.md"
