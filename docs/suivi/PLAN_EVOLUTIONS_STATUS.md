# Suivi — Plan d'évolutions Studio / Jeu

**Généré** : 2026-10-11 14:01 CEST  
**Plan** : `PLAN_PROPOSITIONS_EVOLUTIONS` · source [`docs/PLAN_PROPOSITIONS_EVOLUTIONS.md`](../PLAN_PROPOSITIONS_EVOLUTIONS.md)  
**Pilot** : [http://192.168.0.140:8080/pilot/#/team](http://192.168.0.140:8080/pilot/#/team)  
**Plan entièrement réalisé** : ❌ non

## Synthèse

| Done | En cours | À relancer | Bloqué | Todo |
|:---:|:---:|:---:|:---:|:---:|
| 6 | 2 | 0 | 1 | 1 |

## Réalisés

### `1.1` — Barrière sémantique causerie / tool_loop (+ presence_brief T5)
- **Preuve** : smoke T1→T5 OK (ab01e3fc) · t5_src=llm · deploy CT100

### `1.2` — Streaming SSE /api/ask/stream + ChatFlow
- **Preuve** : SSE live CT100: POST /ask/stream start+ping+delta+done · UI useApi/ChatFlow · tests askStream+sse_ask · deploy 2026-10-09

### `1.3` — Modularisation Pilot Web (pilot.js)
- **Preuve** : 17 modules ES <1000L (pilot_*.js) · stub doc pilot.js · gen_chunks --check OK (17 chunks) · build Vite dist/ 957ms OK · pytest test_pilot_static PASS
- **Team** :
  - `queued` [327159f2](http://192.168.0.140:8080/pilot/#/team?task=327159f2-ba9a-43c5-be5b-e3899026e80c) — Ticket plan 1.3 LIVE OpenCode .143 — Modularisation Pilot Web (pilot.js). Découper en modules ES <10
  - `done` [d14a9f03](http://192.168.0.140:8080/pilot/#/team?task=d14a9f03-7274-449c-83fe-4510c113d50f) — Triage échec dev_studio — analyser et proposer correctif/relance (parent=412a7852-185f-4721-a1ba-722
  - `failed` [412a7852](http://192.168.0.140:8080/pilot/#/team?task=412a7852-185f-4721-a1ba-722e3aa40a20) — Ticket plan 1.3 LIVE OpenCode .143 — Modularisation Pilot Web (pilot.js). Découper en modules ES <10

### `2.1` — Persistance SQLite hub_player_store
- **Preuve** : hub_db.gd SQLite threadé WAL + queue async BEGIN IMMEDIATE/COMMIT · hub_player_store.gd table player_positions + auto-migration JSON + miroir périodique · db_selftest.gd OK · smoke_sqlite_prime_hub.sh kill -9 sans corruption
- **Team** :
  - `running` [3ac060bc](http://192.168.0.140:8080/pilot/#/team?task=3ac060bc-136e-455b-a195-19d0cbd3d9a4) — Ticket plan 2.1 LIVE — SQLite hub_player_store. Gate depends_on=2.3. Ne démarre que si 2.3 done. Mar
  - `cancelled` [098673ed](http://192.168.0.140:8080/pilot/#/team?task=098673ed-4fdd-4823-af57-258d99ec55f4) — Ticket plan 2.1 LIVE — SQLite hub_player_store. Conductor gate depends_on=2.3. Ne démarre que si 2.3

### `2.3` — NavigationServer3D navmesh prime-hub
- **Preuve** : navmesh NavigationServer3D LIVE 2026-10-11: hub_nav.gd bake 193 polys/16 empreintes ~0.6s; PATH_BUDGET_PER_TICK supprimé (budget_per_tick=0); selftest 40/40 entités/tick ~34us (nav_selftest.gd); smoke_navmesh_prime_hub.sh OK; /healthz navmesh.ok + /v1/dev/navmesh/probe source=navmesh (fallback A* grille hors bornes)
- **Team** :
  - `running` [3ac060bc](http://192.168.0.140:8080/pilot/#/team?task=3ac060bc-136e-455b-a195-19d0cbd3d9a4) — Ticket plan 2.1 LIVE — SQLite hub_player_store. Gate depends_on=2.3. Ne démarre que si 2.3 done. Mar
  - `done` [df8ab93a](http://192.168.0.140:8080/pilot/#/team?task=df8ab93a-eadb-4d68-be23-29c3377456e2) — Ticket plan 2.3 LIVE OpenCode .143 — NavigationServer3D navmesh prime-hub (Lost Heaven). Implémente 
  - `cancelled` [098673ed](http://192.168.0.140:8080/pilot/#/team?task=098673ed-4fdd-4823-af57-258d99ec55f4) — Ticket plan 2.1 LIVE — SQLite hub_player_store. Conductor gate depends_on=2.3. Ne démarre que si 2.3

### `5.1` — Packaging atomique server_overlay CT100
- **Preuve** : CT100 packaging atomique LIVE 1.0.0+4bcc331: server_overlay/pyproject.toml + overlay.map (33 fichiers); server_overlay_package.py build/verify/apply/rollback; deploy_compagnon_100.sh --smoke OK; marker /opt/orchestrateur/.server_overlay_version package_sha=8128a4e3470abded597b70e855289bab608e23c4fd6acbe273e4062ec272e5a5; smoke tools/smoke_server_overlay_package.sh OK; rollback testé
- **Team** :
  - `queued` [298598ff](http://192.168.0.140:8080/pilot/#/team?task=298598ff-ac0d-4eaa-80a3-6d1a6cb53448) — Ticket plan 5.1 LIVE — packaging atomique server_overlay. Gate depends_on=5.2. Mark /v1/team/plan/ma
  - `cancelled` [cb82a394](http://192.168.0.140:8080/pilot/#/team?task=cb82a394-e5f5-4490-9c39-90337233d0a8) — Ticket plan 5.1 LIVE OpenCode — packaging atomique server_overlay CT100. Preuve: chemins + deploy_co
  - `done` [d29a9100](http://192.168.0.140:8080/pilot/#/team?task=d29a9100-aec3-48b0-8e3e-5469a72aff09) — Ticket plan 5.1 LIVE OpenCode — packaging atomique server_overlay CT100. Gate depends_on=5.2. ide_cl
  - `cancelled` [b7abdff8](http://192.168.0.140:8080/pilot/#/team?task=b7abdff8-2baa-42fd-9408-e318faf502f5) — Ticket plan 5.1 LIVE — packaging atomique server_overlay. Gate depends_on=5.2. Mark 5.1 done.

## En cours

### `3.1` — Live World Stream Hub → Compagnon
- **Preuve** : chain v2 LIVE 9fbe70dd
- **Team** :
  - `running` [0f62265a](http://192.168.0.140:8080/pilot/#/team?task=0f62265a-6228-4264-b618-2754024022a5) — Ticket plan 3.1 LIVE OpenCode .143 — Live World Stream Hub→Compagnon. Code émetteur hub + consommate

### `5.2` — Ruff + tests headless Godot CI
- **Preuve** : reopen: faux done ops_probe dry-run healthz — relance ide_cli LIVE
- **Team** :
  - `queued` [f35a71da](http://192.168.0.140:8080/pilot/#/team?task=f35a71da-ca7a-4748-a578-b472ee12512e) — Ticket plan 5.2 LIVE OpenCode .143 — Ruff + tests headless Godot CI (PAS une sonde healthz). Configu

## À relancer (échecs Team)

_Rien à relancer._

## Bloqués (prérequis / L2)

### `3.2` — Mémoire relationnelle jeu ↔ bureau
- **Blocage** : prérequis non done: 3.1
- **Team** :
  - `queued` [46ff8496](http://192.168.0.140:8080/pilot/#/team?task=46ff8496-edb4-4f2d-97ae-81e527881a3a) — Ticket plan 3.2 LIVE — mémoire relationnelle jeu↔bureau. Gate depends_on=3.1. Mark 3.2 done.
  - `cancelled` [9ba09fb5](http://192.168.0.140:8080/pilot/#/team?task=9ba09fb5-1a9d-4ece-92ca-2bf6cdb83560) — Ticket plan 3.2 LIVE — mémoire relationnelle. Gate depends_on=3.1. Mark 3.2 done.

## Todo

### `2.2` — Découpage hub_sim.gd & main.gd
- **Team** :
  - `done` [c210d345](http://192.168.0.140:8080/pilot/#/team?task=c210d345-9792-4a58-acfb-1440fdbe8f59) — Ticket plan 2.2 LIVE — découpage hub_sim/main. Gate depends_on=2.1. Mark 2.2 done.
  - `cancelled` [93207146](http://192.168.0.140:8080/pilot/#/team?task=93207146-ebdb-41ea-b29b-fd69fc71f93b) — Ticket plan 2.2 LIVE — découpage hub_sim/main. Gate depends_on=2.1. Mark 2.2 done.

## Échecs Team liés au plan (hors ticket)

_Aucun._

## Rafraîchir

```bash
python3 tools/suivi_plan_evolutions.py --refresh
python3 tools/suivi_plan_evolutions.py --mark 1.2 done --evidence 'SSE live + smoke'
```
