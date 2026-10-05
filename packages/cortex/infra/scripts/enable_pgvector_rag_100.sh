#!/usr/bin/env bash
# Passe Postgres Orchestrateur (.100) sur l'image pgvector/pgvector:pg16
# puis migre rag_chunks JSONB → vector + ré-ingest.
#
# Usage (depuis monorepo) :
#   bash packages/cortex/infra/scripts/enable_pgvector_rag_100.sh
#
set -euo pipefail

REMOTE_USER="${LBG_ORCH_CT100_USER:-root}"
REMOTE_HOST="${LBG_ORCH_CT100_HOST:-192.168.0.100}"
REMOTE="${REMOTE_USER}@${REMOTE_HOST}"
REMOTE_DIR="${LBG_ORCH_CT100_DIR:-/opt/orchestrateur}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORTEX_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
RAG_SRC="${CORTEX_ROOT}/orchestrator/services/rag"

echo "==> Sync package rag → ${REMOTE}"
rsync -az --delete \
  --exclude '__pycache__' --exclude '*.pyc' --exclude 'README.md' \
  "${RAG_SRC}/" "${REMOTE}:${REMOTE_DIR}/backend/src/services/rag/"

echo "==> Switch postgres image → pgvector/pgvector:pg16"
ssh "${REMOTE}" bash -s <<'EOF'
set -euo pipefail
cd /opt/orchestrateur
COMPOSE=docker-compose.yml
if ! grep -q 'pgvector/pgvector:pg16' "$COMPOSE"; then
  # Remplace image postgres:16 (variantes tag) par pgvector
  sed -i -E 's|image:\s*postgres:16([.-][a-zA-Z0-9._-]+)?|image: pgvector/pgvector:pg16|' "$COMPOSE"
fi
grep -A2 -E '^\s+postgres:' "$COMPOSE" | head -6
docker compose pull postgres
docker compose up -d postgres
# Attendre ready
for i in $(seq 1 30); do
  if docker compose exec -T postgres pg_isready -U orchestrateur >/dev/null 2>&1; then
    echo "postgres ready"
    break
  fi
  sleep 1
done
docker compose exec -T postgres psql -U orchestrateur -d orchestrateur -c 'CREATE EXTENSION IF NOT EXISTS vector;'
docker compose exec -T postgres psql -U orchestrateur -d orchestrateur -c '\dx'
# Recreate backend pour recharger code + reset cache schéma process
docker compose up -d --force-recreate backend
sleep 2
docker compose exec -T backend printenv LBG_RAG_ENABLED LBG_RAG_EMBED_MODEL | head -5
EOF

echo "==> Migrate schema + ingest"
ssh "${REMOTE}" bash -s <<'EOF'
set -euo pipefail
cd /opt/orchestrateur
docker compose exec -T backend bash -lc '
  export PYTHONPATH=/app
  python - <<PY
import asyncio
from src.services.rag.store import force_vector_migration, reset_memory_for_tests
from src.services.rag.ingest import ingest_all

async def main():
    reset_memory_for_tests()
    mode = await force_vector_migration()
    print("store_mode", mode)
    stats = await ingest_all()
    print(stats)

asyncio.run(main())
PY
'
docker compose exec -T postgres psql -U orchestrateur -d orchestrateur -c '\d rag_chunks'
docker compose exec -T postgres psql -U orchestrateur -d orchestrateur -c 'SELECT source_kind, count(*) FROM rag_chunks GROUP BY 1;'
EOF

echo "==> Smoke retrieve (vector)"
ssh "${REMOTE}" bash -s <<'EOF'
set -euo pipefail
cd /opt/orchestrateur
docker compose exec -T backend bash -lc '
  export PYTHONPATH=/app
  python - <<PY
import asyncio
from src.services.rag.store import ensure_schema, reset_memory_for_tests
from src.services.rag.retrieve import retrieve_chunks

async def main():
    reset_memory_for_tests()
    print("mode", await ensure_schema(force_refresh=True))
    chunks = await retrieve_chunks("ne pas clôturer mission si smoke rouge")
    print("n", len(chunks))
    for c in chunks[:3]:
        print(f"  {c.score:.3f} [{c.source_kind}:{c.source_id}]")

asyncio.run(main())
PY
'
EOF

echo "OK pgvector RAG"
