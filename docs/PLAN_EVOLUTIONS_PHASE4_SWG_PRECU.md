# Plan d’Évolutions Phase 4 — Boucle Majeure « Star Wars Galaxies Pre-CU » dans Lost Heaven (O2 / O3)

**Date** : 2026-11-01  
**Statut** : **100 % ACHEVÉ & VALIDÉ (5/5 Tickets DONE)**  
**Source de vérité** : Monorepo `LBG_Studios` (`packages/prime-hub` & `packages/prime-client`, runtime `.246:8787`)  
**Références canons** : [`ARBRES_TALENTS_PRECU.md`](world/ARBRES_TALENTS_PRECU.md) · [`BIBLE_MMO.md`](world/BIBLE_MMO.md) · [`m10_skills_catalog.json`](../packages/cortex/content/m10/m10_skills_catalog.json)

---

## 1. Principe Directeur

Porter l'intégralité de la boucle systémique de **Star Wars Galaxies (Pre-CU)** (`skills → survey → resources → craft → experiment → HAM/cantina/medcenter → harvesters`) dans **Lost Heaven** sous autorité déterministe **Godot Headless (`prime-hub` `:8787`)** — zéro propriété intellectuelle Star Wars, zéro retour à Core3/Python sur le chemin joueur, et zéro mutation libre par LLM sur l'économie ou le combat.

---

## 2. Bilan des 5 Tickets Phase 4

- [x] **Ticket 4.1** : Arbres de Compétences `Novice → 4×4 Boxes → Master` & Plafond de `250 Skill Points` (`hub_skills.gd`, `catalog_skills.json`, `talents_craft_panel.gd`, `precu_skills_tree_selftest.gd`)
- [x] **Ticket 4.2** : Prospection Dynamique (`Survey Tool`) & Spawns de Ressources à Statistiques `1..1000` (`OQ`, `CD`, `PE`, `MA`, `SR`) (`hub_survey.gd`, `resources_spawns_lh.json`, `survey_resources_selftest.gd`)
- [x] **Ticket 4.3** : Artisanat Profond : Assemblage Pondéré par Ressources & Phase d'Expérimentation (`hub_crafting.gd`, `craft_experimentation_selftest.gd`)
- [x] **Ticket 4.4** : Boucle Sociale & Médicale : Pools `HAM`, `Wounds` (Medcenter) & `Battle Fatigue` (Cantina La Perle) (`hub_ham_medical.gd`, `ham_cantina_medcenter_selftest.gd`)
- [x] **Ticket 4.5** : Extracteurs de Terrain (`Harvesters`), Trémies `Hopper` & Arbitrage Autonome IA O3 (`hub_harvesters.gd`, `hub_bot_autonomy.gd`, `harvesters_outpost_selftest.gd`)
- [x] **Ticket 4.6 (Client 2D Top-Down)** : Interface Joueur SWG Pre-CU complète dans `packages/prime-client` (`swg_ham_hud.gd`, `swg_radial_menu.gd`, `swg_skills_panel.gd`, `swg_survey_panel.gd`, `swg_experiment_panel.gd`, validée par `client_modular_selftest.gd`)

---

## 3. Endpoints REST (`prime-hub` `:8787`)

| Pilier SWG Pre-CU | Méthode & Route | Description |
|-------------------|-----------------|-------------|
| **4.1 Skills 4×4** | `GET /v1/skills/tree` | Snapshot des 8 professions 4×4, Skill Points `/250`, jauges d'XP et modificateurs |
| **4.1 Skills 4×4** | `POST /v1/skills/learn` | Apprentissage d'une box sous contrôle de prérequis, XP et plafond 250 SP |
| **4.1 Skills 4×4** | `POST /v1/skills/surrender` | Abandon d'une box feuille (`surrender`) pour respécialiser ses Skill Points |
| **4.2 Prospection** | `GET /v1/survey/spawns` | Liste des gisements actifs et de leurs stats `OQ/CD/PE/MA/SR` (`1..1000`) |
| **4.2 Prospection** | `POST /v1/survey/ping` | Sondage radar géologique (densité locale `0..100%` et boussole directionnelle) |
| **4.2 Prospection** | `POST /v1/survey/sample` | Extraction d'échantillons typés avec conservation des stats dans l'inventaire |
| **4.3 Artisanat** | `POST /v1/craft/assemble` | Assemblage sur établi CAO pondéré par les stats des ressources + ouverture session d'expérimentation |
| **4.3 Artisanat** | `POST /v1/craft/experiment` | Dépense de points d'expérimentation (`amazing_success` .. `critical_failure`) sur `power`, `durability`, `quality_pct` |
| **4.4 HAM / Soins** | `GET /v1/medical/status` | État des 3 barres `HAM` (`Health`, `Action`, `Mind`), `Wounds` et `Battle Fatigue` |
| **4.4 HAM / Soins** | `POST /v1/show/watch` | Écouter/regarder un artiste à La Perle : dissipe la `Battle Fatigue` et buff `Mind` |
| **4.4 HAM / Soins** | `POST /v1/medical/treat_wounds` | Traitement des `Wounds` au Medcenter (amplifié par les medpacks artisanaux) |
| **4.5 Harvesters** | `GET /v1/harvesters/list` | Liste des extracteurs actifs, maintenance et niveau de remplissage `Hopper` |
| **4.5 Harvesters** | `POST /v1/harvesters/deploy` | Pose d'un extracteur hors-bâtiment CAO sur une veine `>= 25%` |
| **4.5 Harvesters** | `POST /v1/harvesters/collect` | Vidange du `Hopper` vers l'inventaire du propriétaire avec stats `1..1000` |

