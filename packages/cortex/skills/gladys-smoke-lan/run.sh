#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

echo "🔍 [Gladys Skill] Lancement du Smoke Test Surfaces LAN..."
bash "${REPO_ROOT}/tools/smoke_lan_surfaces.sh" --functional "$@"
