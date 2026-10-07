# prime-hub — autorité Lost Heaven (Godot headless)

**Statut 2026-10-07** : **prod joueur** sur `.246` (WS `:8787` / HTTP `:8789`).  
**Règle ADR 0026 §5** : **même contrat** `lbg-ws/2` + HTTP C10/C11 — le client `prime-client` ne change pas.  
Peel inventaire/quests/auth/dialogue : proxy → Python lab `:8797` (pas encore natif Godot).

## Pourquoi

Même moteur que `prime-client` ; pathfinding / combat futurs.  
**Changement de boîte** derrière le contrat gelé — pas un 2ᵉ MMO.

## Phases

| Phase | Done quand | Notes |
|-------|------------|--------|
| **G0** Scaffold | Projet Godot headless + WS accept + `healthz` | ✅ |
| **G1** Parité move | 1 humain + flotte + AABB + auth resolve | ✅ |
| **G2** Peel | inventaire / board / auth / dialogue HTTP | ✅ proxy → Python |
| **G3** Vivant | PNJ wander, goals POI, greet/ambient chat | ✅ |
| **G4** Cutover | Godot WS `:8787` + HTTP `:8789` ; Python lab `:8797` | ✅ |
| **G4a** A* | `find_path` / detour bots (grille AABB) | ✅ |
| **G4b** Resume | `player_positions.json` + LastPos client | ✅ |
| **Unify :8787** | HTTP+WS même port | ⏸ reporté |
| **Peel natif** | HTTP sans Python | ⏳ prochain |

## Ports (live)

| Service | Port |
|---------|------|
| **prime-hub Godot** (monde) | **8787** WS / **8789** HTTP |
| hub_runtime Python (peel only) | **8797** |
| Core3 | hors chemin joueur (`stop_core3_player_path_246.sh`) |

Voir [`docs/RUNTIME_GODOT.md`](../../docs/RUNTIME_GODOT.md).

## Lancer (dev)

Prérequis : Godot **4.6** (editor OK avec `--headless`).

```bash
cd packages/prime-hub
bash scripts/fetch_godot.sh   # une fois → tools/godot
bash scripts/run_headless.sh
# → http://127.0.0.1:8789/healthz
# → ws://127.0.0.1:8787/ws   (ou 8788 en lab local)
```

### Deploy `.246`

```bash
bash packages/cortex/infra/scripts/deploy_prime_hub_246.sh
bash packages/cortex/infra/scripts/stop_core3_player_path_246.sh   # une fois
bash packages/prime-client/tools/deploy_prime_client_patch_246.sh
```

## Fichiers

- `project.godot` — export / headless
- `scenes/server_main.tscn` + `scripts/server_main.gd`
- `scripts/hub_ws_server.gd` — TCP + upgrade WebSocket `lbg-ws/2`
- `scripts/hub_sim.gd` — positions + bots + A* + goals
- `scripts/hub_player_store.gd` — reprise session
- `scripts/hub_http.gd` — `/healthz` + proxy peel
- `scripts/hub_collision.gd` — AABB + pathfinding

## Anti double-build

1. Pas de nouveau protocole client.  
2. Pas de rewrite SpaceMolt / Core3 en parallèle.  
3. Features jeu d’abord sur **contrat** ; si Python les a déjà, on **porte** ou on **proxifie**, on ne réinvente pas.
