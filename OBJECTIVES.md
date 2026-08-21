# Objectifs LBG Studios

**Ordre** : Studio (**O1**) puis Jeu (**O2**).

**Étoile du nord produit** (origine, avant le recentrage packaging) :  
IA incarnée sur **PC/infra** → persona au **cœur du MMO** → évolution **contrôlée** du monde.  
Checklist restauration (vert/jaune/rouge) : [`docs/RESTAURATION_PRODUIT.md`](docs/RESTAURATION_PRODUIT.md).

## O0 — Cadre (ce repo)

- [x] Dépôt `Teome0245/LBG_Studios` = point de départ docs / Cursor / Team
- [x] Registre + objectifs versionnés ici
- [x] Allowlist Cursor Cloud Agent inclut ce repo (`LBG_CURSOR_AGENT_REPOS` sur 140)
- [x] Workspace Cursor : `LBG_Studios.code-workspace` + `~/projects/projects.active.code-workspace`

## O1 — Studio (prioritaire)

Cortex opérationnel recentré : Pilot, orchestrateur, Campus/Lyra, Cursor Cloud Agent, desktop hybride — **sans** client web legacy `/mmo/`.

| Critère done | Mesure | État |
|--------------|--------|------|
| Code Cortex extrait | `packages/cortex/` | OK |
| Pilot LAN | Deploy `tools/deploy_cortex_140.sh` → 140:8080 | OK |
| Team / healthz | `GET /v1/pilot/status` backend+orchestrator ok | OK |
| Sprint évolution 7j | Timer `lbg-team-evolution-sprint-job` sur 140 ; L1 auto / L2 Pilot | OK (2026-08-18) |
| Méta-autonomie L3 (Miroir→apply) | Judge, leçons, mutator, Feature Proposer, post-judge, `#/team/metrics` — [`packages/cortex/docs/plan_meta_autonomie_l3.md`](packages/cortex/docs/plan_meta_autonomie_l3.md) | OK (2026-08-21) |
| Accueil Pilot | Cartes Studio/Campus/Ops/Jeu/Projet + liens LAN (Cockpit, Orch UI, `:8792`) | OK |
| Freeze soft | `LEGACY.md` sur LBG_IA_MMORPG / new_mmo | OK |
| Smoke LAN surfaces | [`docs/SMOKE_LAN.md`](docs/SMOKE_LAN.md) + `tools/smoke_lan_surfaces.sh` | OK (2026-07-31) |
| Fil produit d’origine | [`docs/RESTAURATION_PRODUIT.md`](docs/RESTAURATION_PRODUIT.md) | OK (checklist) |

## O2 — Jeu (ensuite)

Client **Godot** `prime-client` + Launchpad + serveur **Prime 246**.

**Plan exécutoire** : [`docs/PLAN_MMO_O2.md`](docs/PLAN_MMO_O2.md) (rails produit P0–P5 + autonomie A1–A4).

| Critère done | Mesure | État |
|--------------|--------|------|
| Client extrait | `packages/prime-client/` + `packages/launchpad` | OK |
| Pas de Core3/DB dans Git | `.gitignore` + extract filtré | OK |
| Smoke documenté | [`packages/prime-client/SMOKE.md`](packages/prime-client/SMOKE.md) + [`docs/SMOKE_LAN.md`](docs/SMOKE_LAN.md) ; patches + `:8792` ready | OK (doc + HTTP 2026-07-31) |
| Login M11 + Launchpad → `J:` | Smoke M11 + M12 (WS+move) + validation humaine 2026-08-03 | OK |
| Pipeline assets | Lien `Infographiste_IA` dans registre | OK |

## Hors scope (volontaire)

- Fusion Infographiste dans ce monorepo ; avatar_app reste en _archive
- Migration Core3 serveur dans Git
- Suppression immédiate des repos GitHub legacy
