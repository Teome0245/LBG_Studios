# Suivi — Plan d'évolutions Studio / Jeu

**Généré** : 2026-10-14 08:03 CEST  
**Plan** : `PLAN_PROPOSITIONS_EVOLUTIONS` · source [`docs/PLAN_PROPOSITIONS_EVOLUTIONS.md`](../PLAN_PROPOSITIONS_EVOLUTIONS.md)  
**Pilot** : [http://192.168.0.140:8080/pilot/#/team](http://192.168.0.140:8080/pilot/#/team)  
**Plan entièrement réalisé** : ✅ OUI

## Synthèse

| Done | En cours | À relancer | Bloqué | Todo |
|:---:|:---:|:---:|:---:|:---:|
| 10 | 0 | 0 | 0 | 0 |

## Réalisés

### `1.1` — Barrière sémantique causerie / tool_loop (+ presence_brief T5)
- **Preuve** : smoke T1→T5 OK (ab01e3fc) · t5_src=llm · deploy CT100

### `1.2` — Streaming SSE /api/ask/stream + ChatFlow
- **Preuve** : SSE live CT100: POST /ask/stream start+ping+delta+done · UI useApi/ChatFlow · tests askStream+sse_ask · deploy 2026-10-09

### `1.3` — Modularisation Pilot Web (pilot.js)
- **Preuve** : 1.3 LIVE modularisation pilot_web en modules ES <1000L — fichiers: packages/cortex/pilot_web/pilot_team.js (872L) + packages/cortex/pilot_web/src/modules/team_fleet.js (629L); 17 modules pilot_*.js tous <1000L + stub pilot.js; smoke: node tools/gen_chunks.mjs --check -> OK 17 chunks alignes; npx vite build -> built in 1.40s; packages/cortex/.venv/bin/python -m pytest packages/cortex/backend/tests/test_pilot_static.py -> 3 passed.
- **Team** :
  - `running` [327159f2](http://192.168.0.140:8080/pilot/#/team?task=327159f2-ba9a-43c5-be5b-e3899026e80c) — Ticket plan 1.3 LIVE OpenCode .143 — Modularisation Pilot Web (pilot.js). Découper en modules ES <10

### `2.3` — NavigationServer3D navmesh prime-hub
- **Preuve** : navmesh NavigationServer3D LIVE 2026-10-11: hub_nav.gd bake 193 polys/16 empreintes ~0.6s; PATH_BUDGET_PER_TICK supprimé (budget_per_tick=0); selftest 40/40 entités/tick ~34us (nav_selftest.gd); smoke_navmesh_prime_hub.sh OK; /healthz navmesh.ok + /v1/dev/navmesh/probe source=navmesh (fallback A* grille hors bornes)

### `2.1` — Persistance SQLite hub_player_store
- **Preuve** : hub_db.gd SQLite threadé WAL + queue async BEGIN IMMEDIATE/COMMIT · hub_player_store.gd table player_positions + auto-migration JSON + miroir périodique · db_selftest.gd OK · smoke_sqlite_prime_hub.sh kill -9 sans corruption

### `2.2` — Découpage hub_sim.gd & main.gd
- **Preuve** : Serveur hub_sim.gd scinde en 5 modules <800L (771L, 447L, 185L, 196L, 142L, 103L, sim_selftest OK) et client main.gd scinde en 4 modules <800L (main 707L, gameplay 529L, quest 281L, net 675L, ui 506L, client_modular_selftest OK)

### `3.1` — Live World Stream Hub → Compagnon
- **Preuve** : hub_world_stream.gd ring buffer :8787 · world_stream.py fetch/cache/greeting · router_prompts.py short_social enrichi · character_layer.py contexte Lost Heaven · core.py GET /world/stream · useApi.js fetchWorldStream · test_world_stream.py 7/7 PASS · package CT100 OK

### `3.2` — Mémoire relationnelle jeu ↔ bureau
- **Preuve** : 3.2 LIVE — relation_memory.py (255L: fetch_relation_memory + append_relation_memory :8787; format_relation_memory_block/report) + useApi.js fetchRelationMemory/appendRelationMemory ; wiring core.py GET+POST /relation-memory, character_layer.py bloc in-game, llm_chat_phase.py attach ; smoke live hub 192.168.0.246:8787 append met+gift -> GET count=2 ok=True, overlay fetch_relation_memory ok=True entries=2 ; pytest compagnon_ui/server_overlay/tests/test_relation_memory.py 6/6 PASS.
- **Team** :
  - `done` [46ff8496](http://192.168.0.140:8080/pilot/#/team?task=46ff8496-edb4-4f2d-97ae-81e527881a3a) — Ticket plan 3.2 LIVE — mémoire relationnelle jeu↔bureau. Gate depends_on=3.1. Mark 3.2 done.

### `5.2` — Ruff + tests headless Godot CI
- **Preuve** : 5.2 LIVE — fichiers: .github/workflows/ci.yml (ruff check .), .github/workflows/godot-headless.yml (Godot 4.6.3 --headless + GODOT_BIN), tools/ci_godot_headless.sh, ruff.toml + pyproject.toml racine. Smoke local: ruff 0.17.0 'All checks passed!' ; bash tools/ci_godot_headless.sh -> sim/nav/db 18/18 OK en 4s.
- **Team** :
  - `done` [f35a71da](http://192.168.0.140:8080/pilot/#/team?task=f35a71da-ca7a-4748-a578-b472ee12512e) — Ticket plan 5.2 LIVE OpenCode .143 — Ruff + tests headless Godot CI (PAS une sonde healthz). Configu

### `5.1` — Packaging atomique server_overlay CT100
- **Preuve** : 5.1 LIVE 1.0.0+b40dbfb — packages/cortex/infra/scripts/deploy_compagnon_100.sh (build atomique/verify/apply/rollback/smoke) ; tools/smoke_server_overlay_package.sh OK build+verify+apply+rollback 36 fichiers ; pytest packages/cortex/infra/tests/test_server_overlay_package.py 6/6 PASS ; CT100 --check OK marker /opt/orchestrateur/.server_overlay_version package_sha=1ec4a79368b5be78… == paquet ; UI :5174=200, /api/character ok compagnon_v1
- **Team** :
  - `done` [298598ff](http://192.168.0.140:8080/pilot/#/team?task=298598ff-ac0d-4eaa-80a3-6d1a6cb53448) — Ticket plan 5.1 LIVE — packaging atomique server_overlay. Gate depends_on=5.2. Mark /v1/team/plan/ma

## En cours

_Rien en cours._

## À relancer (échecs Team)

_Rien à relancer._

## Bloqués (prérequis / L2)

_Aucun blocage._

## Todo

_File vide._

## Échecs Team liés au plan (hors ticket)

_Aucun._

## Rafraîchir

```bash
python3 tools/suivi_plan_evolutions.py --refresh
python3 tools/suivi_plan_evolutions.py --mark 1.2 done --evidence 'SSE live + smoke'
```
