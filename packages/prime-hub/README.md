# prime-hub — autorité Lost Heaven (Godot headless)

**Décision pilote 2026-10-07** : bascule process vers Godot Dedicated / headless.  
**Règle ADR 0026 §5** : **même contrat** `lbg-ws/2` + HTTP C10/C11 — le client `prime-client` ne change pas.  
`hub_runtime` Python (`.246:8787`) reste **autorité live** jusqu’à parité + cutover.

## Pourquoi (choix produit)

Surnuméraire pour la charge hub actuelle, mais anticipé pour pathfinding / combat / même moteur que le client.  
Ce n’est **pas** un 2ᵉ MMO : c’est un **changement de boîte** derrière le contrat gelé.

## Phases

| Phase | Done quand | Notes |
|-------|------------|--------|
| **G0** Scaffold | Projet Godot headless + WS accept + `healthz` HTTP stub | ✅ |
| **G1** Parité move | 1 humain + flotte + AABB + auth resolve ; client inchangé pointe `:8788` | ✅ |
| **G2** Peel | inventaire / board / auth / dialogue HTTP | ✅ proxy → Python `:8787` |
| **G3** Vivant | PNJ wander, goals POI, greet/ambient chat | ✅ |
| **G4** Cutover | Godot WS `:8787` + HTTP `:8789` ; Python lab `:8797` | ✅ |
| **G4a** A* | `find_path` / detour bots (grille AABB) | ✅ |
| **Unify :8787** | HTTP+WS même port | ⏸ reporté (TCP multiplex headless instable) |

## Ports (// Core3 + hub_runtime pendant transition)

| Service | Port |
|---------|------|
| hub_runtime Python (live) | **8787** |
| prime-hub Godot (spike) | **8788** WS / **8789** HTTP |
| Core3 lab | 50000 / sidecar 8791 |

## Lancer (dev)

Prérequis : Godot **4.6** (editor OK avec `--headless`).

```bash
cd packages/prime-hub
bash scripts/fetch_godot.sh   # une fois → tools/godot
bash scripts/run_headless.sh
# → http://127.0.0.1:8789/healthz
# → ws://127.0.0.1:8788/ws
```

Auth G0 : tout `session_token` non vide → login OK (oid 100001).  
HTTP inventaire/quests reste sur Python `:8787` jusqu’à G2.

### Deploy `.246`

```bash
bash packages/cortex/infra/scripts/deploy_prime_hub_246.sh
# → http://192.168.0.246:8789/healthz
# → ws://192.168.0.246:8788/ws
```

Client de test (sans couper le live `:8787`) : pointer temporairement  
`prime-client/config/hub_runtime.json` → `"ws_url": "ws://192.168.0.246:8788/ws"`.

## Fichiers

- `project.godot` — export / headless
- `scenes/server_main.tscn` + `scripts/server_main.gd`
- `scripts/hub_ws_server.gd` — TCP + upgrade WebSocket `lbg-ws/2`
- `scripts/hub_sim.gd` — positions + bots (port mince de `sim.py`)
- `scripts/hub_http.gd` — `/healthz` (+ catalog plus tard)

## Anti double-build

1. Pas de nouveau protocole client.  
2. Pas de rewrite SpaceMolt / Core3 en parallèle.  
3. Features jeu d’abord sur **contrat** ; si Python les a déjà, on **porte** ou on **proxifie**, on ne réinvente pas.
