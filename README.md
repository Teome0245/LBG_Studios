# LBG Studios

**Étoile du nord** du produit LBG — point de départ Cursor / Team / docs.

| Priorité | Objectif | Package |
|----------|----------|---------|
| **O1** | **Studio** — Cortex, Pilot, Campus, agents | [`packages/cortex`](packages/cortex/) |
| **O2** | **Jeu** — Godot Prime Client → serveur 246 | [`packages/prime-client`](packages/prime-client/) |

Voir [`OBJECTIVES.md`](OBJECTIVES.md) et [`docs/REGISTRE.md`](docs/REGISTRE.md).

## Démarrer

```bash
# Workspace Cursor
code /home/sdesh/projects/LBG_Studios/LBG_Studios.code-workspace

# Cortex (Studio) — source de vérité progressive
cd packages/cortex
# Deploy Pilot/API → 140 : bash ../../tools/deploy_cortex_140.sh

# Jeu — client Godot
cd packages/prime-client
# Sync J: / patches 246 : tools/ dans ce package
```

## Remotes liés (hors monorepo pour l’instant)

| Dépôt | Rôle |
|-------|------|
| `../Infographiste_IA` | Pipeline assets / LoRA |
| `../avatar_app` | Bac avatars web |
| Legacy | `../LBG_IA_MMORPG`, `../new_mmo` (upstream historique) |

## Règle

Toute **nouvelle** feature Studio → `packages/cortex`.  
Toute **nouvelle** feature jeu (après O1 vert) → `packages/prime-client`.  
Correctifs urgents dans les repos legacy OK ; pas de nouvelle feature hors O1/O2.
