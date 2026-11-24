#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <script_blender_py> [args...]"
    exit 1
fi

SCRIPT_BLENDER="$1"
shift

echo "🎨 [Gladys Skill] Délégation Blender Headless vers Atelier Omarchy (.143)..."
ssh -o BatchMode=yes -o ConnectTimeout=5 lbg@192.168.0.143 "blender --background --python '${SCRIPT_BLENDER}' -- $*"
