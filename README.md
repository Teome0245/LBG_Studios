# LBG Studios

**Étoile du nord** du produit LBG — point de départ Cursor / Team / docs.

| Priorité | Objectif | Package |
|----------|----------|---------|
| **O1** | **Studio** — Cortex, Pilot, Campus, agents | [`packages/cortex`](packages/cortex/) |
| **O2** | **Jeu** — Godot Prime Client → serveur 246 | [`packages/prime-client`](packages/prime-client/) |

Voir [`OBJECTIVES.md`](OBJECTIVES.md), [`docs/PRIORITES_ACTUELLES.md`](docs/PRIORITES_ACTUELLES.md) (snapshot priorités), [`docs/REGISTRE.md`](docs/REGISTRE.md) (repos, chemins, LAN), restauration produit [`docs/RESTAURATION_PRODUIT.md`](docs/RESTAURATION_PRODUIT.md).  
Smoke LAN (Pilot, Cockpit, Orch UI, Core3 `:8792`) : [`docs/SMOKE_LAN.md`](docs/SMOKE_LAN.md) — `bash tools/smoke_lan_surfaces.sh [--functional]`.  
LLM local (110/111) : [`packages/cortex/docs/local_llm_route_matrix.md`](packages/cortex/docs/local_llm_route_matrix.md).  
Sprint évolution 7 j (Team / Thémis, L1 auto / L2 Pilot) : [`packages/cortex/docs/team_evolution_sprint.md`](packages/cortex/docs/team_evolution_sprint.md).

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
| Orch UI `.100:5174` | SPA Vue Lyra / carte agents (sources `_archive/LBG_IA`) |
| Prime / PreCU `:8792` | État serveurs + comptes Core3 |
| Legacy | `../LBG_IA_MMORPG`, `../new_mmo` ; archive `../_archive/avatar_app` |

## Règle

Toute **nouvelle** feature Studio → `packages/cortex`.  
Toute **nouvelle** feature jeu (après O1 vert) → `packages/prime-client`.  
Correctifs urgents dans les repos legacy OK ; pas de nouvelle feature hors O1/O2.
