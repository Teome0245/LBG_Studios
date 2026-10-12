# Hub runtime — spike ADR 0026 (hors Core3)

Serveur mince Lost Heaven : HTTP catalog/tick + WebSocket `lbg-ws/2`.

## Démarrer (local)

```bash
cd packages/cortex
.venv/bin/python -m tools.hub_runtime.server
# → http://127.0.0.1:8787/healthz
# → ws://127.0.0.1:8787/ws
```

Smoke local :

```bash
bash tools/hub_runtime/smoke_hub_runtime.sh
```

## Déployer sur `.246` (// Core3)

Port **8787** — n’écrase pas gateway `:50000` ni sidecar `:8791`.

```bash
bash packages/cortex/infra/scripts/deploy_hub_runtime_246.sh --smoke
# unit: lbg-hub-runtime.service
# → http://192.168.0.246:8787/healthz
# → ws://192.168.0.246:8787/ws
```

## Godot

1. `packages/prime-client/config/hub_runtime.json` → `"enabled": true`  
   (`ws_url` pointe déjà vers `.246:8787` après deploy)
2. Lancer `prime-client` → écran login → **Enter** (pas besoin login Core3)
3. ZQSD pour bouger ; **Nix / Lia / Mira / Kael** patrouillent ; PNJ hub **vivants** (wander)  
4. **Entrée** (ou hotbar Chat) → chat WS ; flotte IA salue à l’entrée  
5. PNJ (Daan, Jax, Guide, Odo, trainers, Habitué, Videur, Sergent, Rumeuriste, …) cliquables

Remettre `"enabled": false` pour le flux M11/M12 classique.

## Endpoints

| Méthode | Path | Rôle |
|---------|------|------|
| GET | `/healthz` | Santé spike |
| GET | `/catalog?type=` | C10 |
| GET | `/v1/inventory` | Inventaire peel |
| GET | `/v1/quests/board` | Board missions |
| POST | `/v1/quests/accept` | Accept (TickGate) |
| POST | `/v1/craft/combine` | Craft stub |
| POST | `/v1/bots/move_to` | Mutation tickée (Nix/Lia/Mira/Kael) |
| GET | `/v1/bots` | Liste flotte IA |
| POST | `/v1/say` | Chat IA/humain → broadcast WS (`source=ia\|human`) |
| POST | `/v1/dialogue/invoke` | Dialogue PNJ stub (compat DialogueBridge) |
| WS | `/ws` | `login` → `enter_world` → `zone_state` / `move` / `chat` |

Chat : humains via WS `{"type":"chat","text":…}` ; flotte Nix/Lia/Mira salue à l’entrée + ambient ; IA externe via `POST /v1/say`.  
Dialogue : clic PNJ → `DialogueBridge` redirigé vers `http_url` + `/v1/dialogue/invoke` (suggestions registry).

## Auth + persistance

- `POST /v1/auth/login` · `/v1/auth/guest` · `/v1/auth/select_character` · `/v1/auth/enter_zone`
- État disque : `LBG_HUB_STATE_DIR` → `accounts.json` + `players_state.json`
- WS `login` valide le `session_token` (compat `spike-local`)

## Peel inventaire / missions

Mêmes chemins que le sidecar `:8791` :

- `GET /v1/inventory?player=`
- `GET /v1/quests/board` · `/v1/quests/status`
- `POST /v1/quests/accept|progress|complete|tip` (TickGate)
- `POST /v1/craft/combine`

Godot : `HubRuntimeCfg` redirige Inventory / MissionBoard / Talents vers `http_url` si spike ON.

## Collision

Même AABB que `ZoneLayers` Godot (`lost_heaven_buildings.json`, portes = corridors walkables).

- Humain : `set_human_pos` clamp serveur  
- Nix : patrouille plaza → marché (contourne starport)  
- Remparts : fence props (portes E/O ouvertes)

Deploy copie JSON dans `/opt/lbg-hub-runtime/data/`.

## Fichiers

- `sim.py` — monde + bot Nix  
- `hub_collision.py` — AABB + fence  
- `economy.py` — inventaire / quêtes / craft  
- `server.py` — FastAPI + WS  
- `smoke_hub_runtime.sh` — smoke HTTP/WS  
