# LBG Studios

**Étoile du nord** du produit LBG — point de départ Cursor / Team / docs.

| Priorité | Objectif | Package |
|----------|----------|---------|
| **O1** | **Studio** — Cortex, Pilot, Campus, agents | [`packages/cortex`](packages/cortex/) |
| **O2** | **Jeu** — client + hub Godot `.246:8787` | [`packages/prime-client`](packages/prime-client/) · [`packages/prime-hub`](packages/prime-hub/) |

Voir [`OBJECTIVES.md`](OBJECTIVES.md), [`docs/PRIORITES_ACTUELLES.md`](docs/PRIORITES_ACTUELLES.md), [`docs/RUNTIME_GODOT.md`](docs/RUNTIME_GODOT.md) (**G5 live**), [`docs/REGISTRE.md`](docs/REGISTRE.md), [`docs/RESTAURATION_PRODUIT.md`](docs/RESTAURATION_PRODUIT.md).  
Smoke LAN : [`docs/SMOKE_LAN.md`](docs/SMOKE_LAN.md) — hub `http://192.168.0.246:8787/healthz`.  
LLM local (110/111) : [`packages/cortex/docs/local_llm_route_matrix.md`](packages/cortex/docs/local_llm_route_matrix.md).  
Sprint évolution 7 j : [`packages/cortex/docs/team_evolution_sprint.md`](packages/cortex/docs/team_evolution_sprint.md).

## Démarrer

```bash
# Workspace Cursor
code /home/sdesh/projects/LBG_Studios/LBG_Studios.code-workspace

# Cortex (Studio) — source de vérité progressive
cd packages/cortex
# Deploy Pilot/API → 140 : bash ../../tools/deploy_cortex_140.sh

# Smoke surfaces LAN
bash tools/smoke_lan_surfaces.sh --functional

# Jeu — client Godot
cd packages/prime-client
# Sync J: / patches 246 : tools/ dans ce package
```

## Remotes liés (hors monorepo pour l’instant)

| Dépôt / runtime | Rôle |
|-----------------|------|
| `../Infographiste_IA` | Pipeline assets / LoRA |
| Cockpit `.100:8093` | Ops infra (sources `_shelf/LBG_Project_03`) |
| Compagnon `.100:5174` | Présence Studio (`packages/cortex/compagnon_ui`) · Desktop `packages/compagnon-desktop` |
| Hub Godot `.246:8787` | Autorité joueur Lost Heaven (G5+) — Core3 / spike Python **OFF** |
| Legacy | `../LBG_IA_MMORPG`, `../new_mmo` ; archive `../_archive/avatar_app` |

## Règle

Toute **nouvelle** feature Studio → `packages/cortex`.  
Toute **nouvelle** feature jeu → `packages/prime-client` / `packages/prime-hub` (pas Core3, pas `hub_runtime` Python).  
Correctifs urgents dans les repos legacy OK ; pas de nouvelle feature hors O1/O2.
