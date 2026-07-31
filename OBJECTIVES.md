# Objectifs LBG Studios

**Ordre** : Studio (**O1**) puis Jeu (**O2**).

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
| Accueil Pilot | Cartes Studio/Campus/Ops/Jeu/Projet + liens LAN (Cockpit, Orch UI, `:8792`) | OK |
| Freeze soft | `LEGACY.md` sur LBG_IA_MMORPG / new_mmo | OK |
| Smoke LAN surfaces | [`docs/SMOKE_LAN.md`](docs/SMOKE_LAN.md) + `tools/smoke_lan_surfaces.sh` | OK (2026-07-31) |

## O2 — Jeu (ensuite)

Client **Godot** `prime-client` + Launchpad + serveur **Prime 246**.

| Critère done | Mesure | État |
|--------------|--------|------|
| Client extrait | `packages/prime-client/` + `packages/launchpad` | OK |
| Pas de Core3/DB dans Git | `.gitignore` + extract filtré | OK |
| Smoke documenté | [`packages/prime-client/SMOKE.md`](packages/prime-client/SMOKE.md) + [`docs/SMOKE_LAN.md`](docs/SMOKE_LAN.md) ; patches + `:8792` ready | OK (doc + HTTP 2026-07-31) |
| Pipeline assets | Lien `Infographiste_IA` dans registre | OK |

## Hors scope (volontaire)

- Fusion Infographiste dans ce monorepo ; avatar_app reste en _archive
- Migration Core3 serveur dans Git
- Suppression immédiate des repos GitHub legacy
