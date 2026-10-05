# RAG LBG v1
#
# Embeddings : nomic-embed-text sur Ollama light (.111)
# Store : Postgres **pgvector** (image `pgvector/pgvector:pg16`) ; fallback JSONB puis mémoire
# Migration ops : bash packages/cortex/infra/scripts/enable_pgvector_rag_100.sh
#
# Flags :
#   LBG_RAG_ENABLED=0|1          (défaut 0)
#   LBG_RAG_EMBED_BASE_URL=http://192.168.0.111:11434
#   LBG_RAG_EMBED_MODEL=nomic-embed-text
#   LBG_RAG_EMBED_DIM=768
#   LBG_RAG_TOP_K=4
#   LBG_RAG_MAX_CHARS=1500
#   DATABASE_URL=…               (même Postgres RouterIA)
#
# Ingest :
#   cd packages/cortex/orchestrator && PYTHONPATH=. python -m services.rag.ingest
#   # ou sur .100 : docker compose exec backend …
#
# Prérequis ops :
#   ollama pull nomic-embed-text   # sur .111
#   image postgres = pgvector/pgvector:pg16 + CREATE EXTENSION vector
## But

Ancrer le chat Compagnon sur leçons / expériences / persona sans fine-tune.

## Hors scope v1

Résumé récursif de chat, indexation du fil brut, MemGPT tools R/W, NotebookLM critique.
