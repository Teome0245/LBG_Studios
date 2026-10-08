# Smoke LAN — surfaces projet LBG Studios

**Date contrôle** : 2026-08-25  
**Script** : [`tools/smoke_lan_surfaces.sh`](../tools/smoke_lan_surfaces.sh)

Relance :

```bash
bash tools/smoke_lan_surfaces.sh
bash tools/smoke_lan_surfaces.sh --functional   # Desktop dry-run + route + proposals
```

## Carte des surfaces (pas à jeter)

| Zone | URL | Rôle |
|------|-----|------|
| **Pilot Studio** (hub) | http://192.168.0.140:8080/pilot/ | Cortex Pilot (O1) — surfaces Orch absorbées |
| | http://192.168.0.140:8080/pilot/#/assistant | Chat produit / ops |
| | http://192.168.0.140:8080/pilot/#/lyra | LyraEngine |
| | http://192.168.0.140:8080/pilot/#/agents/map | Carte agents |
| | http://192.168.0.140:8080/pilot/#/providers | Catalogue LLM |
| **Simple Chat** (lab) | http://192.168.0.100:3080/ | Open WebUI — chat LLM seul (pas Cursor) |
| **Cockpit P03** | http://192.168.0.100:8093/pilot/#/cockpit | Mur infra / équipe |
| **Orch UI** (chat produit) | http://192.168.0.100:5174/ | SPA Orchestrateur — chat unique (rétabli, plus de redirect forcé) |
| **Orch API** | http://192.168.0.100:3000/health | Santé providers / Lyra (proxies Pilot) |
| **Prime Hub Godot** | http://192.168.0.246:8787/healthz · ws://192.168.0.246:8787/ws | Autorité joueur Lost Heaven G5 ([`RUNTIME_GODOT.md`](RUNTIME_GODOT.md)) |
| **Prime comptes** | http://192.168.0.246:8792/ | Comptes lab (hors chemin joueur) |
| **PreCU comptes** | http://192.168.0.245:8792/ | Réf. lecture seule (hors Launchpad) |
| **Patches** | http://192.168.0.246:8080/patches/prime/manifest.json | Client Prime |
| **MCP front** | http://192.168.0.100:8766/healthz | MCP |

Pilot Accueil / menus : liens vers toutes ces surfaces (Studio · Campus · Ops · Jeu · Projet).

Ollama / executor (hors smoke HTTP UI) : **`.110:11434`** heavy · **`.111:11434`** light · **`.141`** CT executor — voir [`REGISTRE.md`](REGISTRE.md).

## Résultat 2026-08-25 (HTTP) — cutover P3

| Check | État |
|-------|------|
| Pilot `/pilot/`, `/healthz`, `/v1/pilot/status` | OK |
| Orch UI `/`, `/lyra`, `/agents/map` | **302 → Pilot** |
| Orch API `/health` + Pilot `/v1/pilot/orch/*` | OK |
| Cockpit / Prime / PreCU / Patches / MCP | voir script |

## Résultat 2026-07-31 (HTTP) — historique

| Check | État |
|-------|------|
| Pilot `/pilot/`, `/healthz`, `/v1/pilot/status` | OK (backend + orchestrator + agents) |
| Cockpit UI + `/v1/pilot/cockpit/snapshot` | OK (`ok: true`) |
| Orch UI `/`, `/lyra`, `/agents/map` | OK (SPA live, avant P3) |
| Orch API `/health` | OK |
| Prime / PreCU `:8792` + `/api/servers` | OK — **Prime & PreCU `ready`** |
| Patches manifest | OK |
| MCP `:8766/healthz` | OK |
| Traefik `/` et Orch `:3000/` | 404 racine (attendu si pas de page) |

## Contrôles fonctionnels

| # | Contrôle | Comment | 2026-07-31 |
|---|----------|---------|------------|
| 1 | **Desktop** dry-run | `POST /v1/pilot/route` + `desktop_action.open_url` + `desktop_dry_run:true` | OK |
| 2 | **Orch** Lyra / carte | Pages 200 + `/health` expose jauges Lyra | OK |
| 3 | **Jeu** | `/api/servers` ready (Prime + PreCU) | OK |
| 4 | **Assistant** | `POST /v1/pilot/action-proposal` HTTP 200 | OK (endpoint) — proposition peut rester `null` si texte non mappé ; worker Desktop `agent-desktop/healthz` OK |

Worker Desktop Windows et login Godot restent **manuels** sur le PC Teome (hors CI LAN).

Dernière passe script : **OK=19 WARN=0 KO=0** (`bash tools/smoke_lan_surfaces.sh --functional`).

## Jetons exécution réelle (Cockpit / Desktop)

| Usage | Variable | Où (chemins seulement) |
|-------|----------|-------------------------|
| Auth Cockpit | `LBG_PILOT_API_TOKEN` | VM **140** `/etc/lbg-project-03.env` |
| Approval DevOps / team | `LBG_DEVOPS_APPROVAL_TOKEN` | idem |
| Approval Desktop | `LBG_DESKTOP_APPROVAL_TOKEN` | **140** (même fichier) **et** `C:\Agent_IA\desktop.env` — **même valeur** |

Workflow LAN solo :

1. Coller le jeton **Pilot** dans Réglages Cockpit.
2. Décocher **Dry-run** pour exécution réelle (Team ops + Desktop).
3. Champ **approval** : laisser vide — injecté serveur après auth Pilot.
4. Si « Approval token requis » : vérifier que le jeton Windows = celui de 140 (hot-reload `desktop.env`).

Garde-fous qui restent : Bearer Pilot, allowlists apps/URL sur le worker, dry-run explicite.

Fil produit / checklist : [`RESTAURATION_PRODUIT.md`](RESTAURATION_PRODUIT.md).

## Compagnon D6 — causerie crédible (voix)

Surface : http://192.168.0.100:5174/ · API cases : `/api/character/voice-smoke`

| Critère | Mesure | Smoke |
|---------|--------|-------|
| **C1 Continuité** | 5 tours même fil LAB sans reset « objectif » / identité | **V7** juste après **V6** (même conversation) — **PASS** 2026-10-08 |
| C2 Collègue | avis sans réciter Agir / dry-run / deploy | **V6** — **PASS** 2026-10-08 |
| C3 Retours | 1 diagnostic + 1 proposition | **V8** — **PASS** 2026-10-08 |

Dernier smoke auto (même `conversation_id`) : `SMOKE_D6_V6V8 OK` · fil `smoke-d6-v6v8-*` · surface `:5174/api/ask`.

**Smoke humain C1–C2** (2026-10-08) : [`smoke_humain_d6_2026-10-08.md`](smoke_humain_d6_2026-10-08.md) — **C1 PASS** · **C2 PARTIEL** (greeting ops FAIL ; fil projet OK) · suite = gap délivrance + `short_social` sur « allons-y ».

```bash
bash tools/smoke_d6_causerie_5174.sh
curl -s http://192.168.0.100:5174/api/character/voice-smoke | jq '.cases[] | {id,criterion,prompt}'
# Manuel : enchaîner V6 → V7 → V8 dans le fil :5174 (ne pas « Nouveau chat »)
```

UI D6.3 : timeline / réflexion / méta **repliées** par défaut en mode ask ; ouvertes si source Agir/Team.

**Pièges ops** (2026-10-02) : Agir/Team **HTTP 502** → `lbg-backend` sur `.140` (souvent `pydantic-settings` manquant dans le venv). Question « c’est quoi le campus » → chat causerie, pas Team live (`team_routing` overlay).

Doc : [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) § D6 · [`character_layer.md`](../packages/cortex/docs/character_layer.md).

## MCP catalog (C10/C11)

```bash
bash packages/cortex/infra/scripts/smoke_mcp_catalog.sh
```

Serveur stdio Cursor : `packages/cortex/tools/mcp_catalog_server/server.py` (outils `catalog`, `get_guide`, `tick_matrix`).

**Autorité joueur G5+** : catalog / tick-matrix / dialogue live sur **`prime-hub` `:8787`** (pas le sidecar Core3 `:8791`).

```bash
# P3 + C1 moves + C12 envelope + C10/C11 lecture
bash tools/smoke_p3_hub_dialogue.sh
# ou : bash tools/smoke_p3_hub_dialogue.sh http://192.168.0.246:8787
```

### Hub gameplay C4 / C5 / C8 (2026-10-07)

```bash
H=http://192.168.0.246:8787
curl -sS "$H/v1/events/active" | jq '{active,event_id,board_quest_id}'
curl -sS "$H/v1/quests/board?player=Voyageur" | jq '{n:(.quests|length), event:.active_event.event_id}'
curl -sS -X POST "$H/v1/salvage" -H 'Content-Type: application/json' \
  -d '{"player":"Voyageur","poi_id":"poi:lh_scrap_pile","x":6042,"z":-1065}' | jq '{ok,loot,event_boost}'
curl -sS "$H/v1/chronicle?player=Voyageur" | jq '{title,line_count,lines:(.lines[:3])}'
curl -sS "$H/v1/trade/catalog" | jq '{vendor:.display_name,n:(.catalog|length)}'
curl -sS -X POST "$H/v1/trade/offer" -H 'Content-Type: application/json' \
  -d '{"player":"Voyageur","sku_id":"drink:eau_filtree","offer_price":8}' | jq '{ok,outcome,price_paid,reputation}'
curl -sS "$H/v1/wiki" | jq '{ok,drift,title,npc:(.npcs|length),poi:(.pois|length)}'
```

## P3 persona dialogue (hub)

Chemin live client : `prime-client` → `POST http://192.168.0.246:8787/v1/dialogue/invoke` (`session_summary` + `history`).  
Smoke C1 historique Pilot (`tools/smoke_c1_suggested_moves.sh` → `:8000`) = régression Python ; **vert produit** = `smoke_p3_hub_dialogue.sh`.

## Chœur terrain (V50–V53)

```bash
bash tools/smoke_choeur_terrain.sh           # truth guard + probe hub + P3 si live
bash tools/smoke_choeur_terrain.sh --skip-live
# Owner bundle Team
BUNDLE=choeur_l1 bash packages/cortex/infra/scripts/smoke_godot_owners.sh
# Job spawn (dry) : python -m lbg_agents.spawn_team_choeur_l1_job
```

## Spawn bêtes densités (open-world)

```bash
bash tools/smoke_beast_spawn_hub.sh          # healthz.beast_count >= 1
bash tools/smoke_beast_engage_hub.sh         # POST /v1/world/beast/engage + loot
# Timer Chœur .140
bash packages/cortex/infra/scripts/install_choeur_l1_timer_140.sh
```

## P5a cour de chasse (hub)

```bash
bash tools/smoke_p5_hunt_yard_hub.sh         # reset → run → victory → claim meute
bash tools/smoke_p5_client_hunt_contract.sh  # contrat hotbar HTTP (OK 2026-10-08)
```

Endpoints : `GET/POST http://192.168.0.246:8787/v1/hunt-yard*` (peel Godot + `tools/hunt_yard.py`).  
Client : hotbar **[1]** près `poi:lh_hunt_chacal` → reset/run/claim (`main.gd`).

## C2 mémoire relations (hub)

```bash
bash tools/smoke_c2_relation_memory_hub.sh   # tip → GET memory → dialogue hint → accept quest
```

Persistance : `players_state.json` → `relation_memory[]` · lecture `GET /v1/relation-memory?player=&npc_id=` · écriture tip/accept/trade + `met` au dialogue.

## Catalog POI + densité combat

```bash
# Régénère packages/prime-hub/data/catalog_poi.json (avant deploy)
python3 packages/cortex/infra/scripts/export_prime_hub_catalog_poi.py
bash tools/smoke_catalog_poi_hub.sh          # GET /v1/catalog?type=poi + /v1/world/combat-density
```

## Voir aussi

- [`REGISTRE.md`](REGISTRE.md) — actifs / runtime
- [`packages/prime-client/SMOKE.md`](../packages/prime-client/SMOKE.md) — sync client / Launchpad
- [`OBJECTIVES.md`](../OBJECTIVES.md) — O1 / O2
