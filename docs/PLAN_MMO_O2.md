# Plan MMO O2 — pivot produit + autonomie

**Date** : 2026-08-03 · **MAJ focus** 2026-08-24  
**Statut** : **canon exécutoire** (remplace la lecture « étape actuelle » de `plan_de_route.md` pour le jeu)  
**Recentrage wahou** : [`FOCUS_WAHOU.md`](FOCUS_WAHOU.md) — aboutis archivés, pari = 30 s Lost Heaven.  
**Repo** : `LBG_Studios` uniquement — legacy `new_mmo` / `LBG_IA_MMORPG` = lecture

## Pourquoi ce fichier

Plusieurs plans coexistaient (`plan_de_route`, `plan_mmorpg`, jalons M9–M12, ADR 0016 upstream, tracks bots).  
Celui-ci est la **source de vérité courte** pour avancer le client Godot + gateway, et la boucle Team.

| Doc | Rôle désormais |
|-----|----------------|
| **Ce fichier** | Priorités O2 + rails autonomie |
| [`docs/world/BIBLE_MMO.md`](world/BIBLE_MMO.md) | **Vérités du monde** + anti-dérive lore · garant runtime = Chœur (V50) |
| [`docs/world/CONCURRENTS_IA_MMO_2026-10.md`](world/CONCURRENTS_IA_MMO_2026-10.md) | Veille concurrents (Everwhere… SpaceMolt) · tickets = Boîte §14 · ADR docs 0002 |
| [`docs/world/INVENTAIRE_PNJ.md`](world/INVENTAIRE_PNJ.md) | Rôles canon PNJ |
| [`docs/world/ARBRES_TALENTS_PRECU.md`](world/ARBRES_TALENTS_PRECU.md) | Équivalence arbres Pre-CU → LBG |
| `packages/cortex/content/m10/m10_skills_catalog.json` | Catalogue talents/craft (schema 3, professions) |
| `RESTAURATION_PRODUIT.md` | Checklist vert/jaune/rouge |
| `OBJECTIVES.md` | Cadre O1/O2 |
| `packages/prime-client/docs/CLIENT_ONLY_GODOT.md` | Vision joueur Godot-only |
| [`PLAN_PRESENCE_ZONE_ENTRAINEMENT.md`](PLAN_PRESENCE_ZONE_ENTRAINEMENT.md) | Zone d'entraînement IA (dials B1–B4 · boucle Studio↔jeu C1–C3) · [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) D6.5 |
| ADR 0016 (`new_mmo/…`) | Axe talents/artisanat — **accepté de facto** |
| ADR 0017 | Core3 spatial + sidecar (historique peel) |
| **ADR 0026** | **Runtime Godot-first** — live `prime-hub` · [`RUNTIME_GODOT.md`](RUNTIME_GODOT.md) · spike hist. [`SPIKE_48H_GODOT_RUNTIME.md`](SPIKE_48H_GODOT_RUNTIME.md) |
| `plan_de_route.md` | Historique + étoile du nord (Studio) — pas le fil M12 |
| `plan_mmorpg.md` | Vision long terme (ignorer le bloc « Godot gelé ») |
| `plan_parallel_next_steps.md` | Bots / WD — **parallèle**, ne bloque pas P1–P4 |

---

## Rail A — Produit MMO

| # | Jalon | Done quand | Owner | État |
|---|--------|------------|--------|------|
| **P0** | Doc pivot | Ce fichier + liens OBJECTIVES / RESTAURATION | Thémis | **fait** 2026-08-03 |
| **P1** | M12 durci | Smoke M12 auto vert ; Launchpad → `J:\…\prime-client` ; login→WS→zone→move | Hermès + Argus | **fait** 2026-08-03 (smoke + move ±1.5 m) |
| **P2** | M10 B2B | UI talents/craft ↔ `:8791` + smoke craft ; critères ADR 0016 ; catalogue schema 3 Pre-CU-LBG | Iris + Dédale | **vert smoke 2026-08-15** ; GET `/v1/inventory` = dump Lua Core3 si perso online, sinon JSON bridge |
| **P2b** | Missions hub | Board Daan Oth ↔ `:8791` accept/complete stub + UI Godot **J** | Iris + Dédale | **vert smoke 2026-08-15** ; **objectifs terrain POI** (progress sur toutes templates hub + HUD objectif hors J) **fait** ; Core3 journal = suite |
| **P2c** | Scène cantina | Show La Perle + tip + formation Talen | Iris | **live hub** 2026-10-14 — `hub_show.gd` idle/live/encore · tip gated show · `POST /v1/show/train` · artiste scène · (`lh_show_perle` + Tip Scène) |
| **P3** | Persona en jeu | Dialogue PNJ + session_summary stables ; Chœur = vérif terrain (V50–V53) | Chœur | **vert** 2026-10-07 : invoke + history + C12 · `smoke_p3_hub_dialogue` + `smoke_choeur_terrain` |
| **P4** | Retrait pont SOE Python | Plus de chemin joueur via `soe_handshake` / retail | Hermès | **clos** — pont SOE définitivement retiré au profit du hub Godot G5+ (`:8787` unifié) |
| **P5** | World Director / bots | Tracks serveur **sans bloquer** P1–P4 | WD | parallèle |
| **P5a** | Cour de chasse (sandbox) | Lia/Nix/Mira vs Chacals — Pilot `#/hunt` + peel hub `/v1/hunt-yard*` | Chœur | **vert hub** 2026-10-07 (`smoke_p5_hunt_yard_hub`) · Pilot Python 2026-08-24 |
| **P6** | Runtime Godot-first | ADR 0026 + [`RUNTIME_GODOT.md`](RUNTIME_GODOT.md) — humain+bots+PNJ **sans** Core3 | Hermès + Iris | **G5 live** 2026-10-07 (`prime-hub` :8787 unifié, peel natif) ; Python OFF |

### Jalons M9–M12 (rappel)

| Jalon | État |
|-------|------|
| M9 carte/minimap | **fait** client |
| M10 talents/craft UI | **B2B smoke vert** — panel live `:8791` + recette + sync inventaire ; GET `/v1/inventory` préfère dump Lua Core3 si online |
| M11 login LBG | **fait** (Launchpad + éditeur) |
| M12 `lbg-ws/2` live | **fait** smoke login→WS→zone_state→move ; polish ZB optionnel |

---

## Rail B — Autonomie (validations humaines gardées)

| # | Point | Livrable | L2 (toi) |
|---|--------|----------|----------|
| **A1** | Mission → code → preuve | Playbook `mmo_jalon_client` : plan/tâches Hermès+Argus → smoke owner → clôture | Approve write hors allowlist / merge PR |
| **A2** | Verify après act | Smokes owner (login M11, WS M12, M9, LAN) ; **pas de clôture succès si rouge** | Force manuel rare |
| **A3** | Scoring playbooks | Mémoire + score → coffee-fill (`team/playbook_scores.py`) | Lecture |
| **A4** | Frontière L1/L2 | Tableau ci-dessous | Toujours L2 sur write sensible |

### Frontière L1 / L2 (A4)

| L1 auto | L2 token / humain |
|---------|-------------------|
| Smokes, healthz, audits | Write hors allowlist Iris |
| Coffee fill, drain Conductor | Build Core3 / Vulcan |
| Iris L3 allowlist après smoke | Think player / Chœur |
| Sync J: / assets bornés | Merge PR Cursor Cloud |
| Briefs PM, prune mémoire | Proto gateway / auth sensibles |

Flag clôture : `LBG_TEAM_MISSION_BLOCK_CLOSE_ON_SMOKE_FAIL=1` (défaut) — smoke QA rouge → mission **reste ouverte** (pas `closed` ni auto `closed_failed`).

---

## Ordre d’exécution

1. **P0** (doc) → **A1 + A2** (boucle) — **fait**  
2. **P1** (M12 smoke login→WS→zone→move) — **fait** 2026-08-03  
3. **A3** scoring — **fait** (`playbook_scores` + coffee-fill)  
4. **P2** M10 · **A4** tenu à jour dans ce fichier · **P3** persona  

## Commandes

```bash
# Smokes owner Godot (A2)
bash packages/cortex/infra/scripts/smoke_godot_owners.sh

# M11 / M12 / M10 unitaires
bash packages/cortex/infra/scripts/smoke_godot_m11_login_lan.sh
bash packages/cortex/infra/scripts/smoke_godot_m12_ws_lan.sh
bash packages/cortex/infra/scripts/smoke_godot_m10_craft_lan.sh
bash packages/cortex/infra/scripts/smoke_godot_quest_hub_lan.sh
BUNDLE=godot_craft bash packages/cortex/infra/scripts/smoke_godot_owners.sh

# Playbook jalon client (A1) — spawn tâches Team
cd packages/cortex && source .venv/bin/activate
LBG_ORCHESTRATOR_URL=http://192.168.0.140:8010 \
  python -m lbg_agents.spawn_team_mmo_jalon_job
```

## Références

- `packages/cortex/docs/jalon_m11_login_lbg.md`
- `packages/cortex/docs/GATEWAY_PRIME_246.md`
- `packages/cortex/docs/adr/0019-team-plan-llm-bus.md`
- `packages/cortex/docs/plan_campus_conductor.md`
- `packages/prime-client/SMOKE.md`
