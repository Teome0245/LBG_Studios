#!/usr/bin/env bash
# Smoke ticket plan 5.1 — packaging atomique server_overlay.
#
# Reproduit localement (sans CT100) le cycle du déploiement atomique :
#   1. build paquet versionné (tarball + MANIFEST.sha256 + VERSION)
#   2. verify checksum tarball + chaque fichier du manifest
#   3. apply dans une racine simulant /opt/orchestrateur (rename atomique)
#   4. attestation marqueur de version (package_sha == paquet)
#   5. rollback → état précédent restauré
#
# Usage :
#   bash tools/smoke_server_overlay_package.sh
#   bash tools/smoke_server_overlay_package.sh --remote   # idem via CT100 réel
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CORTEX="$ROOT/packages/cortex"
TOOL="${CORTEX}/infra/scripts/server_overlay_package.py"
BUILD="${CORTEX}/infra/scripts/build_server_overlay_package.sh"
PYTHON="${PYTHON:-python3}"

REMOTE=0
[[ "${1:-}" == "--remote" ]] && REMOTE=1

TMP="$(mktemp -d /tmp/opencode/overlay_smoke.XXXXXX)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

jf() { "${PYTHON}" -c "import sys,json;print(json.loads(sys.stdin.read().strip().splitlines()[-1]).get(sys.argv[1],''))" "$1"; }

echo "==> [1/5] build paquet atomique"
BUILD_JSON="$(bash "$BUILD" --json --out "$TMP/dist")"
VERSION="$(printf '%s' "$BUILD_JSON" | jf version)"
PACKAGE_SHA="$(printf '%s' "$BUILD_JSON" | jf package_sha)"
TARBALL="$(printf '%s' "$BUILD_JSON" | jf tarball)"
TARBALL_SHA="$(printf '%s' "$BUILD_JSON" | jf tarball_sha256)"
FILES="$(printf '%s' "$BUILD_JSON" | jf files)"
[[ -f "$TARBALL" && -f "${TARBALL}.sha256" ]] || { echo "ERR: tarball/sha manquant" >&2; exit 1; }
[[ "${#PACKAGE_SHA}" -eq 64 ]] || { echo "ERR: package_sha invalide" >&2; exit 1; }
echo "    version=${VERSION} files=${FILES} package_sha=${PACKAGE_SHA:0:16}…"

echo "==> [2/5] verify checksum (tarball + manifest)"
VERIFY_JSON="$( "${PYTHON}" "$TOOL" --json verify --tarball "$TARBALL" --sha256 "$TARBALL_SHA" )"
VCHECKED="$(printf '%s' "$VERIFY_JSON" | jf files_verified)"
[[ "$VCHECKED" -eq "$FILES" ]] || { echo "ERR: fichiers vérifiés $VCHECKED != $FILES" >&2; exit 1; }
echo "    ${VCHECKED} fichiers conformes au MANIFEST.sha256"

echo "==> [3/5] apply atomique (racine simulée /opt/orchestrateur)"
RROOT="$TMP/opt"
BK="$TMP/backup"
mkdir -p "$RROOT/backend/src/services"
echo "# ANCIEN-ROUTER" > "$RROOT/backend/src/services/router_prompts.py"
APPLY_JSON="$("${PYTHON}" "$TOOL" --json apply --tarball "$TARBALL" --root "$RROOT" \
  --backup-dir "$BK" --sha256 "$TARBALL_SHA" | tail -n1)"
APPLIED="$(printf '%s' "$APPLY_JSON" | jf files_applied)"
[[ "$APPLIED" -eq "$FILES" ]] || { echo "ERR: apply $APPLIED != $FILES" >&2; exit 1; }
grep -q "ANCIEN-ROUTER" "$RROOT/backend/src/services/router_prompts.py" && { echo "ERR: overlay non appliqué" >&2; exit 1; }
echo "    ${APPLIED} fichiers posés (rename atomique), ancien écrasé"

echo "==> [4/5] attestation marqueur de version"
STATUS_JSON="$("${PYTHON}" "$TOOL" --json status --root "$RROOT" | tail -n1)"
MSHA="$(printf '%s' "$STATUS_JSON" | jf package_sha)"
[[ "$MSHA" == "$PACKAGE_SHA" ]] || { echo "ERR: marker $MSHA != $PACKAGE_SHA" >&2; exit 1; }
echo "    marker package_sha=${MSHA:0:16}… == paquet"

echo "==> [5/5] rollback → état précédent"
BKTF="$(ls "$BK"/overlay_backup-*.tar.gz | head -1)"
RB_JSON="$("${PYTHON}" "$TOOL" --json rollback --root "$RROOT" --backup-tar "$BKTF" | tail -n1)"
grep -q "ANCIEN-ROUTER" "$RROOT/backend/src/services/router_prompts.py" || { echo "ERR: rollback router" >&2; exit 1; }
[[ ! -f "$RROOT/.server_overlay_version" ]] || { echo "ERR: marqueur non retiré" >&2; exit 1; }
echo "    $(printf '%s' "$RB_JSON" | jf restored) restaurés · $(printf '%s' "$RB_JSON" | jf removed) nouveaux retirés"

if [[ "$REMOTE" -eq 1 ]]; then
  echo "==> [remote] vérif version déployée sur CT100"
  bash "${CORTEX}/infra/scripts/deploy_compagnon_100.sh" --check || true
fi

echo "OK — packaging atomique server_overlay (ticket 5.1) : build+verify+apply+rollback · version=${VERSION} sha=${PACKAGE_SHA:0:16}…"
