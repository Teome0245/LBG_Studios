#!/usr/bin/env bash
# Build du paquet atomique server_overlay (ticket plan 5.1).
#
# Produit dans --out (défaut : dist/server_overlay) :
#   server_overlay-<version>.tar.gz          paquet versionné
#   server_overlay-<version>.tar.gz.sha256   checksum du paquet
#   (le paquet embarque MANIFEST.sha256 + VERSION → checksum de version)
#
# Usage :
#   bash packages/cortex/infra/scripts/build_server_overlay_package.sh [--out DIR] [--json]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORTEX_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
OVERLAY_DIR="${CORTEX_ROOT}/compagnon_ui/server_overlay"
TOOL="${SCRIPT_DIR}/server_overlay_package.py"
PYTHON="${PYTHON:-python3}"

OUT="${LBG_OVERLAY_OUT:-${CORTEX_ROOT}/dist/server_overlay}"
JSON=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    --json) JSON="--json"; shift ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "ARG inconnu: $1" >&2; exit 2 ;;
  esac
done

[[ -f "${OVERLAY_DIR}/pyproject.toml" ]] || { echo "ERR: pyproject.toml manquant (${OVERLAY_DIR})" >&2; exit 1; }
[[ -f "${OVERLAY_DIR}/overlay.map" ]] || { echo "ERR: overlay.map manquant (${OVERLAY_DIR})" >&2; exit 1; }

exec "${PYTHON}" "${TOOL}" ${JSON} build \
  --overlay-dir "${OVERLAY_DIR}" \
  --out "${OUT}"
