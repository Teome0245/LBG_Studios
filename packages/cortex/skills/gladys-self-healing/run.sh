#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

echo "🩺 [Gladys Skill] Démonstration de la Boucle d'Auto-Réparation..."
python3 "${REPO_ROOT}/tools/test_self_healing_loop.py" "$@"
