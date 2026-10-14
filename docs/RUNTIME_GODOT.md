# Runtime joueur Lost Heaven — Godot-first (G5+)

**Date** : 2026-10-13 (suite produit réalignée · P3/P5/navmesh faits)  
**Live depuis** : 2026-10-07  
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
| **C2** | `GET /v1/relation-memory` · inject dialogue | tip/accept/trade/`met` → `players_state.relation_memory` · smoke `tools/smoke_c2_relation_memory_hub.sh` |
| **P5** | densités + `POST /v1/world/beast/engage` | aggro/leash · telegraph boss ~1,4 s · respawn meute ~28 s / boss ~90 s · loot inventaire |

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

### Fait (ne plus traiter comme backlog ouvert)

| Item | Clos | Preuve |
|------|------|--------|
| **P3** Persona / dialogue / wiki en jeu | 2026-10-07 | C3–C8 live · [`PLAN_MMO_O2.md`](PLAN_MMO_O2.md) |
| **P5 / P5a** Combat · cour de chasse · telegraph boss | 2026-10-08 | `/v1/hunt-yard*` · smoke hub · densités + engage |
| **Navmesh** `NavigationServer3D` | 2026-10-11 | ticket 2.3 · `hub_nav.gd` · smoke `tools/smoke_navmesh_prime_hub.sh` |
| Anti-saccade v1 | 2026-10-07→11 | lissage client · `PATH_BUDGET_PER_TICK` supprimé · ~34 µs/entité |
| Anti-saccade v2 | 2026-10-07 | gateway non-bloquante · 1 tick/frame · `zone_state` ~10 Hz |
| Pont Studio↔Monde | 2026-10-12 | World Stream 3.1 · mémoire relationnelle 3.2 |

### Ouvert (polish / contenu)

1. ~~**O-JEUX-ESCORT**~~ — **live** 2026-10-14 · `hub_escort.gd` · smoke `tools/smoke_escort_hub.sh`.
2. ~~**O-JEUX-SHOW**~~ — **code** 2026-10-14 · `hub_show.gd` · tip live + formation Talen · smoke `tools/smoke_show_hub.sh` · deploy `.246` avec ce commit.
3. **Gameplay hub** — hotbar restants, craft UX — [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md).
4. Unification chemin client Git vs runtime 140 (`LBG_PRIME_CLIENT_ROOT`) — [`REGISTRE.md`](REGISTRE.md).

## Anti double-build

Contrat `lbg-ws/2` + HTTP C10/C11 **gelé**. Process = Godot only.  
Suggestions monde = file Studio uniquement (pas de mutation auto).
