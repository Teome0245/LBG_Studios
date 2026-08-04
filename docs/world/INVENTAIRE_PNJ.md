# Inventaire PNJ — rôles canon

**Date** : 2026-08-03  
**Source data** : `packages/cortex/agents/src/lbg_agents/npc_registry.json` (61 entrées)  
**Ancres LH** : `packages/prime-client/assets/maps/lost_heaven_npc_anchors.json` (25 matchs pilot)  
**Bible** : [`BIBLE_MMO.md`](BIBLE_MMO.md) (V20–V24, V50–V54)  
**Talents** : [`ARBRES_TALENTS_PRECU.md`](ARBRES_TALENTS_PRECU.md)  
**Garant runtime** : Chœur du monde (`player_ia`) — pas un PNJ de cette liste

---

## Légende

| Colonne | Sens |
|---------|------|
| **Rôle canon** | Ce que le personnage *est* (dialogue + gameplay) |
| **Hub LH** | Ancré Lost Heaven (building) |
| **Doublon** | Même persona sous plusieurs ids registry |
| **Debt** | Zone / lore encore « Mos Eisley » — à migrer wording |

**Statuts** : `canon` · `relief` (triplon / backup) · `fantasy_stub` (hors hub LBG) · `debt_me` (texte ME à nettoyer)

---

## 1. Hub Lost Heaven — roster actif (ancré)

| Nom | Id principal | Rôle canon | POI LH | Statut | Notes |
|-----|--------------|------------|--------|--------|-------|
| Jax Moro | `npc:core3_barman_jax` | bartender | cantina | canon | Comptoir |
| Habitué | `npc:habitue_cantina` / core3 | patron | cantina | canon | |
| Maître de salle | `npc:maitre_salle` / core3 | host | cantina | canon | |
| Artiste de scène | `npc:artiste_scene` / core3 | **performer** (pas trainer) | cantina | canon | Spectacle ; ne vend pas skills |
| Videur | `npc:videur` / core3 | bouncer | cantina | canon | |
| **Talen Ress** | `npc:core3_talen_ress` | **entertainer_trainer** | auberge | canon | Danse / musique / scène — **référent formation** |
| Guide de quartier | `npc:guide_quartier` / core3 | guide | starport | canon | |
| Agent de circulation | `npc:agent_circulation` / core3 | traffic | starport | canon | |
| Theo Nash | `npc:core3_pilot_alliance_c` | pilot | starport | canon | |
| Dorn Pike | `npc:core3_pilot_freelance_c` | pilot | starport | canon | |
| **Garr Vek** | `npc:core3_pilot_imperial_a` | **pilot_trainer** | starport | debt_me | Instructeur formation space ; ancré LH (remplace C) |
| Mord Kael | `npc:core3_pilot_imperial_c` | pilot | — | relief | Relève imperial ; plus d’ancre LH |
| Sergent de rue | `npc:sergent_rue` / core3 | sergeant | gate | canon | |
| Garde | `npc:guard` / core3 | guard | gate | canon | |
| Rumeuriste | `npc:rumeuriste` / core3 | rumormonger | market | canon | |
| Daan Oth | `npc:core3_daan_oth` | quest_giver | mission_post | canon | |
| Scribe | `npc:scribe` / core3 | archivist | town_hall | canon | |
| Odo Merr | `npc:core3_medic_trainer_c` | medic_trainer | clinic | canon | |
| Tobin Ress | `npc:core3_brawler_trainer_c` | combat_trainer (brawler) | training_hall | canon | |
| Unar Tek | `npc:core3_marksman_trainer_c` | combat_trainer (marksman) | training_hall | canon | |
| Yara Nis | `npc:core3_scout_trainer_c` | scout_trainer | training_hall | canon | |
| Kell Asa | `npc:core3_artisan_trainer_c` | artisan_trainer | artisan_hall | canon | |
| Vorn Thess | `npc:core3_politician_trainer_c` | politician_trainer | town_hall | canon | |
| **Kisreudi Teste** | `npc:scientist_mos` → `npc:core3_kisreudi` | **scientist / resident** | housing_npc | canon | Fel'Rani (T1) — **pas danse** |

---

## 2. Trainers — professions (triplons)

Chaque métier a souvent A/B/C (titulaire + relèves). **En jeu LH**, l’ancre pointe en général sur le **C** (ou Talen pour entertainer).

| Profession | Titulaire / relèves | Ancré LH | Skills M10 liés (V30) |
|------------|---------------------|----------|------------------------|
| Artisan | Bix Torren, Hana Meru, **Kell Asa** | Kell Asa | crafting · schematics outil/misc |
| Medic | Fen Taro, Nessa Rhyl, **Odo Merr** | Odo Merr | medicine |
| Scout | Elin Vor, Perrin Koch, **Yara Nis** | Yara Nis | gathering (prospecteur / terrain) |
| Brawler | Korr Ven, Mira Kael, **Tobin Ress** | Tobin Ress | (combat — hors M10 vitrine) |
| Marksman | Sela Voss, Jax Morr, **Unar Tek** | Unar Tek | (combat — hors M10 vitrine) |
| Politician | Mace Dulon, Sira Kell, **Vorn Thess** | Vorn Thess | badge / social (badge_quartier) |
| **Entertainer** | **Bige Coto**, **Lyra Velo**, **Talen Ress** | **Talen Ress** | danse / musique / scène — **pas Kisreudi** |
| **Pilotage** | **Garr Vek** (A), Lina Thess (B), Mord Kael (C) | **Garr Vek** | shuttle / space (V32) |

Doublons registry entertainer :  
`npc:entertainer_trainer_mos` (= Bige), `…_relief` (= Lyra), `…_relief2` (= Talen) — même personas que `core3_*`.

---

## 3. Cas Kisreudi

| Champ | Canon |
|-------|-------|
| Rôle | Scientifique de terrain / résidente |
| Race | **`race:fel_rani`** (Fel'Rani, origine Arvandor) — T1 2026-08-03 |
| Lieu | Lost Heaven (housing PNJ) |
| Pas | Danse, barmaid, formation entertainer |

**Action** : constraints registry + V21 ; formation danse = Talen / triplon.

---

## 4. La Perle de Scrapaltai — staff cantina (canon V13 / T2)

| Rôle | Qui | Peut parler de… |
|------|-----|-----------------|
| bartender | Jax (+ Sira Vale, Torrik Fenn relief) | boissons, ambiance La Perle |
| host | Maître de salle | tables, scène |
| performer | Artiste de scène | show à La Perle, pas formation skill |
| bouncer | Videur | sécurité |
| patron | Habitué | rumeurs non autoritaires |
| **trainer danse** | **Talen Ress** (auberge) / Bige / Lyra | formation entertainer ; show → La Perle |

---

## 5. Hors hub / stubs (ne pas propager en dialogue Scrapaltai)

| Nom | Id | Rôle | Statut |
|-----|-----|------|--------|
| Alchimiste | `npc:alchemist` | alchemist | fantasy_stub — « Atelier des mixtures » |
| Guérisseuse | `npc:healer` | healer | fantasy_stub — Dispensaire |
| Aubergiste | `npc:innkeeper` | innkeeper | fantasy_stub — Pomme Rouge |
| Maire | `npc:mayor` | mayor | fantasy_stub |
| Marchande | `npc:merchant` | merchant | fantasy_stub |
| Forgeron | `npc:smith` | smith | fantasy_stub |

Ces fiches peuvent rester pour tests Studio ; **interdits** comme vérité monde joueur (couche D).

---

## 6. Pilotes / informants non ancrés (réserve)

Pilotes A/B (Alliance, Freelance, Imperial) et informants Nira Kell / Vex Sorn : présents registry, **pas** d’ancre LH dédiée (sauf C starport / Daan). Utilisables en rotation ; ne pas inventer un second hub pour eux.

---

## 7. Dette wording (reste)

- Renommer factions pilot « imperial / alliance » → labels LBG (**T3**).
- Summaries Core3 encore verbeux « ME / SWG » sur certains reliefs (hors roster ancré).

Hub zones / factions « Civils Lost Heaven » : **fait** (T4 2026-08-03).
Kisreudi race Fel'Rani : **fait** (T1).

---

## Historique

| Date | Changement |
|------|------------|
| 2026-08-03 | Premier inventaire 61 PNJ ; roster LH 25 ; clarification entertainer vs Kisreudi |
| 2026-08-03 | T2 — La Perle canon ; staff + Talen mis à jour |
| 2026-08-03 | T1 Fel'Rani ; T4 zones hub Lost Heaven |
