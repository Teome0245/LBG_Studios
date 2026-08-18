# Restauration produit — étoile du nord

**Date** : 2026-08-18  
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
| `open_url` réel (allowlist host) | **vert** | 2026-08-03 : `https://example.org` OK sur worker |
| `search_web_open` | **vert** | 2026-08-03 : DDG réel OK (`LBG_DESKTOP_WEB_SEARCH=1`) |
| `notepad_append` (proxy dictée) | **vert** | 2026-08-03 : `C:\Users\Public\lbg_rang1_notes.txt` |
| Mail IMAP lecture | **vert** | 2026-08-03 : `mail_imap_preview` OK (`.51`, user `sdesharches`, INBOX ; TLS **993** + `INSECURE_SSL`) |
| Dictée micro → STT → Notepad | **jaune** | Append texte OK ; micro/STT **reporté** (pas urgent) |
| `session_summary` poste ↔ Assistant | **vert** | 2026-08-03 : `export` + `mmo-bridge` HTTP OK (Pilot Cortex) |
| Audit disque / selfcheck infra (SSH, healthz) | **vert** | Supervisé GIR (ex. « audit disque prime 246 ») |
| Team ops (Héphaïstos) hors dry-run | **vert** | Dry-run Cockpit propagé + inject `devops_approval` à la création tâche (2026-07-31) |
| Approval sans double collage | **vert** | Inject serveur si Bearer Pilot OK |

## Rang 2 — Persona MMO / pont

| Fonction | État | Où / note |
|----------|------|-----------|
| Serveur Prime 246 + comptes `:8792` | **vert** | Runtime ready (smoke LAN) |
| Client Godot `prime-client` + Launchpad | **vert** (login) | M11+WS Launchpad OK via `J:\…\prime-client` (2026-08-03) ; suite M12/M10 → [`PLAN_MMO_O2.md`](PLAN_MMO_O2.md) |
| Sidecar joueurs IA `:8791` | **jaune** | Sondes Team `player_ia` ; pas focus courant |
| Dialogue / Lyra *en jeu* (persona) | **jaune** | Multi-tours (`history` + LineEdit) + `session_summary` ; lore Scrapaltai/Lost Heaven ; smoke `tools/smoke_rang2_persona_dialogue.sh` |
| Bac Python `mmmorpg_server` / web `/mmo/` | **rouge** | Gelé volontairement |

## Rang 3 — Évolution monde / code par l’IA

| Fonction | État | Où / note |
|----------|------|-----------|
| Forge OpenGame (staging) | **jaune** | Proposition / dry-run ; pas merge tronc |
| Auto-patch / rebuild DevOps aveugle | **rouge** | Hors scope tant que rang 1 pas assez fiable |
| Équipe Fable autoconsult 12 h | **vert** | Timer `lbg-team-autoconsult-job` sur 140 |
| Sprint évolution 7j (Thémis) | **vert** | Timer `lbg-team-evolution-sprint-job` ; L1 auto / L2 Pilot ; [`team_evolution_sprint.md`](../packages/cortex/docs/team_evolution_sprint.md) |

## Cadre O0 / O1 (remise en forme)

| Item | État |
|------|------|
| Repo `LBG_Studios` source de vérité | **vert** |
| `packages/cortex` Pilot 140 | **vert** |
| Surfaces LAN liées (Cockpit, Orch, `:8792`) | **vert** |
| Smoke `tools/smoke_lan_surfaces.sh` | **vert** |
| Smoke Team `smoke_vm_lan.sh` (Argus) | **vert** (2026-08-03 : Ollama sondé sur `.110`, soft-fail) |
| Pas de réintro client web legacy `/mmo/` | **vert** |
| Pilot Vite (modules ES, Three npm, bundle `dist/`) | **vert** (2026-08-18 ; servir `dist/` si présent, sinon sources) |
| Orchestrateur local sans `hybrid_proactive_agent` legacy | **vert** (stub Cortex 2026-08-18) |
| LLM local Qwen 27b (`.110`) + light `.111` | **vert** |

---

## Prochaine traction

**O2 / MMO** (priorité jeu après login OK) — voir [`PLAN_MMO_O2.md`](PLAN_MMO_O2.md) :

1. A1+A2 autonomie (playbook jalon + smokes owner anti-clôture).
2. ~~P1 M12 durci (smoke WS + move)~~ — fait 2026-08-03.
3. P2 M10 — catalog/smoke `:8791` OK ; suite craft_combine ADR 0016 ; P3 persona.

**Rang 1** (déjà largement vert) :

1. ~~Exercer Team ops avec dry-run décoché~~ — OK (healthz réel 2026-07-31).
2. Smoke optionnel Desktop **réel** (Cockpit + inject) dans `smoke_lan_surfaces.sh --functional`.
3. ~~Smoke Team Argus (`smoke_vm_lan.sh`)~~ — OK 2026-08-03.
4. ~~Parcours URL / web / notepad / session_summary~~ — OK 2026-08-03 ([`PLAN_RANG1_ASSISTANT.md`](PLAN_RANG1_ASSISTANT.md)).
5. ~~Mail IMAP~~ — OK 2026-08-03 ; dictée STT reportée.
6. Rang 2 : [`PLAN_RANG2_PERSONA.md`](PLAN_RANG2_PERSONA.md).
