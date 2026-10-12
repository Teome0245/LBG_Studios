# Suivi — Plan d'évolutions Studio / Jeu

**Généré** : 2026-10-12 08:57 CEST  
**Plan** : `PLAN_PROPOSITIONS_EVOLUTIONS` · source [`docs/PLAN_PROPOSITIONS_EVOLUTIONS.md`](../PLAN_PROPOSITIONS_EVOLUTIONS.md)  
**Pilot** : [http://192.168.0.140:8080/pilot/#/team](http://192.168.0.140:8080/pilot/#/team)  
**Plan entièrement réalisé** : ❌ non

## Synthèse

| Done | En cours | À relancer | Bloqué | Todo |
|:---:|:---:|:---:|:---:|:---:|
| 6 | 3 | 0 | 1 | 0 |

## Réalisés

### `1.1` — Barrière sémantique causerie / tool_loop (+ presence_brief T5)
- **Preuve** : smoke T1→T5 OK (ab01e3fc) · t5_src=llm · deploy CT100

### `1.2` — Streaming SSE /api/ask/stream + ChatFlow
- **Preuve** : SSE live CT100: POST /ask/stream start+ping+delta+done · UI useApi/ChatFlow · tests askStream+sse_ask · deploy 2026-10-09

### `1.3` — Modularisation Pilot Web (pilot.js)
- **Preuve** : 17 modules ES <1000L (pilot_*.js) · stub pilot.js · gen_chunks --check OK (17 chunks) · build Vite dist/ 957ms OK · pytest test_pilot_static PASS

### `2.3` — NavigationServer3D navmesh prime-hub
- **Preuve** : navmesh NavigationServer3D LIVE 2026-10-11: hub_nav.gd bake 193 polys/16 empreintes ~0.6s; PATH_BUDGET_PER_TICK supprimé (budget_per_tick=0); selftest 40/40 entités/tick ~34us (nav_selftest.gd); smoke_navmesh_prime_hub.sh OK; /healthz navmesh.ok + /v1/dev/navmesh/probe source=navmesh (fallback A* grille hors bornes)

### `2.1` — Persistance SQLite hub_player_store
- **Preuve** : hub_db.gd SQLite threadé WAL + queue async BEGIN IMMEDIATE/COMMIT · hub_player_store.gd table player_positions + auto-migration JSON + miroir périodique · db_selftest.gd OK · smoke_sqlite_prime_hub.sh kill -9 sans corruption

### `5.1` — Packaging atomique server_overlay CT100
- **Preuve** : CT100 packaging atomique LIVE 1.0.0+4bcc331: server_overlay/pyproject.toml + overlay.map (33 fichiers); server_overlay_package.py build/verify/apply/rollback; deploy_compagnon_100.sh --smoke OK; marker /opt/orchestrateur/.server_overlay_version package_sha=8128a4e3470abded597b70e855289bab608e23c4fd6acbe273e4062ec272e5a5; smoke tools/smoke_server_overlay_package.sh OK; rollback testé

## En cours

### `2.2` — Découpage hub_sim.gd & main.gd
- **Preuve** : Serveur hub_sim.gd scinde en 5 modules <800L (hub_sim 771L, hub_combat 447L, hub_presence 185L, hub_sim_ambient 196L, hub_sim_views 142L, hub_sim_defs 103L) - sim_selftest.gd OK headless - client main.gd en cours

### `3.1` — Live World Stream Hub → Compagnon
- **Preuve** : chain v2 LIVE 9fbe70dd

### `5.2` — Ruff + tests headless Godot CI
- **Preuve** : reopen: faux done ops_probe dry-run healthz — relance ide_cli LIVE

## À relancer (échecs Team)

_Rien à relancer._

## Bloqués (prérequis / L2)

### `3.2` — Mémoire relationnelle jeu ↔ bureau
- **Blocage** : prérequis non done: 3.1

## Todo

_File vide._

## Échecs Team liés au plan (hors ticket)

_Aucun._

## Rafraîchir

```bash
python3 tools/suivi_plan_evolutions.py --refresh
python3 tools/suivi_plan_evolutions.py --mark 1.2 done --evidence 'SSE live + smoke'
```
