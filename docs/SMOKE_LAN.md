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
| **Prime Hub Godot** | http://192.168.0.246:8789/healthz · ws://192.168.0.246:8787/ws | Autorité joueur Lost Heaven ([`RUNTIME_GODOT.md`](RUNTIME_GODOT.md)) |
| **Prime comptes** | http://192.168.0.246:8792/ | Comptes (lab ; Core3 hors chemin joueur) |
| **PreCU comptes** | http://192.168.0.245:8792/ | État + comptes PreCU |
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
| **C1 Continuité** | 5 tours même fil LAB sans reset « objectif » / identité | **V7** juste après **V6** (même conversation) — **PASS** 2026-10-06 |
| C2 Collègue | avis sans réciter Agir / dry-run / deploy | **V6** — **PASS** 2026-10-06 |
| C3 Retours | 1 diagnostic + 1 proposition | **V8** — **PASS** 2026-10-06 |

Dernier smoke auto (même `conversation_id`) : `SMOKE_D6_V6V8 OK` · modèle `lbg-compagnon-e4b-v1` · surface `:5174/api/ask`.

```bash
curl -s http://192.168.0.100:5174/api/character/voice-smoke | jq '.cases[] | {id,criterion,prompt}'
# Manuel : enchaîner V6 → V7 → V8 dans le fil :5174 (ne pas « Nouveau chat »)
```

UI D6.3 : timeline / réflexion / méta **repliées** par défaut en mode ask ; ouvertes si source Agir/Team.

Doc : [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) § D6 · [`character_layer.md`](../packages/cortex/docs/character_layer.md).

## MCP catalog (C10/C11)

```bash
bash packages/cortex/infra/scripts/smoke_mcp_catalog.sh
```

Serveur stdio Cursor : `packages/cortex/tools/mcp_catalog_server/server.py` (outils `catalog`, `get_guide`, `tick_matrix`).

## Voir aussi

- [`REGISTRE.md`](REGISTRE.md) — actifs / runtime
- [`packages/prime-client/SMOKE.md`](../packages/prime-client/SMOKE.md) — sync client / Launchpad
- [`OBJECTIVES.md`](../OBJECTIVES.md) — O1 / O2
