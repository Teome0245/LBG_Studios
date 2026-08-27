# Bible MMO — Vérités du monde LBG

**Date** : 2026-08-03  
**Statut** : **V1–V42 validées** (pilote 2026-08-03) · V50–V54 + ancres = canon vivant  
**Rôle** : ancrer le lore, bloquer les dérives LLM / prompts / contenu  
**Compléments** : [`INVENTAIRE_PNJ.md`](INVENTAIRE_PNJ.md) · [`ARBRES_TALENTS_PRECU.md`](ARBRES_TALENTS_PRECU.md) · [`BOITE_IDEES_GAMEPLAY.md`](BOITE_IDEES_GAMEPLAY.md) · [`m10_skills_catalog.json`](../../packages/cortex/content/m10/m10_skills_catalog.json)  
**Produit** : [`PLAN_MMO_O2.md`](../PLAN_MMO_O2.md) · ADR 0009 (Scrapaltai / Lost Heaven) · ADR 0016 (talents + artisanat)  
**Garant runtime (cible)** : **Chœur du monde** (`studio_player_ia_choeur` / rôle Team `player_ia`)

---

## Comment utiliser ce fichier

1. **Toute vérité** ci-dessous est autoritaire pour dialogue, quêtes, docs et UI.
2. Si un PNJ / LLM / stub **contredit** une vérité → on corrige la data, pas le monde.
3. Scrapaltai / Lost Heaven = **hub joueur actuel**, pas l’univers entier.
4. Avant d’inventer un lieu, un métier ou un PNJ : vérifier l’[inventaire](INVENTAIRE_PNJ.md).
5. Avant d’ajouter un skill : vérifier l’[équivalence Pre-CU](ARBRES_TALENTS_PRECU.md) + catalogue M10 ; **référence runtime** = PreCU **245** (lecture seule, V4).
6. Le **Chœur du monde** est le garant *runtime* (bots / smoke / écart) ; ce fichier reste le garant *écrit*.
7. **Ne jamais modifier** le serveur PreCU **192.168.0.245** (modèle SWG Pre-CU d’origine).

---

## Couches du cosmos (ne pas confondre)

| Couche | Quoi | Exemples | Statut produit |
|--------|------|----------|----------------|
| **A — Hub jouable** | Monde où le joueur spawn / joue aujourd’hui | Planète **Scrapaltai**, ville **Lost Heaven** | Actif (client Godot + Prime) |
| **B — Réseau stellaire LBG** | Autres mondes / origines raciales | Arvandor, Terre1, Mecha_Prime, Khar_Zuun, Thalassia, … | Lore + races ; pas tous jouables |
| **C — Technique moteur** | Ids zone / legacy SOE | Zone id `tatooine`, anciens labels « Mos Eisley » | Invisible joueur ; migration en cours |
| **D — Fantasy stub** | Contenu générique non LBG | Quêtes loups/bandits, auberge « Pomme Rouge » | **Gelé / à remplacer** — ne pas propager |

**Vérité C0** : le joueur voit **Scrapaltai / Lost Heaven**, jamais « Tatooine » ni « Mos Eisley » dans l’UI ou le dialogue.

---

## Vérités du monde (V1)

### Identité produit

| ID | Vérité |
|----|--------|
| **V1** | LBG Prime est un MMO **LBG**, pas Star Wars. Pas d’Empire, Jedi, Hutt, Tatooine en surface joueur. |
| **V2** | Boucle centrale : **compétences → schémas → ressources → craft → économie** (axe talents Pre-CU / ADR 0016). |
| **V3** | Le client produit est **Godot `prime-client`**. Le lore doit tenir sans assets retail SWG. |
| **V4** | **PreCU 245** (`192.168.0.245`) = **modèle / référence** SWG Pre-CU le plus proche de l’original. **Lecture seule** pour reprendre infos (skills, craft, XP, datatables). **Interdit** de le modifier, patcher ou « LBG-iser ». Toute évolution produit = **Prime 246** + `LBG_Studios`. |

### Géographie hub

| ID | Vérité |
|----|--------|
| **V10** | **Scrapaltai** = planète désertique hub (Ø ~10 465 km). Carte : [`SCRAPALTAI_CARTE_PLANETE.md`](../../packages/cortex/docs/SCRAPALTAI_CARTE_PLANETE.md). |
| **V10b** | **Zalem** = capitale planétaire Scrapaltai (métropole verticale, pentagone central carte). **Non jouable v1** — lore / shuttles futurs. Ton : cité de ferraille en hauteur (réf. structurelle Gunnm, univers LBG propre). |
| **V11** | **Lost Heaven** = **petite ville** avant-poste — seul hub **gameplay** (spawn, POI, trainers). Cadran col **8** / row **3** sur la carte planète. **Pas la capitale.** |
| **V12** | POI hub figés côté client : starport, cantina, banque, auberge, marché, hall d’entraînement, clinique, bureau des missions, mairie, atelier artisan, logements PNJ, porte. |
| **V13** | La cantina hub de Lost Heaven s’appelle **« La Perle de Scrapaltai »** (`poi:lost_heaven_cantina`). Canon depuis 2026-08-03 (T2). |

### Personnages (anti-dérive)

| ID | Vérité |
|----|--------|
| **V20** | Un PNJ a **un rôle canon** (registry + inventaire). Il ne s’attribue pas un autre métier. |
| **V21** | **Kisreudi Teste** = scientifique de terrain / résidente hub. **Pas** entraîneuse de danse, **pas** barmaid. |
| **V22** | Formation **danse / musique / scène** = triplon entertainer (**Bige Coto**, **Lyra Velo**, **Talen Ress**). Ancre LH active : **Talen Ress** (auberge). Performer cantina : **Artiste de scène** (spectacle, pas trainer skills). |
| **V23** | Les races LBG (Fel'Rani, Tinkling, …) ont une planète d’origine (couche B). Être présent à Lost Heaven ≠ être natif de Scrapaltai. |
| **V24** | Afficher une race sur un PNJ (ex. Fel'Rani) sans l’ancrer dans le registry = **dérive** ; corriger portrait / `race_id` / prompt. |

### Gameplay talents

| ID | Vérité |
|----|--------|
| **V30** | Structure talents = **équivalent Pre-CU** : novice → 4 branches × 4 boxes → master (noms LBG). Détail : [`ARBRES_TALENTS_PRECU.md`](ARBRES_TALENTS_PRECU.md). |
| **V31** | Un schematic a un **skill / box requis** et une **catégorie** ; pas de craft magique hors arbre. |
| **V32** | Les 6 starters Pre-CU mappent : Artisan, Prospecteur (Scout), Médecine, Scène (Entertainer), Poing, Visée — + Citoyen (Politician) et Pilotage shuttle. Trainers : voir inventaire. |
| **V33** | Progression joueur ≠ lifecycle bots IA Core3 (learning/decay). Ne pas confondre les deux dans le lore joueur. |
| **V34** | Panneau M10 court = vitrine des novices P0/P1 ; combat (Poing/Visée) peut rester hors UI tant que craft B2B n’est pas vert. |
| **V35** | Miroir technique `precu_skill_id` (ex. `crafting_artisan_novice`) autorisé côté serveur ; **jamais** exposé tel quel au joueur. |

### Chœur du monde (garant)

| ID | Vérité |
|----|--------|
| **V50** | **Chœur du monde** (`player_ia`, agent `studio_player_ia_choeur`) = garant **runtime** des Vérités + arbres talents. Persona Team sur 246 (IDLE/probe aujourd’hui). |
| **V51** | Aujourd’hui : sonde sidecar joueurs IA (Lia, Nix, …) et validation monde. **Cible** : détecter écarts Bible / inventaire PNJ / catalogue M10 et les remonter (Team / Pilot). |
| **V52** | Un tick Chœur qui *joue* (danse, craft, survey) doit respecter le rôle des bots et les boxes Pre-CU-LBG — pas inventer de métier hors catalogue. |
| **V53** | Owner P3 persona (dialogue PNJ stables) = Chœur côté *vérif terrain* ; implémentation pont = Iris / dialogue_llm. |
| **V54** | Scribe (N6) = mémoire civile *in-world* ; Chœur = conscience *ops* du monde. Les deux anti-dérivent, à des couches différentes. |

### Dialogue & IA

| ID | Vérité |
|----|--------|
| **V40** | `world_hint` client + entrée registry (`summary`, `goals`, `constraints`) = source prompt. Pas d’invention de villes / planètes. |
| **V41** | Interdit en dialogue : Willowdale, Brindlemark, Mos Eisley, Tatooine, noms fantasy génériques non listés ici. |
| **V42** | Si le registre est muet sur un fait → le PNJ dit qu’il ne sait pas / renvoie vers guide, scribe ou rumeuriste — **il n’invente pas**. |

### Maturité contenu (protéger ≠ restreindre le monde)

Principe : le **canon monde est large (palier C)**. Les paliers **B** puis **A** sont des **filtres de présentation** liés au profil maturité du joueur — ils n’effacent pas le lore, les factions ni les quêtes du serveur. On **adoucit / omet / détourne** côté client + prompts ; on ne réécrit pas Scrapaltai pour tout le monde.

| ID | Vérité |
|----|--------|
| **V60** | **Canon = C** (« fictionnel sauf illégal »). Violence, crime, horreur narrative, insultes in-world, thèmes adultes **peuvent** exister dans le lore et les données taguées. Interdit absolu (tous paliers) : exploitation sexuelle de mineurs, CSAM, doxxing / harm IRL, contents illégaux hors fiction. |
| **V61** | Trois **paliers joueur** (du plus large au plus protégé) : **C** mature / défaut compte adulte déclaré · **B** teen / maturité moyenne · **A** soft / bienveillance max. Un compte peut **monter** (C) avec preuve d’âge / déclaration + confirmation ; **descendre** (B/A) librement (parental, confort). |
| **V62** | Filtre **B** (si actif) : pas de nudité / sexe explicite en surface ; violence non clinique (pas de gore détaillé) ; sexualité → ellipse / sous-entendu ; insultes soft. Le sombre (corruption, mort, trafic *évoqué*) reste OK. |
| **V63** | Filtre **A** (si actif, empile B) : ton hub plutôt bienveillant ; violence minimalisée (conséquence, pas spectacle) ; pas d’horreur sadique ; flirt très léger max ; pas d’insulte lourde PNJ→joueur. Les quêtes « sombres » restent jouables via **variantes soft** (même objectif, formulation adoucie), pas via suppression sèche de la quête. |
| **V64** | Contenu tagué `maturity: C|B|A` (dialogue lines, quêtes, assets, prompts). Runtime : `player.maturity_cap` = max autorisé. Le LLM / client ne reçoit que le matériel `≤ cap` + consigne de palier. **Pas** de dépendance au refus du modèle Ollama comme policy. |
| **V65** | « Protéger sans restreindre » = **même monde**, **vues différentes**. Interdit de retirer un lieu / PNJ / arc canon uniquement parce qu’un joueur est en A ; obligatoire de fournir une **surface A-compatible** (texte alternatif, fade-to-black, rumeur atténuée). |

---

## Points narratifs importants (ancres)

À développer plus tard ; **ne pas contredire** en attendant.

| Ancre | Lieu / sujet | Note |
|-------|----------------|------|
| **N1** | Arrivée shuttleport Lost Heaven | Premier contact ; guide de quartier |
| **N2** | **La Perle de Scrapaltai** (cantina hub) | Social, rumeurs, scène ; formation danse via Talen (auberge) / show = Artiste de scène |
| **N3** | Hall d’entraînement + atelier artisan | Porte d’entrée talents / craft |
| **N4** | Clinique | Médecine de camp ↔ medic trainers |
| **N5** | Bureau des missions (Daan Oth) | Quêtes LBG (remplacer stubs fantasy) |
| **N6** | Archives / scribe | Mémoire civile, anti-dérive lore *in-world* |
| **N7** | Kisreudi — science de terrain | Échantillons Scrapaltai, pas divertissement |
| **N8** | Réseau stellaire | Voyageurs d’Arvandor / Mecha_Prime / etc. passent par LH |
| **N9** | Chœur du monde | Garant runtime (bots Lia/Nix + écart Bible/M10) — pas un PNJ de cantina |
| **N10** | Tone Scrapaltai | « Patchwork · Récup’ · Élégante désolation » — métal oxydé, cuir usé, accents bleu pâle / orange cuivré (extrait Boîte à idées) |
| **N11** | Faune désert | Bestiaire P0 autour LH — `packages/cortex/content/world/bestiaire_scrapaltai.json` |
| **N12** | MJ IA / monde vivant | Fonction plan `MJ IA` = Chœur + events (pas PNJ cantina) — voir `BOITE_IDEES_GAMEPLAY.md` §7 |

---

## À trancher (plus tard — hors V1–V42)

Points ouverts ; **ne pas inventer** en attendant une décision datée ici.

| ID | Sujet | Options / note | Bloque ? |
|----|-------|----------------|----------|
| **T1** | Race Kisreudi | **Tranché 2026-08-03** — `race:fel_rani` (Arvandor), présente à Lost Heaven (V23/V24) | — |
| **T2** | *La Perle de Scrapaltai* | **Tranché 2026-08-03** — label POI + V13 canon | — |
| **T3** | Factions pilotes | Labels « imperial / alliance » → noms LBG | Non (debt wording) |
| **T4** | Zones registry « Mos Eisley » | **Tranché 2026-08-03** — roster hub + factions → Lost Heaven | — |
| **T5** | Stubs fantasy (alchimiste, Pomme Rouge…) | Garder tests Studio vs purge | Non (couche D gelée) |
| **T6** | Combat Poing/Visée dans UI M10 | Garder hors vitrine (V34) vs exposer | Non (P2 craft d’abord) |
| **T7** | Caps Chœur `world_truth_guard` | Implémenter smoke écart Bible/M10 | Non (cible V51) |
| **T8** | Maturité contenu A/B/C | **Tranché 2026-08-27** — canon C + filtres B puis A (V60–V65) | Impl runtime (compte + tags + prompt) |

---

## Règles d’édition

1. Ajouter une vérité = nouvelle ligne `Vxx` + date dans l’historique ci-dessous.
2. Renommer un lieu / PNJ = maj inventaire + registry + ancres + `world_hint` le même jour.
3. Contenu legacy (`LBG_IA_MMORPG`) = lecture ; **canon narratif** = ce dossier `docs/world/`.
4. Trancher un **T*** = décision datée dans ce tableau + maj data le même jour.

### Historique

| Date | Changement |
|------|------------|
| 2026-08-03 | Création V1 : couches A–D, V1–V42, ancres N1–N8, inventaire PNJ séparé, catalogue M10 enrichi |
| 2026-08-03 | Chœur garant (V50–V54, N9) ; V30–V35 Pre-CU ; doc ARBRES_TALENTS_PRECU ; catalogue schema 3 |
| 2026-08-03 | **Validation pilote V1–V42** ; backlog T1–T7 (doutes reportés) |
| 2026-08-03 | M10 craft stub + smoke combine ; **T2/V13** La Perle canon ; piste 1 (label POI + prompts) |
| 2026-08-03 | **T1** Kisreudi = Fel'Rani ; **T4** zones/factions hub Lost Heaven ; catalog schema 3 poussé sur 246 |
| 2026-08-04 | **V4** — PreCU 245 = référence SWG Pre-CU lecture seule (ne pas modifier) |
| 2026-08-04 | Garr Vek → `pilot_trainer` ancré starport LH ; P2 craft HTTP sidecar ; Rang2 §5 quest enrich MVP |
| 2026-08-04 | Extrait Boîte à idées → `BOITE_IDEES_GAMEPLAY.md` ; ancres N10–N11 ; bestiaire P0 |
| 2026-08-04 | Loots→schematics M10 + templates quêtes LBG (anti-fantasy) |
| 2026-08-04 | Relecture `plan MMMORPG.md` ; N12 MJ IA ; escort/enquête |
| 2026-08-27 | **T8 / V60–V65** — maturité contenu : canon C, filtres B→A selon joueur (protéger ≠ amputer le monde) |
