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
| **Anneau explore** | `life/explore_ring_lh.json` · ~3 km autour plaza LH · clamp `POST /v1/bots/move_to` · pas Scrapaltai entière / pas Zalem (C13) |
| **Objectifs** | `short` / `medium` / `long` par persona |
| **Autonomie bots** | Tirage quête / explore (anneau) / hub |
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
3. **Combat / cour de chasse** — P5a déjà amorcé ; brancher sur `prime-hub`
4. **Navmesh Godot** — remplacer A* grille AABB quand besoin

## Anti double-build

Contrat `lbg-ws/2` + HTTP C10/C11 **gelé**. Process = Godot only.  
Suggestions monde = file Studio uniquement (pas de mutation auto).
