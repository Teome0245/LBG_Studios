# Smoke LAN — surfaces projet LBG Studios

**Date contrôle** : 2026-07-31  
**Script** : [`tools/smoke_lan_surfaces.sh`](../tools/smoke_lan_surfaces.sh)

Relance :

```bash
bash tools/smoke_lan_surfaces.sh
bash tools/smoke_lan_surfaces.sh --functional   # Desktop dry-run + route + proposals
```

## Carte des surfaces (pas à jeter)

| Zone | URL | Rôle |
|------|-----|------|
| **Pilot Studio** | http://192.168.0.140:8080/pilot/ | Cortex Pilot (O1) |
| **Cockpit P03** | http://192.168.0.100:8093/pilot/#/cockpit | Mur infra / équipe |
| **Orch UI** | http://192.168.0.100:5174/ | SPA Orchestrateur |
| | http://192.168.0.100:5174/lyra | Lyra riche |
| | http://192.168.0.100:5174/agents/map | Carte agents |
| **Orch API** | http://192.168.0.100:3000/health | Santé providers / Lyra |
| **Prime comptes** | http://192.168.0.246:8792/ | État + comptes Core3 Prime |
| **PreCU comptes** | http://192.168.0.245:8792/ | État + comptes PreCU |
| **Patches** | http://192.168.0.246:8080/patches/prime/manifest.json | Client Prime |
| **MCP front** | http://192.168.0.100:8766/healthz | MCP |

Pilot Accueil / menus : liens vers toutes ces surfaces (Studio · Campus · Ops · Jeu · Projet).

## Résultat 2026-07-31 (HTTP)

| Check | État |
|-------|------|
| Pilot `/pilot/`, `/healthz`, `/v1/pilot/status` | OK (backend + orchestrator + agents) |
| Cockpit UI + `/v1/pilot/cockpit/snapshot` | OK (`ok: true`) |
| Orch UI `/`, `/lyra`, `/agents/map` | OK |
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

## Voir aussi

- [`REGISTRE.md`](REGISTRE.md) — actifs / runtime
- [`packages/prime-client/SMOKE.md`](../packages/prime-client/SMOKE.md) — sync client / Launchpad
- [`OBJECTIVES.md`](../OBJECTIVES.md) — O1 / O2
