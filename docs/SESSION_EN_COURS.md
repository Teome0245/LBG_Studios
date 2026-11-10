# Session en cours — LBG Studios

**Mis à jour** : 2026-11-09  
**Branche** : `main`  
**Outil** : partagé Cursor ↔ Antigravity — **lire au démarrage, mettre à jour avant de partir**.  
**Backlog non traité** : [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md)  
**Fil** : canon O1/O2/O3 + SWG Pre-CU Copie Quasi-Complète 100% — **Résolution conflits touches + Publication Patch Launchpad v2.1.5 (246:8080) OK**.

---

## Dernières actions réalisées (2026-11-09)
1. **Refonte & Dépoussiérage des contrôles clavier (`client_ui_dialogue.gd` & `swg_space_flight_3d.gd`)** :
   - Élimination du conflit majeur `KEY_D` (aller à droite ZQSD qui déclenchait le Datapad) ➔ Datapad déplacé sur `V` ou `Ctrl+D`.
   - Élimination des collisions de touches de fonctions `F9` (Debug HUD vs Espace 3D) et `F10` (Heal vs Login Panel).
   - Nouvelle cartographie ergonomique F-Keys :
     - `F4` : Sabre laser (dégainer / rengainer)
     - `F5` : Sonde de traque Arakyd
     - `F6` : Force Heal
     - `F8` : Vol Spatial JTL 3D
     - `F9` : Debug HUD
     - `F10` : Panneau de connexion / compte
     - `F11` : Bascule Plein écran
2. **Correction Focus Espace & Pilotage Souris Sol + Espace (`swg_space_flight_3d.gd` & `player_controller.gd`)** :
   - Désactivation du vol de focus sur les boutons HUD (`focus_mode = FOCUS_NONE`) : appuyer sur ESPACE au sol ne déclenche plus jamais l'entrée dans l'espace.
   - **Déplacement à la souris au sol** : support du simple clic au sol et du maintien continu du clic gauche (le personnage suit le curseur en temps réel). Suppression du clamp prématuré qui bloquait les clics lointains.
   - **Pilotage à la souris dans l'espace (JTL 3D)** : orientation fluide du X-Wing par déplacement de la souris (tangage/lacet/roulis auto), tir laser au clic gauche, et accélération/décélération à la molette.
3. **Synchronisation & Publication du Patch Client Launchpad** :
   - Synchronisé via `sync_prime_client_to_win.py` vers Windows SDS `J:/swgemu/clients/prime-client` (19 fichiers).
   - Déployé sur le serveur de patches `192.168.0.246:8080` via `deploy_prime_client_patch_246.sh` (version `2026-11-09T17:19:24Z`, 287 fichiers).
4. **Intégration des Nouveaux Modèles VRM (`O:\OneDrive\Pictures\IA\Models`)** :
   - Déploiement et cartographie des 8 nouveaux modèles VRM importés dans le jeu :
     - **`NeonNeko.vrm`** : Avatar félin avec oreilles et queue de chat intégrées ➔ Affecté à **Fel'Rani** (`twilek` / Arvandor).
     - **`Saiyan4.vrm`** : Avatar sauvage à fourrure et carrure de combat ➔ Affecté à **Varkoon** (`wookiee` / Arvandor).
     - **`Greeny.vrm`** : Avatar reptilien vert ➔ Affecté à **Pykrel** (`rodian` / Arvandor).
     - **`DemonHorn.vrm`** : Avatar à cornes crâniennes pointues ➔ Affecté à **K'Miri** (`zabrak` / Khar'Zuun).
     - **`Rebecca.vrm`** : Avatar d'ingénieure cyber ➔ Affecté à **Tinkling** (échelle $\times 0.50$, taille ~45 cm).
     - **`Mia.vrm`** : Avatar citoyenne de Lost Heaven ➔ Affecté à **Humain** (Terre1 / Corellien).
     - **`Marie.vrm`** : Nouvel avatar exploratrice de terrain d'Arvandor.
     - **`Espeon.vrm`** : Nouvel avatar familier quadrupède psionique des dunes.
   - Synchronisation complète des assets VRM sur les 5 dossiers cibles Windows SDS `.10` (`J:/swgemu/clients/swg-client`, `J:/swgemu/clients/prime-client`, `A:/LBG_Studios/...`, `C:/Agent_IA/...`).
   - Selftests 100% verts (`swg_client_3d_selftest.gd`, `client_modular_selftest.gd`).

---

## Objectif actuel

Continuité multi-outils : même canon **O1 Compagnon / O2 MMO banc / O3 Joueurs IA** ([`OBJECTIVES.md`](../OBJECTIVES.md)).  
Réplique exhaustive 100% Star Wars Galaxies Pre-CU : achèvement des **5 Piliers d'Élite dans l'ordre** :

- [x] **Point 1 : Villes de Joueurs & Politique (*Player Cities & Elections*) (`hub_player_cities.gd`)** :
  - Fondation de cités par les joueurs, 5 échelons d'expansion (Outpost ➔ Village ➔ Township ➔ City ➔ Metropolis).
  - Élections démocratiques régulières de Maires au suffrage universel par les citoyens résidents (`start_election`, `cast_vote`, `conclude_election`).
  - Décrets municipaux & spécialisations civiques : Centre Industriel (-10% temps craft), Sanctuaire Médical, Avant-poste Scientifique, District des Plaisirs, Refuge de Clonage.
  - Fiscalité locale paramétrable (taxes foncières, taxes sur les ventes des marchands, taxes de spatioport).
  - Rendu 3D : Modélisation générative de l'Hôtel de Ville (`build_city_hall`) avec colonnade en marbre, dôme doré et terminal politique interactif (`terminal_cityhall`).

- [x] **Point 2 : Bio-Ingénierie & Échantillonnage d'ADN (*Bio-Engineer*) (`hub_bio_engineer.gd`)** :
  - Sonde d'échantillonnage génétique sur la faune sauvage (Chacals, Banthas, Dewbacks, Dragons Krayt) avec extraction de profils de robustesse, prouesse et férocité.
  - Cuve d'incubation génétique en laboratoire (`incubate_creature`) : fusion de deux matrices d'ADN pour forger des chimères mutantes uniques destinées aux *Creature Handlers*.
  - Synthèse d'enzymes biomédicales mutagènes pour Médecins et Chefs cuisiniers.
  - Rendu 3D : Modèle procédural de l'Incubateur Génétique (`build_bio_incubator`) avec cuve de fluide bioluminescent vert émissif (`OmniLight3D`).

- [x] **Point 3 : Ingénierie Droïde Avancée (*Droid Engineer*) (`hub_droid_engineer.gd`)** :
  - Confection de châssis modulaires : Droïde Astromécano Série R2, Droïde de Protocole Série 3PO, Droïde Sonde Probot, Droïde Souris MSE-6, Droïde de Combat Série IG.
  - Montage de modules spécialisés : extension de soute (+25 slots ambulants), atelier mobile de craft nomade, dispensaire médical automatique, radar de scan sonar, tourelle blaster E-Web.
  - Commandes tactiques en jeu (`/follow`, `/stay`, `/patrol`, `/store_item`, `/dispense_meds`, `/play_music`).
  - Rendu 3D : Modélisation procédurale du droïde R2-D2 (`build_r2_astromech`) avec dôme bleu pivotant, œil holographique et roulettes de déplacement.

- [x] **Point 4 : Parcs à Thèmes Galactiques & Donjons Classiques (`hub_theme_parks.gd`)** :
  - **Palais de Jabba le Hutt (Tatooine)** : Suite de quêtes d'allégeance de la pègre auprès de Bib Fortuna, Reelo Baruk et Jabba (obtention de la Hache Vibro et de l'insigne d'Exécuteur).
  - **Retraite de l'Empereur (Naboo)** : Missions d'espionnage impérial d'élite avec Dark Vador et l'Empereur Palpatine (badge d'Inquisiteur et cape de Maître Impérial).
  - **Donjon de la Corvette Corellienne** : Instance raid chronométrée sous compte à rebours 3600s (60 min) avec progression de ponts (Sas ➔ Machines ➔ Pont de Commandement), sauvetage d'otages et sabotage de l'hyperdrive.
  - **Raid Boss Dragon Krayt** : Antre du dragon millénaire (95 000 HP) avec drop garanti de Perles de Krayt légendaires et d'écailles composites.
  - Rendu 3D : Sas pressurisé blindé de la Corvette Corellienne (`build_corvette_airlock`) avec gyrophares d'alarme rouge et voyants d'urgence.

- [x] **Point 5 : Multi-Planètes & Biomes Stellaires (`hub_galaxy_planets.gd`)** :
  - Catalogue des 5 mondes majeurs de SWG :
    - **Tatooine** : Désert aride, dunes, soleil binaire, canyons et camps Tuskens.
    - **Naboo** : Plaines luxuriantes verdoyantes, cascades, marécages et dômes en marbre de Theed.
    - **Endor** : Lune forestière dense, séquoias géants, canopée humide et villages arboricoles Ewoks.
    - **Dathomir** : Ciel carmin brumeux, badlands toxiques, Rancors sauvages et temples des Sœurs de la Nuit.
    - **Corellia** : Plaines tempérées maritimes, berceau naval et chantiers de Coronet City.
  - Transition atmosphérique, météo dynamique et billetterie de transit inter-mondes.
  - Rendu 3D : Console de navigation galactique (`terminal_planets`) pour voyager entre les 5 planètes.

- [x] **Portage Intégral sur Prime Client (`packages/prime-client`) (2D au sol + Extension Spatiale JTL 3D)** :
  - **Gameplay Planétaire 2D au sol (100% fidèle SWG sans 3D)** :
    - *Boîte de Dialogue Universelle SWG 2D* (`scripts/swg_dialog_box.gd`) : Menus narratifs interactifs pour les 5 nouveaux systèmes (Hôtel de Ville & Élections de Maire, Incubateur Bio & Synthèse ADN, Commandes Droïdes R2/MSE, Donjon Raid Corvette Corellienne, Cartographie & Transit vers les 5 planètes).
    - *Rendu 2D des Entités* (`scripts/entity.gd`) : Sabre laser Jedi avec lame de plasma émissive orientée selon `facing_angle` (dégainable avec `[F7]`), droïdes astromécanos R2 (corps blanc, dôme bleu, œil rouge), sondes Arakyd de traque avec anneau radar pulsant (`[F8]`), insignes de factions GCW et lairs de créatures.
    - *Raccourcis & Commandes Chat* (`client_ui_dialogue.gd` & `main.gd`) : Raccourcis `[F7]` (sabre laser), `[F8]` (sonde Arakyd), `[F10]` (soin Force Heal), `[F9]` (vol spatial), commandes `/saber`, `/probe`, `/space`, `/forceheal`.
  - **Extension Spatiale Jump to Lightspeed (JTL) 3D Incrustée (`scripts/swg_space_flight_3d.gd`)** :
    - Bascule instantanée sol 2D ➔ orbite spatiale 3D via `[F9]` ou dialogue de Spatioport/X-Wing.
    - *SubViewport 3D* plein écran avec champ d'étoiles procédural, modélisation 3D du chasseur Incom T-65B X-Wing, chasseurs TIE ennemis en dogfight, canons lasers rouges 3D animés.
    - *HUD Spatial 2D Overlay* : Répartiteur d'énergie Tri-Voie dynamique (Armes `[F5]`, Boucliers `[F6]`, Moteurs `[F7]`), télémétrie de vitesse (MGLT), jauges de boucliers avant/arrière et saut hyperspatial (`[H]`).
  - **Validation & Synchronisation** :
    - `client_modular_selftest.gd` : 22 composants SWG 2D + Extension Spatiale JTL 3D validés à 100% (code 0).
    - Synchronisation Windows SDS `.10` (`J:/swgemu/clients/prime-client`) : 16 fichiers synchronisés avec succès via `tools/sync_client_to_win.py --client prime`.
    - CI globale headless Godot (`tools/ci_godot_headless.sh`) : 19 suites de tests validées (code 0).


--- 

## Historique archivé

- Les sessions et jalons détaillés antérieurs au 2026-11-09 ont été archivés dans [`docs/_archive/SESSION_HISTORY_2026_OCT_NOV.md`](_archive/SESSION_HISTORY_2026_OCT_NOV.md).
- Voir également [`docs/PRIORITES_ACTUELLES.md`](PRIORITES_ACTUELLES.md) et [`docs/SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md).

---

## Prompt de démarrage (coller dans Antigravity)

```
Repo : LBG_Studios. Réponses en français.
Lis dans l’ordre : AGENTS.md → docs/SESSION_EN_COURS.md → docs/PRIORITES_ACTUELLES.md
→ le handoff @docs/handoff_…md si cité.
Confirme en ≤10 lignes : objectif, contraintes, prochain pas — avant toute édition.
En fin de session : mets à jour docs/SESSION_EN_COURS.md.
```
