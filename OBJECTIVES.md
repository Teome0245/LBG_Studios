# Objectifs LBG Studios

**Ordre** : Studio (**O1**) puis Jeu (**O2**).

## O0 — Cadre (ce repo)

- [x] Dépôt `Teome0245/LBG_Studios` = point de départ docs / Cursor / Team
- [x] Registre + objectifs versionnés ici
- [ ] Allowlist Cursor Cloud Agent inclut ce repo
- [ ] Workspace Cursor ouvert sur ce repo au quotidien

## O1 — Studio (prioritaire)

Cortex opérationnel recentré : Pilot, orchestrateur, Campus/Lyra, Cursor Cloud Agent, desktop hybride — **sans** client web legacy `/mmo/`.

| Critère done | Mesure |
|--------------|--------|
| Code Cortex extrait | `packages/cortex/` (orchestrator, backend, agents, pilot_web allégé, infra) |
| Pilot LAN | `http://192.168.0.140:8080/` servi / déployable depuis ce layout |
| Team / healthz | API Team + healthz OK après deploy depuis `packages/cortex` |
| Accueil Pilot | Carte Jeu Prime (Godot/Launchpad), pas de lien produit `/mmo/` |
| Freeze soft | Features hors O1/O2 gelées dans repos legacy |

## O2 — Jeu (ensuite)

Client **Godot** `prime-client` + Launchpad + serveur **Prime 246**.

| Critère done | Mesure |
|--------------|--------|
| Client extrait | `packages/prime-client/` (+ `packages/launchpad` sources utiles) |
| Pas de Core3/DB dans Git | `.gitignore` + absence `third_party` Core3 / databases |
| Smoke documenté | Launchpad/Godot → gateway 246 ; patches `http://192.168.0.246:8080/patches/prime/` |
| Pipeline assets | Lien documenté vers `Infographiste_IA` (pas fusion forcée) |

## Hors scope (volontaire)

- Fusion Infographiste + avatar dans ce monorepo
- Migration Core3 serveur dans Git
- Suppression immédiate des repos GitHub legacy
