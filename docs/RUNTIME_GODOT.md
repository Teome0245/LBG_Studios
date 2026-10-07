# Runtime joueur Lost Heaven — Godot-first (G5+)

**Date** : 2026-10-07  
**ADR** : [`0026-runtime-hors-core3.md`](../packages/cortex/docs/adr/0026-runtime-hors-core3.md)

## Autorité actuelle

| Rôle | Process | Port | Statut |
|------|---------|------|--------|
| **Monde + peel HTTP + WS** | `lbg-prime-hub` (Godot headless) | **8787** (HTTP+WS unifiés) | **Prod joueur** |
| hub_runtime Python | — | — | **OFF** (peel G5) — `stop_core3_and_spike_246.sh` |
| Core3 Prime / bots / gateway / sidecar / comptes | — | — | **OFF** (watchdogs désactivés) |

Client : `packages/prime-client/config/hub_runtime.json`  
→ `http_url` **et** `ws_url` sur `:8787`

Launchpad **≥ 2.1.4** : profil **Prime Godot only** (PreCU retiré) ; sonde `http://192.168.0.246:8787/healthz`.  
Zip : `http://192.168.0.246:8080/releases/launchpad/LBG-Launchpad-win.zip`

## Peel natif (G5)

- Auth : `/v1/auth/login|guest|select_character|enter_zone|resolve`
- Inventaire / board / quêtes / tip / craft
- Catalog C10 + guide + tick-matrix (`data/catalog_*.json`)
- Dialogue invoke (+ LLM Ollama optionnel `.110`)
- Persistance : `data/accounts.json`, `players_state.json`, `player_positions.json`
- Flotte IA : marche + goals ; **pas** d’annonce chat « vers X / j’y suis »

### Tickets concurrents live sur `:8787` (2026-10-07)

| ID | Surface | Notes joueur |
|----|---------|--------------|
| **C3** | Compagnon Nix | greet + escort court au spawn |
| **C4** | `GET /v1/events/active` · board `lh_scrap_fall_salvage` | Event chute scrap au boot LAN ; rumeur Jax/Daan |
| **C5** | `GET /v1/chronicle?player=…` | Journal session (quête/tip/salvage/craft) · Scribe « chronique » |
| **C8** | `POST /v1/salvage` | Hotbar **`[1]`** près `poi:lh_scrap_pile` → loot → craft `kit_reparation` (**T**) |
| **C7** | `GET /v1/trade/catalog` · `POST /v1/trade/offer` | Jax — boissons ±15 % (rep basse ±8 %) ; coups dialogue La Perle |
| **C6** | `GET /v1/wiki` (`?format=md`) | Panel Menu → Wiki ; Guide quartier `open_wiki` ; drift npc/poi/M10 |
| Quêtes | `progress_steps` + backfill | Terminer (J) seulement si étapes OK ; 400 métier ≠ « réseau KO » |

Client : `HubRuntimeCfg.set_player_name` aligne inventaire/board/craft sur le perso connecté (ex. Teome).

## Vie hub (G5+)

Design : [`design/HUB_LIFE_TRIPLONS.md`](design/HUB_LIFE_TRIPLONS.md)

| Qui | Mission |
|-----|---------|
| **PNJ** | Tenir le monde **fonctionnel** (Triplons work/leisure/rest) |
| **Joueurs** (humain + IA) | Faire **évoluer** le monde (quêtes, craft, explore, suggestions Studio) |

| Brique | Rôle |
|--------|------|
| **Triplons** | Groupes 3 PNJ · cycle `work` → `leisure` → `rest` · ≈ ⅔ visibles |
| **Flotte IA** | `ai_players.json` · login = persona out-game · pont `player_bridge_*` · admin 0–4 · cap 10/20 · LAN |
| **Objectifs** | `short` / `medium` / `long` par persona |
| **Autonomie bots** | Tirage quête / explore / hub |
| **Suggestions monde** | File `data/world_suggestions.jsonl` · Studio, pas auto-monde |
| **Surface agent** | `GET /v1/agent/bootstrap` · `GET /v1/agent/skill` · `/skill.md` |

`/healthz` expose `life` + `ai_seats`.

## Ops

```bash
bash packages/cortex/infra/scripts/deploy_prime_hub_246.sh
bash packages/cortex/infra/scripts/stop_core3_and_spike_246.sh   # Core3 + Python OFF (timers inclus)
bash packages/prime-client/tools/deploy_prime_client_patch_246.sh
bash packages/prime-client/tools/publish_client_bootstrap_246.sh  # Launchpad zip
```

Garder l’UI comptes Core3 `:8792` uniquement si besoin lab :

```bash
bash packages/cortex/infra/scripts/stop_core3_and_spike_246.sh --keep-account-admin
```

## Suite produit (post-G5+)

1. **Persona / compagnon en jeu** — rail P3 ([`PLAN_MMO_O2.md`](PLAN_MMO_O2.md))
2. **Gameplay hub** — quêtes terrain POI, craft UX, dialogue riche
3. **Combat / cour de chasse** — P5a **sur `prime-hub`** (`/v1/hunt-yard*`, `tools/hunt_yard.py`) · smoke `tools/smoke_p5_hunt_yard_hub.sh`
4. **Navmesh Godot** — remplacer A* grille AABB quand besoin
5. **Anti-saccade (2026-10-07)** — client : lissage positions remote ; hub : budget A* `PATH_BUDGET_PER_TICK=2`
6. **Anti-saccade v2** — gateway **non-bloquante** (plus de `OS.delay_usec` sur HTTP/WS accept) ; max 1 tick/frame ; `zone_state` ~10 Hz sans doublon `bots[]`

## Anti double-build

Contrat `lbg-ws/2` + HTTP C10/C11 **gelé**. Process = Godot only.  
Suggestions monde = file Studio uniquement (pas de mutation auto).
