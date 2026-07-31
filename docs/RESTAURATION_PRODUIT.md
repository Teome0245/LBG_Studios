# Restauration produit — étoile du nord

**Date** : 2026-07-31  
**But** : ne pas perdre l’objectif d’origine pendant le recentrage O0/O1.

Vision (note 2026-04-28) : IA incarnée sur **PC/infra** → même famille au **cœur du MMO** → **évolution contrôlée** du monde / code.

Doc pivot : [`packages/cortex/docs/vision_projet.md`](../packages/cortex/docs/vision_projet.md) · [`plan_de_route.md`](../packages/cortex/docs/plan_de_route.md) § *Étoile du nord*.

Légende : **vert** = utilisable aujourd’hui · **jaune** = partiel / à solidifier · **rouge** = pas encore / gelé volontairement.

---

## Rang 1 — Assistant PC & infra

| Fonction | État | Où / note |
|----------|------|-----------|
| Ouvrir une app sur le PC (`open_app`, vghd…) | **vert** | Cockpit Supervisé / Chat GIR ; jetons 140 ↔ `C:\Agent_IA\desktop.env` alignés ; inject approval serveur |
| Dry-run Desktop | **vert** | Réglages Cockpit + smoke `--functional` |
| Ouvrir URL allowlistée | **jaune** | Dry-run OK ; réel = allowlist worker |
| Recherche web / mail lecture | **jaune** | Flags worker ; peu smoke E2E |
| Dictée → Notepad | **jaune** | Cible produit ; pas parcours E2E stable |
| Audit disque / selfcheck infra (SSH, healthz) | **vert** | Supervisé GIR (ex. « audit disque prime 246 ») |
| Team ops (Héphaïstos) hors dry-run | **vert** | Dry-run Cockpit propagé + inject `devops_approval` à la création tâche (2026-07-31) |
| `session_summary` poste ↔ Assistant | **jaune** | UI Pilot/Cockpit restaurée ; usage pont MMO à exercer |
| Approval sans double collage | **vert** | Inject serveur si Bearer Pilot OK |

## Rang 2 — Persona MMO / pont

| Fonction | État | Où / note |
|----------|------|-----------|
| Serveur Prime 246 + comptes `:8792` | **vert** | Runtime ready (smoke LAN) |
| Client Godot `prime-client` + Launchpad | **jaune** | Extract OK ; login manuel PC |
| Sidecar joueurs IA `:8791` | **jaune** | Sondes Team `player_ia` ; pas focus courant |
| Dialogue / Lyra *en jeu* (persona) | **jaune** | Lyra UI `:5174` = style LLM, pas exécuteur ; pont jeu à poursuivre |
| Bac Python `mmmorpg_server` / web `/mmo/` | **rouge** | Gelé volontairement |

## Rang 3 — Évolution monde / code par l’IA

| Fonction | État | Où / note |
|----------|------|-----------|
| Forge OpenGame (staging) | **jaune** | Proposition / dry-run ; pas merge tronc |
| Auto-patch / rebuild DevOps aveugle | **rouge** | Hors scope tant que rang 1 pas assez fiable |
| Équipe Fable autoconsult 24/7 | **jaune** | Roster + presets ; autonomie L1 partielle |

## Cadre O0 / O1 (remise en forme)

| Item | État |
|------|------|
| Repo `LBG_Studios` source de vérité | **vert** |
| `packages/cortex` Pilot 140 | **vert** |
| Surfaces LAN liées (Cockpit, Orch, `:8792`) | **vert** |
| Smoke `tools/smoke_lan_surfaces.sh` | **vert** |
| Pas de réintro client web legacy `/mmo/` | **vert** |

---

## Prochaine traction (rang 1 d’abord)

1. ~~Exercer Team ops avec dry-run décoché~~ — OK (healthz réel 2026-07-31).
2. Smoke optionnel Desktop **réel** (Cockpit + inject) dans `smoke_lan_surfaces.sh --functional`.
3. Parcours mail / web / dictée un par un.
4. Puis rang 2 : pont `session_summary` → persona MMO (ADR 0004).
