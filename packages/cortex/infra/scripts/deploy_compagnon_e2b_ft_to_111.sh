#!/usr/bin/env bash
# Déploie un tag Ollama Compagnon FT depuis .10 (ou un GGUF) vers .111.
#
#   bash …/deploy_compagnon_e2b_ft_to_111.sh --tag lbg-compagnon-e2b-v2 --gguf /path/model.gguf
#   bash …/deploy_compagnon_e2b_ft_to_111.sh --tag lbg-compagnon-e2b-v2 --gguf /path/model.gguf --activate
#
# Mode --from-host (ollama save) si disponible sur la machine source.
#
set -euo pipefail

TAG="lbg-compagnon-e4b-v2"
FROM_HOST="${LBG_FT_FROM_HOST:-192.168.0.10}"
TO_HOST="${LBG_OLLAMA_LIGHT_HOST:-192.168.0.111}"
GGUF=""
ACTIVATE=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORTEX_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PERSONA_DIR="${CORTEX_ROOT}/infra/llm_persona_e2b"
TMP_MF="$(mktemp /tmp/lbg-e2b-v2.XXXXXX.Modelfile)"

cleanup() { rm -f "$TMP_MF"; }
trap cleanup EXIT

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag) TAG="${2:-}"; shift 2 ;;
    --from-host) FROM_HOST="${2:-}"; shift 2 ;;
    --to-host) TO_HOST="${2:-}"; shift 2 ;;
    --gguf) GGUF="${2:-}"; shift 2 ;;
    --activate) ACTIVATE=1; shift ;;
    -h|--help) sed -n '1,16p' "$0"; exit 0 ;;
    *) echo "arg inconnu: $1" >&2; exit 2 ;;
  esac
done

echo "==> tag=${TAG}  to=${TO_HOST}"

# Modelfile SYSTEM depuis pack caractère (FROM rempli selon mode)
python3 "${PERSONA_DIR}/build_modelfile.py" \
  --base "PLACEHOLDER_BASE" \
  --out "$TMP_MF" >/dev/null

if [[ -n "$GGUF" ]]; then
  [[ -f "$GGUF" ]] || { echo "GGUF introuvable: $GGUF" >&2; exit 1; }
  # Remplace FROM placeholder par chemin GGUF distant
  sed -i "s|^FROM PLACEHOLDER_BASE|FROM /tmp/${TAG}.gguf|" "$TMP_MF"
  echo "==> scp GGUF + Modelfile → ${TO_HOST}"
  scp -q "$GGUF" "root@${TO_HOST}:/tmp/${TAG}.gguf"
  scp -q "$TMP_MF" "root@${TO_HOST}:/tmp/Modelfile.${TAG}"
  ssh "root@${TO_HOST}" "ollama create ${TAG} -f /tmp/Modelfile.${TAG} && ollama show ${TAG} | head -25"
else
  echo "==> tentative ollama save sur ${FROM_HOST}"
  if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "root@${FROM_HOST}" \
      "ollama list | grep -F '${TAG}' && ollama help 2>/dev/null | grep -q save"; then
    echo "ERR: pas de tag/save sur ${FROM_HOST} — utiliser --gguf /chemin/model.gguf" >&2
    exit 3
  fi
  ssh "root@${FROM_HOST}" "rm -f /tmp/${TAG}.ollama.tar && ollama save ${TAG} /tmp/${TAG}.ollama.tar"
  scp -q "root@${FROM_HOST}:/tmp/${TAG}.ollama.tar" "root@${TO_HOST}:/tmp/${TAG}.ollama.tar"
  ssh "root@${TO_HOST}" "ollama load /tmp/${TAG}.ollama.tar && ollama show ${TAG} | head -25"
fi

echo "==> smoke generate ${TO_HOST}"
curl -sS --max-time 180 "http://${TO_HOST}:11434/api/generate" \
  -d "{\"model\":\"${TAG}\",\"prompt\":\"Salut, qui es-tu en une phrase ?\",\"stream\":false,\"options\":{\"num_predict\":60}}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('response') or d.get('error') or '')[:400])"

if [[ "$ACTIVATE" -eq 1 ]]; then
  REMOTE_USER="${LBG_ORCH_CT100_USER:-root}"
  REMOTE_HOST="${LBG_ORCH_CT100_HOST:-192.168.0.100}"
  echo "==> activate on .100 → ${TAG}"
  ssh "${REMOTE_USER}@${REMOTE_HOST}" bash -s <<EOF
set -euo pipefail
ENVF=/opt/orchestrateur/.env
upsert() {
  local key="\$1" val="\$2"
  if grep -q "^\${key}=" "\$ENVF"; then sed -i "s|^\${key}=.*|\${key}=\${val}|" "\$ENVF"
  else echo "\${key}=\${val}" >> "\$ENVF"; fi
}
upsert LBG_COMPAGNON_LAB_CHAT_MODEL "${TAG}"
upsert LBG_COMPANION_LLM_MODEL "${TAG}"
cd /opt/orchestrateur
docker compose up -d --force-recreate backend
docker compose exec -T backend printenv LBG_COMPAGNON_LAB_CHAT_MODEL
EOF
fi

echo "OK ${TAG} @ ${TO_HOST} (rollback: lbg-compagnon-e4b-v1 ou e2b-v1)"
