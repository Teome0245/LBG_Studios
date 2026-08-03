# Runbook — Plan Team LLM down → heuristique only

**Date** : 2026-08-03  
**ADR** : [0019](adr/0019-team-plan-llm-bus.md)

## Symptômes

- `POST /v1/team/plan` lent ou timeout
- `meta.llm.ok: false` / `meta.fallback: heuristic`
- Pilot badge `source: heuristic` alors que `LBG_TEAM_PLAN_LLM=1`
- Ollama 110/111 down, ou `LBG_REASON_LLM_DISABLED=1`

## Comportement attendu (pas un bug)

Le plan **ne bloque jamais** la Team : si le LLM échoue ou est off → **heuristique mots-clés** (`roles.plan_from_objective`).  
`source` ∈ `heuristic|llm|hybrid`. Avec `LBG_TEAM_PLAN_LLM=0` (défaut) : toujours heuristic.

## Checklist ops (140)

1. Flag plan LLM :
   ```bash
   grep LBG_TEAM_PLAN_LLM /etc/lbg-ia-mmo.env || true
   # Couper : LBG_TEAM_PLAN_LLM=0 puis restart orch
   ```
2. REASON / Ollama :
   ```bash
   curl -sS http://192.168.0.110:11434/api/tags | head
   curl -sS http://192.168.0.111:11434/api/tags | head   # light si configuré
   ```
3. Test forcé sans LLM :
   ```bash
   curl -sS -X POST http://127.0.0.1:8010/v1/team/plan \
     -H 'Content-Type: application/json' \
     -d '{"objective":"valide le LAN et brief PM","use_llm":false}'
   ```
4. Trace dernier plan : `GET /v1/team/meta` → `features.traces.last_plan`
5. Smoke :
   ```bash
   bash packages/cortex/infra/scripts/smoke_team_plan_bus.sh
   ```

## Règles produit

| Situation | Action |
|-----------|--------|
| Démo / prod instable LLM | `LBG_TEAM_PLAN_LLM=0` |
| Bench Atlas | `=1` + profil `LBG_TEAM_PLAN_LLM_PROFILE=json` |
| Timeout Pilot | proxy déjà à 120s ; réduire objectif / garder `use_llm:false` |
| JSON LLM invalide | auto-fallback heuristic (voir tests Vague 2) |

## Ne pas faire

- Remplacer Team par CrewAI pour « réparer » le plan
- Forcer cloud sans failover local documenté (`LBG_REASON_*`)
