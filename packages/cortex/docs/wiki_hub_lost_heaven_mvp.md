# Wiki hub — Lost Heaven (MVP généré)

**Ticket** : C6 · **Généré** : 2026-10-06 · **Live** : `GET http://192.168.0.246:8787/v1/wiki` (2026-10-07) · **Script** : `packages/cortex/tools/generate_wiki_hub_lost_heaven_mvp.py`

**Sources** : [`INVENTAIRE_PNJ.md`](../../../docs/world/INVENTAIRE_PNJ.md) §1 · [`m10_skills_catalog.json`](../content/m10/m10_skills_catalog.json)

> Document **généré** — ne pas éditer à la main. Regenerer via le script. Pas de lore inventé hors inventaire / M10.

---

## PNJ hub (extrait inventaire)

| Nom | Id | Rôle | POI |
|-----|----|------|-----|
| Jax Moro | `npc:core3_barman_jax` | bartender | cantina |
| Habitué | `npc:habitue_cantina` | patron | cantina |
| Maître de salle | `npc:maitre_salle` | host | cantina |
| Artiste de scène | `npc:artiste_scene` | performer (pas trainer) | cantina |
| Videur | `npc:videur` | bouncer | cantina |
| Talen Ress | `npc:core3_talen_ress` | entertainer_trainer | auberge |
| Guide de quartier | `npc:guide_quartier` | guide | starport |
| Agent de circulation | `npc:agent_circulation` | traffic | starport |
| Theo Nash | `npc:core3_pilot_alliance_c` | pilot | starport |
| Dorn Pike | `npc:core3_pilot_freelance_c` | pilot | starport |
| Garr Vek | `npc:core3_pilot_imperial_a` | pilot_trainer | starport |
| Mord Kael | `npc:core3_pilot_imperial_c` | pilot | — |
| Sergent de rue | `npc:sergent_rue` | sergeant | gate |
| Garde | `npc:guard` | guard | gate |
| Rumeuriste | `npc:rumeuriste` | rumormonger | market |
| Daan Oth | `npc:core3_daan_oth` | quest_giver | mission_post |
| Scribe | `npc:scribe` | archivist | town_hall |
| Odo Merr | `npc:core3_medic_trainer_c` | medic_trainer | clinic |
| Tobin Ress | `npc:core3_brawler_trainer_c` | combat_trainer (brawler) | training_hall |
| Unar Tek | `npc:core3_marksman_trainer_c` | combat_trainer (marksman) | training_hall |
| Yara Nis | `npc:core3_scout_trainer_c` | scout_trainer | training_hall |
| Kell Asa | `npc:core3_artisan_trainer_c` | artisan_trainer | artisan_hall |
| Vorn Thess | `npc:core3_politician_trainer_c` | politician_trainer | town_hall |
| Kisreudi Teste | `npc:scientist_mos` | scientist / resident | housing_npc |

_Total roster §1 parsé : **24** entrées._

---

## Professions M10 (extrait)

| Id | Nom | Trainers (rôles) |
|----|-----|------------------|
| `artisan` | Artisan de rue | artisan_trainer |
| `prospecteur` | Prospecteur | scout_trainer |
| `medecin` | Médecine de camp | medic_trainer |
| `scene` | Scène | entertainer_trainer |
| `poing` | Poing | combat_trainer |
| `visee` | Visée | combat_trainer |
| `citoyen` | Citoyen de quartier | politician_trainer |
| `shuttle` | Pilotage shuttle | pilot |

## Arbres / playstyles UI (extrait M10)

| Id | Nom | Profession | Blurb |
|----|-----|------------|-------|
| `gathering` | Prospection | `prospecteur` | Repérer et extraire ressources du désert et des épaves. |
| `crafting` | Artisanat | `artisan` | Assembler outils, kits et pièces au banc de rue ou à l'atelier. |
| `medicine` | Médecine | `medecin` | Soins de camp, kits de terrain, stabilisation. |
| `scene` | Scène | `scene` | Danse, musique, spectacle et réconfort moral. |
| `pilot` | Pilotage | `shuttle` | Conduite shuttle / apron Lost Heaven. |
| `social` | Social / quartier | `citoyen` | Présence civile, badges, réseaux de Lost Heaven. |
| `brawler` | Poing | `poing` | Combat mêlée (hors vitrine M10 courte). |
| `marksman` | Visée | `visee` | Combat distance (hors vitrine M10 courte). |

---

## Notes MVP

- Drift inventaire ↔ registry = fail smoke data (Argus).
- Formation scène = Talen Ress / triplon ; **pas** Kisreudi (V21).
- Wiki = guide joueur data-driven ; Scribe (C5) = chronique session séparée.
