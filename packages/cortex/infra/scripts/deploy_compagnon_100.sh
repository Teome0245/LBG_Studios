#!/usr/bin/env bash
# Déploie le Compagnon UI (packages/cortex/compagnon_ui) sur CT `.100` → :5174
#
# Déploiement ATOMIQUE du sous-package `server_overlay` (ticket plan 5.1) :
#   build paquet versionné → upload → vérif checksum → apply (rename par fichier)
#   → marqueur de version → wiring backend → rebuild → smoke → rollback si échec.
#
# Usage (depuis la racine LBG_Studios ou packages/cortex) :
#   bash packages/cortex/infra/scripts/deploy_compagnon_100.sh            # déploie
#   bash packages/cortex/infra/scripts/deploy_compagnon_100.sh --smoke    # + smoke
#   bash packages/cortex/infra/scripts/deploy_compagnon_100.sh --check    # version déployée
#   bash packages/cortex/infra/scripts/deploy_compagnon_100.sh --build-only
#   bash packages/cortex/infra/scripts/deploy_compagnon_100.sh --rollback # restaure N-1
#
# Prérequis : SSH root@192.168.0.100 ; stack docker /opt/orchestrateur
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORTEX_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
UI_ROOT="${CORTEX_ROOT}/compagnon_ui"
OVERLAY_DIR="${UI_ROOT}/server_overlay"
PACKAGE_TOOL="${SCRIPT_DIR}/server_overlay_package.py"
BUILD_SCRIPT="${SCRIPT_DIR}/build_server_overlay_package.sh"
LOCAL_DIST="${LBG_OVERLAY_OUT:-${CORTEX_ROOT}/dist/server_overlay}"
RAG_PACKAGE="${CORTEX_ROOT}/orchestrator/services/rag"
KNOWLEDGE_DIR="${CORTEX_ROOT}/knowledge"
KNOWLEDGE_PACK="${KNOWLEDGE_DIR}/character/compagnon_v1.json"
STUDIO_BRAIN_PACK="${KNOWLEDGE_DIR}/studio_brain_v1.json"
STUDIO_ROOT="$(cd "${CORTEX_ROOT}/../.." && pwd)"
SUIVI_DOCS="${STUDIO_ROOT}/docs/suivi"
SUIVI_TOOL="${STUDIO_ROOT}/tools/suivi_plan_evolutions.py"
PYTHON="${PYTHON:-python3}"

REMOTE_USER="${LBG_ORCH_CT100_USER:-root}"
REMOTE_HOST="${LBG_ORCH_CT100_HOST:-192.168.0.100}"
REMOTE="${REMOTE_USER}@${REMOTE_HOST}"
REMOTE_DIR="${LBG_ORCH_CT100_DIR:-/opt/orchestrateur}"
STAGING_DIR="${REMOTE_DIR}/.overlay_staging"
BACKUP_DIR="${REMOTE_DIR}/.overlay_backup"
MARKER="${REMOTE_DIR}/.server_overlay_version"

SMOKE=0
MODE="deploy"
[[ "${1:-}" == "--smoke" ]] && SMOKE=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --smoke) SMOKE=1; shift ;;
    --check) MODE="check"; shift ;;
    --build-only) MODE="build-only"; shift ;;
    --rollback) MODE="rollback"; shift ;;
    -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
    *) echo "ARG inconnu: $1" >&2; exit 2 ;;
  esac
done

die() { echo "ERR: $*" >&2; exit 1; }

[[ -d "${UI_ROOT}/src" ]] || die "compagnon_ui introuvable: ${UI_ROOT}"
[[ -f "${OVERLAY_DIR}/pyproject.toml" && -f "${OVERLAY_DIR}/overlay.map" ]] \
  || die "server_overlay non formalisé (pyproject.toml/overlay.map manquants)"

py_field() {  # py_field <json> <key>
  "${PYTHON}" -c "import sys,json;print(json.loads(sys.argv[1]).get(sys.argv[2],''))" "$1" "$2"
}

# ---------------------------------------------------------------------------
# 1. Build du paquet atomique (version + checksum de version)
# ---------------------------------------------------------------------------
echo "==> Build paquet server_overlay atomique"
BUILD_JSON="$(bash "${BUILD_SCRIPT}" --json --out "${LOCAL_DIST}")"
VERSION="$(py_field "${BUILD_JSON}" version)"
PACKAGE_SHA="$(py_field "${BUILD_JSON}" package_sha)"
TARBALL="$(py_field "${BUILD_JSON}" tarball)"
TARBALL_SHA="$(py_field "${BUILD_JSON}" tarball_sha256)"
FILES="$(py_field "${BUILD_JSON}" files)"
TARBALL_NAME="$(basename "${TARBALL}")"
[[ -n "${VERSION}" && -n "${PACKAGE_SHA}" && -f "${TARBALL}" ]] || die "build invalide: ${BUILD_JSON}"
echo "    version=${VERSION} package_sha=${PACKAGE_SHA:0:16}… files=${FILES}"
echo "    tarball=${TARBALL} sha256=${TARBALL_SHA:0:16}…"

if [[ "${MODE}" == "build-only" ]]; then
  echo "OK  build-only : ${TARBALL}"
  exit 0
fi

ssh_remote() { ssh -o BatchMode=yes -o ConnectTimeout=10 "${REMOTE}" "$@"; }

# ---------------------------------------------------------------------------
# 2. --check : version déployée sur CT100 (checksum de version)
# ---------------------------------------------------------------------------
if [[ "${MODE}" == "check" ]]; then
  echo "==> Version déployée sur ${REMOTE_HOST}"
  ssh_remote "mkdir -p ${STAGING_DIR}"
  if [[ -f "${PACKAGE_TOOL}" ]]; then
    rsync -az "${PACKAGE_TOOL}" "${REMOTE}:${STAGING_DIR}/server_overlay_package.py" 2>/dev/null || true
  fi
  REMOTE_STATUS="$(ssh_remote "python3 ${STAGING_DIR}/server_overlay_package.py --json status --root ${REMOTE_DIR}" 2>/dev/null || true)"
  [[ -n "${REMOTE_STATUS}" ]] || die "status distant indisponible (marqueur absent ?)"
  echo "${REMOTE_STATUS}" | "${PYTHON}" -m json.tool
  REMOTE_SHA="$(py_field "${REMOTE_STATUS}" package_sha)"
  if [[ "${REMOTE_SHA}" == "${PACKAGE_SHA}" ]]; then
    echo "OK  CT100 à jour : ${VERSION} (${PACKAGE_SHA:0:16}…)"
  else
    echo "WARN CT100=${REMOTE_SHA:0:16}… ≠ local=${PACKAGE_SHA:0:16}… (déploiement requis)"
  fi
  exit 0
fi

# ---------------------------------------------------------------------------
# 3. --rollback : restaure la sauvegarde précédente
# ---------------------------------------------------------------------------
if [[ "${MODE}" == "rollback" ]]; then
  echo "==> Rollback server_overlay sur ${REMOTE_HOST}"
  ssh_remote "mkdir -p ${STAGING_DIR}"
  rsync -az "${PACKAGE_TOOL}" "${REMOTE}:${STAGING_DIR}/server_overlay_package.py"
  ssh_remote "python3 ${STAGING_DIR}/server_overlay_package.py --json rollback --root ${REMOTE_DIR} --backup-dir ${BACKUP_DIR}" \
    | "${PYTHON}" -m json.tool
  ssh_remote "cd ${REMOTE_DIR} && docker compose up -d --force-recreate backend frontend"
  echo "OK  rollback appliqué"
  exit 0
fi

# ---------------------------------------------------------------------------
# 4. Upload + vérif checksum + apply atomique (backup/rollback prêts)
# ---------------------------------------------------------------------------
echo "==> Upload paquet → ${REMOTE}:${STAGING_DIR}"
ssh_remote "mkdir -p ${STAGING_DIR} ${BACKUP_DIR}"
rsync -az "${TARBALL}" "${TARBALL}.sha256" "${PACKAGE_TOOL}" "${REMOTE}:${STAGING_DIR}/"

echo "==> Vérif checksum + apply atomique"
APPLY_OUT=""
if ! APPLY_OUT="$(ssh_remote "python3 ${STAGING_DIR}/server_overlay_package.py --json verify --tarball ${STAGING_DIR}/${TARBALL_NAME} --sha256 ${TARBALL_SHA} && python3 ${STAGING_DIR}/server_overlay_package.py --json apply --tarball ${STAGING_DIR}/${TARBALL_NAME} --root ${REMOTE_DIR} --backup-dir ${BACKUP_DIR} --marker ${MARKER} --sha256 ${TARBALL_SHA}")"; then
  echo "ERR: apply distant échoué — tentative de rollback" >&2
  ssh_remote "python3 ${STAGING_DIR}/server_overlay_package.py --json rollback --root ${REMOTE_DIR} --backup-dir ${BACKUP_DIR} || true"
  exit 1
fi
APPLY_JSON="$(printf '%s\n' "${APPLY_OUT}" | tail -n1)"
BACKUP_TAR="$(py_field "${APPLY_JSON}" backup_tarball)"
APPLIED="$(py_field "${APPLY_JSON}" files_applied)"
[[ "$(py_field "${APPLY_JSON}" ok)" == "True" ]] || die "apply non ok: ${APPLY_JSON}"
echo "    ${APPLIED} fichiers appliqués · backup=${BACKUP_TAR}"
echo "    marqueur version=${MARKER} (package_sha=${PACKAGE_SHA:0:16}…)"

# ---------------------------------------------------------------------------
# 5. Sync UI frontend (hors server_overlay) + assets non-overlay
# ---------------------------------------------------------------------------
echo "==> Sync Compagnon UI → ${REMOTE}:${REMOTE_DIR}/frontend/"
rsync -az --delete \
  --exclude 'node_modules' \
  --exclude 'dist' \
  --exclude 'server_overlay' \
  --exclude '.env' \
  "${UI_ROOT}/" "${REMOTE}:${REMOTE_DIR}/frontend/"

if [[ -d "${RAG_PACKAGE}" ]]; then
  echo "==> Package services/rag → backend"
  rsync -az --delete \
    --exclude '__pycache__' --exclude '*.pyc' --exclude 'README.md' \
    "${RAG_PACKAGE}/" "${REMOTE}:${REMOTE_DIR}/backend/src/services/rag/"
fi

if [[ -d "${KNOWLEDGE_DIR}" ]]; then
  echo "==> Knowledge RAG (rag_facts + lessons + character) → backend/knowledge"
  ssh_remote "mkdir -p ${REMOTE_DIR}/backend/knowledge/character"
  rsync -az \
    "${KNOWLEDGE_DIR}/rag_facts.jsonl" \
    "${KNOWLEDGE_DIR}/lessons_learned.json" \
    "${REMOTE}:${REMOTE_DIR}/backend/knowledge/"
  if [[ -f "${KNOWLEDGE_PACK}" ]]; then
    rsync -az "${KNOWLEDGE_PACK}" \
      "${REMOTE}:${REMOTE_DIR}/backend/knowledge/character/compagnon_v1.json"
    rsync -az "${KNOWLEDGE_PACK}" \
      "${REMOTE}:${REMOTE_DIR}/backend/src/config/character/compagnon_v1.json"
    rsync -az "${KNOWLEDGE_PACK}" \
      "${REMOTE}:${REMOTE_DIR}/backend/src/services/character/compagnon_v1.json"
  fi
  if [[ -f "${STUDIO_BRAIN_PACK}" ]]; then
    echo "==> Studio Brain pack → knowledge + character"
    rsync -az "${STUDIO_BRAIN_PACK}" \
      "${REMOTE}:${REMOTE_DIR}/backend/knowledge/studio_brain_v1.json"
    rsync -az "${STUDIO_BRAIN_PACK}" \
      "${REMOTE}:${REMOTE_DIR}/backend/src/config/character/studio_brain_v1.json"
    rsync -az "${STUDIO_BRAIN_PACK}" \
      "${REMOTE}:${REMOTE_DIR}/backend/src/services/character/studio_brain_v1.json"
  fi
fi

if [[ -d "${SUIVI_DOCS}" ]]; then
  echo "==> Sync docs/suivi + tools → ${REMOTE_DIR}"
  ssh_remote "mkdir -p '${REMOTE_DIR}/docs/suivi' '${REMOTE_DIR}/tools'"
  rsync -az "${SUIVI_DOCS}/" "${REMOTE}:${REMOTE_DIR}/docs/suivi/"
fi
if [[ -f "${SUIVI_TOOL}" ]]; then
  rsync -az "${SUIVI_TOOL}" "${REMOTE}:${REMOTE_DIR}/tools/suivi_plan_evolutions.py"
fi

# ---------------------------------------------------------------------------
# 6. Wiring backend idempotent (routers + env) — aligné sur le paquet
# ---------------------------------------------------------------------------
echo "==> Wiring backend (factory routers + env)"
ssh_remote 'bash -s' <<'WIRING'
set -euo pipefail
FACTORY=/opt/orchestrateur/backend/src/app/factory.py
python3 - <<'PY'
from pathlib import Path
p = Path("/opt/orchestrateur/backend/src/app/factory.py")
routers = [
    ("desktop_approval", "desktop_approval_router"),
    ("character_api", "character_api_router"),
    ("spontaneity_api", "spontaneity_api_router"),
    ("tts_api", "tts_api_router"),
]
text = p.read_text()
imp_anchor = "from src.routers.team import router as team_router\n"
inc_anchor = "    app.include_router(core_router)\n"
changed = False
for module, alias in routers:
    if alias not in text:
        imp = f"from src.routers.{module} import router as {alias}\n"
        inc = f"    app.include_router({alias})\n"
        text = text.replace(imp_anchor, imp_anchor + imp, 1) if imp_anchor in text else imp + text
        text = text.replace(inc_anchor, inc_anchor + inc, 1) if inc_anchor in text else text + inc
        changed = True
p.write_text(text)
print("factory.py: routers wired" if changed else "factory.py: already wired")
PY

ENVF=/opt/orchestrateur/.env
if [[ -f "$ENVF" ]]; then
  grep -q '^CORTEX_ORCHESTRATOR_URL=' "$ENVF" || echo 'CORTEX_ORCHESTRATOR_URL=http://192.168.0.140:8010' >> "$ENVF"
  grep -q '^LBG_TTS_ENABLED=' "$ENVF" || echo 'LBG_TTS_ENABLED=1' >> "$ENVF"
  grep -q '^LBG_TTS_PROVIDER=' "$ENVF" || echo 'LBG_TTS_PROVIDER=edge' >> "$ENVF"
  grep -q '^LBG_TTS_FALLBACK=' "$ENVF" || echo 'LBG_TTS_FALLBACK=piper' >> "$ENVF"
  grep -q '^LBG_EDGE_VOICE=' "$ENVF" || echo 'LBG_EDGE_VOICE=fr-FR-DeniseNeural' >> "$ENVF"
  grep -q '^LBG_PIPER_URL=' "$ENVF" || echo 'LBG_PIPER_URL=http://192.168.0.111:8098' >> "$ENVF"
  grep -q '^LBG_PIPER_VOICE=' "$ENVF" || echo 'LBG_PIPER_VOICE=fr_FR-siwis-medium' >> "$ENVF"
fi
REQ=/opt/orchestrateur/backend/requirements.txt
if [[ -f "$REQ" ]] && ! grep -qiE '^edge-tts([=<>]|$)' "$REQ"; then
  echo 'edge-tts>=6.1.0' >> "$REQ"
fi
mkdir -p /var/lib/lbg/compagnon /var/lib/lbg/spontaneity /var/lib/lbg/character
echo "wiring ok"
WIRING

# ---------------------------------------------------------------------------
# 7. Rebuild Docker (frontend + backend)
# ---------------------------------------------------------------------------
echo "==> Rebuild Docker frontend + backend"
ssh_remote "cd ${REMOTE_DIR} && docker compose build frontend backend && docker compose up -d --force-recreate frontend backend"

# ---------------------------------------------------------------------------
# 8. Smoke + rollback automatique si échec
# ---------------------------------------------------------------------------
rollback_remote() {
  echo "==> ROLLBACK server_overlay (smoke échoué)"
  if [[ -n "${BACKUP_TAR}" ]]; then
    ssh_remote "python3 ${STAGING_DIR}/server_overlay_package.py --json rollback --root ${REMOTE_DIR} --backup-tar ${BACKUP_TAR}" \
      | "${PYTHON}" -m json.tool || true
  else
    ssh_remote "python3 ${STAGING_DIR}/server_overlay_package.py --json rollback --root ${REMOTE_DIR} --backup-dir ${BACKUP_DIR}" || true
  fi
  ssh_remote "cd ${REMOTE_DIR} && docker compose up -d --force-recreate backend frontend" || true
}

run_smoke() {
  local i ui_ok=0
  for i in $(seq 1 15); do
    if curl -fsS "http://${REMOTE_HOST}:5174/" >/dev/null 2>&1; then
      ui_ok=1; echo "OK  UI :5174"; break
    fi
    sleep 2
  done
  [[ "$ui_ok" -eq 1 ]] || { echo "ERR: UI :5174 indisponible"; return 1; }
  local api_ok=0
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if curl -fsS "http://${REMOTE_HOST}:3000/health" >/dev/null 2>&1; then
      api_ok=1; echo "OK  API :3000/health"; break
    fi
    sleep 2
  done
  [[ "$api_ok" -eq 1 ]] || { echo "ERR: API :3000/health"; return 1; }
  curl -fsS -X POST "http://${REMOTE_HOST}:5174/api/ask" \
    -H 'Content-Type: application/json' \
    -d '{"prompt":"Bonjour","mode":"auto","profile":"compagnon"}' \
    | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('response') or {}; print('chat', (r.get('content') or '')[:120])" \
    || { echo "ERR: /api/ask"; return 1; }
  curl -fsS "http://${REMOTE_HOST}:5174/api/character/" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print('character', d.get('ok'), d.get('pack_id'), 'dials', len(d.get('dials') or {}))" \
    || { echo "ERR: /api/character"; return 1; }
  curl -fsS "http://${REMOTE_HOST}:5174/api/tts/health" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print('tts', d.get('ok'), 'enabled', d.get('enabled'), 'voice', d.get('voice'))" \
    || { echo "ERR: /api/tts/health"; return 1; }
  # Attestation checksum de version (marqueur distant == paquet local)
  local remote_sha
  remote_sha="$(ssh_remote "python3 ${STAGING_DIR}/server_overlay_package.py --json status --root ${REMOTE_DIR}" \
    | python3 -c "import sys,json;print(json.loads(sys.stdin.read().strip().splitlines()[-1]).get('package_sha',''))")"
  [[ "${remote_sha}" == "${PACKAGE_SHA}" ]] || { echo "ERR: marker sha ${remote_sha} != ${PACKAGE_SHA}"; return 1; }
  echo "OK  marker package_sha ${remote_sha:0:16}…"
  return 0
}

if [[ "$SMOKE" -eq 1 ]]; then
  echo "==> Smoke Compagnon + attestation checksum"
  if ! run_smoke; then
    rollback_remote
    die "smoke échoué — rollback ${VERSION} effectué"
  fi
fi

echo "OK  Compagnon http://${REMOTE_HOST}:5174/ · version ${VERSION} (${PACKAGE_SHA:0:16}…) · API :3000 · Pilot ops http://192.168.0.140:8080/pilot/"
