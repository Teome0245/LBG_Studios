# ADR 0019 — Plan LLM borné + bus messages Team + mémoire

**Statut** : accepté — Vague 0–4 ✅ ; L3 Iris allowlist ✅ ; déploiement 140 ops  
**Date** : 2026-08-03  
**Validé** : 2026-08-03

## Livré

| Vague | Contenu |
|-------|---------|
| 0–1 | Schémas, `team_messages`, mémoire JSONL, API |
| 2 | Plan LLM borné + merge heuristic |
| 3 | Hooks bus autoconsult/followups + Pilot fil |
| 4 | Clôture mission Lyra, prune, **persist `campus_mission.json`**, learning verify |
| 5 (partiel) | Runbook LLM down ; traces `features.traces` dans `/v1/team/meta` |
| L3 Iris | `team/iris_l3.py` — apply auto allowlist après smoke (`LBG_IRIS_FORGE_L3=1`) |

## Flags / paths

- `LBG_TEAM_PLAN_LLM`, `LBG_TEAM_BUS_HOOKS`, `LBG_TEAM_CAMPUS_MISSION_AUTO_CLOSE`
- `LBG_TEAM_MISSION_PATH` (défaut à côté de la DB Team)
- `LBG_TEAM_MEMORY_*` + timer `lbg-team-memory-prune-job`
- `LBG_IRIS_FORGE_L3`, `LBG_IRIS_FORGE_L3_ALLOWLIST` (CSV optionnel)

## Ops

- Smoke : `infra/scripts/smoke_team_plan_bus.sh` (+ `--functional` dans `tools/smoke_lan_surfaces.sh`)
- Runbook : `docs/runbook_team_plan_llm_down.md`
- Install prune : `infra/scripts/install_team_memory_prune_job_vm.sh`

## Références

- `campus_conductor.py`, `plan_llm.py`, `bus_hooks.py`, `memory.py`, `iris_l3.py`
