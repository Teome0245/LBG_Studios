# Arbres talents — équivalence Pre-CU → LBG

**Date** : 2026-08-03  
**Statut** : canon design (O2) — données jouables encore partielles (M10 vitrine)  
**Réfs** : [`BIBLE_MMO.md`](BIBLE_MMO.md) V2 / V30–V35 · ADR 0016 · `packages/cortex/content/m10/m10_skills_catalog.json`  
**Garant runtime (à terme)** : **Chœur du monde** (`player_ia`)  
**Référence Pre-CU runtime** : serveur **245** — lecture seule (Bible **V4**) ; ne pas modifier.

---

## Principe

On **reprend la structure** SWG Pre-CU (pas l’IP Star Wars) :

```
novice → 4 branches × 4 boxes → master
```

Boucle : `skills → schematics → resources → craft → experiment → economy`.

Les ids moteur Core3 (`crafting_artisan_novice`, …) restent en **miroir technique** (`precu_skill_id`) tant que le serveur lit `skills.iff`.  
Les **noms joueur** = LBG uniquement.

### Où lire le Pre-CU « vrai »

| Source | Usage |
|--------|--------|
| **PreCU 245** (`192.168.0.245`) | Référence vivante — skills, craft, experiment, datatables. **Lecture seule.** |
| TRE / `skills.iff` (serveur) | Dump technique si besoin d’export |
| Ce fichier + `m10_skills_catalog.json` | Canon **LBG** (noms, priorités, vitrine M10) |

Toute découverte sur 245 se **recopie** dans le catalogue / docs Studios — on ne patch pas 245.

---

## Les 6 starters Pre-CU → LBG

| # | Pre-CU (moteur) | Profession LBG | Arbre M10 | Trainer LH | Priorité UI |
|---|-----------------|----------------|-----------|------------|-------------|
| 1 | `crafting_artisan` | **Artisan de rue** | `crafting` | Kell Asa | **P0** (axe ADR 0016) |
| 2 | `outdoors_scout` | **Prospecteur** | `gathering` | Yara Nis | **P0** (survey / ressources) |
| 3 | `science_medic` | **Médecine de camp** | `medicine` | Odo Merr | **P1** |
| 4 | `social_entertainer` | **Scène** | `scene` | Talen Ress (+ Bige, Lyra) | **P1** (cantina / Perle) |
| 5 | `combat_brawler` | **Poing** | `brawler` | Tobin Ress | **P2** (hors vitrine M10 courte) |
| 6 | `combat_marksman` | **Visée** | `marksman` | Unar Tek | **P2** |

### Hors starters, présents hub

| Pre-CU / proche | LBG | Note |
|-----------------|-----|------|
| `social_politician` | **Citoyen de quartier** | Badge / mairie — Vorn Thess |
| Pilot / JTL (neutral…) | **Pilotage shuttle** | Apron LH d’abord ; arbre spatial plus tard |

---

## Forme d’une profession (équivalent box)

```
{prof}_novice
  ├─ branche_a_01 … _04
  ├─ branche_b_01 … _04
  ├─ branche_c_01 … _04
  └─ branche_d_01 … _04
{prof}_master
```

### Artisan de rue (P0 — détail)

| Box LBG | Miroir Pre-CU typique | Effet |
|---------|----------------------|--------|
| `artisan_novice` | `crafting_artisan_novice` | Accès craft de base |
| `artisan_outils_01…04` | engineering / tools | Kits, outils |
| `artisan_conso_01…04` | domestic / food-like | Rations, consommables |
| `artisan_pieces_01…04` | components | Pièces pour schémas avancés |
| `artisan_survey_01…04` | survey (souvent scout+artisan) | Qualité ressources |
| `artisan_master` | `crafting_artisan_master` | Porte élites craft (plus tard) |

**M10 aujourd’hui** : seul `artisan_rue_r1` ≈ novice + outils_01 / conso_01 (kit + ration).

### Prospecteur (P0)

| Box LBG | Miroir | Effet |
|---------|--------|--------|
| `prospecteur_novice` | `outdoors_scout_novice` | Déplacement / camp basique |
| `prospecteur_survey_01…04` | harvest / trapping-like | Survey ressources |
| `prospecteur_piste_01…04` | exploration | POI / pistes désert |
| `prospecteur_camp_01…04` | camping | Camp, survie |
| `prospecteur_faune_01…04` | creature | (plus tard) |
| `prospecteur_master` | `outdoors_scout_master` | |

### Médecine de camp (P1)

Novice → Soin / Kits / Terrain / Toxines → master. Miroir `science_medic_*`.

### Scène — Entertainer (P1)

Aligné playbook Lia (`social_entertainer_dance_01…04`, healing) :

| Tier | LBG | Pre-CU |
|------|-----|--------|
| 0 | `scene_novice` + `scene_danse_01` | `social_entertainer_novice`, `…_dance_01` |
| 1–3 | `scene_danse_02…04` | `…_dance_02…04` |
| 4–5 | `scene_soin_01…02` | `…_healing_01…02` (buff morale) |

Trainer canon : **Talen Ress** (pas Kisreudi).

### Poing / Visée (P2)

Structure combat Pre-CU conservée ; **pas** dans le panneau M10 court tant que craft n’est pas B2B.

### Citoyen / Pilotage

- Citoyen : boxes Badge / Réseau / Mairie / Rumeur (politician allégé).  
- Shuttle : Apron / Nav courte / Cargo / Escorte — **pas** full JTL tant que Godot n’a pas le spatial.

---

## XP (types LBG)

| XP LBG | Alimente | Note Pre-CU |
|--------|----------|-------------|
| `xp_artisanat` | Artisan | ≈ crafting general / engineering |
| `xp_prospection` | Prospecteur | ≈ scout / trapping / harvest |
| `xp_medecine` | Médecine | ≈ medical |
| `xp_scene` | Scène | ≈ dance / music / entertainer healing |
| `xp_quartier` | Citoyen | ≈ political |
| `xp_pilotage` | Shuttle | ≈ space (réduit) |
| `xp_poing` / `xp_visee` | Combat | ≈ combat_* |

---

## Rôle du Chœur

| Phase | Chœur fait |
|-------|------------|
| **Maintenant** | Sonde bots Lia/Nix (dont progression entertainer / craft) sur `:8791` |
| **Cible** | Garant runtime : un bot qui **monte** un arbre Pre-CU-LBG sans contredire la Bible ; alerte si skill / dialogue / lieu dérive |
| **L2** | Think tick = jouer une box (survey→craft ou danse) + rapport écart vs catalogue |

Voir Bible **V50–V54**.

---

## Historique

| Date | Changement |
|------|------------|
| 2026-08-03 | Mapping 6 starters + politician/pilot ; détail Artisan / Prospecteur / Scène ; lien Chœur |
| 2026-08-04 | Réf. PreCU 245 lecture seule (V4) |
