# Session en cours — LBG Studios

**Mis à jour** : 2026-11-07  
**Branche** : `main`  
**Outil** : partagé Cursor ↔ Antigravity — **lire au démarrage, mettre à jour avant de partir**.  
**Backlog non traité** : [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md)  
**Fil** : canon O1/O2/O3 + SWG Pre-CU Raccordement Prime 2D & Hub + O3 Autonomie Bots IA + 3D Formateurs 4x4 & Survey Tool Holographique — **100 % Livré, Validé CI & Déployé**.

---

## Objectif actuel

Continuité multi-outils : même canon **O1 Compagnon / O2 MMO banc / O3 Joueurs IA** ([`OBJECTIVES.md`](../OBJECTIVES.md)).  
Séquence stratégique validée : **1 (Prime 2D/Hub) ➔ 3 (Autonomie Flotte O3) ➔ 2 (Approfondissement 3D Formateurs & Survey)**.

- [x] **Étape 1 : Raccordement Systèmes SWG Pre-CU à Prime 2D & Prime-Hub (`.246:8787`)** :
  - *Factions GCW* : `HubFaction` (`scripts/hub_faction.gd`), recruteurs PNJ (Lt Kren, Cap Vao), Civilian / On-Leave / Special Forces (PvP ouvert), hostilité et routes HTTP `/v1/factions/*`.
  - *Nids de Créatures (Lairs)* : `HubCreatures` (`scripts/hub_creatures.gd`), seuils de vagues de défenseurs (75%, 50%, 25%), transformation en décombres à 0 PV et pillage de butin rare (œufs fossilisés, crédits). Représentation visuelle 2D dans `entity.gd`.
  - *Espèces SWG & Image Designer* : Catalogue de 6 espèces avec bonus HAM, fenêtres de sélection et retouche visuelle (`swg_species_system.gd`, `swg_species_dialog.gd`).
  - *PCD Datapad* : Intégration de 4 PCD (Landspeeder X-34, Swoop Bike, Dewback, Chiot).
  - *Selftest & Déploiement* : `swg_factions_lairs_selftest.gd` 100% PASS, déployé sur `.246:8787` et synchronisé vers Windows SDS `.10` (`J:/swgemu/clients/prime-client`).

- [x] **Étape 3 : Autonomie O3 des Joueurs IA sur les Systèmes SWG** :
  - *Arbitrage autonome Pre-CU (`hub_bot_autonomy.gd`)* :
    - Détection et assaut autonome des nids de créatures (`attack_creature_lair`) quand la santé est $\ge 70\%$.
    - Pillage autonome des décombres de nids détruits (`harvest_lair_debris`).
    - Enrôlement autonome dans la Guerre Civile Galactique GCW (`enlist_gcw_faction`).
    - Érection autonome d'habitations et tentes personnelles (`build_player_house`).
  - *Validation CI* : `bot_autonomy_swg_selftest.gd` 100% PASS (10 tests unitaires et intégrés).
  - *CI Headless Godot globale (`tools/ci_godot_headless.sh`)* : 18 suites validées à 100% sans régression. Redéployé en live sur `.246:8787`.

- [x] **Étape 2 : Approfondissement SWG Pre-CU 3D (Formateurs PNJ 4x4 & Survey Tool 3D)** :
  - *Formateurs PNJ de Professions (Skill Trainers 3D)* :
    - 5 Formateurs spécialisés déployés dans Lost Heaven : Vorn (Bagarreur & Tireur), Dax (Artisanat), Ordo (Éclaireur/Survie), Elan (Médecine) et Selene (Artiste de scène).
    - Dialogue interactif dédié (`swg_dialog_box.gd`) avec explications immersives et options de formation.
    - Menus radiaux enrichis (`swg_radial_menu.gd`) avec option `🎓 Entraîner Compétences`.
    - Arbre 4x4 interactif (`swg_skills_panel.gd`) : ouverture ciblée sur la profession du formateur (`open_for_trainer`), apprentissage direct (`learn_box_direct`) et effet holographique festif 3D d'auréole dorée (`trigger_skill_up_effect`).
  - *Prospection Survey Tool 3D Holographique* :
    - Balise holographique 3D (`trigger_survey_beacon_3d`) : faisceau vertical cyan, étincelles d'impulsion sonar et panneau d'affichage 3D billboard (concentration %, stats OQ/CD/PE).
    - Synchronisation dynamique avec le panneau Survey (`update_survey_from_world`).
    - Extraction géologique de terrain (`_execute_sample_resource`) : posture agenouillée, échantillonnage de minerais réels avec stats 1..1000 injectés dans l'inventaire.
  - *Validation & Sync* : `swg_client_3d_selftest.gd` 100% PASS (12 piliers testés), synchronisation des 21 fichiers vers Windows SDS .10 (`J:/swgemu/clients/swg-client`).

**Boucle d'Évolution Réalisée & Déployée (Séquence 4 ➔ 1 ➔ 2 ➔ 3)** :
- [x] **Point 4 : La Boucle d'Arbitrage & Moissonnage Automatique** :
  - *SuperAgent Router déployé sur Cortex .140* : Activation des routes `/v1/pilot/team/super-agent/*` pour la gestion des événements critiques et demandes d'arbitrage.
  - *Outil d'analyse `tools/mmo_evolution_analyst.py`* : Moissonnage en direct des suggestions des bots (`/v1/dev/world_suggestions`) et télémétrie du hub .246, classification par volets, génération de RFC et émission d'alertes `session.approval_needed` vers l'Overlay Bureau (Lyra) et Pilot.
  - *Gatekeeper CI & Déploiement* : Automatisation du passage de `tools/ci_godot_headless.sh` (18 suites Godot) et du déploiement via `deploy_prime_hub_246.sh`.
- [x] **Point 1 : Économie, Artisanat & Ressources (`EVO-ECO-20261103-01`)** :
  - *Composants d'Atelier* : Ajout de la recette de recyclage `used_capacitor` (Condensateur recyclé à partir de Ferraille) dans `catalog_recipes.json` pour débloquer le craft des kits de réparation par Sola, Lia et Mira.
  - *Troc Cantina La Perle* : Intégration de condensateurs au catalogue de Jax Moro et bonification de la marge de négociation de troc à 20% dans `vendor_negotiation_jax.json`.
- [x] **Point 2 : Quêtes, Expérience & Compétences (`EVO-QST-20261103-02`)** :
  - *Piste Ouest vers le Ksar Nomade* : Template de quête `lh_recon_ksar_ouest` ajouté dans `quests_lbg_templates.json` pour diversifier les flux de bots et de joueurs vers la Porte Ouest (`poi:lost_heaven_gate_west`) et le Ksar (`poi:ksar_nomade`) avec récompenses équilibrées (35 cr, 50 XP prospection, 25 XP quartier, rations, eau).
- [x] **Point 3 : Combat, HAM & Survie Médicale (`EVO-CBT-20261103-03`)** :
  - *Stabilisation HAM Hors les Murs* : Déverrouillage dans `hub_ham_medical.gd` des soins d'urgence en milieu hostile si le soignant utilise un baume de terrain ou un bandage antivenin. Dissipation immédiate de 25 points de Battle Fatigue en expédition.
  - *Recette artisanale* : Création de la recette `baume_urgence_terrain` (eau + ruban de liaison sous `medecin_novice`) dans `catalog_recipes.json`.
  - *Fiabilisation CI* : Résolution de la collision de seed d'ID joueur dans `ham_cantina_medcenter_selftest.gd`. 18/18 suites de tests headless Godot PASS en 136s. Déploiement validé sur `.246:8787`.

**Chantiers « Âme de SWG Pre-CU »** :
- [x] **Instance Parallèle SWG Pre-CU 3D & Déploiement Launchpad Windows .10** :
  - *Instance Dédiée Complète (`packages/swg-client` & `packages/swg-hub`)* :
    - Étape 1 : Contrôleur TPS `CharacterBody3D`, `SpringArm3D`, postures physiques (standing $1.8\text{m}$, kneeling $1.15\text{m}$, prone $0.55\text{m}$), combo fatal *Dizzy Fall*.
    - Étape 2 : Terrain 3D grande échelle ($16\times 16\text{ km}$, 64m chunks, FastNoiseLite dunes, City Flat Affector pour Lost Heaven) et pipeline d'assets POB intérieur multi-cellules (Cantina La Perle, comptoir en U, stage musiciens, néons).
    - Étape 3 : 33 professions Pre-CU (6 de base, 26 élites, Politician), 594 boîtes de compétences 4x4, plafond 250 Skill Points et surrender sécurisé.
    - Selftests 100% verts : `swg_client_3d_selftest.gd`, `swg_hub_selftest.gd`, `swg_professions_selftest.gd`.
  - *Enrichissement du Monde 3D & Atmosphère SWG Pre-CU* :
    - *Hub Urbain Complet* : Spatioport de Lost Heaven avec piste d'atterrissage surélevée, balises lumineuses et navette spatiale posée (Shuttle Lambda-style), Centre Médical avec cuves de bacta luisantes, Grand Hôtel de Ville à colonnades et bannières pourpres, quartier résidentiel en pisé avec escaliers extérieurs et auvents, portes fortifiées Ouest et Est avec bastions de garde.
    - *Mobilier Urbain & Terminaux Authentiques* : Esplanade centrale avec Terminaux de Missions, Bazar, Banque galactique, Clonage, véhicule Landspeeder X-34 stationné, Vaporisateurs d'humidité (Moisture Vaporators GX-8), lampadaires de rue et amas de fret cargo.
    - *Wilderness & Faune Vivante* : Campement nomade de Scout avec feu de camp crépitant dans les dunes, extracteur minier lourd (Mining Harvester), éperons rocheux/mesas de grès rouge, cactus du désert, grand Marcheur des Dunes herbivore (Dewback), meute de chacals dorés, scarabée obsidien géant et droïde astromécano R2-T8.
    - *Système d'Interactions & Menus Radiaux Complets* :
    - *Détection de proximité & Prompt flottant* : Affichage dynamique de `◈ [E] ou [Clic-Droit] : <Nom Entité> ◈` au bas de l'écran dès qu'une entité se trouve à portée ($\le 6\text{m}$).
    - *Boîte de dialogue interactive SWG (`swg_dialog_box.gd`)* : Dialogues complets avec répliques et lore avec Lia (danse & musique cantina, dissipation de 50 Fatigue, buff mental), Jax Moro (achat de lait bleu et rations), Maire Odo Merr (statut cité de rang 3, housing, compétences), Docteur Vane (soins HAM complets, cuve de bacta), Gardes de la Milice (primes) et Droïde R2-T8 (scan géologique).
    - *Terminaux interactifs* : Terminal de missions (`swg_missions_terminal_dialog.gd`) avec contrats de primes et transport, Borne bancaire (`swg_bank_terminal_dialog.gd`) avec dépôts/retraits de crédits, Terminal de Bazar (`swg_bazaar_panel.gd`), Borne de clonage (assurance active).
    - *Interactions Véhicule, Faune & Bivouac* : Pilotage direct du Landspeeder X-34 (vitesse propulsée $\times 2.5$), repos au feu de camp nomade (fatigue dissipée), apprivoisement de créatures (Creature Handler Tame) et dépeçage Scout.
  - *Combat 3D, Hotbar d'Action, Radar & Cycle Temporel* :
    - *Hotbar SWG 8 slots (`swg_action_hotbar.gd`)* : Raccourcis `[1..8]` pour Tir Blaster, Tir Visé, Étourdissement Dizzy, Stimpack Bacta, Sonde géologique, Camouflage Scout, Familier et Speeder.
    - *Système de Combat 3D (`swg_combat_system_3d.gd`)* : Projectiles blaster lasers rouge/cyan avec traînée et étincelles d'impact, chiffres de dégâts flottants 3D (Floating Combat Text), mort des bêtes avec transformation en cadavres dépeçables au sol.
    - *Radar Mini-Carte Circulaire SWG* : Boussole avec point cardinal Nord, suivi du joueur et points de couleur (jaune PNJ, rouge bêtes hostiles, cyan terminaux/POB).
    - *Cycle Jour/Nuit Dynamique* : Rotation continue du double soleil binaire avec transition crépuscule et nuit illuminant les néons et feux de camp de Lost Heaven.
    - *Respawn Automatique & Clonage d'Urgence [F5]* : Timer de résurrection automatique (8s pour les PNJ citoyens, 18s pour la faune laissant le temps au dépeçage Scout), et touche `F5` pour réanimer instantanément 100% de la population et de la faune.
    - *Modèle 3D Compagnon & Améliorations Graphiques PBR* :
      - Remplacement de la capsule joueur par le modèle humanoïde complet du Compagnon (`Compagnon.vrm` / `LadyKoi.vrm`) avec orientation naturelle vers l'avant (-Z) et caméra orbitale TPS.
      - **Suppression Définitive de la T-Pose & Rig Mirroring (`swg_vrm_animator.gd`)** : Détection automatique `is_arm_mirrored = rest_l.origin.x < 0.0`. Inversion adaptative du signe Z (`z_sign = 1.0 if is_arm_mirrored else -1.0`). Les bras de tous les VRM (Compagnon, LadyKoi, Anna, Aurora) sont désormais abaissés naturellement le long du corps au repos (plus de bras horizontaux, plus de bras en l'air).
      - **Restauration Intégrale du Skin Natif de Lia** : Exclusion explicite de Lia de tout aplat ou filtre monochrome dans `swg_world_3d.gd`. Lia conserve 100% de ses textures faciales, chevelure, shaders et tenue d'origine. Danse de Cantina gracieuse avec déhanchement en 8 et légères ondulations de bras sans lever les bras.
      - **Entrée Libre dans les Bâtiments (Système POB Ouvert)** : Découpage de larges passages franchissables (au lieu de boîtes de collision pleines) pour l'Hôtel de Ville (grand hall avec estrade du Maire Odo Merr et tapis pourpre), le Centre Médical (porte clinique avec bureau du Docteur Vane et cuves de Bacta intérieures) et la Cantina.
      - **Système de Diversification des Skins (`swg_skin_system.gd`)** : 9 palettes de tenues distinctives par rôle PNJ (blouse médicale pour Vane, toge pourpre et or pour le Maire, armures composite rouge bordeaux pour la milice, tablier pour Jax, treillis pour Nix). Sélecteur de 5 skins pour le joueur en temps réel via la touche `[F6]`.
      - **Comptoir de Cantina en U & Jax Moro Débloqué** : Vrai comptoir en fer à cheval (U-shape) avec intérieur dégagé, étagères arrière-bar avec carafes de lait bleu luminescentes, et Jax positionné au centre tourné vers les clients. Lia positionnée sur la scène de spectacle surélevée sous les projecteurs ambrés.
      - **Système de Missions avec Balises Waypoints GPS 3D** : Connexion de l'acceptation de mission (`_on_mission_accepted`) avec balise holographique 3D verticale de 28m, enregistrement sur la Carte Planétaire `[M]` et le Radar boussole, suivi des cibles, accomplissement automatique et versement de crédits.
      - **Buffs Cantina & Dissipation de Battle Fatigue** : Proximité avec Lia (<14m) dissipant la fatigue de combat (-8 pts/s) avec actualisation du HUD HAM et notification immersive de bien-être.
      - **Locomotion Véhicule Landspeeder X-34** : Activation via hotbar `[8]` ou Datapad avec accroche du modèle sous les pieds du joueur, accélération $\times 2.8$ ($18\,\text{m/s}$), son de moteur ionique en continu et rangement instantané.
      - **Monture Vivante Dewback des Sables** : Possibilité d'enfourcher le grand Dewback quadrupède avec selle en cuir (`build_dewback_mount_visual`), vitesse tout-terrain boostée ($10.5\,\text{m/s}$) et vue surélevée.
      - **Spatioport & Transport Galactique par Navette Lambda (`swg_travel_dialog.gd`)** : Terminal de voyage avec 5 destinations (Mos Eisley, Anchorhead, Ksar Nomade, Theed Naboo, Plaines Minières), ascension animée de la navette dans le ciel, transition de saut hyperspatial et atterrissage à destination.
      - **Déploiement Physique de Structures (Campement Scout & Harvester Minier)** : Actions du Menu Radial posant concrètement sur le terrain un campement scout (feu crépitant, tente, zone de repos HAM) ou un extracteur personnel lourd (piston en forage continu, trémie de stockage récoltable via `[E]`).
      - **Synthétiseur Audio Galactique Procédural (`swg_audio_synthesizer.gd`)** : Moteur sonore sans fichier audio externe générant en pur GDScript les tirs blaster (glissando laser FM), vrombissement de speeder, jingle de victoire/mission accomplie, gazouillis du droïde R2 et rugissement de navette.
      - **Peuplement Cité Lost Heaven** : Nouveaux PNJ actifs (Pilote Corran au Spatioport, Kaelen marchand de droïdes, Torin mécanicien Landspeeder, habitué accoudé au bar, apothicaire, armurier).
      - Rehaussement graphique PBR : Tonemapping ACES cinématographique chaud, Glow/Bloom HDR sur les lasers et enseignes néon, SSAO (Screen Space Ambient Occlusion) pour des ombres de contact profondes sous les structures et les pieds, SSR et ombres douces.
      - Nouveaux panneaux SWG Pre-CU complets câblés au clavier et au Datapad latéral :
        - Touche `[I]` : Sac à dos 40 slots & Papier-Doll d'équipement (silhouette anatomique 6 slots).
        - Touche `[T]` : Artisanat avec expérimentation et estimation du risque d'échec critique.
        - Touche `[M]` : Carte planétaire tactique temps réel, radar POI et pose de Waypoints personnalisés au clic.
        - Touche `[F6]` : Changement de tenue / skin joueur en direct.
      - **Camp Hostile Tusken & IA d'Aggro Active** :
        - Campement nomade des Pillards des Sables (`build_tusken_camp`) implanté dans les dunes Ouest vers le canyon avec huttes en cuir, totems d'armes Gaffi et feu de camp.
        - Spawns de 3 Tuskens hostiles (`Pillard Tusken Chasseur`, `Guerrier Tusken d'Élite`, `Gaffi Master Tusken`) dotés d'un modèle 3D authentique (masque respirateur, yeux cylindriques, buse à air, cartouchière, robe du désert et bâton Gaffi).
        - IA d'agressivité continue (`_update_ai_and_aggro`) : détection à 18m (ou 3.5m si camouflage Scout `[6]` actif), hurlement Tusken ou rugissement prédateur (`play_tusken_roar`), charge vers le joueur et attaques au contact infligeant des dégâts HAM directs avec chiffres flottants rouges.
      - **Caravane Marchande Itinérante de Lost Heaven** :
        - Convoi marchand en marche continue (`_update_merchant_caravan`) reliant la Porte Ouest et la Porte Est le long de la grand-rue.
        - Composé d'un Bantha de bât massif à grandes cornes spiralées (`build_caravan_bantha`) chargé de malles d'épices, du marchand ambulant Doran Karr et d'un garde d'escorte armé.
      - **Loot Réel, Dépeçage Scout & Consommables dans l'Inventaire** :
        - Méthodes d'inventaire `add_item`, `has_item`, `remove_item` avec empilement automatique (Stacking SWG 40 slots).
        - Dépeçage Scout (`harvest_meat`, `harvest_hide`, `harvest_bone`) et fouille de corps (`loot_corpse`) transférant effectivement les ressources brutes, crédits et stimpacks dans le sac à dos `[I]` avec marquage anti-duplication et cadavre vidé.
        - Consommation d'objets câblée (`_on_inventory_item_used`) : Stimpacks Bacta A (+250 Santé/Action), Rations des Dunes (+150 Santé/+200 Mental) et Lait Bleu de Tatooine (+300 Action/+300 Mental).
        - Nouveaux effets sonores procéduraux intégrés dans `swg_audio_synthesizer.gd` (cri Tusken, bruit de dépeçage, son de gorgée/soin bacta).
      - **Les 6 Piliers SWG Pre-CU 3D Majeurs (Intégration & Déploiement Complets)** :
        - [x] **Volet 2 : Nids de Créatures (Lairs) & Vagues de Riposte** (`swg_creature_lair_3d.gd`) : Monticules rocheux destructibles (1400/1800 PV) avec seuils de riposte à 75%, 50% et 25%, alerte de meute coordonnée, effondrement en décombres pillables (`harvest_debris`) avec crédits et œufs fossilisés rares.
        - [x] **Volet 3 : GCW Factions & Guerre Civile Galactique** (`swg_faction_system.gd`, `swg_faction_dialog.gd`) : Alignement Impérial/Rebelle, statuts Civilian / On-Leave / Special Forces (PvP ouvert), recruteurs Lieutenant Kren et Capitaine Vao, patrouilles de Stormtroopers et Soldats Rebelles, tourelles défensives automatiques.
        - [x] **Volet 5 : Spectacle Cantina & Entertainer Flourishes** (`swg_world_3d.gd`) : Commandes `/flourish 1..8`, observation active `/watch` et `/listen`, gerbes d'étincelles disco et cônes de lumière dynamiques, jauge d'inspiration cantina conférant le buff d'Harmonie Mentale (+100 Mental Max, regen boostée).
        - [x] **Volet 4 : Datapad PCD Montures & Véhicules** (`swg_datapad_panel.gd`, `swg_world_3d.gd`) : Contrôle personnel des appareils (PCD) pour invocation et rangement instantanés du Landspeeder X-34, Swoop Bike, Dewback de selle et Chiot des Sables avec sifflet d'appel sonore.
        - [x] **Volet 1 : Housing Posable 3D & Bâtiments Entrables POB** (`swg_asset_pipeline.gd`, `swg_world_3d.gd`) : Structure habitable en pisé avec pas de porte franchissable (sans téléportation), intérieur meublé d'une table basse, banquette et coffre de maison sécurisé, vendeur personnel PNJ `Daran`, commande `/house` ou `/placehouse`.
        - [x] **Volet 6 : Espèces & Races SWG Pre-CU / Image Designer** (`swg_species_system.gd`, `swg_species_dialog.gd`, `swg_player_controller_3d.gd`) : Catalogue des 6 espèces canoniques (Humain, Twi'lek aux lekku, Androïde/Cyborg, Zabrak d'Iridonia, Wookiee géant, Rodien chasseur) avec morphologie adaptée, teintes de peau/pelage, bonus raciaux HAM et salon d'Image Designer accessible via `[F6]` ou `/species`.
        - [x] **Selftest Global SWG 3D Validé & Déployé** : `packages/swg-client/tools/swg_client_3d_selftest.gd` 100% vert (10/10 sous-suites), synchronisation immédiate des 17 scripts sur Windows `.10:5005` (`J:/swgemu/clients/swg-client/`).
      - **Cadre de Ciblage Tactique & Jauges HAM Cible (`swg_target_frame.gd`)** :
        - Unité cadre supérieure affichant en temps réel le nom, la distance en mètres, l'insigne d'alignement (`[HOSTILE]`, `[CITOYEN]`, `[CADAVRE]`, `[STRUCTURE]`) et les 3 jauges HAM de la cible (Santé, Action, Mental).
        - Touche `[Tab]` pour cycler et verrouiller intelligemment la cible vivante la plus proche (portée 45m).
      - **Boîte de Chat Spatial & Commandes Galactiques (`swg_chat_box.gd`)** :
        - Interface de communication en bas à gauche avec onglets `[Spatial]` et `[Combat/Système]`.
        - Saisie `[Entrée]` avec interprétation des commandes Slash authentiques SWG : `/dance`, `/kneel`, `/prone`, `/stand`, `/camp`, `/harvester`, `/speeder`, `/dewback`, `/clone`, `/shout <msg>`, `/help`.
        - Journal de combat temps réel relatant les dégâts blaster, les frappes reçues, les abattages et les transactions.
      - **Artisanat Connecté au Sac à Dos (`swg_crafting_panel.gd`)** :
        - Schémas connectés aux ressources réelles de l'inventaire (`inventory_ref`) : Stimpacks avancés, Blaster DH-17 Custom, Gilet en cuir renforcé, Couteau Vibro Scout.
        - Contrôle strict des prérequis de composants, déduction automatique des matières premières et insertion des objets créés dans le sac à dos `[I]`.
    - Synchronisé en direct et validé sous Windows .10 dans `J:\swgemu\clients\swg-client` via l'agent FastAPI :5005 (`SWG_CLIENT_3D_SELFTEST_OK`). CI Godot headless 18/18 PASS.

- [x] **Étape 4 (O2/O3) : Faune, Métier Scout & Domptage Creature Handler** :
  - *Bestiaire Lost Heaven* : 9 espèces indexées dans `bestiaire_lh.json` (chacal doré, scarabée obsidien, fennec mirage, marcheur des dunes, chiot chacal, jeune scarabée, bébé marcheur, scorpion titan, serpent de sable) avec tables de dépeçage et paramètres de domptage.
  - *Dépeçage Scout (Harvesting)* : Extraction sélective Viande (`Meat`), Peau/Cuir (`Hide`), Os (`Bone`) sur cadavres de bêtes fraîches avec bonus multiplicateur lié à la compétence `prospecteur_faune` (jusqu'à ×3.0 en Master), sécurité anti-duplication et attribution d'XP prospection.
  - *Camps de Survie (Scout Camps)* : Déploiement d'abris de toile et camps de chasseurs dans les terres sauvages (rayon 15–30m, régénération HAM boostée ×1.5 à ×2.2, répulsion des prédateurs, interdiction intra-muros).
  - *Camouflage d'odeur (Mask Scent)* : Dissimulation olfactive réduisant la détection des bêtes sauvages.
  - *Creature Handler* : Domptage d'animaux juvéniles basé sur la portée, le jet de difficulté et la compétence, transformation en familier lié (`loyalty`, `hunger`, `health`), invocation terrain (`call_pet`), ordres tactiques (`follow`, `stay`, `attack`, `guard`), nourrissage (`feed_pet`) et stockage (`store_pet`).
  - *Intégration & Tests* : Service `hub_creatures.gd`, câblage dans `hub_sim.gd`, `hub_combat.gd` et `hub_http.gd`, selftest `creatures_scout_selftest.gd` 100 % vert et intégré dans `tools/ci_godot_headless.sh`.
- [x] **Étape 3 (O2/O3) : Commerce & Vendeurs Joueurs (Player Vendors) & Usines (Factories)** :
  - *Player Vendors* : Déploiement de marchands PNJ personnalisés (caution 100 cr, espacement urbain ≥3m), gestion de stock SKU avec prix libres, descriptions et statistiques d'artisanat fidèles, transactions directes avec taxe commerciale de 5% reversée et coffre bancaire sécurisé pour encaissement par le propriétaire.
  - *Usines de fabrication en série (Factories)* : Déploiement d'usines (équipement, consommables, structures), chargement de Schémas Manufacturés (*Manufacturing Schematics*) figeant les recettes et stats, trémies d'ingrédients et d'énergie, cycles de production en série et conditionnement automatique en Caisses Manufacturées (*Factory Crates*).
  - *Bazar public & Bourse locale* : Panneau d'affichage public avec plafond de prix (max 20 000 cr pour préserver l'utilité des boutiques personnelles), frais d'inscription de 20 cr et transactions atomiques instantanées.
  - *Intégration & Tests* : Service `hub_vendors_factories.gd`, câblage dans `hub_sim.gd` et `hub_http.gd`, selftest `vendors_factories_selftest.gd` 100 % vert et intégré à `tools/ci_godot_headless.sh`.
- [x] **Étape 2 (O2/O3) : Housing Libre & Villes de Joueurs (Player Cities)** :
  - *Housing Libre & Actes de Propriété* : Modèles de structures (`tente nomade`, `petite maison en pisé`, `bunker métallique moyen`, `cantina privée`, `hall de guilde`) avec empreinte physique, contrôle de distance urbaine (protection intra-muros Lost Heaven), détection et rejet des chevauchements de fondations.
  - *Permissions & ACL* : Gestion fine des droits de propriété (`is_public`, liste d'administration, liste d'invités `entry_list`, bannissement strict `ban_list` avec expulsion automatique), et compte de maintenance pour éviter la dégradation.
  - *Décoration Intérieure Libre* : Pose libre de meubles et trophées au sol (`local_x, local_y, local_z`, orientation `yaw`), micro-ajustement de déplacement et rotation, verrouillage anti-vol et reprise dans l'inventaire.
  - *Cités de Joueurs & Municipalités* : Détection automatique des regroupements d'habitations (≥3 structures), élévation de rang civique (*Campement* ➔ *Hameau* ➔ *Village* ➔ *Bourgade* ➔ *Cité Métropolitaine*), organisation d'élections de maire par vote des résidents, fixation des impôts fonciers et commerciaux, et pose d'infrastructures civiques municipales (`shuttleport`, `cloning_facility`, etc.).
  - *Intégration & Tests* : Service `hub_housing_cities.gd`, câblage dans `hub_sim.gd` et `hub_http.gd`, selftest `housing_cities_selftest.gd` 100 % vert et intégré à `tools/ci_godot_headless.sh`.
- [x] **Étape 1 (O2) : Combat Tactique SWG (HAM Targeted Hits, Postures & Combos d'États)** :
  - *Postures SWG* : États dynamiques `Upright`, `Kneeling` (+15% précision), `Prone` (+25% précision, -20% vulnérabilité distante, +35% dégâts reçus au corps-à-corps).
  - *Ciblage des 3 pools HAM* : `Head Shot` (cible le Mental / Mind), `Leg Sweep` (cible l'Action, force Knockdown au sol), `Body Hit` (cible la Santé / Health). Incapacitation complète si l'un quelconque des 3 pools tombe à 0 !
  - *Le Combo Fatal SWG Pre-CU* : État `Dizzy` (vertige) + `Knockdown` (au sol) interdisant strictement de se relever sans purger le vertige (`dizzy_fall`), état `Stun` (réduction d'armure de 50%), état `Blind` (malus de visée de 45%), état `Intimidate` (dégâts divisés par 2).
  - *Encombrement d'Armure (Armor Encumbrance)* : Calcul en temps réel des pénalités d'armure sur les réserves Health, Action et Mind.
  - *Intégration & Tests* : Service `hub_swg_combat.gd`, câblage dans `hub_sim.gd` et `hub_http.gd`, selftest `swg_combat_selftest.gd` 100 % vert et intégré à `tools/ci_godot_headless.sh`.
- [x] **Instance Parallèle SWG Pre-CU 3D Dédiée (`packages/swg-client` & `packages/swg-hub`) — Étapes 1, 2 & 3 Livrées + Lancement Launcher** :
  - *Projets Godot 4 Dédiés* : `packages/swg-client` (Client 3D TPS) et `packages/swg-hub` (Serveur autoritaire 3D headless), découplés de `prime-client` / `prime-hub` pour préserver le banc d'essai existant et donner carte blanche à la 3D pure.
  - *Étape 1 — Contrôleur Joueur 3D TPS SWG (`swg_player_controller_3d.gd`)* :
    - Caméra orbitale 3ème personne avec `SpringArm3D` anti-collision décor, zoom molette progressif (vue 1ère personne 0.8m à vue MMO 16m), double mode de contrôle SWG (curseur libre pour interfaces ou mouselook au maintien clic-droit).
    - Déplacements 3D fluides (marche 3.5 m/s, course 7.0 m/s, sprint 10.0 m/s, saut).
    - 3 Postures 3D physiques : Debout (1.8m), Accroupi (1.15m, vitesse 2.4 m/s), Couché / Prone (0.55m, vitesse 1.2 m/s) avec redimensionnement temps réel de la `CapsuleShape3D` et du mesh.
    - Combo fatal *Dizzy Fall* physique (se relever en état Dizzy force une chute au sol en prone).
  - *Étape 2 — Terrain 3D Grande Échelle 16x16km & Pipeline d'Assets POB (`swg_terrain_system_3d.gd`, `swg_asset_pipeline.gd`)* :
    - *Terrain Continu par Chunks 64m* : Générateur de hauteur fractale FastNoiseLite simulant les dunes de Lost Heaven, streaming dynamique de chunks autour du joueur avec mesh 3D et collision physique exacte `create_trimesh_shape()`.
    - *Affecteurs d'Aplanissement Urbain (City Flat Affectors)* : Lissage progressif et aplanissement automatique sous les villes (Lost Heaven aplanie à Y=0.0m avec blend de 40m).
    - *Architecture POB Multi-Cellules* : Bâtiments SWG à cellules intérieures communicantes (Cantina La Perle avec dôme extérieur, cellule Bar avec comptoir en fer à cheval et néons, cellule Scène des danseurs avec spots directionnels).
    - *Palettes de Teintes 4 Canaux* : Pipeline de matériaux teintés SWG (couleurs primaires/secondaires configurables pour armures et vêtements).
    - *Miroir Altitudes Serveur Autoritaire* : Calcul d'altitude déterministe identique sur `swg_server_main.gd` pour validation physique et anti-triche.
  - *Étape 3 — Les 33 Professions SWG Pre-CU & 250 Skill Points (`swg_precu_professions.json`, `swg_professions_service.gd`)* :
    - *33 Professions Authentiques* : 6 professions de base (Artisan, Brawler, Marksman, Scout, Medic, Entertainer) + 26 professions avancées/élites (Rifleman, Teras Kasi, Creature Handler, Armorsmith, Doctor, Architect, Bio-Engineer, Smuggler, etc.) + Politician.
    - *594 Boîtes de Compétences Indexées* : Arbres 4x4 complets, vérification stricte des prérequis d'accès aux élites (ex: Marksman Rifles IV requis pour Rifleman Novice).
    - *Plafond Strict de 250 Skill Points* : Gestion des points dépensés/restants et abandon sécurisé (`surrender_skill`) avec remboursement intégral et contrôle de non-dépendance.
  - *Lancement Direct via Launcher & Scripts Dédiés* :
    - Profil `swg-3d` intégré dans `packages/launchpad/launchpad.config.json` et `packages/launchpad/main.js`.
    - Scripts de lancement direct fournis : `tools/launch_swg_client_3d.sh` (Linux) et `tools/launch_swg_client_3d.bat` (Windows).
  - *Tests de Validation* : `swg_client_3d_selftest.gd`, `swg_hub_selftest.gd` et `swg_professions_selftest.gd` **100% verts**.
- [x] **Restitution Complète de l'Ergonomie, Menus & UI de SWG Pre-CU (Lost Heaven, Godot 4 Client)** :
  - *Datapad Personnel Authentique (`swg_datapad_panel.gd`)* : 3 onglets physiques : Waypoints planétaires avec puces de couleur (activer/boussole/supprimer), Familiers & Droïdes PCD (*Pet Control Device*) avec cartes d'état et commandes d'invocation `/call`, `/store`, ordres `/follow`, `/stay`, `/trick`, et onglet Schémas d'artisanat.
  - *Fiche de Personnage SWG & 9 Attributs HAM (`swg_character_sheet.gd`)* : Structure 3 colonnes iconique (Santé: Health, Strength, Constitution ; Action: Action, Quickness, Stamina ; Esprit: Mind, Focus, Willpower), barres de Wounds noires réduisant le pool effectif max, jauge de Battle Fatigue (0–1000) influençant l'efficacité des soins, titre honorifique et citoyenneté.
  - *Terminal de Marché / Bazar & Boutiques Joueurs (`swg_bazaar_panel.gd`)* : Arborescence des catégories SWG (Minéraux, Chimiques, Organiques, Composants, Armes/Armures, Mobilier), tableau des lots avec prix immédiats / enchères, vendeur et localisation, panneau d'inspection de qualité, et onglet de mise en vente au bazar (plafonné à 20 000 cr conformément aux règles SWG).
  - *Terminal de Gestion Foncière & Cités de Joueurs (`swg_structure_panel.gd`)* : Suivi du Réservoir de Maintenance (Maintenance Pool en crédits, coût horaire, jours restants, versements bancaires), gestion des accès ACL (bascule Public / Privé, Entry List des résidents, Ban List), et données municipales (rang civique, maire, impôts fonciers).
  - *Câblage Ergonomique Global (`main.gd`, `client_ui_dialogue.gd`, `swg_ham_hud.gd`)* : Raccourcis claviers canoniques SWG (`C` pour Fiche Perso, `D` pour Datapad, `B` pour Bazar, `Ctrl+H` pour Propriétés, `Échap` pour fermeture en cascade), boutons dédiés dans le dock Datapad Système en bas-droite, et couverture complète dans `client_modular_selftest.gd`.
- [x] **Connexions Client GUI & Autonomie O3 SWG Pre-CU (« Les deux » - Livré & Validé)** :
  - *Client GUI (`packages/prime-client`)* :
    - Menu Radial (`swg_radial_menu.gd`) : contextes pour cadavres (dépeçage viande/cuir/os), créatures (apprivoisement tame, attaque), familiers (ordres stay/follow, nourrissage, chenil), vendeurs (boutique, gestion stock/caisse), housing (entrer, droits ACL, maintenance, déco 3D) et terrain (campement scout, postures accroupi/couché/debout).
    - HUD HAM (`swg_ham_hud.gd`) : badges de postures dynamiques et statuts de combat actifs (`DIZZY`, `KNOCKDOWN`, `STUN`, `BLIND`, `INTIMIDATE`), Datapad Système avec boutons *Bazar & Boutiques [B]* et *Propriétés & Villes [H]*.
    - Raccordement réseau (`main.gd`) avec requêtes HTTP dédiées et retours hotbar instantanés.
    - Selftest `client_modular_selftest.gd` 100% vert.
  - *Autonomie Flotte IA O3 (`packages/prime-hub`)* :
    - Arbitrage autonome complet dans `hub_bot_autonomy.gd` (`evaluate_swg_precu_priority`) : survie/campement en milieu hostile si blessé, dépeçage autonome de cadavres de faune, retrait bancaire de boutique, réapprovisionnement de maintenance foncière.
    - Combat tactique IA (`evaluate_tactical_combat_step`) : choix de posture optimale (prone défensif si danger mortel, kneeling si tir/cible à terre) et combos tactiques (Leg Sweep knockdown, Head Shot sur cible au sol, Intimidate).
    - Selftest `bot_autonomy_swg_selftest.gd` 100% vert et intégré dans la CI `tools/ci_godot_headless.sh`.
    - CI complète Godot Headless (23/23 suites) 100% verte en 121s ; tests Cortex Backend (152/152) 100% verts ; Ruff linter All checks passed.

**2026-11-02** :
- **Séquence Utilisateur « 1 puis 2 » Déployée & Validée (Portrait 3D HUD SWG + Polish Textures Châssis VRM)** :
  - **1. Volet 1 (O2 Prime Client) — Aperçu 3D Vivant dans l'encart HAM (Haut-Gauche)** :
    - *Composant `SwgPortrait3D` (`SubViewportContainer` 48×48 px)* : Rendu 3D haute fidélité (96×96 suréchantillonné), caméra buste/visage calibrée (`_camera.current = true`, `fov: 34°`, 3/4 face), éclairage studio à trois points + `WorldEnvironment` avec lumière ambiante douce pour déboucher les ombres du visage.
    - *Animations dynamiques & SAE* : Respiration idle oscillante, inclinaison subtile de la tête, clignement automatique des yeux (160ms toutes les 3.5 à 5s). Réaction en temps réel aux jauges HAM (expression faciale de détresse et pulsation d'alerte rouge sur la rim light si Santé < 25% ou fatigue critique).
    - *Synchronisation & Déploiement* : Code `swg_portrait_3d.gd` et `swg_ham_hud.gd` injectés en direct sur `J:/swgemu/clients/prime-client/` sur le poste Windows `.10`. Patch client `2026-11-02T21:14:38Z` (272 fichiers) et bootstrap Launchpad publiés sur `.246:8080`.
  - **2. Volet 2 (O1 Compagnon) — Polish Textures Châssis Androïde VRM (Pygmalion)** :
    - *Texture Carrosserie & Châssis (`body_skin_android.png` 1024×1024)* : Intégration de la texture mecha complète avec plaques pectorales biseautées, chanfreins métalliques titane satiné, 19 473 pixels de liserés néon cyan actifs (`#00f5d4`), rotules mécaniques concentriques aux jointures et col mécanique à servomoteurs 360°.
    - *Texture Visage (`face_skin_android.png`)* : Teint azur doux avec fines gravures cybernétiques et démarcations androïdes sous les orbites.
    - *Injection binaire `Compagnon.vrm`* : Textures injectées directement dans les buffers d'images GLB du modèle VRM (Image 11 Body, Image 5 Face), permettant un affichage unifié sous Three.js et Godot sans dépendance de surcouche.
    - *Déploiement Multi-Surfaces* :
      * *Windows `.10` (Bureau RDP)* : Synchronisation locale `sync_vrm_desktop` vers `C:\Agent_IA\compagnon-desktop\overlay\vrm\` et relance interactive de l'overlay Electron (5 processus actifs en Session 1).
      * *CT100 (`192.168.0.100`)* : Injection Docker de `body_skin_android.png`, `face_skin_android.png` et `Compagnon.vrm` dans `lbg-frontend:/usr/share/nginx/html/vrm/` (`:5174`).
- **Implémentation Canons Super-Agent & Équipe Visuelle (Inspirations Pentiminax & Axial Studio / Blobs)** :
  - **1. Super-Agent Event Filter & Routeur Étanche (Canon Pentiminax)** :
    - *Service déterministe par code* : Création de `packages/cortex/backend/services/super_agent_filter.py` implémentant le `SuperAgentRouter`. Séparation hermétique entre le Routeur de médiation humaine et les Workers spécialisés (`code`, `game`, `studio`, `ops`).
    - *Contextes étanches & zéro fuite* : Chaque worker dispose d'un contexte mémoire propre et borné sans pollution transversale.
    - *Filtrage déterministe & assainissement* : Masquage automatique des secrets (`[REDACTED_SECRET]`), détection stricte des besoins d'approbation humaine (`requires_human_approval`) et priorisation (`CRITICAL`, `HIGH`, `NORMAL`, `LOW`) avant toute transmission au modèle ou à l'orchestrateur.
    - *Endpoints Pilot Team* : Ajout de `GET /v1/pilot/team/super-agent/status` (synthèse temps réel des workers) et `POST /v1/pilot/team/super-agent/event` dans `packages/cortex/backend/api/v1/routes/pilot/team.py`.
    - *Tests & Qualité* : Suite unitaire `backend/tests/test_super_agent_filter.py` (5 tests passants), enrichissement de `test_pilot_team.py`, 152/152 tests backend PASS, Ruff check 100 % vert.
  - **2. Mini Agent Office & Boucle Interactive « They ask. You answer » (Canon Axial Studio / Blobs)** :
    - *Team Bar dans l'Overlay Bureau* : Intégration dans `packages/compagnon-desktop/overlay/index.html` d'une barre d'équipe visuelle (`#team-bar`) avec puces d'agents réactives (`Lyra` Studio, `Cline` Code, `Hub` MMO .246) affichant leur statut via des pastilles lumineuses pulsantes (`idle`, `active`, `asking`).
    - *Réactions expressives VRM & Lip-sync* : Dans `packages/compagnon-desktop/overlay/overlay.js`, lorsqu'un agent sollicite une validation (`session.approval_needed`), l'avatar adopte une pose de réflexion (`think`), exprime la requête via lip-sync vocal (`say("Cline demande ton arbitrage")`) et met en surbrillance la puce de l'agent.
    - *Arbitrage interactif* : Au clic sur `Allow`, l'avatar confirme d'une pose d'approbation (`approve`) avec expression joyeuse (`happy`) et confirmation vocale (`say("C'est validé !")`). Au clic sur `Deny`, il croise les bras (`crossArms`) avec expression sobre (`tense`).
  - **3. Mode Fantôme & Clic Traversant (Inspiration VSeeFace / Desktop Click-Through)** :
    - *Passage transparent des clics* : Implémentation de `setIgnoreMouseEvents(clickThrough, { forward: true })` dans `packages/compagnon-desktop/main.js` pour permettre de cliquer au travers de l'avatar et d'interagir directement avec ses fenêtres (IDE, navigateur) sans interférence.
    - *Raccourci Global & Bascule Rapide* : Raccourci global `Ctrl+Shift+F` (`CommandOrControl+Shift+F`) enregistrable via `registerGhostShortcuts()`, entrée dédiée dans le menu contextuel clic-droit et dans le menu de la barre des tâches (Tray).
    - *Feedback visuel* : Classes `mode-ghost` dans l'overlay avec lueur cyan douce et statut textuel `👻 Mode Fantôme (Ctrl+Shift+F)` informant l'utilisateur. IPC `setClickThrough` et `onClickThroughChanged` exposés dans `preload.js`.
  - **4. Séquenceur de Spectacle Continu `ShowRoutineManager` (Inspiration iStripper / vghd.exe)** :
    - *Routines continues multi-danses* : Implémentation dans `packages/compagnon-desktop/overlay/vrm/vrm_pet.js` du moteur de spectacle enchaînant fluidement chorégraphies mocap (`dance.vrma`, `samba.vrma`, `disco.vrma`, `robot.vrma`, `spin.vrma`), poses clés (`fingerHeart`, `wave`, `bow`), expressions faciales et répliques vocales lip-sync (`say(...)`).
    - *Trois shows intégrés* : `Show K-Pop Idol (~45s)`, `Show Club Electro (~40s)` et `Show Fiesta Latina (~40s)`.
    - *Éclairage de scène dynamique (Show FX)* : 2 projecteurs Three.js colorés (Cyan néon `#00f5d4` & Magenta néon `#ff007f`) pulsant au rythme de la musique et s'éteignant en fondu à la fin de la routine.
    - *Menus & Déclenchement direct* : Entrée dédiée `🎭 Spectacles & Shows (iStripper)` dans le menu clic-droit sur l'avatar et dans le menu Tray de la barre des tâches, avec option d'arrêt immédiat.
    - *Déploiement live Windows SDS `.10`* : Bundle recompilé avec `esbuild` (`vrm_pet.bundle.js` 2.2 Mo), déployé via `Agent_IA` et Electron redémarré en Session 1 (5 processus actifs).
  - **5. Polish & Stabilisation Spectacles & Mode Fantôme (Correction Dérive & Opacité)** :
    - *Verrouillage In-Place des Danses (Root Motion Lock)* : Correction dans `packages/compagnon-desktop/overlay/vrm/vrm_pet.js` (fonction `loadVRMA`). La dérive latérale (axe X pouvant atteindre +1.16m dans certains clips Mixamo) et en profondeur (axe Z) est désormais neutralisée à 0 pour toute animation de danse. L'axe Y est harmonisé autour de la hauteur de repos naturelle (`restHipsY`) avec rebond maîtrisé (`* 0.45`). L'avatar ne dérive plus et ne peut plus jamais sortir de son cadre.
    - *Réinitialisation Propre des Poses & Pas de Figeage en l'Air* : Dans `playVRMA`, `clampWhenFinished` est passé à `false` pour éviter que les sauts restent bloqués sur la dernière frame suspendue. Dans `stopVRMA` et à la fin des spectacles (`endShow`), appel systématique à `vrm.humanoid.resetNormalizedPose()` garantissant que l'avatar retombe instantanément les deux pieds sur terre au repos.
    - *Cadrage Caméra Inébranlable* : Dans `frameVrm`, la visée de la caméra corps entier est verrouillée au centre absolu (`targetCamPos.set(0, lookY, dist)` et `targetLookAt.set(0, lookY, 0)`).
    - *Mode Fantôme 100 % Opaque* : Dans `packages/compagnon-desktop/overlay/index.html`, passage de `body.mode-ghost` à `opacity: 1 !important; pointer-events: none !important;`. L'avatar reste parfaitement solide et net à l'écran, sans aucune transparence délavée, tout en laissant passer tous les clics de souris vers le bureau et les fenêtres arrière.
    - *Déploiement Live Windows `.10`* : Bundle réédité avec esbuild (2.2 Mo), uploadé sur `C:\Agent_IA\compagnon-desktop\overlay\` via l'API `:5005`, et overlay Electron redémarré avec succès.
  - **6. Pipeline de Conversion Automatisée de Nouvelles Danses (`FBX` -> `.vrma`)** :
    - *Outil `tools/convert_fbx_to_vrma.sh` & `tools/fbx2vrma/`* : Intégration du moteur de conversion Mixamo/DeepMotion FBX vers VRMA 1.0 officiel (52 os humanoïdes, 30 os de doigts, suppression des échelles et translations non-hips non conformes, GLB binaire).
    - *Conversion Unitaire & Batch* : Supporte aussi bien un fichier unique (`./tools/convert_fbx_to_vrma.sh ma_danse.fbx`) qu'un dossier complet (`./tools/convert_fbx_to_vrma.sh ~/dossier_danses/ --deploy`). Copie automatique dans `compagnon-desktop` et `compagnon_ui` + option de synchronisation directe sur le frontend CT100 (`:5174`).
- **Correction Urbanisme Remparts Lost Heaven & POI Hors Enceinte** :
  - *Bâtiments à cheval sur les remparts replacés à l'intérieur* :
    - `Logements N` (`poi:lost_heaven_lodge_n`) : replacé de `z: -370.0` à `z: -430.0` (au lieu de couper le rempart Nord à `-358.3`, il est désormais bien en retrait à l'intérieur avec une rue dégagée).
    - `Logements E` (`poi:lost_heaven_lodge_e`) : replacé de `(5460.0, -540.0)` à `(5245.0, -630.0)` (au lieu d'être à cheval sur le rempart Nord-Est, il s'intègre harmonieusement dans le quartier artisanal entre le hall d'entraînement et la cantina, à 150m à l'intérieur de l'enceinte).
  - *Suppression des faux bâtiments d'habitation extérieurs* : Dans `hub_buildings_layer.gd`, exclusion du rendu de maison fermée pour les POI extérieurs (`hunt_yard`, `salvage_scrap`, `city_gate`, `spawn`), éliminant les deux rectangles blancs parasites à l'extérieur de la Porte Est.
  - *Correction étiquette "Logements Ouest"* : Correction de la collision lexicale dans `_compact_french_building_label` où `"ouest"` était détecté comme `"est"`.
  - *Déploiement* : Patch client `2026-11-02T19:59:30Z` (275 fichiers) déployé sur `.246:8080`.
  - *Cause racine identifiée* : Dans `hub_buildings_layer.gd` (`is_north`) et `hub_props_layer.gd` (`b_rad`, `r_sub`), des inférences de type implicites `:=` sur des ternaires non typés ont provoqué des `Parse Error` sous Godot 4.6. En conséquence, le moteur refusait de charger les scripts et remplaçait silencieusement les nœuds par des `Node2D` vides, rendant invisibles tous les bâtiments, remparts et props du monde.
  - *Correction appliquée* : Typage explicite strict de toutes les variables (`Array[Vector2]`, `float`, `bool`), préchargement de `HubRuntimeCfg` dans les panneaux UI.
  - *Validation instantanée* : Test Godot headless validant l'attachement des scripts et le chargement effectif des 32 bâtiments, 59 props et 32 chemins/remparts. 18/18 tests de la CI réussis en 50 s.
  - *Déploiement* : Patch client `2026-11-02T19:51:09Z` (275 fichiers) déployé sur `.246:8080`, serveur hub headless opérationnel sur `.246:8787`.
  - **Squelettes Géants de Léviathans / Dragons Krayt (Style SWG)** : Implémentation du rendu procédural vectoriel haute fidélité `_draw_krayt_skeleton` dans `hub_props_layer.gd` (colonne vertébrale segmentée, arches de côtes recourbées émergeant du sable avec ombres portées, crâne fossilisé monumental à cornes et orbites). Déploiement au goulot du Canyon des Épaves (`5650, -3270`) et dans la plaine des ossements au sud (`5250, -1850`).
  - **Épaves de Vaisseaux & Débris Industriels Scrapaltai** : `_draw_starship_wreck` avec fuselages écrasés en biseau, cratères d'impact de sable, tuyères de réacteurs noircies, blindage riveté patiné orange/bleu pétrole et ailes détachées (Cargo Ikaros à l'Est `6700, -1650`, Chasseur écrasé au canyon `5820, -3130`).
  - **Amas Rocheux Massifs & Relief Naturel Dyson Logos** : `_draw_boulder_cluster` dessinant des affleurements de grès érodé avec facettes taillées, arêtes éclairées et ombres portées (Canyon Nord, Canyon Sud, Ksar Nord, Portes Est et Ouest).
  - **Ksar de l'Oasis Remodelé & Tentes Nomades Bédouines** : `_draw_nomad_tent` avec toiles tendues bordeaux/écrue en quartiers alternés, mâts centraux, piquets d'ancrage et auvents d'entrée ouverts. Bâtiments du Ksar agrandis (68 à 80m) pour circulation fluide et portes larges (20 à 22m). Bosquet de palmiers étendu.
  - **Avant-poste Minier de Zalem Étoffé (Sans Rempart Superflu)** : Bâtiments agrandis (72 à 84m) et espacés, suppression de la barrière ouest inutile, intégration de silos de raffinage industriels (`_draw_mine_silo`) et de conteneurs de fret lourds (`_draw_cargo_container`).
  - **Résolution Découpe du Sol & Désencombrement des Noms** : `planet_backdrop.gd` unifié statiquement sur toute la planète (36 km × 36 km sans double translation ni couture au dézoom, suppression des lignes horizontales parasites). `entity.gd` et `hub_buildings_layer.gd` nettoyés : désactivation de l'affichage forcé de masse de tous les PNJ au dézoom, ajout de cartouches de texte architecturaux lisibles avec fondu au dézoom global.
  - **CI & Déploiement** : 18/18 tests headless Godot passants, patch client v`2026-11-02T12:00:14Z` (272 fichiers) publié sur `.246:8080`, serveur hub headless redéployé et validé sur `.246:8787`.
- **Compagnon Desktop & Monitoring UI — Volets 1 (Overlay Bureau) & 2 (Monitoring Web) Validés & Déployés** :
  - **1. Overlay Bureau Windows (`compagnon-desktop`)** :
    - *Mouse Tracking interactif* : Implémentation dans `vrm_pet.js` du suivi du regard vers le curseur de la souris (`vrm.lookAt(lookTarget)` avec interpolation douce sur les axes X/Y et retour au centre automatique).
    - *Interaction tactile & Pokes au simple-clic* : Clic gauche interactif différentié (simple-clic déclenche une réaction amicale vivante aléatoire `wave`, `fingerHeart`, `approve`, `jump`, `stretch` avec bulle réactive brève ; double-clic ouvre la fenêtre de chat).
    - *Menu contextuel natif au clic droit* : Clic droit sur l'avatar du bureau ouvre un menu popup contextuel complet (`showOverlayContextMenu`) permettant d'ouvrir le chat, lancer les poses ou le pack danses (Groove, Samba, Hip-Hop, Disco, Robot, Pirouette), basculer le cadrage (Buste / Corps entier), déclencher la marche sur la barre des tâches ou masquer l'avatar.
    - *Rebundle esbuild & Synchronisation Windows SDS `.10`* : Recompilation de `vrm_pet.bundle.js` (2.2 Mo), synchronisation locale vers `C:\Agent_IA\compagnon-desktop\overlay\vrm\` et relance interactive de l'overlay en Session 1 (5 processus Electron opérationnels).
  - **2. Panneau Monitoring 3D & Web (`compagnon_ui` / `LyraPanel.vue`)** :
    - *Cadrage dynamique Buste vs Corps entier* : Transition fluide du conteneur `#lyra-face-host` (220px en vue Buste, 285px en vue Corps entier `.framing-full-host`) pour laisser respirer la silhouette en pied lors des danses et de la marche.
    - *Réaction expressive & Lip-sync spontané au Chat* : Watcher sur les messages du chat (`useChat().messages`) déclenchant automatiquement la parole (`vrmInst.say(text)`) et les poses adaptées au ton du dialogue (salut amical `wave` sur "bonjour/salut/quoi de neuf", réflexion `think` sur "réfléchir/vérifier/proposer", approbation `approve` sur "parfait/d'accord/validé", posture confiante `crossArms` sur alertes).
    - *Build Vite & Déploiement CT100* : 76/76 tests unitaires passants, compilation Vite verte (`dist/assets/index-DpjoYZse.js`), déploiement SSH Docker validé dans `lbg-frontend` sur CT100 (`:5174`, HTTP 200).
- **Intégration Aperçu 3D du Compagnon / Joueur dans le HUD SWG (`prime-client`) — Ticket 1 Priorité Utilisateur** :
  - **Module `SwgPortrait3D` (`SubViewport3D`)** : Création de `packages/prime-client/scripts/swg_portrait_3d.gd` (`SubViewportContainer` 48×48 px) avec rendu 3D haute fidélité (96×96 suréchantillonné), caméra buste/visage calibrée (`fov: 34°`, 3/4 face), éclairage studio à trois points (Key light zénithale, Fill light chaude et Rim light cyan holographique caractéristique de Scrapaltai).
  - **Import VRM direct & Fallback procédural autonome** : Chargement direct du modèle officiel `Compagnon.vrm` via `GLTFDocument` (57 blendshapes détectés dont `Fcl_EYE_Close`, `Fcl_ALL_Joy`, `Fcl_ALL_Sorrow`). Fallback mécanique complet en géométrie procédurale si le binaire n'est pas présent.
  - **Micro-animations & Réaction vivante au HAM** : Respiration idle oscillante, inclinaison subtile de la tête / regard vivant, clignement naturel automatique des yeux (160ms toutes les 3.5 à 5s). Bascule d'expression faciale et pulsation d'alerte sur la rim light lorsque la santé est basse ou la fatigue élevée.
  - **Cadre holographique & Badge Posture** : Encadrement net cyan `#3dd2f0` avec badge textuel translucide de posture (« Debout », « Combat ») intégré au bas du médaillon 3D sans chevauchement.
  - **Validation & Déploiement** : Suite `client_modular_selftest.gd` enrichie et validée, patch client `2026-11-02T10:56:16Z` (272 fichiers) publié et vérifié sur `.246:8080/patches/prime/`.
- **Launchpad v2.1.5 — Affichage Version, Auto-Mise à Jour Intégrée & Fix Chemins Persistants** :
  - **Affichage de la version** : Version affichée dans la barre de titre (`LBG MMO v2.1.5`) et dans le panneau d'information à gauche (`Version Launchpad : v2.1.5`).
  - **Auto-Mise à Jour transparente** : Au clic sur « Vérifier Mises à Jour », le Launchpad interroge `http://192.168.0.246:8080/releases/launchpad/version.json`. Si une version plus récente est publiée sur le serveur de patch, il télécharge automatiquement `app.asar` (~76 Ko) sans retélécharger tout le runtime Electron de 100 Mo.
  - **Application en 1 clic** : Dès le téléchargement terminé, un bouton vert `★ Redémarrer Launchpad (v2.1.5 prête)` apparaît. Au clic, un script batch transparent applique le nouveau package et relance immédiatement le Launchpad.
  - **Packaging & Déploiement LAN** : Script `packages/launchpad/scripts/pack_asar.js` intégré dans `publish_client_bootstrap_246.sh`. Fichiers `version.json`, `app.asar` et `installer-manifest.json` déployés et vérifiés sur `.246:8080`.
  - **Correction du bug d'écrasement des chemins** : Dans `packages/launchpad/main.js`, `migratePrimeClientPath` préserve fidèlement les dossiers configurés par l'utilisateur (`C:\LBG_MMO\...`) et synchronise `launchArgs = ['--path', profile.gameDir]`. Fallbacks automatiques si `J:` n'existe pas.
- **Géographie 2D style Dyson Logos, Oasis vivante du Ksar, Falaises Hachurées, Fond Infini & Caravane Déployée (.246)** :
  - **Falaises et Crêtes Hachurées Style Dyson Logos** : implémentation dans `hub_props_layer.gd` du rendu procédural des falaises géologiques (`kind: "cliff"`) avec crêtes marquées et hachures régulières (Cratère de Zalem, Canyon des Épaves, Promontoire rocheux du Ksar).
  - **Oasis Vivante du Ksar & Al-Khali** : bassins d'eau turquoise miroitante (`oasis_pool`), bosquets de palmiers en éventail (`palm_tree`), et arches monumentales en pierre (`stone_arch`).
  - **Fond de Carte Infini & Suppression des Dalles Carrées** : adaptabilité dynamique de `planet_backdrop.gd` à la caméra et au dézoom sans coupure visible, clear color fixée sur le sable de Scrapaltai (`Color(0.70, 0.60, 0.46)`), et neutralisation des sprites fantômes.
- **Urbanisme & Architecture Lost Heaven, Agrandissement Cantina (160m), Ancrage sur les Allées & Déploiement .246** :
  - **Agrandissement Majeur de La Cantina La Perle (160m / 80px)** : surface presque triplée, grand comptoir en U au Nord-Ouest pour Jax Moro, grande scène surélevée à l'Est avec projecteurs pour l'artiste, 4 salons intimes avec banquettes en demi-cercle (booths SWG) le long des murs, et immense piste centrale pour danser et circuler librement.
  - **Urbanisme Radial en Étoile** : réorientation de tous les bâtiments face à la Plaza centrale (`4749, -737`) et aux avenues.
    - Cantina : à l'Est, porte Ouest face à la Plaza.
    - Banque : à l'Ouest, porte Est face à la Plaza.
    - Auberge : au Nord, porte Sud face à la Plaza.
    - Grand Marché : au Sud, porte Nord face à la Plaza.
    - Clinique : au Nord-Ouest, porte Sud.
    - Hall d'entraînement : au Nord-Est, porte Sud.
    - Mairie : au Sud-Ouest, porte Nord.
    - Bureau des Missions : au Sud-Est, porte Nord.
    - Terminal Starport : déplacé sur l'aile Ouest comme terminal d'arrivée, dégageant complètement le centre-ville.
  - **Allées Pavées & Lanternes Dorées Synchronisées** : dans `hub_ground_layer.gd`, les allées mènent au pixel près sur le parvis de chaque bâtiment, et un halo de lanterne dorée éclaire chaque seuil de porte.
  - **Ancrages PNJ & Show Live** : `lost_heaven_npc_anchors.json`, `hub_sim_defs.gd` et `hub_show.gd` synchronisés. Jax est derrière son bar, l'artiste sur sa scène, le videur devant la porte Ouest.
  - **Validation & Déploiement** : 18/18 suites de tests headless Godot passées avec succès. Patch client (272 fichiers) publié sur `:8080/patches/prime/`, serveur `prime-hub` redémarré sur `:8787`.
  - **CI & Qualité Globale (2026-11-02)** :
    * **CI Godot Headless** : **18/18 suites PASS en 45s** (`bash tools/ci_godot_headless.sh` couvrant simulation, navigation, bâtiments CAO, persistance SQLite, contrats O3, météo, troc, métiers, arbre compétences SWG, prospection ressources, expérimentation craft, boucles HAM cantina/medcenter, extracteurs harvesters, inventaire DnD et modules client).
    * **Tests Cortex Backend** : **146/146 tests PASS en 8.17s** (`python -m pytest backend/tests`).
    * **Tests Joueurs IA Kernel (O3)** : **5/5 tests PASS en 0.17s** (`python -m pytest agents/tests/test_player_ia_kernel.py`).
    * **Linter Ruff** : **All checks passed** (`ruff check .`).
  - **Suppression du résidu de route sud** : retrait de la ligne coupant le rempart sud dans `hub_ground_layer.gd`, confirmation de la sortie unique et sinueuse par la Porte Est.
  - **Caravane Marchande & PNJs de Garnison** : intégration dans `hub_sim_defs.gd` de la Vigie des Dunes, du Gardien de la Source et du Ferrailleur du Canyon.
  - **Déploiement LAN .246 validé** : patch client (270 fichiers) publié sur `:8080/patches/prime/`, serveur `prime-hub` redémarré sur `:8787` avec la caravane active (diffusion de l'étape Porte Est confirmée dans le stream mondial). CI 18/18 headless Godot validée.


  * **Échelle canonique physique `size_m` (72m à 144m)** : Rétablissement de la vraie taille canonique des bâtiments dans `hub_buildings_layer.gd` (36px à 72px de demi-taille), alignée au pixel près sur la boîte de collision de `HubCollision` et `ZoneLayers`. Plus aucun mur invisible à 30 mètres en dehors des bâtiments : l'entrée dessinée correspond exactement au seuil de passage.
  * **Intérieurs visitables et spacieux** : Les surfaces au sol sont triplées avec de larges couloirs entre les tables, le comptoir et les lits d'examen.
  * **Hitbox PNJ précise (`radius_px` réduit de 28px/18px à 8px)** : Cliquer à côté d'un PNJ sur le sol fait maintenant marcher le personnage au lieu de déclencher une sélection ou un dialogue intempestif.
  * **Clic gauche intelligent** : Un simple clic cible et fait marcher le personnage vers sa destination ; le dialogue modal ne s'ouvre que si le joueur est au contact immédiat (< 4.5m) ou ré-appuie sur sa cible, ou via le Radial Menu (clic droit -> Discuter).
  * Patch Prime Client `2026-11-02T07:07:06Z` déployé sur `.246:8080/patches/prime/`.

**2026-11-01** :
- **Patch Client & Serveur — Téléportation Dev, Fix Collision Remparts & Désencombrement UI** :
  * **⚡ Téléportation Dev / Admin** : Ajout dans le menu radial SWG (clic droit terrain) de l'option `⚡ Téléporter ici (Dev)`. Téléporte instantanément le joueur aux coordonnées ciblées, met à jour le serveur WS/UDP et recentre la caméra.
  * **Fix Remparts & Palissades (anti-traversée Nix)** : Intégration dans `HubCollision` (serveur) du tracé de la palissade (`lost_heaven_props.json`) avec détection des segments bloqués et corridors de portes. Activation stricte côté client (`enforce_hub_fence = true`), bloquant tout bot ou compagnon de traverser les murs d'enceinte en dehors des portes ouvertes.
  * **Désencombrement des noms & étiquettes de PNJ** : Les étiquettes ne sont plus forcées globalement. Affichage adaptatif : joueur local, compagnons de groupe (Nix, Lia), cible active et monstres en combat sont affichés, tandis que les PNJ distants sont épurés au dézoom pour éliminer l'empilement illisible.
  * **Rendu Battlemap VTT / Dyson Logos** : Remplacement des pointillés par de vrais remparts épais crénelés avec merlons, bastions de pierre et ombres portées douces ; ajout de croissants de dunes naturels, affleurements de rochers de grès et foyers de feux de camp avec halos chaleureux.
  * Patch Prime Client `2026-11-01T22:43:50Z` déployé sur `.246:8080/patches/prime/`.
- **Phase 4 (Tickets 4.1 à 4.5) — Transposition complète de la boucle Star Wars Galaxies Pre-CU dans Lost Heaven (`prime-hub` & `prime-client`)** :
  * **Ticket 4.1 (`hub_skills.gd` & `catalog_skills.json`)** : 8 professions complètes en structure `Novice → 4 branches × 4 boxes → Master`, plafond de 250 Skill Points, jauges d'XP spécialisées, `learn_box` / `surrender_box` et modificateurs passifs (`experimentation_points`, `survey_range`, `wound_heal_efficiency`, `fatigue_heal_power`, `harvester_slots`).
  * **Ticket 4.2 (`hub_survey.gd` & `resources_spawns_lh.json`)** : Gisements dynamiques rotatifs dotés de statistiques `1..1000` (`oq`, `cd`, `pe`, `ma`, `sr`), sondage radar `survey_ping` et extraction `sample_resource` conservant les statistiques de la veine dans l'inventaire joueur.
  * **Ticket 4.3 (`hub_crafting.gd`)** : Calcul pondéré de la qualité d'assemblage selon les statistiques des ressources consommées, numérotation de série `LH-xxxx`, signature `crafted_by` et sessions d'expérimentation multi-tentatives (`amazing_success` à `critical_failure`).
  * **Ticket 4.4 (`hub_ham_medical.gd`)** : Triple barre `HAM` (`Health`, `Action`, `Mind`), accumulation de `Wounds` et `Battle Fatigue` en combat, guérison sociale de la fatigue et buff d'Esprit à la Cantina La Perle (`watch_entertainer`), et traitement des blessures au Medcenter (`treat_wounds`).
  * **Ticket 4.5 (`hub_harvesters.gd` & `hub_bot_autonomy.gd`)** : Pose d'extracteurs sur gisements (`>= 25%` hors bâtiments CAO), cycles de maintenance et remplissage de trémie (`Hopper`), collecte vers l'inventaire et arbitrage autonome O3 (`evaluate_swg_precu_priority`).
  * **Validation CI Headless Godot** : 5 nouvelles suites unitaires (`precu_skills_tree_selftest.gd`, `survey_resources_selftest.gd`, `craft_experimentation_selftest.gd`, `ham_cantina_medcenter_selftest.gd`, `harvesters_outpost_selftest.gd`) intégrées à `tools/ci_godot_headless.sh` (**17/17 PASS**).  

**Plan d'Évolutions Phase 2 (100 % ACHEVÉ & VALIDÉ — 8/8 Tickets DONE)** :
- [x] **Ticket 2.1** : Contrat d'Environnement Universel O3 (`AgentEnvironmentAdapter`)
- [x] **Ticket 4.1** : Banc d'Évaluation de Non-Refus Heretic (`tools/eval_heretic_dialogue.py`)
- [x] **Ticket 3.1** : Mobilier Procédural & Vie Intérieure des Bâtiments CAO
- [x] **Ticket 1.1** : Interaction Vocale Mains-Libres STT (*Voice-In*)
- [x] **Ticket 1.2** : Conscience Contextuelle de l'Espace de Travail (*Focus Awareness*)
- [x] **Ticket 3.2** : Météo Dynamique & Repli Bâtiments (Tempête de sable)
- [x] **Ticket 2.2** : Émergence Sociale : Propagation des Rumeurs Inter-Villages
- [x] **Ticket 5.1** : Projection Cognitive des Joueurs IA dans le Cerveau 3D

**Plan d'Évolutions Phase 3 ([`PLAN_EVOLUTIONS_PHASE3.md`](PLAN_EVOLUTIONS_PHASE3.md) — 100 % ACHEVÉ & VALIDÉ — 7/7 Tickets DONE)** :
- [x] **Ticket 1.1** (O1) : Synthèse Vocale TTS Locale & Lip-Sync Visèmes VRM
- [x] **Ticket 2.1** (O2) : Cycle Jour / Nuit Circadien & Éclairage Bâtiments CAO
- [x] **Ticket 3.1** (O3) : Coordination Tactique en Binôme (`AgentEnvironmentAdapter`)
- [x] **Ticket 2.2** (O2) : Métier Récupérateur : Établis d'Assemblage Mécatronique
- [x] **Ticket 3.2** (O3) : Économie de Troc P2P & Négociations d'Échanges
- [x] **Ticket 1.2** (O1) : Vision Contextuelle Ponctuelle sur Demande (OCR / VLM)
- [x] **Ticket 5.1** (Studio) : Replay Chronologique & Timeline Synaptique Pilot Web

**2026-10-31** :
- **Phase 3 Ticket 1.2 — Vision Contextuelle Ponctuelle sur Demande / Incident (`packages/cortex/backend`, `Agent_IA`, `compagnon_ui`)** :
  * Action `capture_active_window_snippet` dans `packages/cortex/windows_agent/Agent_IA/executor.py` : capture ciblée en mémoire (`MemoryStream` -> Base64) de la seule fenêtre de premier plan (`GetForegroundWindow` / `GetWindowRect`), zéro stockage disque.
  * Service `packages/cortex/backend/services/vision_service.py` et routes `/v1/vision/health`, `/v1/vision/analyze` dans `api/v1/routes/vision.py` (purge mémoire immédiate après analyse, heuristique OCR d'erreurs + fallback mini-VLM local `.111`).
  * Injection du contexte visuel dans `packages/cortex/compagnon_ui/server_overlay/router_prompts.py` (`is_vision_intent_prompt`, `format_vision_context_block`).
  * Suite de tests unitaires `packages/cortex/backend/tests/test_vision_service.py` (3/3 passants).
- **Phase 3 Ticket 5.1 — Replay Chronologique & Timeline Synaptique Pilot Web (`packages/cortex/backend` & `pilot_web`)** :
  * Buffer circulaire temporel (`_brain_timeline_buffer`, 1000 impulsions / ~15 min) et endpoints `POST/GET /v1/pilot/brain/timeline` dans `packages/cortex/backend/api/v1/routes/pilot/status.py`.
  * Suite de tests unitaires `packages/cortex/backend/tests/test_pilot_brain_timeline.py` (2/2 passants).
  * Contrôleur de Scrubber temporel (`#brain-timeline-bar` : Pause, Direct, curseur `-15 min ... 0s`) dans `pilot_web/index.html`, `src/modules/team_brain.js` et méthode `replaySnapshot()` dans `brain_3d/brain_3d.js`.
- **Phase 3 Ticket 1.1 (Unification Frontend TTS & Visèmes VRM)** :
  * Consolidation dans `packages/cortex/compagnon_ui/src/lib/tts.js` des fonctions historiques (`speakText`, `stopTts`, `fetchTtsHealth`, `sanitizeForSpeech`) et du contrôleur Lip-Sync (`createSpeechOutputController`, `generateClientVisemes`, `playVisemes` dans `vrm_pet.js`). 76/76 tests JS et build Vite `compagnon_ui` verts.
- **Résolution des Blocages de Connexion & Latence Pilot Web (Campus Team / Presence / Joueurs IA)** :
  * **Causes racines identifiées** :
    1. *Course critique SQLite multi-threads* : `ensure_schema()` réexécutait `executescript(_MESSAGES_SCHEMA)` à chaque lecture de messages sans verrou, provoquant `sqlite3.DatabaseError: another row available` et des deadlocks en cascade.
    2. *Absence d'index sur `updated_ts`* : dans `team_tasks.db` (281 Mo, 35 474 tâches accumulées), chaque requête `ORDER BY updated_ts DESC` scannait toute la table (1,06 s par requête) avec saturation de la file d'attente d'Uvicorn.
    3. *Sondes réseau synchrones bloquantes* : `check_port` exécutait 5 `socket.create_connection` synchrones de 0,8s bloquant l'event loop principal de FastAPI pendant 2,4s à chaque requête `GET /v1/pilot/status`.
    4. *Dépendance manquante* : `python-multipart` manquant dans le venv de la VM 140 (requis par `stt.py`).
  * **Correctifs appliqués & Déployés** :
    - `messages.py` & `store.py` : protection stricte de toutes les requêtes SQLite par `_db_lock`, flag `_schema_ensured` pour n'exécuter `ensure_schema` qu'une seule fois, et création des index B-tree composites `idx_team_tasks_updated`, `idx_team_tasks_status_updated` et `idx_team_tasks_role_updated` (requêtes accélérées de 1,06 s à 0,5 ms — gain x590).
    - `status.py` : conversion des sondes de ports en coroutines asynchrones parallèles (`check_port_async` via `asyncio.gather`), éliminant tout blocage de l'event loop.
    - Installation de `python-multipart` sur la VM 140 et redémarrage propre des services `lbg-orchestrator` et `lbg-backend`.
  * **Résultats vérifiés** :
    - `/v1/pilot/team/presence/snapshot` : **70 ms** (badge snapshot OK vert, 23 agents affichés).
    - `/v1/pilot/player-ia/runtime` : **73 ms** (10 bots online affichés).
    - `/v1/pilot/team/campus/status` : **0,66 s** (délai dépassé 15s éradiqué).
- **Phase 3 Ticket 2.2 — Métier Récupérateur : Établis d'Assemblage Mécatronique & Recettes de Terrain (`prime-hub`)** :
  * Création de `packages/prime-hub/scripts/hub_crafting.gd` et `packages/prime-hub/data/craft/schematics_scrap.json` : 4 recettes de terrain canoniques (*Kit de réparation mécatronique*, *Filtre à condensat d'oasis*, *Batterie régulée de ferraille*, *Torche de prospection nocturne*).
  * Validation stricte d'ancrage CAO de proximité `is_near_craft_bench(pos, 8.0)` via `hub_collision.gd` au Hangar Dépôt Nord (`warehouse_craft_bench`), refus déterministe à distance.
  * Consommation atomique d'ingrédients sous autorité serveur (`craft_combine`) et snap en posture Triplon `craft`.
  * Self-test unitaire headless : `packages/prime-hub/tools/crafting_schematics_selftest.gd` validé en CI.
- **Phase 3 Ticket 3.2 — Économie de Troc P2P & Négociations d'Échanges entre Joueurs IA (`prime-hub`)** :
  * Création de `packages/prime-hub/scripts/hub_trade.gd` : matrice de valeur relative bornée (garde-fou anti-déséquilibre, ex. 2 ferrailles = 1 capsule d'eau), protocole d'offre et acceptation sans intermédiaire PNJ.
  * Estimation autonome des surplus et déficits d'inventaire dans `hub_bot_autonomy.gd` (`evaluate_barter_needs`).
  * Échange bilatéral atomique sous autorité Godot Hub (zéro duplication, zéro mutation libre LLM).
  * Intégration rumeur dynamique dans `HubWiki` suite aux trocs réalisés au Cantina (*« Nix_BarterTest a troqué 2 Ferraille contre 1 Capsule d'eau avec Lia_BarterTest (Cantina La Perle) »*).
  * Résolution SQLite transactionnelle dans `hub_db.gd` : segmentation automatique des lots SQL (`_exec_sql_chunk`) pour respecter la limite `MAX_ARG_STRLEN` (128 KB) d'execve sous Linux.
  * Self-test unitaire headless : `packages/prime-hub/tools/barter_trade_selftest.gd` validé en CI.
- **CI & Qualité Globale** :
  * CI Godot Headless : **12/12 tests PASS en 18s** (`bash tools/ci_godot_headless.sh`).
  * Pytest Cortex Backend : **144/144 tests PASS en 6.93s** (`packages/cortex/.venv/bin/pytest packages/cortex/backend/tests`).
  * Compagnon UI Frontend : **76/76 tests PASS en 1.54s** (`node --test packages/cortex/compagnon_ui/src/lib/*.test.js`).
  * Linter Ruff : **All checks passed** (`ruff check .`).
- **Phase 3 Ticket 1.1 — Synthèse Vocale TTS Locale & Visèmes VRM (`packages/cortex/backend`)** :
  * Création de `packages/cortex/backend/services/tts_service.py` : moteur TTS avec support des voix locales (Kokoro/Piper sur `.111`), fallback déterministe mock/WebSpeech, et générateur de visèmes VRM synchronisés (`aa`, `ih`, `ou`, `ee`, `oh`).
  * Endpoints REST dans `packages/cortex/backend/api/v1/routes/tts.py` : `/v1/tts/health`, `/v1/tts/voices`, `/v1/tts/synthesize`.
  * Suite de tests unitaires complète `backend/tests/test_tts.py` (6/6 tests passants).
- **Volume Temporaire de Sauvegarde Proxmox 300 Go (R720 — `192.168.0.201`)** :
  * **Contexte & Risque** : Panne matérielle du NAS Synology DS1815+ (`192.168.0.51`). Le montage VZDump `/mnt/pve/nas-lun-backup` retombait sur la racine `pve-root` des hyperviseurs, provoquant la saturation de `.200` (NUC) et risquant celle de `.201` (R720).
  * **Solution déployée** :
    - Allocation d'un LV Thin de 300 Go `/dev/pve/backup_temp` dans le thin-pool `pve/data` de `lbgr720` (ext4, label `BACKUP_TEMP`).
    - Montage système persistant sur `/mnt/backup-temp` (inscrit dans `/etc/fstab`, 292 Go disponibles réels).
    - Déclaration dans le cluster Proxmox (`pvesm add dir backup-temp --path /mnt/backup-temp --content backup --nodes lbgr720`).
    - Statut vérifié : `backup-temp` actif et opérationnel pour recevoir les sauvegardes de machines sans toucher au disque système.
  * **Nettoyage préventif `.200`** : Suppression de l'archive orpheline du CT 111 (28 Go), racine stabilisée à 41% (38 Go libres).
- **Phase 3 Ticket 2.1 — Cycle Jour / Nuit Circadien & Éclairage Bâtiments CAO (`prime-hub` & `prime-client`)** :
  * Création de `packages/prime-hub/scripts/hub_world_clock.gd` : gestionnaire d'horloge circadienne (24 min réelles = 24h jeu, 4 phases : aube, zénith, crépuscule, nuit profonde).
  * Intégration dans `hub_events.gd` et `hub_sim_views.gd` (diffusion de `world_time`, `day_phase` et `sun_intensity`).
  * Interaction gameplay : allumage automatique des lanternes nocturnes sur les bâtiments CAO (`hub_buildings_layer.gd`), et amplification du rayon d'agressivité des prédateurs nocturnes (+60% de nuit).
  * Self-test unitaire headless : `packages/prime-hub/tools/day_night_selftest.gd` validé en CI.
- **Phase 3 Ticket 3.1 — Coordination Tactique en Binôme & Escorte Coopérative (`prime-hub`)** :
  * Extension du contrat `AgentEnvironmentAdapter` et de `GodotHubAdapter` : actions de groupe (`FORMATION_FOLLOW`, `COVER_TARGET`, `TACTICAL_RETREAT`).
  * Logique de binôme dans `hub_bot_autonomy.gd` : formation dynamique de paires (leader / escort), suivi spatial avec maintien de distance tactique et riposte coordonnée face aux menaces.
  * Self-test unitaire headless : `packages/prime-hub/tools/tactical_escort_selftest.gd` validé en CI.
- **Intégration Visualisation Cerveau 3D & Conscience Synaptique (Pilot Web & Compagnon Lyra)** :
  * **Étape 1 — Interactions Avancées Cerveau 3D Pilot Web (`packages/cortex/pilot_web`)** :
    - `brain_3d.js` : implémentation de `tempFocusPole(poleKey, durationSec)` pour zoom cinématique fluide temporaire avec retour automatique à l'orbite 360°, fonction `resetView()` et signal infra enrichi.
    - `team_brain.js` : détection fine des transitions d'état (`detectStateChanges`) réagissant aux reconnexions des VMs (140, Orchestrateur, Godot Hub `.246`) et à l'activité des agents (`busy`, `review`), clics interactifs sur chaque ligne du flux d'activité déclenchant focus et pulsation, table contextuelle `POLE_ACTIONS` avec boutons d'actions directes vers le Studio (`#brain-pole-action-btn`, `#brain-pole-pulse-btn`), et bascule Auto-focus (`#brain-btn-autofocus`).
    - Build Vite validé (`dist/`) et déployé sur la VM 140 (`http://192.168.0.140:8080/`, HTTP 200).
  * **Étape 2 — Visualisation de Conscience 3D pour Lyra (`compagnon_ui` & `compagnon-desktop`)** :
    - Composant `LyraConscience3D.vue` : sphère/tore knot de conscience holographique Three.js réactif en temps réel aux 4 piliers cognitifs de Lyra (`chaleur`, `energie`, `patience`, `confiance` depuis `/lyra/state`). Couleur du cœur modulée par la Chaleur (bleu froid -> cyan -> ambre doré), vitesse d'onde/rotation pilotée par l'Énergie, stabilité par la Patience, densité du halo externe par la Confiance. Toolbar interactive (orbite 360°, recentrage, pulsion synaptique, focus cinématique par pôle).
    - Page dédiée `BrainConsciencePage.vue` (`/brain`) : grand écran immersif avec réglage interactif des jauges en temps réel, presets express (Chaleureuse, Créative, Neutre, Concise) et flux cognitif.
    - Intégration dans `NavRail.vue` (icône d'accès direct 🧠) et dans `LyraPage.vue` (vue 3D commutable en direct).
    - Intégration bureau `compagnon-desktop` (`main.js`) : raccourci « 🧠 Conscience 3D de Lyra » dans le menu Tray ouvrant l'interface.
- **Lancement Phase 3 d'Évolutions ([`PLAN_EVOLUTIONS_PHASE3.md`](PLAN_EVOLUTIONS_PHASE3.md)) & Déploiement Validé des Surfaces LAN** :
  * **Surfaces LAN & Runtime Live** :
    - Déploiement overlay CT100 (`192.168.0.100:5174`, API `:3000`) et assets VRMA complets (`tools/deploy_to_ct100.sh` et `deploy_compagnon_100.sh --smoke`).
    - Redémarrage et synchronisation de `prime-hub` sur `.246:8787` (`deploy_prime_hub_246.sh`). 10 bots, 24 PNJ, 7 bêtes, météo et rumeurs live.
    - Audit global LAN : 18/18 surfaces opérationnelles (`smoke_lan_surfaces.sh --quick`).
  * **Formalisation du Plan Phase 3** : 7 tickets structurés et chiffrés articulant TTS/visèmes VRM, cycle jour/nuit circadien, escorte tactique IA, établis de craft, troc P2P et timeline Cerveau 3D.
- **Formalisation ADR 0029 — Doctrine Anti-Recodage Global (Rust & Hype vs Pragmatisme Produit)** :
  * **Décision architecturale** : refus catégorique du piège du « Big Bang Rewrite » en Rust.
  * **Répartition des rôles** : Python (cerveau/orchestration O1), Godot 4 (corps/espace/physique/client O2), Rust (scalpel réservé aux optimisations chirurgicales isolées sur preuve de benchmark, ex. GDExtension ou relay binaire).
  * **Documents actés** : [`packages/cortex/docs/adr/0029-doctrine-anti-recodage-rust-pragmatisme.md`](../packages/cortex/docs/adr/0029-doctrine-anti-recodage-rust-pragmatisme.md), indexé dans `docs/REGISTRE.md` et dans les règles Antigravity `.agents/rules/lbg-studios.md`.
- **Protocole de Production Hybride : Cline (Codeur Local) ↔ Antigravity (Supervision & Contrôle)** :
  * **Décision opérationnelle** : à la demande de l'utilisateur, Cline (`huihui_ai/qwen2.5-coder-abliterate:14b` sur `.110`) prend en charge l'écriture/génération du code source local 0 €, tandis qu'Antigravity assure le rôle de superviseur/gatekeeper (cadrage des mandats, inspection `git diff`, revue critique de robustesse, et exécution des tests CI).
  * **Règle persistée** : formalisée dans `.agents/rules/cline-delegation-review.md` et `.cursor/rules/cline-delegation-review.mdc`.
- **Alignement Agents Locaux Mains Code (`.143` Omarchy ↔ Ollama `.110`)** :
  * **Diagnostic Tool-Calling Claude Code vs Ollama** : Claude Code attend le format propriétaire Anthropic `tool_use`. En local avec Ollama, le modèle génère du JSON brut qui s'affiche comme texte sans exécuter les outils.
  * **Configuration Cline CLI & VS Code** :
    - Fichiers `~/.cline/data/settings/providers.json` et `~/.cline/data/globalState.json` mis à jour pour cibler directement `huihui_ai/qwen2.5-coder-abliterate:14b` sur `http://192.168.0.110:11434`.
    - Cline supporte nativement le protocole d'outils Ollama (Plan/Act) et s'utilise soit en terminal (`cline -P ollama`), soit via l'extension VS Code (`saoudrizwan.claude-dev`).
  * **Rappels d'Architecture (ADR 0025 & ADR 0028)** :
    - **OpenCode** (`opencode run`) : nominal Team Studio (Métis).
    - **Cline** : second avis local 0 € API.
    - Contrainte CPU `.110` : toujours cibler des fichiers précis (1 à 3 fichiers), éviter les scans exhaustifs de monorepo.
- **Pack Danses Mocap VRMA Réalistes (Différenciation Groove/Samba, Robot, Disco & Pirouette)** :
  * **Diagnostic initial & causes racines** :
    1. *Doublon binaire Groove / Samba* : `dance.vrma` et `samba.vrma` possédaient le même hash SHA256 (`b74b4cee08...`), issu d'une copie identique lors de l'intégration initiale.
    2. *Danses procédurales rigides (« très loin de ressembler à des danses réelles »)* : `Robot`, `Disco` et `Pirouette` étaient animés via de simples équations trigonométriques `Math.sin(tempo)` dans `vrm_pet.js` (les jambes restaient immobiles en T-pose, seuls les bras bougeaient de façon saccadée, et la pirouette tournait le modèle comme une toupie sans animation du corps).
    3. *Échec silencieux sur le bureau Windows SDS `.10`* : les fichiers `.vrma` n'étaient pas physiquement synchronisés dans `C:\Agent_IA\compagnon-desktop\overlay\vrm\animations\`. Lorsque Electron essayait de charger les clips, l'échec 404 local forçait un repli procédural où l'avatar restait coincé debout avec un simple sautillement vertical inerte.
  * **Intégration de véritables animations Mocap VRMA 52/53 os** :
    - *🎵 Groove (`dance.vrma`)* : Nouvelle animation pop/groove 52 os (8.21s, conversion Three.js mocap) — **100% distincte de la Samba** (`dance.vrma`: `84e4cdba...` vs `samba.vrma`: `b74b4cee...`).
    - *💃 Samba (`samba.vrma`)* : Danse festive latino/samba mocap 52 os (18.16s, déhanché ample et balancement fluide).
    - *🧢 Hip-Hop (`hiphop.vrma`)* : Danse street/hip-hop athlétique mocap 52 os (15.33s, cadence rythmée et rebonds).
    - *🤖 Robot (`robot.vrma`)* : Véritable danse robotique / popping mocap 52 os (15.42s, conversion Mixamo HF `Robot_Hip_Hop_Dance.fbx` avec blocages d'articulations et onde corporelle complète).
    - *🪩 Disco (`disco.vrma`)* : Véritable danse funk/soul/disco 70s mocap 52 os (16.04s, conversion Mixamo HF `Northern_Soul_Dance.fbx` avec pas de danse, jeu de jambes et tours).
    - *💫 Pirouette (`spin.vrma`)* : Véritable pirouette mocap 53 os (tour complet avec impulsion corporelle, cambrure et retombée gracieuse sur les appuis).
    - *💃 Salsa (`salsa.vrma`)* : Danse salsa latino mocap 52 os (28.08s, conversion Mixamo HF `Salsa_Dancing.fbx`).
  * **Résilience & Fallback Transparent Desktop Pet** :
    - Mise à jour de `loadVRMA()` dans `vrm_pet.js` : en cas d'absence ou 404 d'un fichier local sur le bureau Windows Electron, chargement automatique via le fallback LAN `http://192.168.0.100:5174/vrm/animations/${targetFile}` — plus aucun freeze ou fallback inerte en T-pose.
    - Neutralisation des artefacts : suppression des rebonds et rotations procédurales parasites (`spinAngle`) lorsque les clips mocap VRMA sont actifs.
    - Extension de `sync_vrm_desktop()` dans `executor.py` pour synchroniser automatiquement l'ensemble des 24 animations `.vrma` vers le bureau Windows.
    - Élargissement de la CSP dans `overlay/index.html` (`connect-src` autorisant CT100 et le loopback) pour débloquer le chargement réseau des animations sous Electron.
    - Ajout de l'auto-synchronisation transparente au démarrage de `main.js` (copie automatique de `A:\` vers `C:\Agent_IA\compagnon-desktop` sous Windows).
    - Création du script en 1 clic `MAJ_COMPAGNON.cmd` à la racine de `A:\LBG_Studios` pour synchroniser et redémarrer l'avatar du bureau immédiatement.
    - **Poussée & Exécution Directe sur Windows SDS `.10` (sans intervention utilisateur)** :
      * Via `Agent_IA` (`http://192.168.0.10:5005`) en Session 1 interactive (`sdesh`).
      * Synchronisation complète des 25 fichiers `.vrma` d'animations mocap dans `C:\Agent_IA\compagnon-desktop\overlay\vrm\animations\` (dont `dance.vrma` Pop Groove hash `84e4cdba1884` 100% distinct de la samba `b74b4cee0805`, `robot.vrma`, `disco.vrma`, `spin.vrma`, `hiphop.vrma`).
      * Déploiement de `vrm_pet.bundle.js` (2.26 MB), `overlay/index.html` (CSP élargie) et `executor.py` dans `C:\Agent_IA\`.
      * Fermeture propre des anciens processus Electron orphelins (`taskkill /F /IM electron.exe /T`) et redémarrage interactif via la tâche planifiée `LBG-Compagnon-Desktop` en Session 1.
      * Intégration de la petite danse idol (`fingerHeart`) dans les interactions spontanées de `main.js` (1 à 2 fois par heure) en complément de la boucle `vrm_pet.js`.
      * Vérification live : 5 processus Electron actifs en Session 1 (`sdesh`), hashes binaires vérifiés, 0 erreur.
  * **Déploiement live CT100 (`192.168.0.100:5174`) & Tests** :
    - Rebundle esbuild `vrm_pet.bundle.js` (2.2 MB).
    - Déploiement direct via `tools/deploy_to_ct100.sh` dans le conteneur `lbg-frontend` sur CT100 (tous les endpoints HTTP 200 vérifiés).
    - Tests de non-régression validés : CI Godot headless 100% verte (9s) et tests unitaires Cortex backend 100% verts (134 passés).
- **Assainissement Périmètre Atlas (Retrait définitif `.142` → `.143:5005` & Alignement Modèles Ollama sur `.140`)** :
  * **Diagnostic** : `packages/cortex/orchestrator/team/admin_infra_platform.py` et `/etc/lbg-ia-mmo.env` sur `.140` (ainsi que `packages/cortex/infra/secrets/lbg.env`) pointaient encore sur l'ex-CT détruit `.142:6001` (`hands_142`) et sur l'ancien modèle `qwen3.8:27b` (au lieu de `qwen2.5-coder-abliterate:14b` et `gemma-4-abliterated:12b-qat` / `E4b-qat`), provoquant de fausses alertes Slack `:danger: Atlas — périmètre LLM / runtime KO (5/6)`.
  * **Correctifs appliqués** :
    - `admin_infra_platform.py` & `test_admin_infra_platform.py` : périmètre Atlas aligné sur `110, 111, 140, 141, 143, 245, 246` (`hands_143` sur `192.168.0.143:5005/healthz`, avec garde-fou automatique contre tout résidu `.142:6001`).
    - `remote_targets.py`, `test_ssh_run.py`, `face_parts_workflow.py`, `ecosystem_grounding.py`, `router_prompts.py` : résolution `hands` / `omarchy` consolidée sur `192.168.0.143`.
    - `lbg.env` & `/etc/lbg-ia-mmo.env` (sur `.140`) : `LBG_AGENT_HANDS_URL` / `LBG_LAN_HOST_HANDS` / `LBG_DESKTOP_TARGETS` / `LBG_NETWORK_KNOWN_DEVICES` basculés sur `.143:5005`, et modèles alignés sur `huihui_ai/qwen2.5-coder-abliterate:14b` (code), `huihui_ai/gemma-4-abliterated:12b-qat` (PM/dialogue), `huihui_ai/gemma-4-abliterated:E4b-qat` (local/forge) et `qwen/qwen3.8-27b` (Groq fast).
  * **Validation live sur `.140`** : services `lbg-orchestrator` et `lbg-agent-dialogue` redémarrés ; audit Atlas `OK: True`, `hosts_ok: 6/6`, `perimeter_has_ko: False`, `0` écart bloquant Ollama/Groq, état d'alerte purgé (`perimeter_ok`).
- **Recadrage Fidèle de la Petite Danse « Mini Heart » & Posture K-Pop Idol (Image de Référence)** :
  * **Analyse des écarts visuels** : l'ancienne version présentait le bras droit levé trop haut au-dessus de l'oreille (`rightUpperArm` Z=0.62 au lieu de 1.05), le bras gauche ballant sans posture, les deux yeux plissés fermés en continu (`happy: 0.9` en VRM ferme les deux yeux en `^ ^`), la bouche grande ouverte comme un trou noir béant (`aa: 0.42`), et l'encart 3D défilait hors champ lors du scroll des boutons dans la fenêtre Compagnon.
  * **Alignement Posture & Doigts (Snap sur la Référence)** :
    - Bras droit : coude maintenu près des côtes/torse (`rightUpperArm: [0.38, 0.18, 1.05]`), avant-bras relevé vers le haut du buste/menton (`rightLowerArm: [0.10, 0.25, -1.80]`), main formant le mini-cœur coréen 🫰 (`rightHand: [0.18, -0.15, 0.22]`, pouce et index croisés, autres doigts repliés dans la paume).
    - Bras gauche : main posée avec style sur la hanche (`leftUpperArm: [0.18, -0.15, -0.92]`, `leftLowerArm: [0.08, 0.15, -1.05]`) pour une silhouette idol vivante et asymétrique.
    - Posture & Déhanché : hanches en appui contrapposto pop avec rebond souple des genoux au tempo ~105 BPM, tête penchée vers la main droite.
  * **Expression Espiègle Idol (« Tehepero » & Regard Vif)** :
    - Éradication de `happy` (0.0) : les deux yeux restent **grands ouverts** avec regard vif et brillant (`surprised: 0.12`).
    - Sourire éclatant avec dents : `relaxed: 0.75` (pommettes hautes, sourire chaleureux) + `ih: 0.32` (dents visibles) + `aa: 0.14` (lèvres entrouvertes naturelles, non béantes).
    - Clin d'œil joueur unilatéral : œil droit clignant en rythme toutes les 3,2 s (`blinkRight: 0.95`, `blinkLeft: 0` - l'œil gauche reste toujours grand ouvert et souriant).
  * **Particules de Cœurs** : projection dynamique émise depuis le bout des doigts au niveau du buste/menton montant vers la joue.
  * **Fix Interface Compagnon (`LyraPanel.vue`)** : ancrage fixe de la zone 3D `#lyra-face-host` en haut du panneau (séparée du conteneur défilant des boutons de poses/danses), évitant que l'avatar ne disparaisse lors du défilement des boutons.
  * **Déploiement Multi-Surfaces & Relance Session 1** :
    - Rebundle esbuild `vrm_pet.bundle.js` synchronisé dans `compagnon-desktop` et `compagnon_ui`.
    - Conteneur `lbg-frontend` rebuildé et redémarré sur CT100 (`:5174`).
    - Synchronisation sur Windows SDS `.10` et correction de la tâche `LBG-Compagnon-Desktop` pour appeler directement `electron.exe` (5 processus vérifiés en `SessionId: 1`).
- **Correctif Définitif Session 0 Windows `.10` (Auto-Watchdog Proactif & Fin des Interventions Manuelles au Reboot)** :
  * **Problème résolu** : À chaque reboot nocturne de Windows, `Agent_IA` démarrait en Session 0 (service/tâche système pré-login). L'utilisateur devait demander manuellement au Compagnon de réparer la Session 0 chaque matin, ce qui tombait parfois en timeout de 122s côté UI.
  * **Solutions pérennes déployées** :
    1. *Watchdog Autonome Proactif (`main.py`)* : ajout d'un thread d'arrière-plan `Session0Watchdog` qui sonde en continu `WTSGetActiveConsoleSessionId()`. Dès qu'un utilisateur se connecte sur la machine (session interactive > 0), le watchdog détecte la session console active et déclenche automatiquement `_run_fix_session0_task()` sans aucune intervention humaine ni commande du Compagnon.
    2. *Trigger Tâche Planifiée Accéléré (`install_fix_session0_task.ps1`)* : délai `AtLogOn` ramené de 45s (`PT45S`) à 5s (`PT5S`).
    3. *Auto-remédiation Compagnon Fiabilisée (`desktop_dispatch.py`)* : délai de lecture ramené de 120s à 30s lors de l'appel `fix_session0` avec passage immédiat en polling actif, éliminant les faux échecs `session0_auto_failed`.
    4. *Déploiement live sur SDS `.10:5005`* : `main.py`, `executor.py`, `install_fix_session0_task.ps1` et `fix_session0_admin.ps1` synchronisés et validés en session interactive (`SessionId: 1`, `session0_risk: false`, sha256 validé).
- **Correctif Définitif `vghd.exe - Qt5Sql.dll introuvable` & Tâche `AgentLocalV0` Session 0 (`Agent_IA` Windows `.10`)** :
  * **Réparation immédiate à distance** : déclenchement de `repair_app_deps` sur `.10:5005` -> `Qt5Sql.dll` et `sqldrivers/` restaurés dans `C:\Users\sdesh\AppData\Local\vghd\bin\`.
  * **Causes racines identifiées** :
    1. Un nouveau `updater.exe` avait été recréé à côté de `updater.exe.disabled_by_lbg`, et la condition `if ((Test-Path $updater) -and -not (Test-Path $disabled))` empêchait sa suppression/renommage.
    2. La tâche planifiée `AgentLocalV0` démarrait toujours `Agent_IA` en Session 0 au boot, faisant échouer `start_agent.ps1` à l'étape du port `:5005` avant même d'atteindre `repair_vghd_deps.ps1` (placé en fin de script).
  * **Correctifs appliqués** :
    - `repair_vghd_deps.ps1`, `backup_vghd_deps.ps1` et `_disable_vghd_updater()` dans `main.py` : suppression systématique de tout `updater.exe` recréé si `updater.exe.disabled_by_lbg` existe déjà.
    - `start_agent.ps1` : exécution de `repair_vghd_deps.ps1` tout en haut du script dès l'ouverture de session utilisateur (avant la vérification du port `:5005`).
    - `fix_session0_admin.ps1` : arrêt et désactivation de la tâche planifiée `AgentLocalV0` (`Disable-ScheduledTask`) en plus du service Windows, et appel immédiat de `repair_vghd_deps.ps1`.
    - Purge des caractères UTF-8 spéciaux (`—`) dans tous les `.ps1` de `Agent_IA` qui causaient `MissingEndCurlyBrace` sous PowerShell 5.1 Windows-1252.
    - `desktop_dispatch.py` (Compagnon CT100 `server_overlay`) & `desktop_apps.py` : ajout des verbes `relancer`/`relance`/`rouvrir`/`redémarrer`/`restart`/`relaunch`, prise en charge directe de `repair_app_deps` (« répare vghd »), nettoyage des pronoms/déterminants/ponctuation collée (`vghd?`, `VGHD.exe`, `-moi le programme vghd`) et repli sur les apps connues dans la phrase.
    - Validation live sur `.10:5005` : `listener_session_id: 1`, `self_session_id: 1`, `session0_risk: false`, tâche `AgentLocalV0` désactivée (`State: 1`), `Qt5Sql.dll` restauré et `updater.exe` supprimé.

- **Résilience Compagnon / Cortex — Tolérance aux Pannes LLM & Délégation Studio Sans Crash** :
  * **Secours Automatique Light 2B** : si le modèle d'analyse/chill (`gemma-4:E4b-qat` sur `.110`) échoue, est déchargé ou timeout, `LocalLLMProvider` retente immédiatement sur `huihui_ai/qwen3.5-abliterated:2B` sur `.111` avant tout abandon.
  * **Fallback Routing Global Fiabilisé** : mise à jour de la règle de fallback dans `routing.json` vers `qwen3.5:2B` (au lieu de reboucler sur `E4b-qat`).
  * **Éradication des Fuites de Dictionnaires d'Erreur dans le Chat** : garde-fou dans `llm_chat_phase.py` pour interdire l'affichage brut de `{'model_used': ..., 'error': True}` dans l'UI en cas de panne totale d'inférence.
  * **Synthèse de Plan de Secours pour Campus (`plan_submit.py`)** : si l'humain demande explicitement de soumettre un plan à la Team/Studio mais que l'inférence LLM cale, un plan de cadrage structuré est généré automatiquement afin d'assurer l'appel `POST /v1/pilot/team/campus/mission` sans bloquer le studio. Test unitaire dédié 100% PASS (9/9).
- **Résolution Incident Relance Compagnon (Verrou d'Instance Electron Session 0 sur SDS `.10`)** :
  * Processus Electron orphelins en Session 0 (service Windows SYSTEM) purgés (`taskkill /F /IM electron.exe`).
  * Mise en place de la tâche planifiée interactive Windows `LBG-Compagnon-Desktop` (`InteractiveToken`, utilisateur `sdesh`) et adaptation de `restart_desktop_overlay` dans `executor.py`.
  * Relance interactive validée avec succès sur le bureau et l'interface Web Compagnon.
- **Plan d'Évolutions Phase 2 — Livrables Tickets 2.1 & 4.1 Déployés & Validés** :
  * **Ticket 4.1 (Forge LLM — Banc d'Évaluation de Non-Refus Heretic)** :
    - Dataset de test canonique : `packages/cortex/knowledge/eval_prompts_dialogue.jsonl` (30 prompts de mise à l'épreuve couvrant contrebande, ferraille volée, dettes de jeu chez Jax, cartels, argot de bordure et ruses contre la milice de Zalem).
    - Moteur d'évaluation automatisé : `tools/eval_heretic_dialogue.py` (détection rigoureuse des refus moralisateurs, analyse des hallucinations de mutations d'inventaire/crédits, mesure de latence et rapport JSON).
    - Suite de tests unitaires : `packages/cortex/backend/tests/test_eval_heretic.py` (5/5 tests unitaires passants).
    - Validation locale : 30/30 prompts validés en mode benchmark mock, vérification Ruff 100% propre, 129/129 tests backend Cortex passants en 9.7s.
  * **Ticket 2.1 (O3 Joueurs IA — Contrat d'Environnement Universel & Découplage)** :
    - Contrat d'environnement abstrait : `packages/prime-hub/scripts/adapters/agent_environment_adapter.gd` définissant les types d'actions normalisées (`MOVE`, `SAY`, `EMOTE`, `INTERACT_POI`, `TRADE`, `CRAFT`, `IDLE`) et la structure universelle `AgentObservation` (espace, entités proches, POIs, événements, dials et inventaire).
    - Adaptateur concret Lost Heaven : `packages/prime-hub/scripts/adapters/godot_hub_adapter.gd` (résolution d'entités, perception spatiale 60m, exécution des actions avec simulation et émission des signaux).
    - Test unitaire & intégration headless : `packages/prime-hub/tools/agent_adapter_selftest.gd` (validation du contrat de base, de l'adaptateur mock pour la portabilité O3 hors Godot, et de l'intégration avec `HubSimScript`).
    - Intégration CI : ajouté dans `tools/ci_godot_headless.sh` — 6/6 tests headless Godot passants en 8s (<10s DoD).
  * **Ticket 2.2 (O3 Joueurs IA — Émergence Sociale : Propagation des Rumeurs Inter-Villages)** :
    - Buffer et mémoire de voyage dans `packages/prime-hub/scripts/hub_bot_autonomy.gd` (`_record_travel_observation`, `share_rumor_at_hub`) : les bots en patrouille à l'Avant-poste Zalem, au Ksar Nomade ou dans les Dunes orientales accumulent des faits contextuels réels.
    - Transfert social au hub : dès que le bot arrive à La Perle (Cantina), à la Plaza ou à l'Auberge, il transfère son souvenir vers le pool partagé `HubWiki` (`add_rumor()`, `get_rumors()`, `get_latest_rumor()`).
    - Dialogue PNJ dynamique (`hub_dialogue.gd`) : Jax et le Rumeuriste intègrent ces rumeurs fraîches lors des salutations ou questions de rumeurs/nouvelles, avec répliques ciblées par village (Zalem, Ksar).
    - Guide joueur et rendu Markdown (`hub_wiki.gd`) : section « Rumeurs & Échos des Caravanes » dans `_render_markdown` et champ `rumors` dans le snapshot `/v1/wiki`.
    - Test unitaire headless : `packages/prime-hub/tools/rumor_propagation_selftest.gd` validé à 100%, intégré dans la CI Godot (8/8 tests passants en 10s).
  * **Ticket 5.1 (Studio 3D — Projection Cognitive des Joueurs IA dans le Cerveau 3D)** :
    - API Backend événements cognitifs : routes `POST /v1/pilot/world/events` et `GET /v1/pilot/world/events` dans `packages/cortex/backend/api/v1/routes/pilot/status.py`, avec injection d'événements dans le snapshot `GET /v1/pilot/player-ia/runtime`.
    - Suite de tests unitaires : `packages/cortex/backend/tests/test_pilot_world_events.py` (135/135 tests backend Cortex passants).
    - Visualisation volumétrique Three.js (`team_brain.js`) : interrogation de la télémétrie des Joueurs IA, projection des micro-décisions vers le pôle *Perception Monde* (`injectInfraSignal("world", ...)`), illumination des anneaux d'action potentials et affichage des pensées synthétiques dans `#brain-activity-feed`.
  * **Ticket 3.1 (O2 Jeu — Mobilier Procédural & Vie Intérieure des Bâtiments CAO)** :
    - Modèle CAO vectoriel enrichi (`FurnitureSpec`, `FloorSpec.furniture`) dans `packages/cortex/services/building_cad/blueprint_model.py` et synchronisé dans `backend/services/building_cad/`.
    - Architecte procédural (`procedural_architect.py`) : ameublement complet de la Cantina « La Perle de Scrapaltai » (comptoir ferraille Jax, tabourets, tables d'alcôve, bureau, couchette, caisse de contrebande) et du Hangar Dépôt Nord (établi soudure lourde, bureau contremaître, racks de stockage).
    - Décomposition serveur Godot hub : `HubBlueprintBuilder.blueprint_to_furniture_anchors()` et ancrages de collision dans `HubCollision.furniture_anchors` (`drink`, `sit`, `rest`, `craft`, `inspect`, `loot`).
    - Cycles de vie Triplon (`hub_life.gd`) : snap automatique des PNJ vers les ancrages selon leur phase de vie (`drink`/`sit` en loisir, `rest` en couchette, `craft` à l'établi).
    - Rendu client 2.5D dans `packages/prime-client/scripts/hub_buildings_layer.gd` (`_draw_blueprint_furniture`) : comptoir avec liseré laiton, tables d'alcôve avec arcades, couchettes avec oreillers, établis lourd avec liseré cyan, bureaux avec mini-terminal, caisses avec renforts croisés X.
    - Tests & CI : `packages/prime-hub/tools/building_cad_selftest.gd` validé à 100%, 6/6 tests headless Godot passants en 7s.
  * **Ticket 1.1 (O1 Compagnon — Interaction Vocale Mains-Libres Voice-In / STT)** :
    - Service et API Backend STT : `packages/cortex/backend/services/stt_service.py` et routes `GET /v1/stt`, `POST /v1/stt` dans `api/v1/routes/stt.py` (détection amont Whisper OpenAI-compatible sur `.111`, mode mock, recommandation client Web Speech API).
    - Tests unitaires backend : `packages/cortex/backend/tests/test_stt.py` (5/5 tests passants, 134/134 tests backend Cortex passants en 9.7s).
    - Bibliothèque STT frontend : `packages/cortex/compagnon_ui/src/lib/stt.js` et tests `stt.test.js` (contrôleur `createVoiceInputController`, formatage et ponctuation automatique `cleanTranscript`, 71/71 tests JS passants).
    - Interface utilisateur `ChatInput.vue` : bouton microphone avec retour visuel réactif (repos, écoute pulsée avec halo rose `animate-pulse`, transcription injectée directement dans la zone de texte).
    - Push-to-Talk Desktop (`compagnon-desktop`) : raccourci global configurable `CommandOrControl+Shift+Space` dans `main.js`, pont IPC `compagnon:voice-toggle` dans `preload.js` déclenchant la saisie vocale et la posture `listening` de l'avatar.
    - Conformité & Lint : `ruff check .` 100% propre sans avertissement.
  * **Ticket 1.2 (O1 Compagnon — Conscience Contextuelle de l'Espace de Travail / Focus Awareness)** :
    - Catégorisation intelligente de l'activité utilisateur (`packages/compagnon-desktop/desktop_targets.js`) : mapping des fenêtres de premier plan vers des ambiances de posture et d'état du compagnon (`coding`/`think`, `gamedev`/`curious`, `terminal`/`alert`, `gaming`/`cheer`, `browsing`/`serene`, `idle`/`relax`).
    - Suite de tests unitaires : `packages/compagnon-desktop/test/focus_awareness.test.js` (6/6 tests passants).
    - Boucle de polling et API IPC Electron : `pollFocusAwareness()`, `startFocusAwareness()` et canal IPC `compagnon:get-focus-context` dans `main.js`, exposé via `preload.js`.
    - Capacité agent local Windows `.10` : action `get_active_window_context` ajoutée dans `packages/cortex/windows_agent/Agent_IA/executor.py` avec `GetForegroundWindow` / `GetWindowTextW`.
    - Module d'état réactif frontend : `packages/cortex/compagnon_ui/src/lib/focusContext.js` et tests `focusContext.test.js` (73/73 tests unitaires passants).
  * **Ticket 3.2 (O2 Jeu — Météo Dynamique : Tempête de Sable sur Scrapaltai & Repli Bâtiments)** :
    - Définition d'événement MMO : `packages/prime-hub/data/events/event_lh_sandstorm.json` (durée d'alerte 180s, durée tempête 900s, accalmie 120s, rayon 1800m).
    - Machine d'état météo serveur Godot : cycle complet dans `packages/prime-hub/scripts/hub_events.gd` (`calm` → `warning` → `storm` → `clearing`), calcul de l'intensité et du flag `weather_shelter_required`.
    - Autonomie des Joueurs IA (`HubBotAutonomy.assign_goal` dans `hub_bot_autonomy.gd`) : dès l'alerte tempête (`is_weather_shelter_active()`), les bots interrompent toute exploration/chasse/patrouille pour se replier vers l'intérieur du bâtiment abrité le plus proche (`cantina`, `inn`, `hall`, `craft`, `clinic`).
    - Intégration simulation & diffusion réseau : synchronisation dans `HubSim._step_bot` et diffusion du bloc `weather` dans le payload `zone_state` (`hub_sim_views.gd`).
    - Test headless & Intégration CI : `packages/prime-hub/tools/weather_storm_selftest.gd` créé et validé, intégré dans `tools/ci_godot_headless.sh` (7/7 tests headless Godot passants en 10s, <10s DoD).

**2026-10-30** :
- **Ajustement Morphologie & Cadrage Encart Buste (Fenêtre Compagnon)** :
  * **Échelle de la tête ramenée à 1.0 (taille naturelle)** : passage de 1.15 à 1.0 dans `updateHeadScale()` pour des proportions parfaitement naturelles et élancées avec le corps mecha.
  * **Cadrage Buste Aéré & Non Tronqué** : recul caméra (`dist = 1.30` au lieu de `1.12`) et visée centrée légèrement plus bas (`lookY = headPos.y - 0.02`), garantissant une marge généreuse au-dessus de la chevelure (zéro coupure en haut) tout en montrant le cou, les épaulières et le buste dans l'encart 220px.
- **Correction Bug Œil Bloqué / Fermé (Bureau & Web)** :
  * **Identification de la cause racine** : lors du clin d'œil de l'animation `fingerHeart`, `em.setValue("blinkRight", winkVal)` n'était jamais remis à 0 à la sortie de la pose, et `setExpressionWeights` ne réinitialisait pas les canaux de clignements unilatéraux.
  * **Correctif appliqué** : ajout de `blinkRight` et `blinkLeft` dans le reset universel de `setExpressionWeights()`, remise à zéro explicite de `blinkRight = 0` dès que la pose se termine ou revient en `idle`.
- **Petite Danse Idol « Finger Heart » K-Pop Bouncy & Rythmée (1 à 2 fois par heure)** :
  * **Chorégraphie Pop Complète (8,5 s)** : rebond vertical au tempo (`danceBounce`), déhanché fluide (`swayHips`, `rollHips`), flexion souple des genoux (`kneeBounce`), tête dodelinante en rythme, bras gauche ondulant avec la hanche et bras droit formant le Mini Heart avec pulsation cardiaque et cyber-cœurs roses. Clin d'œil joueur en rythme qui se réouvre parfaitement.
  * **Cadence & Vérification Immédiate** : intervalle programmé toutes les ~25 à 35 minutes (`t + 1500s + Math.random() * 600s`), avec un 1er passage test à 25 secondes après le chargement pour vérification visuelle immédiate.
  * **Bouton dédié dans l'UI** : ajout de `💖 Mini Heart` dans la grille du Pack Danses de `LyraPanel.vue` pour déclenchement à la demande.
- **Déploiement Synchronisé Multi-surfaces** :
  * Bundle `vrm_pet.bundle.js` recompilé (`finger_heart_v6`).
  * Déployé sur **CT100** (`lbg-frontend`) avec patch du bundle et du bouton dans `index.js`.
  * Synchronisé sur Windows SDS `.10` (secours HTTP LAN port 5174 intégré dans `sync_vrm_desktop` si `A:` non monté) et overlay Electron redémarré (PID 8880).

**2026-10-28** :
- **Spécification & Runbook de Forge LLM Décensurée (Dialogue PNJ MMO & Compagnon)** :
  * **Inspiration & Source de Veille** : analyse de la vidéo TikTok @madameb0nplan introduisant l'outil open-source [Heretic](https://github.com/p-e-w/heretic) (`p-e-w/heretic`) pour l'ablation directionnelle (décensure chirurgicale) automatique par Optuna/TPE.
  * **Document de référence rédigé** : [`packages/cortex/docs/forge_modeles_dialogue_pnj_compagnon.md`](../packages/cortex/docs/forge_modeles_dialogue_pnj_compagnon.md) (et indexé dans [`docs/REGISTRE.md`](REGISTRE.md)).
  * **Runbook opérationnel complet** :
    - Matrice de sélection : modèles compacts (Qwen 0.8B/2B) pour les foules et l'interactif rapide sur `.111`, modèles intermédiaires (7B/9B/E4B) pour quêtes MMO et Compagnon chill, modèles lourds (14B) pour le code et l'atelier sur `.110`.
    - Station de forge : utilisation des environnements GPU (Colab T4 / A100 éphémère ou SDS Windows `.10` 1050 Ti avec `--quantization bnb_4bit`) sans impacter les nœuds CPU de prod `.110`/`.111`.
    - Pipeline 6 étapes : `heretic` (co-minimisation des refus et de la divergence KL) → conversion GGUF (`convert_hf_to_gguf.py`) → quantisation `Q4_K_M` → Modelfile Ollama custom (stop tokens, system prompt sans refus, `think false`) → push LAN → déclaration dans `reason_route_matrix()`.
    - Rappel strict des règles `OBJECTIVES.md` : aucune mutation dure en LLM libre (l'économie, l'inventaire et les combats restent sous l'autorité absolue du Godot Hub `.246:8787`).

**2026-10-27** :
- **Animation Spontanée « Finger Heart » K-Pop & Particules Cyber-Cœurs (1 à 2 fois par heure)** :
  * **Pose Corporelle & Doigts Articulés** (`POSE_EULERS.fingerHeart`) :
    - Squelette des doigts étendu dans `BONE_NAMES` (`rightThumb*`, `rightIndex*`, `rightMiddle*`, etc.).
    - Pouce et index droits croisés en mini cœur près de la joue/menton (`rightHand: [0.15, -0.22, 0.22]`, coude fléchi `rightLowerArm: [-0.42, -0.35, -1.92]`), les 3 autres doigts repliés dans la paume.
    - Buste cambré, hanches féminines et tête penchée espiègle vers l'épaule (`head: [-0.05, -0.08, 0.22]`).
  * **Micro-animation & Expression « Tehepero »** :
    - Pulsation battement de cœur organique du geste (`heartPulse`) et micro-balancement de tête (`headSway`).
    - Expression coquine avec grand sourire bouche ouverte montrant les dents/langue (`happy: 0.90`, `aa: 0.42`) et clin d'œil malicieux périodique (`blinkRight`).
  * **Effet Cyberpunk Visuel** : émission de 3 sprites de mini-cœurs néon roses luminescents (`#ff2a8d`, rendu additif `AdditiveBlending`) flottant doucement vers le haut au-dessus des doigts.
  * **Déclenchement Autonome Périodique (sans bouton)** : intervalle programmé entre 30 et 45 minutes (`t + 1800s + Math.random() * 900s`), soit exactement 1 à 2 fois par heure (avec un premier essai à ~75s après chargement pour validation visuelle immédiate).
  * **Déploiement synchronisé** : bundle `vrm_pet.bundle.js` recompilé (`finger_heart_v5`), déployé sur CT100 (`lbg-frontend`) et synchronisé sur Windows SDS `.10` (`sync_vrm_desktop` + restart overlay).
- **Intégration & Promotion de Qwen2.5-Coder-14B Abliterated (Rôle Code Studio & Claude Code)** :
  * **Téléchargement & Validation Ollama .110** : installation réussie de `huihui_ai/qwen2.5-coder-abliterate:14b` (Q4_K_M, 9.0 Go, décensuré) sur `.110`. Smoke test validé en ~2.8 tok/s sur CPU Xeon.
  * **Promotion Rôle Code Studio (Cortex / Pilot)** :
    - `packages/cortex/orchestrator/team/reason_llm.py` : `CODE_REASON_DEFAULT = "huihui_ai/qwen2.5-coder-abliterate:14b"`, assigné au profil `"code"` (`LBG_REASON_MODEL_CODE`).
    - `packages/cortex/compagnon_ui/server_overlay/ollama_audit.py` & orchestrateur : rôle `reason_code` configuré par défaut sur `qwen2.5-coder-abliterate:14b`.
    - `packages/cortex/compagnon_ui/server_overlay/routing.json` : promotion en tête des modèles de raisonnement technique (`technical_reasoning`).
    - Matrice canonique mise à jour dans `.agents/rules/local-llm-route-matrix.md` et `docs/local_llm_route_matrix.md`.
  * **Configuration Claude Code** : mise à jour de `~/.claude/settings.json` avec `model: "huihui_ai/qwen2.5-coder-abliterate:14b"`, `ANTHROPIC_DEFAULT_SONNET_MODEL` et `OPUS` pointés sur `14b`.
- **Ajustement de la Morphologie (Échelle Tête 1.15) & Recentrage Cadrage Buste (Web & Desktop)** :
  * **Échelle de la tête réduite à 1.15** (`updateHeadScale`) : passage de 1.28 à 1.15 pour affiner le port de tête, éliminer l'effet bobblehead excessif et rétablir des proportions élancées et harmonieuses avec le corps mecha sur les deux environnements (fenêtre Compagnon et pet bureau).
  * **Recentrage vertical de la tête dans la fenêtre Compagnon** (`framing === 'bust'`) : visée repositionnée au niveau du pont du nez / yeux (`lookY = headPos.y + 0.015`, `dist = 1.12`) pour centrer parfaitement le visage dans le cadre avec une marge aérée au-dessus des cheveux, tout en dévoilant le cou, les épaulières mecha et le haut du buste.
  * **Déploiement synchronisé** : bundle `vrm_pet.bundle.js` recompilé (`head_scale_v4`), déployé sur CT100 (`lbg-frontend`) et synchronisé sur Windows SDS `.10` avec redémarrage de l'overlay Electron.
- **Intégration du Cerveau 3D & Réseau Synaptique (Option 1 — Inspiration TikTok @ccodelabfr)** :
  * **Contexte & Inspiration** : Transposition de l'univers 3D de @ccodelabfr (*« J'ai donné un cerveau à mon IA 🧠⚡ »*) pour doter le Studio d'une représentation volumétrique vivante de la conscience et des mémoires de l'IA.
  * **Moteur 3D procédural Three.js WebGL autonome** ([`brain_3d/brain_3d.js`](../packages/cortex/pilot_web/brain_3d/brain_3d.js), 0 asset binaire externe) :
    - Double hémisphère anatomique avec scissure centrale, gyri et sulci ondulants, tronc cérébral et cervelet.
    - ~1500 particules neuronales luminescentes aux couleurs thématiques (cyan/cobalt pour la logique et la simulation, or/magenta/rose pour le RAG, l'émotion et Lyra).
    - Réseau synaptique d'axones interconnectés (`LineSegments` additifs) avec train d'impulsions lumineuses circulant en temps réel.
  * **6 Pôles Cognitifs Interactifs cliquables avec anneaux de données orbitaux** :
    - ⚡ *Cortex Frontal* : Orchestrateur & Planification des intentions (`intent: monitor / chat / jobs`).
    - 💖 *Système Limbique* : Homéostasie et humeur en direct (`confidence`, `curiosity`, `stress`, `fatigue`).
    - 📚 *Hippocampe & RAG* : Corpus philosophique Mec Chill / Stoïcisme et grounding d'atelier.
    - 🤖 *Noyau Campus & Fleet* : Supervision des agents spécialisés de la Team.
    - 🌐 *Perception Monde* : Simulation Godot Prime `.246:8787` et signaux du monde.
    - 🎭 *Lobe Compagnon* : Lyra Desktop Pet SDS `.10` et posture d'incarnation.
  * **HUD Cybernétique & Télémétrie en direct** ([`src/modules/team_brain.js`](../packages/cortex/pilot_web/src/modules/team_brain.js) & [`brain_3d/brain_3d.css`](../packages/cortex/pilot_web/brain_3d/brain_3d.css)) :
    - Polling régulier de `GET /v1/pilot/orchestrator/brain/status` avec jauges animées et boîte de flux de conscience (« narrative »).
    - Raycasting Three.js au survol avec tooltips HUD dynamiques projetées en 2D.
    - Clic sur un pôle avec focus caméra fluide (lerp) et inspection de sa fiche détaillée.
    - Bouton *⚡ Impulsion Synaptique* déclenchant une décharge visuelle d'ondes à travers tout le cerveau.
    - Filtres d'affichage par hémisphère (*Vue globale*, *Hémisphère Analytique*, *Hémisphère RAG & Humeur*).
    - Bouton de bascule Veille / Éveil connecté à `/v1/pilot/orchestrator/brain/toggle`.
  * **V2 Hyper-Dynamique & Télémétrie Cérébrale Infra en Temps Réel** :
    - Réponse au retour utilisateur sur le manque d'activité : transformation de la scène statique en un véritable réseau cérébral effervescent reflétant en continu l'activité des VMs et des agents IA.
    - **300 Influx Synaptiques Vifs 3D (Action Potentials / Sparks)** : particules or et cyan circulant à grande vitesse le long des axones avec redistribution continue.
    - **Arcs Électriques Crépitants (Neural Lightning)** : décharges fractales entre les pôles majeurs avec crépitement électrique dynamique.
    - **Ondes Cérébrales EEG (Gamma 36–54 Hz)** : modulation volumétrique de la luminosité sur l'ensemble des 1500 neurones du cortex.
    - **Connexion Télémétrique Directe aux Serveurs & Agents de l'Infra** :
      * Sondage en temps réel de `/v1/pilot/status` (santé Core .140, Orchestrateur, LLM .110, Hub Godot .246) et `/v1/pilot/team/fleet` (les 7 agents).
      * **Flux d'Activité Cérébrale & Signaux Infra Live** (`#brain-activity-feed`) : affichage horodaté des cycles de contrôle, cœurs LLM, ticks Godot Hub et veille cognitive des agents.
      * À chaque signal reçu, le pôle concerné s'illumine (halo x2, rotation accélérée) et projette une décharge d'influx à travers le cerveau.
    - **HUD Télémétrique Enrichi** : affichage en direct de la fréquence EEG (Hz), du débit d'influx synaptiques/s et des puces de statut des 4 nœuds d'infrastructure.
    - **Bouton « 🔥 Surcharge Cognitive »** (`#brain-btn-surge`) : stimulation immédiate à x3.2 pour tester les décharges maximales du cerveau.
    - Fichiers mis à jour et synchronisés : `brain_3d/brain_3d.js`, `src/modules/team_brain.js`, `index.html` (cache buster v3), `brain_3d.css`, et bundles `dist/`.
- **Assainissement Qualité, Lint & Validation CI Locale (2026-10-27)** :
  * `packages/compagnon-desktop/scripts/bundle-vrm.py` : correction de l'import multi-lignes pour conformité Ruff E401 (`ruff check .` 100% vert).
  * `packages/cortex/backend/tests/test_bridge_sidecar_runtime.py` : injection de `m10_craft_stub` dans `sys.path` pour importer proprement `hunt_yard_bridge`.
  * **Tests Cortex Backend** : 124/124 tests passants en 10.6s (`pytest backend/tests`).
  * **Tests Headless Godot (Jeu)** : 5/5 tests passants en 7s (`ci_godot_headless.sh` — HubSim, Navigation 3D, Bâtiments CAO & Portes découpées, SQLite WAL, Client Prime modulaire & DnD).

**2026-10-26** :
- **Rééquilibrage des Proportions Tête & Cadrage Buste 3D (Web CT100 & Desktop .10)** :
  * **Diagnostic du décalage Buste vs Corps** :
    - L'échelle de tête était fixée statiquement à `1.68` (+68% Chibi), et le cadrage buste (`framing === 'bust'`) visait directement les yeux à courte distance (`dist = 1.15`, FOV 25°), ce qui écrasait le champ de vision, masquait la poitrine et les épaules, et produisait un effet de tête énorme en gros plan.
    - À l'inverse, en vue corps entier (en pied sur le bureau Windows), la grande silhouette élancée avec de longues jambes donnait l'impression d'une tête menue par comparaison.
  * **Harmonisation dynamique (`updateHeadScale`)** :
    - En **vue buste** : échelle ajustée à `1.15` pour un port de tête fin, naturel et parfaitement proportionné aux épaules et au décolleté mecha.
    - En **vue corps entier** : échelle calée à `1.28` pour offrir une présence visuelle harmonieuse sans paraître trop petite face au reste du corps.
    - Cadrage caméra portrait/buste recentré sur le haut du sternum (`headPos.y - 0.20`, distance `1.38m`, FOV 24°) : dégage les épaules mecha, la poitrine et les bras dans les 60% inférieurs tout en maintenant la tête avec de l'air dans les 40% supérieurs.
  * **Rebundle & Déploiement multi-surfaces** :
    - Recompilation esbuild de `vrm_pet.bundle.js` (2.1 MB) avec cache-buster `?v=head_balance_v1` dans `LyraPanel.vue`.
    - Déploiement validé sur CT100 (`192.168.0.100:5174`, injection dans `lbg-frontend:/usr/share/nginx/html/vrm/` et mise à jour de `index-CNZnjJ_B.js`).
    - Synchronisation locale via `sync_vrm_desktop` et redémarrage de l'overlay Electron sur Windows `.10` (PID 4880).
- **Intégration Vue Campus Pixel Art « Bureau des Agents » (Option B — Inspiration TikTok @alexisdubain.ai)** :
  * Habillage complet de la carte interactive du campus (`packages/cortex/pilot_web/office_map/office_map.js`) inspiré du projet *Bureau des Agents* / *VibesMoney* :
    - Rendu 100% procédural Canvas 2D (autonome, aucun asset binaire externe manquant).
    - Robots cubiques animés avec visière sombre, yeux dorés luminescents et carrosserie aux couleurs du rôle (Chef violet, Infra vert/titane, Front cyan, LLM ambre/or, Prime saphir, Pont rose out-game, Lyra cyan androïde).
    - Bureaux individuels avec plateau bois, ordinateur portable, reflets d'écran allumés, clavier et tasse de café.
    - Props décoratifs par zone : racks serveurs aux LEDs animées Core/LLM, machine à espresso au Café, borne d'arcade rétro dans la Salle de jeux.
    - Animations dynamiques en temps réel : frappe effrénée au clavier (`typing`) en statut `busy`, respiration douce en `idle`, alerte lumineuse en `review`, et marche animée (`walk1`/`walk2`) lors des déplacements inter-zones.
    - Bulles de pensée/action affichant la tâche en cours au-dessus de chaque agent.
  * Déploiement et validation en direct sur `192.168.0.140:8080` (fichiers `/opt/LBG_IA_MMO/pilot_web/office_map/office_map.js` et `/opt/LBG_IA_MMO/pilot_web/dist/`).
  * Accessible immédiatement dans le Pilot via l'URL : `http://192.168.0.140:8080/#/team/office?view=map`.
- **Intégration Danses Mocap VRMA Haute Fidélité & Cadrage Dynamique** :
  * Mise en place du pipeline de conversion Mixamo FBX vers le standard officiel VRMA 1.0 (`@pixiv/three-vrm-animation`, 52 os avec translation et rotation du bassin).
  * Génération et intégration de 2 animations mocap complètes de haute fidélité :
    - `samba.vrma` / `dance.vrma` : Danse festive latino / samba / salsa (18.16s, déhanché, balancement des bras, fluidité complète).
    - `hiphop.vrma` : Danse hip-hop / street bounce (15.33s, cadence rythmée, rebond athlétique, attitudes et gestes de mains).
  * Mise à jour de `VRMA_MAP` et de `setPose()` dans `vrm_pet.js` pour jouer directement les clips mocap VRMA natifs sans interruption ni fallback procédural forcé.
  * Neutralisation des faux rebonds verticaux parasites dans `vrm.scene.position.y` lorsque la mocap VRMA est active (préservation du root motion natif).
  * Rebundle esbuild (`vrm_pet.bundle.js` 2.1 MB) et déploiement immédiat dans `compagnon-desktop` et `compagnon_ui/public/vrm/`.
  * Déploiement live validé sur CT100 (`192.168.0.100:5174`, injection dans `lbg-frontend`, HTTP 200 vérifié sur `/vrm/animations/samba.vrma`, `hiphop.vrma`, `dance.vrma`).
  * Ajout des déclencheurs directs dans le menu Tray de `compagnon-desktop/main.js`.
- **Intégration du Compagnon « Mec Chill » (MC) & Corpus Philosophique RAG (Modèle E4b-qat sur .110)** :
  * **Inspiration TikTok (@justeunmecchill123)** : Transposition de l'IA « MC » (Mec Chill) pour ancrer le compagnon dans un corpus philosophique solide et une personnalité flegmatique, sage et détendue.
  * **Corpus RAG philosophique dédié** (`packages/cortex/knowledge/philo_corpus.jsonl`) : 18 fragments structurés couvrant le Stoïcisme (Épictète, Marc Aurèle, Sénèque), le Bouddhisme/Taoïsme (impermanence, lâcher-prise, Wu Wei), le Rationalisme serein (Descartes, Spinoza), le Transcendantalisme (Emerson) et la sagesse d'atelier (résolution calme des bugs/pannes, anti-panique, gestion des trolls).
  * **Ingestion RAG enrichie** : extension de `load_knowledge_snippets()` dans `orchestrator/services/rag/ingest.py` pour indexer `philo_corpus.jsonl` et `rag_facts.jsonl`.
  * **Profil système Mec Chill** dans `compagnon_ui/server_overlay/router_prompts.py` (`mec_chill`, `chill`, `philo`) : posture calme, bienveillante et flegmatique, dichotomie du contrôle, esprit complice face aux aléas techniques du studio.
  * **Routage modèle dédié sur .110** : configuration automatique de `huihui_ai/gemma-4-abliterated:E4b-qat` sur l'hôte heavy `.110` (`LAB_CHILL_MODEL_DEFAULT = "huihui_ai/gemma-4-abliterated:E4b-qat"`, tier heavy, profile chill) dans `router_prompts.py`, `llm_chat_phase.py` et la matrice canonique `reason_route_matrix()`.
  * **Déclenchement RAG continu** dans `rag_grounding.py` et `llm_chat_phase.py` : injection du contexte philosophique dès que le profil chill est actif ou lors d'échanges sur la sérénité/philosophie en causerie.
- **Génération & Modélisation CAO de Bâtiments Lost Heaven (Inspiration CADCraft + Claude)** :
  * **Inspiration TikTok (@luis.cardenas.c / CADCraft + Claude)** : Adoption de l'approche CAO vectorielle et paramétrique (plutôt que maillage 3D polygonal brut sans intérieur) pour concevoir des bâtiments cohérents, praticables et rigoureusement cotés pour le MMO.
  * **Spécification & Module Studio CAO** (`packages/cortex/services/building_cad/`) :
    - `blueprint_model.py` : modèle de données complet (empreinte au sol, étages, cloisons, portes, fenêtres, pièces praticables, matériaux, export legacy).
    - `procedural_architect.py` : algorithmes de tracé architectural (murs porteurs, fenêtres régulières, subdivision de pièces, corridors de dégagement).
    - `lost_heaven_presets.py` & `blueprint_exporter.py` : catalogue d'archétypes (Cantina « La Perle de Scrapaltai », Hangar Docks & Ferraille) et pipeline d'export d'assets.
    - CLI d'exportation : `packages/prime-client/tools/procedural_building/generate_blueprints.py`.
  * **Compilateur de Collision & Découpe de Portes (`prime-hub`)** :
    - Création de `packages/prime-hub/scripts/hub_blueprint_builder.gd` : décompose les murs en segments AABB individuels et découpe physiquement les ouvertures de portes pour laisser le passage totalement libre aux joueurs et PNJ dans la simulation headless.
    - Extension de `packages/prime-hub/scripts/hub_collision.gd` : résolution automatique de `cad_blueprint_ref` et intégration native des pièces intérieures navigables sans altérer les collisions historiques AABB.
  * **Rendu Vectoriel des Pièces & Cloisons (`prime-client`)** :
    - Mise à niveau de `packages/prime-client/scripts/hub_buildings_layer.gd` : cache de blueprints, traçage des cloisons intérieures et découpes de portes en 2.5D projetée (`Projection3D2D`).
    - Blueprints canoniques instanciés : `packages/prime-client/assets/maps/blueprints/poi_lost_heaven_cantina.json` et `poi_lost_heaven_warehouse_dock.json`, liés dans `lost_heaven_buildings.json`.
  * **Validation & CI Headless** :
    - Test unitaire complet Python : `packages/cortex/backend/tests/test_building_cad.py` (roundtrip JSON, génération procédurale cantina/hangar, export).
    - Self-test headless Godot : `packages/prime-hub/tools/building_cad_selftest.gd` (validation du passage libre à travers la porte et du blocage par les murs).
    - Intégration dans `tools/ci_godot_headless.sh`.
    - Documentation d'architecture complète : [`docs/architecture/BUILDING_CAD_GENERATOR.md`](../docs/architecture/BUILDING_CAD_GENERATOR.md).
- **Nettoyage Inventaire Ollama & Migration Routage (12b-qat & E4b-qat)** :
  * **Suppression `e2b` sur .110 et .111** : retrait de `huihui_ai/gemma-4-abliterated:e2b` via l'API Ollama DELETE sur les deux hôtes (libération de ~13.3 Go de RAM/disque).
  * **Redirection canonique `12b` -> `12b-qat`** : aliasing vérifié sur `.110` (même digest SHA256) et synchronisation via l'API `copy`.
  * **Bascule du code vers `E4b-qat` et `12b-qat`** :
    - `packages/cortex/orchestrator/team/reason_llm.py` : `FORGE_REASON_DEFAULT = "huihui_ai/gemma-4-abliterated:E4b-qat"`.
    - `packages/cortex/compagnon_ui/server_overlay/router_prompts.py` : `LAB_CHAT_QUALITY_MODEL_DEFAULT = "huihui_ai/gemma-4-abliterated:E4b-qat"`.
    - `packages/cortex/compagnon_ui/server_overlay/routing.json` : suppression de l'ancien `e2b` et déduplication `12b`.
    - `packages/cortex/compagnon_ui/server_overlay/ollama_audit.py` & orchestrator : mise à jour des rôles `reason_forge`, `reason_default` et `jobs_planner` vers `E4b-qat`.
    - `packages/prime-hub/scripts/hub_dialogue.gd` : fallback dialogue Godot pointé sur `E4b-qat`.
    - `~/.claude/settings.json` : Claude Code configuré avec `model: E4b-qat`, Sonnet: `12b-qat`, Opus/Haiku: `E4b-qat`.
    - Canon mis à jour dans `.agents/rules/local-llm-route-matrix.md` et `packages/cortex/docs/local_llm_route_matrix.md`.
- **Durcissement Cycle de Vie & Fuites Mémoire WebGL (`vrm_pet.js`)** :
  * **Libération VRAM GPU (`destroy`)** : appel de `VRMUtils.deepDispose(vrm.scene)` et `renderer.forceContextLoss()`.
  * **Purge des Textures Dynamiques** : enregistrement et `tex.dispose()` de toutes les textures procédurales et chargées par `applyAndroidTheme`.
  * **Désallocation Animation & Mixers** : arrêt `mixer.stopAllAction()`, `mixer.uncacheRoot(vrm.scene)`, `vrmaClips.clear()`, et `cancelAnimationFrame(animId)`.
  * **Optimisation de la Boucle de Rendu** : élimination des 3 `try/catch` silencieux par frame (60 FPS) remplacés par des vérifications directes de type/existence.
  * **Sécurisation Asynchrone** : vérification de disponibilité de `vrm` dans `loadVRMA` et ajout d'un `.catch(...)` pour éviter les `UnhandledPromiseRejection`.
  * **Recompilation & Déploiement** : recompilation esbuild `vrm_pet.bundle.js` (2.1 MB) et réplication immédiate dans `packages/cortex/compagnon_ui/public/vrm/`.

**2026-10-23** :
- **Restauration Canal Ops Slack (#lbg-ops)** :
  * Diagnostic de la perte des notifications depuis le 14/10 à 13:09 suite à écrasement de `/etc/lbg-ia-mmo.env` sur `.140`.
  * Restauration des variables `LBG_SLACK_WEBHOOK_OPS`, `LBG_SLACK_BOT_TOKEN`, `LBG_SLACK_APP_TOKEN`, `LBG_SLACK_CHANNEL_OPS` depuis le backup `.bak.20261005084818`.
  * Redémarrage et validation opérationnelle de `lbg-slack-hitl-poll.service` et message de test émis avec succès (status 200).
- **Auto-diagnostic NAS & Prévention saturation Proxmox** :
  * Détection panne matérielle / réseau du NAS Synology DS1815+ (`192.168.0.51`) : 100% loss, absent table L2 Freebox OS.
  * Identification du risque critique Proxmox : iSCSI déconnecté sur `.201`, bascule de `/mnt/pve/nas-lun-backup` sur `/dev/mapper/pve-root` (suspension des `vzdump` nécessaire).
- **Apprentissage et outillage Compagnon / Studio** :
  * Script canonique d'auto-diagnostic créé : [`tools/diag_nas_and_slack.sh`](../tools/diag_nas_and_slack.sh) (Freebox L2, NAS, iSCSI/Proxmox, Slack, surfaces LAN).
  * Ancrage écosystème enrichi dans `router_prompts.py` (`_OPS_TRUTH`), `ecosystem_grounding.py` (faits + hints), `infra_lan_intent.py` (regex NAS/iSCSI/Slack) et `studio_brain_v1.json` (leçons & faits).
  * 35/35 tests passants et déploiement atomique live sur CT100 (`192.168.0.100:5174`, version `1.0.0+c14a10f`).
- **Pack danses VRM Desktop & Web** : assainissement `vrm_pet.js`, élimination des requêtes VRMA fantômes (HTML SPA), `stopVRMA(0)` synchrone, cinématiques procédurales des danses à 60 FPS, rebundle esbuild déployé sur Windows SDS `.10` et CT100 `lbg-frontend`.
- **Routage Compagnon & barrière anti-déraillement** :
  * Élimination du déraillement absurde vers `AI · TOOL_LOOP` (Diagnostic cockpit) sur les confirmations courtes (« c'est bien ça. », « ok faity », « vas-y », etc.) via `_CONFIRMATION_RE` (confiance 0.98), rétrogradation automatique de toute hallucination `tools` du SLM sans mot-clé explicite de diagnostic, et neutralisation de la relance mémoire dans `_contextual_followup`.
  * Suppression de l'injection artificielle `Réponds uniquement en français. Voici ma question : ` dans `llm_chat_phase.py` qui incitait le modèle à répéter bêtement les consignes système (« Je prends note de la consigne... »).
  * Recadrage anti-bluff sur les sites web et services distants dans `_OPS_TRUTH` (pas de fausse prétention de gestion de prod magique sans code source/repo/accès) et directive de compréhension du français familier (« fais-y », « ok faity »).
  * 16/16 tests passants dans `test_reflection_router.py` et déploiement live validé sur CT100 (`192.168.0.100:5174`).

## Snapshot priorités (voir détail dans PRIORITES_ACTUELLES)

| Rail | État |
|------|------|
| **O1 Compagnon** | D0–D6 OK ; D8 avatar bridge **live sur .10** ; routage causerie & anti-divagation **déployé sur CT100** |
| **O1 ops** | Lot gaps A–F2 + tick L3 livré 2026-10-07 ; L3 **DONE** `days_ok=3/3` (2026-10-11) ; métriques 7j Fleet **OK** |
| **O2 hub** | P6 Godot-first G5+ **live** (`.246:8787`) ; P3 wiki live ; P5 telegraph boss **vert** 2026-10-08 ; zone entraînement B1–B4 OK |
| **O3 Joueurs IA** | Pont `*_bridge` + dials OK ; noyau découplé / adapters = **cible** |
| **Interdit** | Core3 / gateway SOE / `hub_runtime` Python sur chemin joueur |

## Prochaines actions (à ajuster en fin de session)

Backlog explicite : [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md) (mis à jour 2026-10-13 post O-VEIL-4 / O-OPS-2 DONE).

1. **Plan d'évolutions (10/10 tickets)** : **100 % réalisé & clôturé** (tickets 1.1..1.3, 2.1..2.3, 3.1, 3.2, 5.1, 5.2 DONE).
2. **Feeling Compagnon O-FEEL-1..3 (rejeux humains `:5174`)** : **100 % validé & clôturé** (C1/C2/PLAN/GO ALL PASS + retour terrain présence naturel).
3. **Mains code & coûts LLM O-IDE-1..3** : **100 % validé & clôturé** (smoke live cline prouvé, diagnostic CPU Ollama .110 chiffré, OpenCode confirmé nominal ADR 0025).
4. **Thème 1 — Autonomie Campus / CI / desktop (O-CAMP-1, O-CAMP-2, O-D7-1)** : **100 % validé & clôturé** (tickets plan réconciliés 10/10 DONE, overlay & 140 synchro, Présence Agents D7 actif sur `.143:5005` avec socket `/run/user/1000/lbg-presence-agents.sock`).
5. **Thème 2 — Ops LAN (O-OPS-1)** : **100 % validé & clôturé** (`smoke_lan_surfaces.sh --functional` 100% vert, 24 OK, 1 WARN, 0 KO ; autorité Godot G5+ `:8787` intégrée, Core3 legacy offline toléré).
6. **Thème 3 — Veille Évolution (O-VEIL-1..4)** : **100 % validé & clôturé** (ADR 0028 formalisé pour DSH & VoiceStudio ; doc de cadrage L1 [`agentic_rag_mapping.md`](../packages/cortex/docs/agentic_rag_mapping.md) ; fiabilisation route LLM veille O-VEIL-4 avec format json Ollama et dimensionnement dynamique timeout/tokens).
7. **Harmonisation Doc & Retrait SOE (O-DOC-1, O-JEUX-3)** : **100 % validé & clôturé** (`OBJECTIVES.md` aligné sur Compagnon présence `:5174` vs Pilot cockpit ops `:8080`, jalon P4 clos dans `PLAN_MMO_O2.md` et `PRIORITES_ACTUELLES.md`).
8. **Ops — Agrégat 7j Fleet (O-OPS-2)** : **100 % validé & clôturé** (`metrics_7d` et `rolling_7d` intégrés dans `team/fleet.py`, DoD plan combler gaps agentiques 100% OK).
9. **O-DOC-2 / root client / toasts HUD** : **clos** 2026-10-14 — Bugbot optionnel abandonné au plateau · `LBG_PRIME_CLIENT_ROOT` → `/opt/LBG_Studios/packages/prime-client` · toasts bas-centre.
10. **Docs périmées (O-DOC-ALIGN)** : **fait** 2026-10-13.
11. **O-JEUX-ESCORT / SHOW / HOTBAR** : **clos** 2026-10-14 — escorte · La Perle · hotbar 2/3/4/9 branchés.
12. **O-CTX-HYGIENE (A1–A3 · B1 · C1–C2 · D1)** : **clos & live** 2026-10-14 — journal · Respire · Studio Brain · prefs monde · nameplates + activité idle/busy/quest · coûts craft/use · deploy CT100 + hub `:8787`.
13. **O-MODS-GRAFT (Agents live · bus ADR 0019 · routeur L1/L2)** : **clos & live** 2026-10-14 — side-panel fleet · `teamBus` · badge méta light/heavy — [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) § *Fil Mods Claude*.
14. **O-UX-DND & Quêtes des villages** : **clos** 2026-10-14 — Inventaire grille drag & drop natif Godot 4 (`InventorySlotBtn`, `HotbarSlotBtn`), swap, stacking même id, assignation hotbar 3 objet rapide, feedback toast · 4 quêtes immersives des villages (`zalem_patrouille_route`, `zalem_pieces_relais`, `ksar_source_oasis`, `ksar_herbes_sables`) avec dialogues, suggestions et catalogue synchronisés pour Capitaine Vael, Soren Kray, Ancien Nadir et Miran Sael · CI headless Godot 4/4 PASS (<5 s).
15. **Canon O1/O2/O3** : **clos** 2026-10-14 — [`OBJECTIVES.md`](../OBJECTIVES.md) + [`PRIORITES_ACTUELLES.md`](PRIORITES_ACTUELLES.md) · Compagnon / MMO banc / Joueurs IA · règle mutations dures.
16. **D8 Avatar bridge Desktop & VRM poses / modèles** : **validé visuellement & live sur .10** 2026-10-15 —
    - Sortie définitive du T-pose (three-vrm 3.x `setNormalizedPose()` + repère d'Euler normalisé Z).
    - Catalogue complet de poses expressives intégré dans `vrm_pet.js` et rebundlé : `idle`, `wave`, `pointLeft`, `pointRight`, `pointScreen`, `think`, `approve`, `cheer`, `bow`.
    - Menus Tray Compagnon enrichis avec déclencheurs directs et bridge HTTP `:8765`.
17. **Compagnon unique, orientation face & Pack d'animations 1** : **clos & déployé live** 2026-10-16 —
    - **Orientation face caméra** : `Compagnon.vrm` identifié comme VRM 1.0 (`v.meta.metaVersion = "1"`). Fix de `faceTheCamera()` avec `rotation.y = 0` (suppression de l'inversion erronée qui le mettait de dos).
    - **Modèle unique** : conservation exclusive du modèle `Compagnon.vrm` dans l'interface et le desktop pour cohérence d'identité.
    - **Pack d'animations 1 intégré** :
      - `dance` (Danse rythmée / groove) : déhanché `hips`, balancement alterné des bras à 4.8 Hz, hochement de tête rythmé, expression faciale `happy`.
      - `angry` (Colère / bouderie) : poings sur les hanches, torse bombé, secousse de tête indignée (6.2 Hz), respiration saccadée, expression faciale `tense`.
      - `walk` (Marche fluide) : cycle complet de marche avec balancement des jambes (`leftUpperLeg`, `rightUpperLeg`), flexion dynamique des genoux (`leftLowerLeg`, `rightLowerLeg`), balancement opposé des bras et bobbing vertical du buste.
    - **UI & Tray** : boutons dédiés ajoutés dans `LyraPanel.vue` (Web `:5174`) et entrées dans le menu Tray de l'application desktop Windows (`.10`).
    - **Overlay sans cadre & promenade sur le bureau (Desktop Pet)** :
      - Suppression intégrale de la bordure, du fond sombre dégradé et de l'ombre portée autour du modèle VRM dans `overlay/index.html`. L'avatar 3D flotte directement sur le fond d'écran et les fenêtres sans aucune boîte visible.
      - Poignée de glissement et label masqués par défaut, apparaissant discrètement au survol de la souris.
      - Système de promenade autonome (`wander`) activé par défaut et connecté à l'animation de marche : Compagnon marche physiquement (`walk`) le long de la barre des tâches ou vers des fenêtres, s'arrête à destination en posture de repos (`idle`), marque une pause naturelle, puis repart.
      - **Orientation directionnelle fluide** : l'avatar pivote dynamiquement dans le sens de son déplacement (profil 3/4 droit `~75°` si elle va à droite, profil 3/4 gauche `~-75°` si elle va à gauche) et revient doucement face caméra dès qu'elle marque un arrêt.
      - **Pieds calés au ras du sol** : recalcul de la projection de caméra (`lookY = box.min.y - 0.012 + visibleH / 2`) et suppression de tout padding inférieur dans l'overlay pour que ses pieds reposent et marchent directement au niveau du bord inférieur de la fenêtre (posée sur la barre des tâches).
      - **Démarche naturelle, posture des bras & zéro moonwalk** :
        - **Bras corrigés** : correction de l'élévation anormale (Z repassé à `-1.25` / `+1.25` pour que les bras pendent le long du corps au lieu de rester écartés en ailes). Suppression intégrale de la torsion axiale X sur l'avant-bras qui tordait le coude vers l'arrière façon "aile de poulet". Flexion naturelle du coude sur l'axe anatomique Z (`-0.20` à gauche, `+0.20` à droite) et oscillation fluide d'avant en arrière sur l'axe Y en opposition aux jambes.
        - **Élimination du moonwalk / patinage** : calcul exact de la cinématique au sol. L'enjambée a été calibrée à `0.10 rad` (~5.7°) à une cadence de `2.7 rad/s`, ce qui correspond exactement aux `48 px/s` de translation de la fenêtre sur l'écran. Le pied d'appui reste désormais immobile sur la barre des tâches pendant que le corps avance (zéro glissement).
        - Flexion physiologique des genoux vers l'arrière quand la jambe passe vers l'avant (`stride * 1.5 + 0.03`).
        - Déroulé des pieds au sol (`leftFoot`, `rightFoot`).
        - Déhanché souple (`hipsRoll: 0.025`, `hipsYaw: -0.035`) et contre-torsion légère du torse (`chestYaw: 0.03`).
      - **Verrouillage strict sur la barre des tâches** :
        - Fix du bug Electron `(marginBottom || 72)` qui forçait 72 px quand `marginBottom = 0`.
        - `pickWanderTarget()` verrouille l'ordonnée Y à 100% sur le bord supérieur de la barre des tâches du moniteur courant (`targetY = wa.y + wa.height - h`). Déplacements limités à une promenade horizontale de gauche à droite sur toute la largeur de l'écran.
      - Pilotable via le menu Tray ("Se promener sur le bureau") et via commande bridge HTTP `:8765` (`cmd: wander`). Recompilé et déployé live sur Windows `.10`.
18. **Thème Mascotte Android Chibi Cyber & Système de Vie Autonome (Desktop Pet)** :
    - **Optiques cybernétiques (Yeux)** : iris et highlights transformés en optiques luminescentes néon cyan (`#00f5d4` et `#80ffff`, émissif 2.5), globe oculaire sombre cybernétique (`#061320`), suppression du regard humain au profit de l'éclat robotique comme l'illustration.
    - **Châssis métallique androïde** : carrosserie du visage et du corps teintée en bleu nuit cyber métallique (`#28426b` et `#243d63`, ombre `#121e33`) avec bordure lumineuse néon cyan (rim lighting MToon `#00f0ff`, mix 0.70).
    - **Chevelure métallique** : bleu nuit profond indigo (`#182846`) avec reflets néon cyan le long des mèches (`#00e5ff`).
    - **Proportions Chibi** : amplification douce de la tête (+14%) pour une silhouette chibi mignonne et expressive.
    - **Cadre compact sans vide vertical (220x420)** : réduction drastique de la hauteur de fenêtre de 620 px à 420 px (gain de 200 px d'espace bureau) sans rétrécir l'avatar. Cadrage resserré avec 2% de marge au sommet de la tête (`dist = neededH / (2 * tan(fov/2))`) et pieds calés au bord inférieur.
    - **Système de vie autonome (fin du mode zombie, plus de vie sur place)** :
      - **Moins de trajets continus** : les promenades sont désormais courtes (80 à 200 px au lieu de traverser tout l'écran) avec de longues pauses de repos (12 à 22 secondes) sur la barre des tâches.
      - **Clignements naturels des yeux** : clignement autonome toutes les 2.5 à 6 secondes via l'expression `blink`.
      - **Micro-gestes autonomes spontanés** : déclenchement aléatoire de postures expressives en pause (`think`, `wave`, `approve`, `cheer`) avec retour fluide en `idle`.
      - **Regard et observation vivante** : hochements curieux et exploration du regard vers l'écran de l'utilisateur, accompagnés d'un transfert de poids naturel sur les hanches (`weightShift`).
    - **Feuille de route Option 3** : modélisation ou adaptation 3D dédiée à terme (châssis robotique avec rotules mécaniques physiques en relief, 2 bras uniquement).
    - Recompilé et déployé sur Windows `.10` (PID 38804), bridge `:8765` opérationnel.
19. **Plan d'Intégration VRM MMO** : **rédigé et acté** (`docs/PLAN_INTEGRATION_VRM_MMO.md`) —
    - Phase A : HUD/Inventaire `prime-client` via `SubViewport3D` sans impacter le tick serveur.
    - Phase B : Avatar 3D in-game et délégation infographie IA (Pygmalion) pour textures et banques d'animations.
20. **Invisibilisation des sous-vêtements & Poses contenues dans le cadre (Desktop Pet)** : **live & validé sur .10** 2026-10-16 —
    - **Invisibilisation totale des sous-vêtements (Skin robotisé natif)** :
      - Correction de la teinte : la peau originale du modèle était bleu/cyan (`RGBA [126, 189, 214]`) et non chair. Remplacement complet des 162 303 pixels sombres du soutien-gorge et de la culotte.
      - **Carrosserie robotique haute fidélité** : génération et injection directe dans le binaire `Compagnon.vrm` (Image 11) et export de `body_skin_android.png` avec plaques d'armure pectorales sculptées, jointures de sternum, segmentations abdominales métalliques, rotules mécaniques de hanches et circuits luminescents néon cyan (`#00f5d4`), fidèle à l'illustration androïde.
      - Aucun bikini ou sous-vêtement résiduel : carrosserie cyber bleu nuit (`#28426b`) uniforme sur l'ensemble du châssis.
    - **Fin des mains hors cadre (Poses contenues)** :
      - Cadrage sécurisé à 95% de la hauteur de fenêtre (`neededH = size.y * 1.05`), pieds sur la barre des tâches, avec marge latérale confortable (largeur 270 px).
      - **Micro-gestes autonomes apaisés** : restriction du roulement d'animation idle aléatoire aux seules postures calmes qui ne sortent jamais du cadre (`crossArms` bras croisés, `think` main au menton, `approve` hochement). Suppression des gestes d'agitation de bras spontanés.
      - **Marche naturelle conservée** : foulée et cadence impeccables (`stride = 0.10 rad` @ 2.7 rad/s, 48 px/s sans aucun moonwalk).
    - Recompilé (`overlay/vrm/vrm_pet.bundle.js`), modèle et texture synchronisés via robocopy et Electron redémarré sur Windows `.10` (PID 15856).
21. **Polish posture crossArms, fluidité de la marche & cadrage animations VRoid/VRMA** : **live & validé sur .10** 2026-10-18 —
    - **Correction pose crossArms** : correction anatomique des angles d'Euler et de la flexion des coudes dans `vrm_pet.js` — les bras se croisent naturellement sur la poitrine au lieu de partir dans le dos (suppression de l'inversion de signe sur `rightLowerArm`).
    - **Fluidification de la marche procédurale (`walk`)** : levée de genou progressive et continue d'ordre supérieur (suppression des à-coups angulaires), micro-rebond vertical des hanches (bobbing à double fréquence), déroulé souple des chevilles et balancement rigoureux des bras en opposition alternée.
    - **Architecture VRoid Studio vs format VRM/VRMA** : cadrage technique documenté sur le standard VRM (modèle 3D géométrique sans pistes d'animation, animations internes Unity de VRoid Studio) et feuille de route pour le format officiel VRMA via `@pixiv/three-vrm-animation`.
    - Recompilé (`overlay/vrm/vrm_pet.bundle.js`), synchronisé via robocopy et Electron redémarré sur Windows SDS `.10` (PID 25944, bridge OK).
22. **Synchronisation vue portrait CT100, pont d'actions Web ↔ Bureau & Roadmap VRMA** : **live & validé** 2026-10-18 —
    - **Vue portrait CT100 (`192.168.0.100:5174`)** : synchronisation du modèle `Compagnon.vrm` (14.8 MB) sur CT100 et rebuild du conteneur Docker `orchestrateur-frontend`. La vue portrait dans le volet monitoring est désormais identique au modèle androïde du bureau (yeux cyber cyan, cheveux sombres, plaques robotiques).
    - **Passerelle d'actions Web ↔ Bureau** :
      - Exposition de `setPose` dans `preload.js` et écouteur IPC dans `main.js` relayé vers `sendVrmPose()`.
      - Dans `LyraPanel.vue`, `triggerPose()` anime le portrait local ET commande instantanément le Desktop Pet sur Windows (via IPC Electron ou fallback HTTP bridge `:8765`).
      - Ajout des boutons "🦾 Confiante" (`crossArms`) et "🙇 Révérence" (`bow`) dans la grille d'actions rapides.
    - **Roadmap VRMA & Références Hoyoverse** : cadrage validé pour l'intégration de `@pixiv/three-vrm-animation` (clips de mocap haute fidélité style Honkai Star Rail / Genshin Impact).
    - Déployé live sur Windows SDS `.10` (PID 26308) et conteneur Docker CT100 (version `1.0.0+5a0e594`).
23. **Passage au format VRMA officiel (`@pixiv/three-vrm-animation`) & Pack mocap haute fidélité** : **live & validé** 2026-10-18 —
    - **Installation de la bibliothèque officielle** : ajout de `@pixiv/three-vrm-animation` (^0.1.x) avec `three` (^0.180.0) et `@pixiv/three-vrm` (^3.5.5) dans `packages/compagnon-desktop/package.json`.
    - **Intégration VRMAnimationLoaderPlugin & THREE.AnimationMixer dans `vrm_pet.js`** :
      - Enregistrement du plugin `VRMAnimationLoaderPlugin` sur le `GLTFLoader`.
      - Instanciation du `THREE.AnimationMixer(vrm.scene)` au chargement du modèle avec écouteur d'événement `finished` pour retour automatique et fondu doux vers `idle`.
      - Fonction `loadVRMA(name, filename)` avec mise en cache dynamique des `AnimationClip` Three.js via `createVRMAnimationClip(animData, vrm)`.
      - Fonctions `playVRMA(name, opts)` et `stopVRMA(fadeSec)` avec transition fluide (`fadeIn`/`fadeOut`).
      - Coexistence harmonieuse mocap VRMA / procédural : `updatePoseSystem()` cède la main sans conflit au mixer pendant la lecture d'un clip mocap et reprend instantanément les poses procédurales (ex: `crossArms`) dès l'arrêt du clip.
      - `mixer.update(dt)` synchronisé dans la boucle de rendu `animate()`.
      - Exposition publique de `playVRMA`, `stopVRMA`, `loadVRMA` et du getter `activeVRMA`.
    - **Pack initial de clips VRMA de référence (17 animations mocap)** :
      - **1 idle vivante élégante** : `lookaround.vrma` / `idle_loop.vrma` (observation fluide de l'environnement).
      - **1 marche gracieuse** : `walk.vrma` (cycle de marche naturel fluide, sans saccade ni moonwalk).
      - **1 pose de repos posée** : `relax.vrma` (posture d'attente relaxée et naturelle) et `sit.vrma` / `sitWave.vrma` (pose assise).
      - Clips complémentaires : `thinking.vrma`, `goodbye.vrma`, `wave_right.vrma`, `clapping.vrma`, `blush.vrma`, `sleepy.vrma`, `surprised.vrma`, `angry.vrma`, `sad.vrma`, `idle_stretch.vrma`.
      - Déployés dans `packages/compagnon-desktop/overlay/vrm/animations/` et `packages/cortex/compagnon_ui/public/vrm/animations/`.
    - **Interface de test Web (`LyraPanel.vue`)** : ajout des boutons d'action rapide "🧘 Repos" (`relax`) et "👁️ Observer" (`lookaround`).
    - **Compilation et déploiement live validés** :
      - Compilation esbuild de `overlay/vrm/vrm_pet.bundle.js` (2.2 MB autonome).
      - Déploiement robocopy vers Windows SDS `.10` : 17 clips `.vrma` présents, Electron redémarré (PID 11904), bridge `:8765` opérationnel.
      - Déploiement CT100 via `deploy_compagnon_100.sh` : conteneur `lbg-frontend` rebuildé, Nginx sert les 17 animations sous `/vrm/animations/` (HTTP 200 OK vérifié).
24. **Correction de la synchronisation de marche & déplacement réel du Desktop Pet** : **live & validé** 2026-10-18 —
    - **Diagnostic du patinage "marche sur place"** :
      - Le clip mocap brut `walk.vrma` bouclait très vite (0.766s par cycle, soit 2.6 pas/sec), tandis que la fenêtre Electron rampait à 48 px/s (seulement 18 px par pas).
      - Sur commande de marche (bouton Web, Tray ou API bridge), la fenêtre restait figée à 0 px/s sans bouger.
      - En vue frontale (face caméra à 0°), l'absence de parallaxe accentuait l'illusion d'un tapis de course sur place.
    - **Calibrage kinésiologique & physique** :
      - **Cadence `timeScale` à 0.72x** : allongement doux du cycle à 1.06s (~0.53s par pas) pour une démarche calme, fluide et altière ("marche gracieuse").
      - **Vitesse de translation à 92 px/s** : augmentation de 48 px/s à 92 px/s dans `config.json` et `main.js`. Chaque pas avance la fenêtre de ~48 px, synchronisant exactement la propulsion des jambes avec le sol de la barre des tâches (zéro patinage).
      - **Orientation 3/4 profil automatique** : dès que la marche est ordonnée sans direction explicite, l'avatar pivote en 3/4 profil droit (`targetHeadingY = 1.25 rad`) pour mettre en valeur le déroulé de jambe, avant de revenir face caméra à l'arrêt.
      - **Déplacement physique sur commande de marche (`startWalkingMovement`)** : que la marche soit déclenchée depuis le bouton "🚶 Marche" de `LyraPanel.vue`, le menu Tray ou le bridge `:8765`, l'avatar entame un vrai déplacement continu (jusqu'à 550 px) le long de la barre des tâches.
    - **Recompilation & Déploiement live** :
      - Compilation esbuild `overlay/vrm/vrm_pet.bundle.js` (2.22 MB).
      - Déploiement robocopy vers Windows SDS `.10` et redémarrage Electron (PID 40200, bridge OK).
      - Déploiement CT100 (`192.168.0.100:5174`) via `deploy_compagnon_100.sh` avec rebuild Docker.
25. **Correction de l'enfoncement dans la barre des tâches, vitesse de marche & Cadrage textures Pygmalion** : **live & validé** 2026-10-19 —
    - **Arbitrage d'architecture Mascotte (2 bras uniquement)** :
      - Confirmation formelle : aucun bras additionnel. Conservation exclusive du squelette humanoïde standard bipède VRM 1.0 garantissant la compatibilité pleine et entière avec l'ensemble des animations VRMA officielles (17 clips mocap) et les poses procédurales sans conflit de bones.
    - **Élimination de la descente dans la barre des tâches (`walkYOffset`)** :
      - Découverte : dans `walk.vrma`, la piste `hips.translation` Y descend jusqu'à `0.7514` (drop de `7.3 cm` par rapport au T-pose de repos `0.8242` de `Compagnon.vrm`), ce qui faisait plonger les pieds sous le bas du cadre dans la barre des tâches.
      - Solution : compensation verticale dynamique `targetWalkY = 0.088m` (+8.8 cm) avec montée rapide (`lerpSpeed = 16.0`, ~80 ms) dès que la marche démarre, et descente douce (`lerpSpeed = 6.0`) à l'arrêt. Les semelles restent parfaitement tangentes au sol sans jamais s'enfoncer.
    - **Synchronisation dynamique de la marche (zéro patinage)** :
      - Cadence mocap adoucie à `timeScale = 0.55x` (cycle complet de 1.39s, soit ~0.70s par pas) pour une démarche calme, altière et élégante.
      - Vitesse de translation augmentée à `165 px/s` dans `config.json` et `main.js`. Chaque pas propulse la fenêtre de `~115 px`, en phase exacte avec l'extension de jambe 3D : le pied d'appui reste scellé au sol sans aucun moonwalk ni patinage "sur place".
    - **Délégation Infographie IA (Pygmalion)** :
      - Rédaction du ticket complet de cadrage et spécifications graphiques [`docs/handoff_pygmalion_textures_compagnon.md`](handoff_pygmalion_textures_compagnon.md) : textures 2048×2048 RGBA (`Body_00_SKIN`, `Face_00_SKIN`, `Hair_00_HAIR`), rotules mécaniques 3D en trompe-l'œil, armure pectorale biseautée, segmentations abdominales et liserés lumineux cyan néon `#00f5d4`.
    - **Compilation & Déploiements validés** :
      - Recompilation esbuild `overlay/vrm/vrm_pet.bundle.js` (2.22 MB).
      - Déploiement robocopy vers Windows SDS `.10` : Electron redémarré (PID 37868), test live de marche `:8765` validé.
      - Déploiement CT100 (`192.168.0.100:5174`) via `deploy_compagnon_100.sh` : conteneurs Docker backend et frontend rebuildés et démarrés.
26. **Élargissement du cadre, Interactions de bureau ciblées & Nouvelles animations/danses** : **live & validé sur .10** 2026-10-19 —
    - **Élargissement du cadre de l'overlay (320×420 px)** :
      - Fin des mains qui sortent du cadre à droite : la largeur de fenêtre passe de 270 px à **320 px** (+50 px de marge latérale, soit +18.5% de champ horizontal en projection Three.js).
      - Marge verticale portée à `neededH = size.y * 1.08` dans `frameVrm()` (+8% de respiration au-dessus de la tête) pour contenir les mains levées lors des gestes amples (`wave_right`, `spin`, `jump`, `clapping`).
    - **Interactions de bureau ciblées (Desktop Pet vivant)** :
      - Fin de l'errance perpétuelle et des allers-retours continus sans but : dès son arrivée sur la barre des tâches, l'avatar marque une pause sereine prolongée (60 à 120 secondes).
      - Système `scheduleNextDesktopInteraction()` dans `main.js` : planifie des interactions intelligentes espacées (aller inspecter une fenêtre ouverte détectée via `listWindows()`, aller saluer les icônes du bureau ou l'horloge système), puis retour automatique et fluide à sa position de repos sur la barre des tâches via `returnToTaskbar()`.
      - Menu Tray enrichi avec sous-menu **"Interagir avec le bureau…"** (inspecter fenêtre active, voir icônes, voir barre des tâches, reprendre position) et option toggle "Interactions bureau autonomes".
    - **Nouvelles animations, Danses & Pirouettes** :
      - Suppression du court-circuitage dans `VRMA_MAP` où `dance: "clapping.vrma"` écrasait la danse au profit d'applaudissements.
      - 💃 **Danse rythmée (`dance`/`groove`)** : chorégraphie procédurale avec tempo à 2.2 Hz, déhanchement en huit (`hipsRoll`, `hipsYaw`), rebond vertical cadencé ("bounce"), balancement alterné des bras, pulsation des coudes et hochement de tête complice.
      - 💫 **Pirouette 360° (`spin`)** : rotation complète fluide sur l'axe Y (`spinAngle`), bras déployés avec grâce et retour face caméra souriant.
      - 🎉 **Victoire / Saut (`jump`/`victory`)** : saut d'impulsion vertical (+4.5 cm en parabole) avec bras levés en V triomphal.
      - 🙆‍♀️ **Étirement (`stretch`)** : étirement relaxant vers le haut branché sur le clip mocap `idle_stretch.vrma`.
      - 👏 **Applaudissements (`clapping`)** : battement de mains joyeux.
      - Boutons interactifs intégrés dans la grille d'actions de `LyraPanel.vue` (Web `:5174`) et dans le menu Tray de la barre des tâches Windows.
    - Recompilé avec esbuild (`vrm_pet.bundle.js`), hotfix syntaxique dans `main.js` (suppression d'un résidu orphelin dans le menu Tray), synchronisé via robocopy et Electron redémarré avec succès sur Windows SDS `.10` (PID 20524, pont HTTP `:8765` opérationnel et vérifié : `event=avatar.idle`, `mood=serene`).
27. **Harmonisation kinésiologique & Refonte des animations Danse, Victoire et Pirouette** : **live & validé sur .10** 2026-10-19 —
    - **Diagnostic du désordre gestuel (inversion anatomique des coudes)** :
      - Découverte majeure : dans le rig standard three-vrm (VRM 1.0 normalized humanoid), la flexion antérieure des deux avant-bras (`leftLowerArm` et `rightLowerArm`) se fait TOUJOURS en **Z négatif**.
      - Dans `dance`, `jump`, `spin`, `cheer`, `angry` et `stretch`, `rightLowerArm` avait été erronément configuré avec un Z positif (`+1.15`, `+0.35`, `+1.35`, `+1.55`), ce qui forçait une hyperextension vers l'arrière / l'extérieur (coude droit luxé/tordu) pendant que le bras gauche pliait normalement.
      - Inversion également corrigée pour `leftLowerArm` dans `pointRight`.
    - **Refonte de la Danse (`dance`)** :
      - Cadence apaisée de 132 BPM frénétique à **63 BPM** (~1.05 Hz, tempo lofi / groove détendu et gracieux).
      - Élimination des secousses axiales brutales du bassin (`hips[0]` = 0, rebond vertical transféré sur la translation physique `vrm.scene.position.y`).
      - Déhanchement doux en huit (`swayHips: 0.07`, `rollHips: 0.05`), contre-ondulation naturelle du torse (`spine`, `chest`), flexion souple des genoux en absorption et balancement coordonné des avant-bras avec coudes naturellement pliés vers l'avant.
    - **Refonte de la Victoire / Saut (`jump`)** :
      - Saut de célébration harmonieux et synchronisé à 4.0 rad/s (au lieu de 8.5 rad/s haché).
      - Trajectoire parabolique avec amorti d'atterrissage absorbé par les genoux (`landingCushion`).
      - Élan triomphal des bras levés en V avec flexion anatomique naturelle des deux coudes (`-0.55` rad) et hochement joyeux de la tête.
    - **Refonte de la Pirouette (`spin`)** : rotation 360° fluide avec bras déployés gracieusement et coudes symétriques en Z négatif (`-0.45`).
    - Recompilé avec esbuild (`vrm_pet.bundle.js` 2.23 MB), déployé par robocopy et Electron redémarré sur Windows SDS `.10` (PID 11720, bridge `:8765` validé).
28. **Travail Pygmalion (Infographiste_IA) & Texture Châssis Androïde Option 1** : **live & validé sur .10** 2026-10-19 —
    - **Pygmalion (`Infographiste_IA`) activé en live** :
      - Connexion au backend ComfyUI actif sur Windows SDS `.10:8188` (GTX 1050 Ti lowvram).
      - Soumission du workflow conforme au handoff [`docs/handoff_pygmalion_textures_compagnon.md`](handoff_pygmalion_textures_compagnon.md) : DreamShaper 8 + LoRA `mmorpg_insp_lora.safetensors`, androïde mascotte chibi 2 bras uniquement, carrosserie titane bleu nuit, plastron et optiques cyan néon `#00f5d4`, rotules mécaniques, épaulettes argentées.
      - Génération réussie du concept de référence : `scratch/pygmalion_compagnon_concept_00001_.png` (398 KB).
    - **Option 1 (Texture 2048×2048 haute définition & intégration 3D)** :
      - Synthèse de la texture complète du corps `body_skin_android.png` (2048×2048) alignée sur le concept Pygmalion : plastron pectoral biseauté néon cyan éclatant avec cœur lumineux, actuators hydrauliques sombres sur l'abdomen, carapace pelvienne, rotules mécaniques concentriques en trompe-l'œil 3D aux épaules, coudes, poignets, hanches et genoux, épaulettes argentées, et bottes magnétiques nettes sans orteils humains.
      - Intégration dans `applyAndroidTheme(v)` de `vrm_pet.js` avec chargement dynamique Three.js MToon et base color blanche `0xffffff` pour une brillance 100% pure des néons cyan sans atténuation sombre.
      - Recompilé avec esbuild (`vrm_pet.bundle.js` 2.23 MB) et déployé en live sur Windows SDS `.10` (PID 40988, `bridge_ok event=avatar.idle mood=serene`).
29. **Textures Canon Mascotte Haute Fidélité 360° (Face expressive, Buste sculpté & Dos mécatronique complet)** : **live & validé sur .10** 2026-10-19 —
    - **Intégration intégrale du Dos (360°)** :
      - **Colonne vertébrale cybernétique (Spine)** : Jonction 3D sans couture le long des bords de texture (X=500 et X=1545) formant une colonne vertébrale mécatronique continue avec 10 vertèbres biseautées et cœurs néon cyan émissifs (`#00f5d4`).
      - **Plaques d'armure scapulaires (Omoplates)** : Épaulières dorsales biseautées profilées en bleu titane satiné (`#2e4872` / `#385888`) avec liseré cyan néon et grilles d'aération thermique / heat sink intercalées.
      - **Carapace fessière et lombaire** : Découpes d'armure galbées sous chaque fesse soulignées de cyan néon, connecteur sacré central au bas du dos et conduits lombaires reliant les flancs.
    - **Face avant & Visage** :
      - Buste en armure bleu titane satinée couvrant les anciens pointillés, galbe souligné d'un double liseré cyan néon 2.5px (`#00f5d4` + cœur `#c0fff6`), sternum en Y inversé et rivets discrets.
      - Visage expressif et lumineux préservant tout le modelé 3D (arête du nez, paupières, pommettes, lèvres glossy framboise-cyber nacrées).
    - **Cheveux** : Dégradé soyeux validé conservé (racines indigo profond -> corps cobalt -> pointes cyan éclatantes).
30. **Assainissement des Prompts Compagnon & Posture JARVIS (élimination boucles dry-run / deploy_* / chatbot isolé + routage E4b-qat / 12b-qat)** : **live & déployé sur CT100 (`1.0.0+9d126f0`)** 2026-10-19 —
    - **Éradication des boucles perroquet dans `router_prompts.py`** : refonte de `BASE_GUARDRAILS`, `LAB_GUARDRAILS`, `LAB_CAUSERIE_GUARDRAILS`, `lab_ops_system_prompt()` et `build_profiles()` ; suppression de toutes les mentions rigides de « deploy_* », « dry-run » et « pas un chatbot isolé » ; recentrage sur une posture naturelle, réactive et courtoise façon JARVIS.
    - **Nettoyage des catchphrases et worldview (`character/compagnon_v1.json`)** : élimination des slogans « Agir d'abord en dry-run » et « Je suis le Compagnon du studio — pas un chatbot isolé » qui étaient injectés systématiquement à chaque tour ; remplacés par des formules naturelles et discrètes.
    - **Alignement routage modèles (`routing.json` & `local_llm_provider.py`)** : promotion de `huihui_ai/gemma-4-abliterated:E4b-qat` (sweet spot interactif réactif, configurable sur .111 ou .110 via `LBG_OLLAMA_E4B_HOST`) et `huihui_ai/gemma-4-abliterated:12b-qat` (qualité max sur .110) en tête de liste, avec support de `LBG_COMPAGNON_LOCAL_MODEL`.
    - **Déploiement atomique CT100 validé** : build paquet `server_overlay-1.0.0+9d126f0.tar.gz` (41 fichiers), upload, vérification checksum sha256 et application atomique réussie ; conteneurs `orchestrateur-backend` et `lbg-frontend` recréés et redémarrés avec succès sur `192.168.0.100:5174`.
31. **Application & Synchronisation de l'identité Android 360° sur la vue Buste (`CT100:5174`)** : **live & validé** 2026-10-19 —
    - **Diagnostic du décalage vue buste** : le conteneur Docker `lbg-frontend` servait une image antérieure non reconstruite (absence de `hair_android.png` et `face_skin_android.png` provoquant des erreurs 404 dans la console du navigateur et un repli sur la texture d'origine violette et le corps uni sans plaques).
    - **Résolution dynamique des chemins de texture (`vrm_pet.js`)** : remplacement du chemin relatif `./vrm/...` par la dérivation contextuelle de `vrmDir` à partir de `modelUrl` (`const base = modelUrl.includes("/") ? modelUrl.substring(0, modelUrl.lastIndexOf("/")) : "./vrm"; const vrmDir = base || "./vrm";`) garantissant un chargement fluide quel que soit le contexte (Web `:5174` ou Overlay Desktop).
    - **Anti-cache & Cache-busting** : injection de paramètres de versioning `?v=chibi_v3` sur les textures dans `vrm_pet.js` et sur `vrm_pet.bundle.js` dans `LyraPanel.vue`.
    - **Recompilation & Déploiement CT100** :
      - Compilation esbuild de `overlay/vrm/vrm_pet.bundle.js` (2.23 MB) et réplication dans `compagnon_ui/public/vrm/`.
      - Synchronisation des textures 360° (`body_skin_android.png`, `face_skin_android.png`, `hair_android.png`) et du bundle vers `/opt/orchestrateur/frontend/public/vrm/` sur CT100 (`192.168.0.100`).
      - Rebuild Docker de l'image `orchestrateur-frontend` et recréation à chaud du conteneur `lbg-frontend`.
      - Vérification HTTP curl complète : 200 OK sur toutes les textures et le bundle avec en-têtes `Cache-Control: no-cache`. La vue buste et l'overlay desktop partagent désormais exactement la même apparence androïde.
    - **Mise à disposition des assets 3D & textures (`N:\Upload\IA\`)** : synchronisation directe des fichiers `Compagnon.vrm`, `body_skin_android.png`, `face_skin_android.png` et `hair_android.png` vers le lecteur réseau de travail `N:\Upload\IA\` via l'agent Windows (`.10:5005`).
32. **Sculpture Étendue des Plaques (Ventre, Côtes & Dos 360°)** : **live & validé** 2026-10-19 —
    - **Cuirasse abdominale complète (Ventre)** : 6 grandes plaques abdominales pleines biseautées (3 étages gauche/droite + carénage pelvien en V, `Y: 630..980`), teintées en bleu titane satiné avec reflets supérieurs bombés, séparées par une Linea alba sombre à liseré néon cyan fin et connectées directement aux plaques costales.
    - **Armure dorsale étendue (Dos complet)** : 3 étages de grandes plaques dorsales sous-scapulaires et lombaires (`Y: 475..930`) encadrant la cyber-spine de part et d'autre, bordées de liserés néon cyan et de rainures mécatroniques sombres, rejoignant les flancs.
    - **Plaques costales & taille cintrée** : 3 paires de plaques costales obliques épousant la cambrure de la taille et affinant la silhouette.
    - **Déploiement multi-surfaces immédiat** : texture `body_skin_android.png` (304 ko) injectée sur CT100 (`lbg-frontend`), déployée sur Windows SDS `.10` (overlay relancé PID 3312) et répliquée à chaud sur `N:\Upload\IA\` avec `Compagnon.vrm`, `face_skin_android.png` et `hair_android.png`.
33. **Correction Réactivité Streaming UI & Filtrage Intentions (Bulle vide + Détournement Diagnostic/Team)** : **live & déployé sur CT100 (`1.0.0+b1aeb85`)** 2026-10-19 —
    - **Correction du bug d'affichage UI de la bulle vide (`useChat.js`)** :
      - *Cause racine* : `beginStream()` conservait la référence de l'objet JS brut (`streamedMessage = msg`), alors que `messages.value.push(msg)` stockait un proxy réactif Vue 3 dans le tableau. Les mutations dans `appendStream` (`msg.content += delta`) et `finishStream` ne déclenchaient aucun setter réactif, maintenant la bulle vide jusqu'à ce qu'un nouveau message utilisateur (`addUserMessage`) provoque un re-render complet.
      - *Résolution* : assignation directe `streamedMessage = messages.value[messages.value.length - 1]` et fiabilisation des vérifications de présence via `toRaw(m) === toRaw(streamedMessage)` dans `finishStream`, `failStream` et `addMessage`. Les deltas SSE s'affichent désormais en temps réel sans latence ni bulle vide.
    - **Éradication des détournements d'intentions vers les outils (`reflection_router.py` & `chat_intent.py`)** :
      - *Vérification conversationnelle* : ajout du filtre `_CONVERSATIONAL_CHECK_RE` (« tu peux vérifier ? », « regarde pourquoi ») orientant directement vers `answer` au lieu de déclencher la boucle d'outils cockpit `## Diagnostic cockpit (boucle outils)`.
      - *Avatar, danses et fonctionnalités créatives* : ajout de `_AVATAR_OR_UI_RE` (danses, animations, VRM, interface, textures, bulle) et assainissement de `_OPS_OVERRIDE_RE` (fin du mot-clé nu « team » qui détournait les phrases créatives comme « fait travailler la team sur les danses » vers le dump SQLite du campus Lyra).
      - *Clarification du prompt système LLM light (`_REFLECT_SYSTEM`)* : instructions strictes interdisant de choisir `tools` ou `team` pour des discussions d'avatar, de design, de bugs ou de vérification courtoise.
    - **Validation & Déploiement CT100** :
      - Suite de tests `test_reflection_router.py` (10 tests) et `test_chat_intent.py` (13 tests) 100% verte.
      - Déploiement atomique du paquet `server_overlay-1.0.0+b1aeb85.tar.gz` sur CT100 via `deploy_compagnon_100.sh`.
      - Rebuild Docker des conteneurs `orchestrateur-backend` et `lbg-frontend` avec compilation Vite client.
      - Tests live vérifiés sur `:5174` : « et donc tu peux vérifier ? » et « tu peux regarder pour intégré plus de danse différentes pour l'avatar ? fait travailler la team sur le sujet » répondent tous deux en mode dialogue naturel (JARVIS) fluide sans dump d'outils.
34. **Plaque Torse, Épaules & Omoplates 360° (Haut du Buste Mecha & Cou Réaligné)** : **live & déployé sur toutes les surfaces** 2026-10-20 —
    - **Ajustement Fin des Proportions du Cou (Menton Dégagé & Report sur Body)** :
      - *Face Skin* : le menton et le haut de la gorge retrouvent leur teinte androïde claire (`Y: 790..890`). La zone sombre du cou mécanique est réduite à la portion médiane (`Y: 895..1024`, centré en 512) avec ses anneaux de servomoteur et sa démarcation supérieure incurvée douce.
      - *Body Skin* : report direct de la base du cou mécanique sombre (`Y: 110..220`), raccordé exactement sous le col du visage. L'échancrure concave en 'U' se place au creux anatomique des clavicules (`Y: 215..265`) avec son liseré néon cyan et ses deux vis de précision.
      - *Plastron & Seins* : plastron claviculaire (`Y: 230..385`), fente centrale en 'Y' (`Y: 270..605`), rivets signature au-dessus des seins (`Y: 345`) et dômes des seins à `Y: 390..605`.
    - **Épaulières Dômes & Omoplates Remontées** : capsules d'épaules semi-sphériques bleu cobalt métal avec arête supérieure/externe néon cyan éclatant (`#00f5d4` + cœur `#c0fff5`), collerette inférieure articulée et rotule mécanique centrale ; plaques scapulaires au dos avec symétrie miroir pixel-à-pixel absolue sur la couture dorsale (`X=495` et `X=1552`).
    - **Déploiement multi-surfaces immédiat** :
      - `N:\Upload\IA\` : `Compagnon.vrm`, `body_skin_android.png`, `face_skin_android.png`, `hair_android.png` mis à disposition via l'agent Windows (`.10:5005`).
      - `Desktop SDS .10` : synchronisation locale dans `C:\Agent_IA\compagnon-desktop\overlay\vrm\` et redémarrage de l'overlay (PID 3828, cache buster `?v=mecha_v7`).
      - `CT100 (192.168.0.100)` : injection docker dans `lbg-frontend:/usr/share/nginx/html/vrm/` (`body_skin_android.png`, `face_skin_android.png`, `vrm_pet.bundle.js`).
35. **Application du Visage Utilisateur (`N:\Upload\IA\face_skin_android.png`) & Découpage UV VRoid** : **live & déployé sur toutes les surfaces** 2026-10-20 —
    - **Importation du Visage Custom Utilisateur** : récupération et application directe de `N:\Upload\IA\face_skin_android.png` (68 957 octets) sur `packages/compagnon-desktop/overlay/vrm/face_skin_android.png` et `packages/cortex/compagnon_ui/public/vrm/face_skin_android.png`.
    - **Carte UV Body Skin VRoid Studio** : capture du patron wireframe fournie par l'utilisateur (buste central, seins en dômes concaves, découpe du col trapézoïdal, bras gauche/droit latéraux, jambes inférieures, pieds/orteils) intégrée comme référence anatomique exacte pour le calage du modèle.
    - **Cache Buster & Rebundle** : passage du cache buster de textures à `?v=mecha_v8` dans `vrm_pet.js` et compilation avec `esbuild` de `vrm_pet.bundle.js` (2.1 MB).
    - **Déploiement multi-surfaces immédiat** :
      - `Desktop SDS .10` : synchronisation locale dans `C:\Agent_IA\compagnon-desktop\overlay\vrm\` et relance de l'overlay (PID 41176).
      - `CT100 (192.168.0.100)` : injection docker dans `lbg-frontend:/usr/share/nginx/html/vrm/` (`body_skin_android.png`, `face_skin_android.png`, `vrm_pet.bundle.js`).
36. **Alignement 360° Cou & Nuque (Body_00_SKIN Pièce Bas-Centre)** : **live & déployé sur toutes les surfaces** 2026-10-20 —
    - **Topologie 3D de la Nuque résolue** : l'analyse 3D de `Compagnon.vrm` a démontré que le mesh du visage (`Face_00_SKIN`) possède 0 vertice sur l'axe arrière de la nuque (`abs(X) < 0.03, Z < -0.01`). La nuque entière (`Y_3d: 1.243 .. 1.471`) est gouvernée par le mesh `Body_00_SKIN` et correspond à l'îlot en dôme / cloche tout en bas au centre (`U: 800..1250, V: 1650..2045`).
    - **Application du Col Mécanique sur la Nuque** :
      - Peinture du servomoteur mécanique sombre (`CHASSIS_DARK`, rayures horizontales `FIBER_LIGHT` et rainures sombres) directement sur la cloche de la nuque (`Y: 1740..2045`), synchronisé en hauteur avec le devant du cou.
      - Colonne cervicale centrale à `X=1024` et câbles d'actionneurs latéraux symétriques à `X=959` et `X=1089`.
      - Liseré supérieur néon cyan éclatant (`#00f5d4` + cœur blanc-cyan `#c8fffa`) incurvé doux à `Y ~ 1748` épousant la base du crâne / naissance des cheveux.
      - Raccordement continu avec la couture dorsale haute (`X: 495.5` et `X: 1552.5`, `Y: 118..220`).
    - **Rebundle & Cache Buster** : passage à `?v=mecha_v9` dans `vrm_pet.js` et compilation `esbuild` de `vrm_pet.bundle.js` (2.1 MB).
    - **Déploiement multi-surfaces immédiat** :
      - `N:\Upload\IA\` : `body_skin_android.png` mis à jour (247 104 octets).
      - `Desktop SDS .10` : synchronisé dans `C:\Agent_IA\compagnon-desktop\overlay\vrm\` et overlay relancé (PID 9080).
37. **Harmonisation Mecha Skin v10 (Mains, Doigts, Ongles Cyber & Carénage Pelvien)** : **live & déployé sur toutes les surfaces** 2026-10-21 —
    - **Identification précise des îlots UV (Retour utilisateur)** :
      - Les 2 plaques du haut de part et d'autre du cou sont les **mains** (dos et paume de mains avec poignets/cuff mécatroniques).
      - Les 5 paires de pavés rectangulaires du bas sont les **doigts** (anciens tracés verts transformés en segments robotiques articulés bleu titane satiné).
      - Les gélules verticales adjacentes sont les **ongles de mains** (anciens tracés roses transformés en ongles cybernétiques néon cyan `#00f5d4` avec cœur émissif `#c0fff6`).
      - Les gélules extérieures sont les **ongles de pieds** (harmonisés en cyan éclatant).
    - **Sculpture & Intégration du Châssis** :
      - Raccordement et affinement du carénage pelvien en pointe biseautée au centre du bassin.
      - Préservation du col de nuque 360° sur la pièce en cloche du bas pour un tour de cou complet sans rupture à l'arrière.
      - Suréchantillonnage net en 2048×2048 pour une netteté maximale des circuits néon et des rivets.
    - **Rebundle & Cache Buster** : passage à `?v=mecha_v10` dans `vrm_pet.js` et compilation `esbuild` de `vrm_pet.bundle.js` (2.1 MB).
    - **Déploiement multi-surfaces immédiat** :
      - `N:\Upload\IA\` : `body_skin_android.png` mis à jour (260 298 octets).
      - `Desktop SDS .10` : synchronisé dans `C:\Agent_IA\compagnon-desktop\overlay\vrm\` et overlay relancé (PID 16364).
      - `CT100 (192.168.0.100)` : injecté dans le conteneur Docker `lbg-frontend:/usr/share/nginx/html/vrm/`.
38. **Mixte Châssis v11 (Haut Original + Centre Échancré _5 + Bas _5)** : **live & déployé sur toutes les surfaces** 2026-10-21 —
    - **Composition chirurgicale selon la demande utilisateur** :
      - *Haut de l'original (`Y: 0..324`)* : col mécatronique à cornes, servomoteur cervical sombre, plastron pectoral biseauté avec fente en Y et liserés cyan, plaques de mains propres aux angles supérieurs.
      - *Partie centrale échancrée de la _5 (`Y: 324..625`)* : segments abdominaux et cambrure des hanches en découpe haute échancrée (`\  /` diagonales) avec pointe de carénage pelvien descendante.
      - *Bas de la _5 (`Y: 625..1024`)* : fond uni sombre sans bloc nuque parasite central, extrémités et phalanges nettes de la _5.
    - **Rebundle & Cache Buster** : passage à `?v=mecha_v11` dans `vrm_pet.js` et compilation `esbuild` de `vrm_pet.bundle.js` (2.1 MB).
    - **Déploiement multi-surfaces immédiat** :
      - `N:\Upload\IA\` : `body_skin_android.png` mis à jour (150 219 octets).
      - `Desktop SDS .10` : synchronisé dans `C:\Agent_IA\compagnon-desktop\overlay\vrm\` et overlay relancé (PID 16904).
      - `CT100 (192.168.0.100)` : injecté dans le conteneur Docker `lbg-frontend:/usr/share/nginx/html/vrm/`.
39. **Châssis Métallique Spéculaire v12 & Tête Chibi Agrandie** : **live & déployé sur toutes les surfaces** 2026-10-21 —
    - **Contrôle & Application du Nouveau Skin Utilisateur** :
      - Intégration des sangles croisées en X en bas au centre (`Y: 700..1024`), de la pointe de carénage pelvien descendante avec needle cyan, des ongles magenta/cyan et des segments de doigts mécatroniques.
      - Suréchantillonnage net en 2048×2048 avec micro-biseautage spéculaire le long des arêtes supérieures des plaques pectorales, abdominales et pelviennes (brossage titane).
    - **Proportions Chibi Accentuees** :
      - Amplification de l'échelle du bone `head` portée de `1.14` à **`1.24` (+24%)** dans `vrm_pet.js` pour une silhouette anime chibi encore plus expressive et mignonne.
    - **Rendu Métallique Three.js & MToon Shader** :
      - *Rim Lighting spéculaire chrome-cyan* : `parametricRimColor = 0x80ffff`, blend factor `rimLightingMix = 0.65` (effet métal poli lustré), fresnel élargi `parametricRimFresnelPower = 2.0` et `parametricRimLift = 0.12`.
      - *Ombres contrastées acier* : `shadeColor = 0x18283e` (contraste dynamique accru typique du métal poli).
      - *Éclairage contre-jour directionnel* : ajout d'un spot spéculaire de rétro-éclairage `DirectionalLight(0x80e8ff, 0.75)` à `(-1.0, 1.8, -2.0)`.
    - **Rebundle & Cache Buster** : passage à `?v=mecha_v12` dans `vrm_pet.js` et compilation `esbuild` de `vrm_pet.bundle.js` (2.1 MB).
    - **Déploiement multi-surfaces immédiat** :
      - `N:\Upload\IA\` : `body_skin_android.png` mis à jour (231 683 octets).
      - `Desktop SDS .10` : synchronisé dans `C:\Agent_IA\compagnon-desktop\overlay\vrm\` et overlay relancé (PID 37976).
      - `CT100 (192.168.0.100)` : injecté dans le conteneur Docker `lbg-frontend:/usr/share/nginx/html/vrm/`.
40. **Backlog ouvert** : 0 sujet ouvert dans [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md).

## Fichiers / surfaces utiles

| Quoi | Où |
|------|-----|
| Canon agents | `AGENTS.md`, `.agents/rules/` |
| Priorités | `docs/PRIORITES_ACTUELLES.md` |
| Registre | `docs/REGISTRE.md` |
| Runtime jeu | `docs/RUNTIME_GODOT.md` |
| Plan évolutions | `docs/PLAN_PROPOSITIONS_EVOLUTIONS.md` |
| Suivi plan évolutions | `docs/suivi/PLAN_EVOLUTIONS_STATUS.md` |
| Sujets pas encore traités | [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md) |
| Handoff visuel Compagnon (clos) | `docs/handoff_antigravity_visuel_compagnon.md` |
| Handoff sonde AD (clos) | `docs/handoff_antigravity_sonde_ad.md` |
| Workspace | `LBG_Studios.code-workspace` |

## Bloquants

_Aucun bloquant documenté pour ce bootstrap._

## Notes de session

- 2026-10-14 : **Élargissement Zone Explorable O2 (NavMesh Multi-Zones, Rayon 9 500 m & Visibilité Client) — validé & testé** —
  - **Anneau & Autonomie Exploration (`explore_ring_lh.json` & `hub_bot_autonomy.gd`)** :
    - `max_radius_m` et `RING_RADIUS_FALLBACK` portés de 6 500 m à **9 500 m** (couvrant largement l'Avant-poste Zalem à l'ouest et le Ksar Nomade au sud sans clamp radial artificiel).
    - Ajout de 6 waypoints d'exploration locaux pour les deux villages (`zalem_route_patrol`, `zalem_dunes_west`, `zalem_relais_nord`, `ksar_oasis_south`, `ksar_dunes_east`, `ksar_route_caravane`).
    - Échantillonnage d'exploration `_random_ring_pos(bot)` contextualisé : exploration locale à proximité de Zalem (-1200, -550) ou Ksar Nomade (4950, -3800) quand les bots patrouillent ces secteurs.
  - **NavMesh 3D Multi-Zones Recast (`hub_nav.gd`)** :
    - Refactorisation de `HubNav` en 3 sous-régions Recast indépendantes (`lost_heaven`, `zalem_outpost`, `ksar_nomade`) unifiées sous la même `map` NavigationServer3D.
    - Performance Recast préservée : bake synchrone déterministe en **696 ms** au total (3 régions, 309 polygones, 26 obstacles de village), zéro régression CI.
    - Résolution de trajectoires intra-bourg C++ instantanée (40 entités / tick en 1,7 ms, soit 44 µs/entité).
    - Sécurisation du fallback A* inter-zones dans `hub_collision.gd` (`max_expand = 800`).
  - **Visibilité Client (`hub_focus.gd` & `scrapaltai_map_config.json`)** :
    - Remplacement des 3 bulles isolées étanches par `in_explorable_zone(core3, 9500.0)` : toutes les entités du monde vivant (PNJ de village, bêtes sauvages, patrouilles IA) restent visibles le long des routes et dans le désert, tout en maintenant l'exclusion stricte du clutter et des 3 villes obsolètes SOE (Mos Eisley, Anchorhead, Bestine).
    - Rayon `hub_focus` aligné à 9 500 m dans `scrapaltai_map_config.json`.
  - **Tests & Preuves** :
    - 4/4 suites CI Godot headless validées à 100% en 5s (`ci_godot_headless.sh` : HubSim, NavMesh 3D, Persistance SQLite, Client DnD).

- 2026-10-14 : **Attribution & Intégration Remédiation Swap CT 111 à Atlas (`admin_infra`) — validé** —
  - **Diagnostic & Clôture Incident** : Swap de `ollama-light` (CT 111 sur Proxmox `.200`) tombé de 99.99% (2 Go saturés) à 0.5% (10 Mo). Responsable identifié : `lbg-laya-serve.service` (PyTorch CPU) dont les pages froides étaient envoyées en swap lors des pics en raison de `vm.swappiness=60`. Réglage pérennisé à `vm.swappiness=10` sur l'hôte Proxmox `.200`.
  - **Gouvernance Team** : Rôle formellement attribué à **Atlas** (`admin_infra`, responsable plateforme LLM locale), pas Dédale (`dev_game`, réservé au gameplay/forge).
  - **Intégration Moteur & Outillage** :
    - `remote_targets.py` : Alias `light`, `ollama-light`, `111` ajoutés dans `_ALIASES` et `_ROLE_ENV` (`192.168.0.111`).
    - `vm_memory_probe.py` : `("light", "111")` ajouté dans `_DEFAULT_HOSTS` pour surveillance continue automatique.
    - `admin_infra_platform.py` : Nouvelles fonctions `check_light_111_swap()` (détection sticky swap) et `remediate_light_111_swap()` (restart de `lbg-laya-serve` et maintien de `vm.swappiness=10` sur Proxmox .200). Détection de gap swap intégrée à `audit_admin_infra_platform()`.
    - `admin_infra_workflow.py` : Workstream `surveillance_swap_ram_light_111` actif, et déclenchement automatique de la remédiation si l'objectif de la tâche cible le swap/111.
    - `studio_admin_atlas.json` : Capacité `light_111_memory_swap` ajoutée au profil d'Atlas.
    - `lessons_learned.json` : Leçon `lesson_atlas_light_111_swap` consignée.
  - **Tests** : 16/16 tests unitaires passants (`test_admin_infra_platform.py` + `test_infra_memory_remediation.py`), `ruff check .` 100% vert.
- 2026-10-14 : **Repositionnement Géographique & 12 Bâtiments de Village (Ksar Nomade & Avant-poste Zalem) — validé & déployé live `.246:8787`** —
  - **Éloignement & Recalage géographique** :
    - *Avant-poste Zalem* déplacé plein Ouest à ~6 km de Lost Heaven : Core3 `(-1200.0, 0.15, -550.0)`, UV carte planétaire `{ "u": 0.525, "v": 0.465 }` (grid col 6, row 2) pile sur le nœud routier rouge menant à la capitale Zalem.
    - *Ksar Nomade* déplacé plein Sud le long de la boucle routière à ~3.1 km : Core3 `(4950.0, 0.15, -3800.0)`, UV carte planétaire `{ "u": 0.665, "v": 0.150 }` (grid col 8, row 1) sur le relais sud au pied des dunes.
    - Distance entre les deux villages portée à ~7 km.
  - **12 Bâtiments de village ajoutés (`lost_heaven_buildings.json`)** :
    - *Avant-poste Zalem* (6 structures) : Poste de commandement (`town_hall`, 64m), Atelier mécanique relais (`trainer_artisan`, 56m), Caserne de la milice (`trainers_combat`, 56m), Relais des convois (`inn`, 52m), Dépôt de ravitaillement (`shops`, 48m), Barrière ouest (`city_gate`, 40m).
    - *Ksar Nomade* (6 structures) : Grande Tente de l'Ancien (`town_hall`, 64m), Tente des soins & onguents (`clinic`, 52m), Bazar nomade & troc (`shops`, 60m), Caravansérail de l'Oasis (`inn`, 56m), Forge des sables (`trainer_artisan`, 48m), Arches de ferraille (`city_gate`, 40m).
    - Les bâtiments intègrent portes, gabarits AABB, toits et enseignes via le moteur de rendu `HubBuildingsLayer` et `BuildingTileRegistry`.
  - **Collision, Navmesh & Sécurité Recast** :
    - `hub_nav.gd` protégé : limitation du calcul des bounds de Recast au périmètre Lost Heaven (`3000..7000`, `-2000..100`), évitant l'explosion du temps de bake sur un mesh 8 km × 5 km (bake Recast maintenu à ~699 ms).
    - `collision_blocks` passe à 26 (tous les bâtiments bloquent le passage et offrent des passages de porte).
  - **Preuve & Déploiement** :
    - Tests headless CI Godot 18/18 checks OK en 6s (`ci_godot_headless.sh`), `ruff check .` vert.
    - Déploiement sur `.246:8787` (`deploy_prime_hub_246.sh`) : 26 collision blocks, PNJ spawnés sur leurs bâtiments respectifs, bots IA (Renn, Ori, Vex) en route active vers les avant-postes.
- 2026-10-13 : **Locomotion Bots IA & Répartition Factions sur 2 Nouveaux POI (O2 Jeu) — validé & déployé live `.246:8787`** —
  - **Déblocage bots IA (`hub_sim.gd`)** : Correction du bug d'anti-stuck où `stuck_ticks >= 6` réinitialisait systématiquement `stuck_ticks = 0`, empêchant d'atteindre le seuil de dégagement `stuck_ticks >= 12` et bloquant les bots dans une boucle infinie contre les obstacles. Préservation de `linger_until` pour des pauses de rôle naturelles de 3 à 7 s à destination.
  - **2 Nouveaux POI calés sur la carte planétaire** :
    - *Avant-poste Zalem* (`city:avant_poste_zalem`, `u: 0.565, v: 0.405`, Core3 `(2400.0, 0.15, -600.0)`) : relais fortifié sur la route rouge de la capitale. Accueille la **Milice locale** (Capitaine Vael) et les **Artisans** (Soren Kray).
    - *Ksar Nomade* (`city:ksar_nomade`, `u: 0.730, v: 0.220`, Core3 `(6850.0, 0.15, -1450.0)`) : campement et oasis de ferraille dans les dunes est au pied des montagnes. Accueille les **Civils du désert** (Ancien Nadir) et la **Confrérie des soins** (Miran Sael).
  - **Intégration moteur & données** : Inscrits dans `scrapaltai_planet_map.json` (Ctrl+M), `scrapaltai_pois.json`, `catalog_poi.json`, `hub_sim_defs.gd` (`POIS` + `HUB_NPCS`), `triplons.json` (solos), `npc_registry.json`, `explore_ring_lh.json` et préférences de voyage des bots dans `ai_players.json`.
  - **Rendu Client (`entity.gd` & `hub_focus.gd`)** : Ajout du micro-bobbing de marche pour les bots en mouvement, orientation `flip_h` automatique selon la vélocité horizontale, et autorisation des rayons outposts dans `hub_focus.gd` pour afficher les PNJ distants sans fuite de clutter legacy.
  - **Preuve & Déploiement Live** : Tests headless CI Godot (`ci_godot_headless.sh`) 100% verts en 3s. Déploiement live sur `.246:8787` via `deploy_prime_hub_246.sh`. Sonde live `/v1/bots` mesurée : **10/10 bots en déplacement actif et exploration fluide** (ex: Mira en route vers Ksar Nomade à 33 m en 3s, Lia libérée vers le sud à 34.5 m).
- 2026-10-14 : **O-CTX-HYGIENE + C2** — A1–A3 · B1 · C1 nameplates · **C2** `hub_activity.gd` (`status` idle/busy/quest + `activity` dans zone_state slim) · D1 coûts · selftest `ACTIVITY_SELFTEST_OK` · deploy hub `:8787` + sync client.
- 2026-10-14 : **O-CTX-HYGIENE clos & déployé** — A1 journal `context_journal` · A2 Respire/nouveau fil · A3 `studio_brain_v1` (~1,6 Ko) · B1 prefs monde · C1 nameplates joueur unifiées · D1 `cost` craft/use · deploy CT100 + hub + sync client `.140`.
- 2026-10-14 : **O-JEUX-HOTBAR** — slots compétence=craft kit · objet=`/v1/inventory/use` · emote=`/v1/say` · compagnon=`/v1/companion/escort` · inventaire clic utilisable · `HOTBAR_API_SELFTEST_OK`.
- 2026-10-14 : **O-JEUX-SHOW (P2c)** — `hub_show.gd` · tip live · formation Talen · live `:8787`.
- 2026-10-14 : **O-JEUX-ESCORT clos & live** — civil suivable porte→clinique.
- 2026-10-13 : **Alignement docs périmées (audit)** —
  - [`REGISTRE.md`](REGISTRE.md) : packages `prime-hub` / `compagnon-desktop` ; autorité joueur **`:8787`** ; `:8792` = lab Core3 OFF ; matrice mermaid + jalons oct. ;
  - [`RESTAURATION_PRODUIT.md`](RESTAURATION_PRODUIT.md) : Rang 2 P3/dialogue/hub **vert** ; Core3 sidecar **rouge** ; prochaine traction = backlog léger (O-OPS-3, polish, unification client) ;
  - [`RUNTIME_GODOT.md`](RUNTIME_GODOT.md) : section « suite » scindée **fait** vs **ouvert** (plus de P3/P5 listés comme TODO) ;
  - [`SMOKE_LAN.md`](SMOKE_LAN.md) en-tête + libellé Compagnon `:5174` ; [`README.md`](../README.md) remotes liés.
- 2026-10-13 : **Fiabilisation LLM veille (O-VEIL-4) & Agrégat métriques 7j Fleet (O-OPS-2) — validés & clôturés** —
  - **O-VEIL-4 (Route LLM veille)** : Injection du paramètre natif `"format": "json"` pour Ollama et `"response_format": {"type": "json_object"}` dans `reason_llm.py` pour le profil `json` ; calcul dynamique du timeout (`min(150, max(45, n_input * 15))`) et `max_tokens` dans `evolution_veille_workflow.py` proportionnels au nombre de pistes (pour éviter les timeouts constatés sur les batchs de 8 pistes) tout en conservant le fallback heuristique ultra-rapide. Tests 5/5 validés.
  - **O-OPS-2 (Agrégat métriques 7j Fleet)** : Calcul d'une fenêtre glissante de 7 jours sur les jobs Cowork (`jobs_7d`), tâches virtuelles Team (`tasks_7d`, L2 pending), stabilité de la mission L3 LAN et décision du pilote Ops Health. Exposé sous `metrics_7d` et `metrics.rolling_7d` dans `team/fleet.py`. Critère DoD §6 dans [`plan_combler_gaps_agentiques.md`](../packages/cortex/docs/plan_combler_gaps_agentiques.md) et [`revue_ops_health_7j.md`](../packages/cortex/docs/revue_ops_health_7j.md) passés à 100% OK. Tests 6/6 validés.
- 2026-10-13 : **Mapping Agentic RAG (O-VEIL-3) — validé & clôturé** —
  - Rédaction du document de cadrage architectural L1 [`agentic_rag_mapping.md`](../packages/cortex/docs/agentic_rag_mapping.md) démontrant la correspondance directe des concepts Agentic RAG sur nos briques natives : routeur d'intentions (`router_prompts.py`), bus SQLite Team (`team_tasks`/`team_messages`), mémoire Compagnon et World Stream (`:8787`). Respect strict de la règle : zéro framework tiers lourd sur le chemin critique.
- 2026-10-13 : **Harmonisation Doc & Retrait SOE (O-DOC-1, O-JEUX-3) — validé & clôturé** —
  - **O-DOC-1 ([`OBJECTIVES.md`](../OBJECTIVES.md))** : Canon harmonisé — clarification formelle : le Compagnon Studio (présence) s'incarne sur `:5174` (`compagnon_ui`) et l'application Desktop Electron (`packages/compagnon-desktop`), tandis que Pilot (`:8080`) est le cockpit ops / méta-autonomie. Smoke LAN 24/24 surfaces OK mis à jour.
  - **O-JEUX-3 ([`PLAN_MMO_O2.md`](PLAN_MMO_O2.md) & [`PRIORITES_ACTUELLES.md`](PRIORITES_ACTUELLES.md))** : Jalon P4 formellement clos. Retrait définitif du pont SOE/Core3 et confirmation de l'autorité exclusive du runtime Godot headless G5+ (`:8787` unifié HTTP+WS).
- 2026-10-13 : **Veille Évolution (O-VEIL-1, O-VEIL-2) — validé & clôturé** —
  - **O-VEIL-1 (DeepSeek Harness / dsh_headless)** : Suite aux résultats de la veille et au constat de charge CPU sur `.110` (O-IDE-2), formalisation de l'ADR 0028 actant un **NO-GO** pour toute greffe `dsh_headless` dans Cortex/Team (OpenCode étant le nominal éprouvé et aucun Node.js n'étant toléré sur 140). DSH reste strictement réservé au poste exploratoire dev `.10`. ADR 0020 clos.
  - **O-VEIL-2 (VoiceStudio / TTS LAN Compagnon)** : Évaluation de VoiceStudio / modèles de clonage vocal lourds (F5-TTS/Chatterbox) : rejet de tout déploiement lourd sans GPU audio dédié. Maintien et validation de la stack nominale de production existante documentée dans [`voice_local.md`](../voice_local.md) : **Edge TTS** (primaire `fr-FR-DeniseNeural` 0 €) + **Piper** LAN `.111:8098` (fallback local ultra-léger).
- 2026-10-13 : **Ops LAN (O-OPS-1) — validé & clôturé** —
  - `tools/smoke_lan_surfaces.sh` modernisé : intégration de l'autorité jeu G5+ Godot-first sur `.246:8787` (`/healthz` et `/v1/events/active`) en vérification nominale ; tolérance gracieuse des sondes Core3/PreCU `:8792` dépréciées (OFF par ADR 0026).
  - Validation complète bout-en-bout avec `bash tools/smoke_lan_surfaces.sh --functional` : **24 OK, 1 WARN (clé cloud), 0 KO**. Pilot Studio, Cockpit P03, Orch UI 5174, Orch API :3000, WebUI 3080, Godot Hub :8787, Patches, MCP, Team WSL, Desktop dry-run route, Cockpit Desktop réel, et Team bus (6/6) tous au vert.
- 2026-10-13 : **Autonomie Campus / CI / desktop (O-CAMP-1, O-CAMP-2, O-D7-1) — validé & clôturé** —
  - **O-CAMP-1 (Audit tickets plan)** : `tools/suivi_plan_evolutions.py --audit` exécuté avec succès : 10/10 tickets DONE, `plan_complete: true`, `orphan_failed: []`, aucun faux done.
  - **O-CAMP-2 (Deploy overlay CT100 & Pilot 140)** : Vérification de cohérence OK, CT 100 à jour, Pilot Web sur `.140` répond 200 OK sur `:8080/` et Orchestrateur `:8010/healthz` OK.
  - **O-D7-1 (Présence Agents D7 sur worker .143)** : Injection de `LBG_SESSION_ISLAND_ENABLED=1`, `LBG_SESSION_ISLAND_FAIL_OPEN=1`, `LBG_SESSION_ISLAND_APPROVAL_TIMEOUT_S=60` pérennisés dans `deploy_linux_agent_143.sh`, `session_emitter.py` complété pour résolution dynamique via `_get_cfg`, `EnvironmentFile` ajouté dans le service systemd `lbg-omarchy-agent.service`. Tests 4/4 verts. Endpoint `http://192.168.0.143:5005/session/status` vérifié live : `enabled: true`, `socket_alive: true` (`/run/user/1000/lbg-presence-agents.sock`).
- 2026-10-13 : **mains code Cline / perf Ollama .110 / décision ADR (O-IDE-1..3) — validé & clôturé** —
  - **O-IDE-1 (Smoke live bout-en-bout)** : Preuve d'exécution complète validée depuis l'Orchestrateur Team (`:8010`) vers l'agent Linux `.143:5005` (`run_cli_agent app=cline`) déclenchant `/home/lbg/.local/bin/cline` avec le modèle `huihui_ai/gemma-4-abliterated:E4b-qat` vers Ollama `.110:11434`.
  - **O-IDE-2 (Mesure de perf & diagnostic VRAM)** : Constat chiffré sur `.110` via `ollama ps` : `size_vram: 0` (exécuté 100 % en RAM CPU) avec 32k context. La latence CPU dépasse 350 s par tour, provoquant le timeout du client Cline (`Error: The operation timed out` à 357 s). Respect strict de la matrice locale : interdiction de descendre sous `E4b-qat` (plancher qualité de codage).
  - **O-IDE-3 (Décision formelle ADR 0025)** : OpenCode headless (`opencode run -m opencode/big-pickle`) est formellement maintenu comme **nominal de production** pour les mains de code Team (Métis / Iris / Dédale). Cline CLI reste un outil de **second avis / option locale 0 € API** prêt pour le jour où `.110` disposera d'accélération VRAM GPU.
  - Documents mis à jour : [`packages/cortex/docs/cline/CLI_SECOND_AVIS.md`](../packages/cortex/docs/cline/CLI_SECOND_AVIS.md), [`packages/cortex/docs/adr/0025-mains-code-143-run-cli-agent.md`](../packages/cortex/docs/adr/0025-mains-code-143-run-cli-agent.md), [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md).
- 2026-10-12 : **polish retour terrain longue durée Compagnon (O-FEEL-3) — validé & clôturé** —
  - `presence_report.py` enrichi : regex de détection étendue aux tournures naturelles de fil long (« comment réagissent les personas sur le terrain », « des nouvelles de Lia »).
  - Personnalisation dynamique du retour terrain selon le persona ciblé (`_persona_from_prompt`), avec conservation du comparatif équilibré Nix vs Mira par défaut.
  - Garantie anti-ops stricte : en cas de hub de jeu inaccessible, réponse collègue fluide sans fuite d'exception brute, de numéro de port (`:8787`) ni de commande bash.
  - `presence_brief.py` nettoyé de toute mention de tâche shell en fallback.
  - Suite de tests unitaire étendue (9/9 tests verts), build atomique `1.0.0+f346979` déployé sur CT 100 (`192.168.0.100:5174`), smokes de rejeu terrain et rejeu humain 7 tours (`smoke_rejeu_humain_d6_5174.sh`) validés 100 % PASS.
- 2026-10-12 : **initialisation outillage MCP REA (Reverse Engineer Anything) — matrice multi-environnements** —
  - Configurations dédiées créées : [`.cursor/mcp.json`](../.cursor/mcp.json) (Cursor), [`.agents/mcp_config.json`](../.agents/mcp_config.json) (Antigravity), [`.mcp.json`](../.mcp.json) (Claude Code, OpenCode), [`.vscode/cline_mcp_settings.json`](../.vscode/cline_mcp_settings.json) (Cline).
  - Wrapper Studio / CLI exécutable créé dans [`tools/rea_runner.sh`](../tools/rea_runner.sh) pour les agents backend/Team (Iris, Métis).
  - Documentation de référence complète dans [`docs/OUTILS_DEV_MCP.md`](OUTILS_DEV_MCP.md) et référencée dans [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md).
  - Outil 100 % local-first réservé à l'audit et à l'ingénierie Dev/Studio (O1), sans impact sur le runtime joueur Godot O2.
- 2026-10-21 : **Rendu Métallique Multi-Plaques & Réharmonisation Complète (Bras, Jambes, Buste v19) — validé & déployé** —
  - **Prise en compte des nouvelles plaques d'armure mecha** :
    - Intégration de l'ensemble des plaques créées par l'utilisateur : coiffes d'épaules, brassards hexagonaux à rivets, plaques de biceps, avant-bras/coudes, cuisses et mollets (130 218 pixels de plaques ombrés au micron près).
    - Nettoyage et symétrisation parfaite du dôme gauche de poitrine (élimination de la zone sombre mouchetée manuelle, alignement symétrique strict avec le dôme droit autour de `X = 512`).
  - **Réapplication des couleurs et du galbe 3D métallique** :
    - Calcul des normales de surface 3D sur chaque plaque (heightmap multi-échelle et dégradés sphériques Blinn-Phong pour les seins).
    - Application de la texture titane satiné mecha : highlights spéculaires zénithaux doux (`RGB 190..235, 220..245, 240..255`), corps de pièce titane poli (`RGB 60..110, 95..160, 145..215`) et ombres de chanfrein.
    - Zéro bavure : les délimitations entre plaques et combinaison restent découpées au rasoir.
  - **Protection absolue des composants technologiques** :
    - 0 pixel altéré sur les liserés néon cyan (`#00f5d4`), les rivets circulaires, les connectiques noires, et les ongles bicolores magenta/cyan.
  - **Shader & Déploiement multi-surfaces synchronisé** :
    - Recompilation `esbuild` de `vrm_pet.bundle.js` (2.1 MB) avec cache-buster `?v=mecha_v19`.
    - `Desktop SDS .10` : synchronisation locale dans `C:\Agent_IA\compagnon-desktop\overlay\vrm\` et redémarrage de l'overlay Electron (PID validé : **33004**).
    - `N:\Upload\IA\` : `body_skin_android.png` réharmonisé et bundle exportés.
    - `CT100 (192.168.0.100)` : injection docker dans `lbg-frontend:/usr/share/nginx/html/vrm/`.
- 2026-10-21 : **Rendu Métallique sur `body_skin_android_5b.png` (Zonage Vert Clair Exclusif v18) — validé & déployé** —
  - **Précision chirurgicale sur les zones Vert Clair (`Lime Green`)** :
    - Détection chromatique exacte (`R: 136..181, G: 187..234, B: 29..75`) à partir du calque d'annotation fourni par l'utilisateur (99 521 pixels de plaques ciblés).
    - Application de la texture métallique 3D cuite (lustre titane satiné avec reflets zénithaux spéculaires) **exclusivement** sur ces 99 521 pixels.
    - Élimination de 100 % des risques de bavure : l'algorithme ne touche à aucun pixel en dehors de ce zonage.
    - Préservation intégrale et absolue de tous les autres éléments de `body_skin_android_5b.png` : épaulières, sangles en X au centre bas, ongles de mains et de pieds (magenta/cyan), liserés néon cyan (`#00f5d4`), joints noirs de découpe, abdomen central sombre et flancs.
  - **Shader MToon** :
    - Maintien du cel-shading direct haute fidélité (`rimLightingMix = 1.0`, zéro matcap/rim 3D qui bave).
    - Cache-buster mis à jour à `?v=mecha_v18` et bundle `vrm_pet.bundle.js` recompilé avec `esbuild`.
  - **Déploiement multi-surfaces synchronisé** :
    - `Desktop SDS .10` : synchronisation locale dans `C:\Agent_IA\compagnon-desktop\overlay\vrm\` et redémarrage de l'overlay Electron (PID validé : **31816**).
    - `N:\Upload\IA\` : `body_skin_android.png` (métallisé sur zones vert clair), `body_skin_android_5b.png` (source d'origine), `metallic_matcap.png`, `vrm_pet.bundle.js` exportés.
    - `CT100 (192.168.0.100)` : injection docker dans `lbg-frontend:/usr/share/nginx/html/vrm/`.
- 2026-10-21 : **Rendu Métallique Direct sur Skin 2D (Masque Utilisateur au Pixel Près, Zéro Bavure v17) — validé & déployé** —
  - **Application directe du lustre métallique dans `body_skin_android.png`** :
    - Intégration du pochoir nettoyé par l'utilisateur (`media_1792579921395.png`, 524 016 pixels de plaques au pixel près).
    - Cuisson du reflet 3D (baking des normales de surface et courbures de dômes du modèle `Compagnon.vrm`) directement dans les teintes de la texture 2D diffuse.
    - Élimination de 100 % des bavures : les délimitations entre les plaques titane et la combinaison noire ou la peau sont désormais au rasoir.
    - Préservation intégrale des liserés néon cyan (`#00f5d4`), des joints noirs d'armure, des rivets, des ongles magenta/cyan et de la texture mate des bras et des jambes.
  - **Shader MToon épuré** :
    - Retrait du MatCap et du Rim dynamique additif sur le corps (`m.matcapTexture = null`, `m.rimMultiplyTexture = null`, `m.parametricRimColor = 0x000000`, `rimLightingMix = 1.0`).
    - L'avatar s'affiche en cel-shading ultra-net, avec des plaques métalliques riches en reflets 2D intégrés sans aucune lueur parasite.
  - **Cache-Buster & Recompilation** :
    - Cache-buster mis à jour à `?v=mecha_v17`.
    - Recompilation `esbuild` de `vrm_pet.bundle.js` (2.1 MB).
  - **Déploiement multi-surfaces synchronisé** :
    - `Desktop SDS .10` : synchronisation locale dans `C:\Agent_IA\compagnon-desktop\overlay\vrm\` et redémarrage de l'overlay Electron (PID validé : **41948**).
    - `N:\Upload\IA\` : `body_skin_android.png` directement métallisé, `metallic_matcap.png`, `rim_multiply_mask.png`, `vrm_pet.bundle.js` exportés.
    - `CT100 (192.168.0.100)` : injection docker dans `lbg-frontend:/usr/share/nginx/html/vrm/`.
- 2026-10-21 : **Rendu Métallique Sélectif sur Plaques Uniquement & Élimination des Rayures (v16) — validé & déployé** —
  - **Masque de modulation sélective géométrique (`rim_multiply_mask.png`)** :
    - Extraction directe de la géométrie 3D de `Compagnon.vrm` (primitives, indices et weights de bones) pour isoler les coordonnées UV du tronc (poitrine/dômes, sternum, abdomen, dos/scapula, hanches/pelvis).
    - Exclusion géométrique à 100 % de tous les membres : bras, mains, jambes, pieds, ongles et combinaison noire sous-jacente.
    - Génération du masque HD 2048×2048 (`white = 1.0` sur les plaques de blindage, `black = 0.0` sur les bras, jambes et tissu).
    - Branchement shader natif MToon via Three.js : `m.rimMultiplyTexture = rimMultiplyMaskTex` dans `vrm_pet.js`. Le shader calcule `rim *= texture2D(rimMultiplyTexture, uv)`, annulant à 100 % le matcap et les reflets spéculaires sur les bras et les jambes (qui redeviennent mats en cel-shading doux) tout en magnifiant le lustre métallique miroir sur les plaques de blindage.
  - **Suppression des rayures sur le MatCap Chrome (`metallic_matcap.png`)** :
    - Remplacement du matcap à méridien coupé par un dégradé sphérique continu Blinn-Phong studio (titane satiné, reflet zénithal doux et halo Fresnel sur les chanfreins).
    - Élimination complète de la sensation de rayure horizontale en travers de la poitrine.
  - **Recompilation & Cache-Buster** :
    - Passage au cache-buster `?v=mecha_v16` sur l'ensemble des textures.
    - Recompilation `esbuild` de `overlay/vrm/vrm_pet.bundle.js` (2.1 MB) et réplication dans `packages/cortex/compagnon_ui/public/vrm/`.
  - **Déploiement multi-surfaces synchronisé** :
    - `Desktop SDS .10` : `C:\Agent_IA\executor.py` mis à jour, synchronisation locale de toutes les textures et du bundle dans `C:\Agent_IA\compagnon-desktop\overlay\vrm\`, overlay Electron relancé avec succès (nouveau PID vérifié : **10764**).
    - `N:\Upload\IA\` : `body_skin_android.png`, `metallic_matcap.png`, `rim_multiply_mask.png`, `vrm_pet.bundle.js` exportés via l'agent.
    - `CT100 (192.168.0.100)` : injection docker dans `lbg-frontend:/usr/share/nginx/html/vrm/` (`body_skin_android.png`, `metallic_matcap.png`, `rim_multiply_mask.png`, `vrm_pet.bundle.js`).
- 2026-10-21 : **Agrandissement Tête Chibi (+68%, scale 1.68) & Roadmap 3D Découpage Réel — validé & déployé** —
  - **Agrandissement supplémentaire de la tête** : Passage de `headBone.scale` de 1.52 à **1.68** (+68%) dans `vrm_pet.js`, pour un look chibi encore plus affirmé et proportionné.
  - **Cadrage dynamique** : Marge supérieure portée à 1.12 (`neededH = size.y * 1.12`) pour une respiration parfaite au-dessus de la chevelure.
  - **Roadmap 3D notée** : Prévoir ultérieurement sous Blender un véritable découpage géométrique en pièces indépendantes de carrosserie mecha (inspiré Robocop / Gynoïde) avec fentes creuses physiques et volumes biseautés réels dans le maillage 3D.
  - **Déploiement multi-surfaces synchronisé** :
    - `Desktop SDS .10` : bundle recompilé avec `esbuild`, déployé via l'agent Windows et Electron redémarré avec succès (PID vérifié : **26236**).
    - `N:\Upload\IA\` : export direct du bundle synchronisé.
    - `CT100 (192.168.0.100)` : injection docker dans `lbg-frontend:/usr/share/nginx/html/vrm/`.
- 2026-10-21 : **Agrandissement Tête Chibi (+52%, scale 1.52) — validé & déployé** —
  - **Agrandissement de la tête** : Passage de `headBone.scale` de 1.38 à **1.52** dans `vrm_pet.js`, renforçant davantage la silhouette chibi mignonne et expressive demandée par l'utilisateur.
  - **Cadrage dynamique** : Marge supérieure portée à 1.10 (`neededH = size.y * 1.10`) pour assurer une respiration confortable au-dessus des cheveux sans clipping.
  - **Déploiement multi-surfaces synchronisé** :
    - `Desktop SDS .10` : bundle recompilé avec `esbuild`, déployé via l'agent Windows et Electron redémarré avec succès (PID vérifié : **42696**).
    - `N:\Upload\IA\` : export direct du bundle synchronisé.
    - `CT100 (192.168.0.100)` : injection docker dans `lbg-frontend:/usr/share/nginx/html/vrm/`.
- 2026-10-21 : **Jonction et Lissage des Plaques du Haut de Cuisse v26 — validé & déployé** —
  - **Suppression du gap de 20 px et fusion des plaques supérieures de cuisse** : Comblement continu de Y=497 à Y=523 dans les colonnes gauche (X: 66..178) et droite (X: 846..958) par une interpolation Hermite fluide (smoothstep).
  - **Lissage morphologique (rayon 2.5 px)** de la zone de raccordement pour éliminer toute démarcation ou rupture visuelle.
  - **Prolongation continue du liseré néon cyan** sur toute la bordure extérieure de la grande plaque de cuisse unifiée.
  - **Recalcul du galbe cylindrique 3D Blinn-Phong** continu sur la plaque fusionnée pour assurer une réflexion spéculaire satinée ininterrompue.
  - **Déploiement multi-surfaces synchronisé** :
    - `Desktop SDS .10` : texture et bundle recompilés avec `esbuild`, déployés via l'agent Windows et Electron redémarré avec succès (PID vérifié : **35984**).
    - `N:\Upload\IA\` : export direct des fichiers synchronisés.
    - `CT100 (192.168.0.100)` : injection docker dans `lbg-frontend:/usr/share/nginx/html/vrm/` avec cache-buster `?v=mecha_thigh_joined_v26`.
- 2026-10-21 : **Carrosserie Mecha Master v25 (Correspondance Complète Torse <-> Membres) — validé & déployé** —
  - **Prise pour référence absolue du design de l'utilisateur (`media_1792615448352.png`)** :
    - Préservation à 100% du travail sur le torse : col montant avec néon, seins galbés, 5 segments d'abdominaux centraux, 6 plaques de côtes latérales gauche et droite avec rivets et néons cyan, coque pelvienne en V, et épaulettes hexagonales.
  - **Correspondance stylistique complète sur tous les membres** :
    - *Avant-bras* : Liserés néon cyan sur les arêtes et fente médiane horizontale assortie aux épaulettes.
    - *Cuisses* : Liseré néon cyan de contour et fente aérodynamique le long du muscle vaste externe.
    - *Rotules de genoux* : Rotules circulaires mécaniques cerclées de néon cyan avec rivet d'ancrage central (assorties aux rivets d'épaules et de hanches).
    - *Tibias / Mollets* : Liserés néon cyan le long de l'arête tibiale descendante.
  - **Lustre Titane 3D Blinn-Phong unifié** : Rendu volumétrique avec galbe cylindrique et sphérique continu sur les 296 548 pixels de plaques, reflets métalliques satinés Three.js sans aucune disparité entre les membres et le torse.
  - **Déploiement multi-surfaces synchronisé** :
    - `Desktop SDS .10` : texture et bundle recompilés avec `esbuild`, déployés via l'agent Windows et Electron redémarré avec succès (PID vérifié : **36724**).
    - `N:\Upload\IA\` : export direct des fichiers synchronisés.
    - `CT100 (192.168.0.100)` : injection docker dans `lbg-frontend:/usr/share/nginx/html/vrm/` avec cache-buster `?v=mecha_master_v25`.
- 2026-10-21 : **Carrosserie Full Cyborg Armor 360° (Bustier Leotard, Rotules de Hanches & Plaques Enveloppantes) — validé & déployé** —
  - **Transformation complète d'après les références (Images 4 & 5)** : Élimination définitive de l'effet "pastilles isolées collées sur combinaison". L'armure enveloppe maintenant 70% du corps avec des pièces maîtresses continues et fonctionnelles.
  - **Sculpture Mecha Haut de Gamme 360°** :
    - *Bustier Leotard Mecha Continu* : Col montant sous la gorge, plastron rigide réunissant les seins d'un seul tenant avec arche sous-mammaire, 5 tablettes de blindage abdominales mécatroniques sculptées avec fentes de séparation, liserés néon cyan verticaux le long des flancs (style Image 4), et coque pelvienne haute en ogive protectrice.
    - *Rotules Circulaires de Hanches (Hip Pivots)* : Deux gros pivots mécaniques concentriques sur les têtes de fémurs avec gorge d'ombre circulaire et anneau néon (détail signature cyborg des images 4 et 5).
    - *Cuisses Enveloppantes avec Panel Lines Industrielles* : Grandes plaques fémorales couvrant 70% de la cuisse avec rainures de découpe aérodynamiques le long du muscle vaste externe (style Robocop/Image 5).
    - *Rotules de Genoux et Coudes Concentriques* : Articulations circulaires mécaniques doubles avec bague de gorge et anneau néon.
    - *Dos 360° Complet* : Grandes carapaces scapulaires continues, colonne vertébrale en exosquelette de modules vertébraux titane avec disques d'amortissement et diodes neurales cyan, et double coque galbée d'armure fessière.
    - *Fillet Morphologique (rayon 3.5 px)* : aucun angle vif, aspect de métal coulé liquide poli.
  - **Déploiement multi-surfaces synchronisé** :
    - `Desktop SDS .10` : texture et bundle recompilés avec `esbuild`, déployés via l'agent Windows et Electron redémarré avec succès (PID vérifié : **47724**).
    - `N:\Upload\IA\` : export direct des fichiers synchronisés.
    - `CT100 (192.168.0.100)` : injection docker dans `lbg-frontend:/usr/share/nginx/html/vrm/` avec cache-buster `?v=cyborg_armor_v3`.
- 2026-10-21 : **Carrosserie Sorayama Curves Master 360° (Courbes Pures & Zéro Carré) — validé & déployé** —
  - **Élimination complète des formes carrées et arêtes dures** : Recalcul intégral des contours par des équations de courbes continues (S-curves de sablier, fuseaux hermitiens, super-ellipses et arcs concaves).
  - **Sculpture anatomique sensuelle & fluide (Style Sorayama pur)** :
    - *Buste & Décolleté* : Dômes pectoraux en goutte d'eau galbée, plastron en cloche douce descendant du cou, et arceau sous-mammaire concave continu.
    - *Taille de guêpe en S-Curve* : Cambrure de sablier continue (largeur passant de 132 px sous les seins à 72 px au creux de la taille, puis s'évasant à 144 px sur le bassin), dégageant les flancs en composite sombre à fibres synthétiques.
    - *Pelvis en ogive gothique adoucie* : Coque en goutte d'eau descendante vers l'entrejambe avec liseré cyan galbé, flanquée d'ailes iliaques arquées.
    - *Membres en fuseaux aérodynamiques* : Épaules sphériques, biceps et avant-bras en amandes galbées, rotules de coudes et de genoux circulaires concentriques parfaites, carénage fémoral en goutte d'eau voluptueuse et lames tibiales effilées.
    - *Dos 360°* : Omoplates ailées, chaîne vertébrale de modules ovoïdes bombés avec diodes cyan, et double coque fessière voluptueuse aux contours parfaitement arrondis.
    - *Fillet morphologique (rayon 3 px)* : élimination de toute arête vive par lissage gaussien et ré-échantillonnage pour un aspect de métal coulé liquide.
  - **Déploiement multi-surfaces synchronisé** :
    - `Desktop SDS .10` : texture et bundle recompilés avec `esbuild`, déployés via l'agent Windows et Electron redémarré avec succès (PID vérifié : **5888**).
    - `N:\Upload\IA\` : export direct des fichiers synchronisés.
    - `CT100 (192.168.0.100)` : injection docker dans `lbg-frontend:/usr/share/nginx/html/vrm/` avec cache-buster `?v=sorayama_curves_v2`.
- 2026-10-21 : **Carrosserie Sorayama Chrome Master 360° Face & Dos (207 788 px chromés) — validé & déployé** —
  - **Finition Chrome Argenté Miroir / Titane Liquide (Style Sorayama)** : Remplacement complet des aplats bleus par une carrosserie argentée haut de gamme (`RGB ~ [205, 218, 230]` à `[248, 252, 255]`), sculptée selon les courbes anatomiques sensuelles de Hajime Sorayama, avec reflets spéculaires étirés et dégradés de modelé volumétrique.
  - **Couverture 360° Face & Dos complète (à partir du gabarit UV vert)** :
    - *Face* : Dômes pectoraux sphériques galbés d'un seul tenant, plastron sternal rigide, arceau sous-mammaire continu, abdomen fuselé à 3 anneaux aérodynamiques, coque pelvienne en V, épaulettes deltoïdes, biceps/avant-bras fuselés avec rotules de coude articulées, carénage fémoral avant, rotules de genoux cerclées et plaques tibiales élancées avec crête saillante.
    - *Dos (360°)* : Colonne vertébrale mécatronique articulée avec disques intervertébraux noirs et canal neural cyan le long de la couture médiane, grandes plaques d'omoplates (scapula) galbées, double coque fessière carénée galbée, et carénage postérieur des mollets.
    - *Châssis sombre mécatronique* : Flancs de la taille, plis des coudes et genoux, aine et cou en composite anthracite sombre texturé avec striures musculaires synthétiques (taille de guêpe ultra contrastée).
  - **Déploiement multi-surfaces synchronisé** :
    - `Desktop SDS .10` : texture et bundle recompilés avec `esbuild`, déployés via l'agent Windows et Electron redémarré avec succès (PID vérifié : **21036**).
    - `N:\Upload\IA\` : export direct des fichiers synchronisés.
    - `CT100 (192.168.0.100)` : injection docker dans `lbg-frontend:/usr/share/nginx/html/vrm/` avec cache-buster `?v=sorayama_v1`.
- 2026-10-21 : **Redistribution Mecha Anatomique & Agrandissement Chibi v22 (138 238 px de plaques) — validé & déployé** —
  - **Agrandissement tête Chibi (+38%)** : Passage de `headBone.scale` à 1.38 (`vrm_pet.js`), renforçant la silhouette chibi mignonne et expressive, avec cadrage dynamique préservant la marge supérieure (+8%).
  - **Redistribution fidèle aux références mecha/cyborg** :
    - *Buste & Sternum* : Dômes pectoraux galbés avec liserés néon cyan émissifs (`#00f5d4`) et plastron central rigide.
    - *Abdomen fuselé & Flancs libres* : Plaque ventrale centrale effilée en flèche vers le bas, dégageant intégralement les flancs en sous-combinaison sombre texturée avec câbles musculaires synthétiques (taille de guêpe svelte).
    - *Pelvis en V & Hanches* : Coque pelvienne centrale en V avec liseré cyan, rotules de hanches et creux de l'aine en mécanique sombre.
    - *Bras & Coudes* : Épaulettes deltoïdes et plaques externes de biceps et avant-bras, avec articulation du coude (bande sombre de 66 px) et poignet dégagés.
    - *Jambes & Genoux* : Plaques fémorales (avant cuisses) s'arrêtant au-dessus du genou, genouillères/rotules articulées indépendantes avec anneau néon, plaques tibiales élancées et plaques de mollets externes.
  - **Déploiement multi-surfaces synchronisé** :
    - `Desktop SDS .10` : textures et bundle recompilé avec `esbuild` déployés, overlay Electron relancé (PID 46204).
    - `N:\Upload\IA\` : export direct des fichiers synchronisés.
    - `CT100 (192.168.0.100)` : injection docker dans `lbg-frontend:/usr/share/nginx/html/vrm/` avec cache-buster `?v=mecha_v22`.
- 2026-10-21 : **Harmonisation Intégrale de la Carrosserie & Plaques Mecha v20 (316 346 px unifiés) — validé & déployé** —
  - **Unification totale des plaques torse & membres** : Résolution du filtre néon trop permissif qui excluait accidentellement les membres (bras/jambes restés plats à luminance ~161). Réintégration complète de l'ensemble des 316 346 pixels de plaques d'armure avec une luminance harmonisée cible (~139-143 sur le torse/épaules/pelvis/biceps, ~146-154 sur les membres).
  - **Heightmap 3D et Normales Blinn-Phong homogènes** : Galbe sphérique continu sur les seins et modelé cylindrique doux sur les membres (radius 85 px), conférant un lustre titane satiné mecha 3D parfaitement unifié sans rupture visuelle.
  - **Préservation stricte au pixel près** : 100 % des néons cyan luminescents (`#00f5d4`), rivets circulaires 3D, coutures mécaniques sombres et ongles des mains/pieds préservés sans aucune bavure.
  - **Déploiement multi-surfaces synchronisé** :
    - `Desktop SDS .10` : synchronisation locale dans `C:\Agent_IA\compagnon-desktop\overlay\vrm\` et redémarrage de l'overlay Electron (PID 47252).
    - `N:\Upload\IA\` : export direct des assets (`body_skin_android.png`, bundle `vrm_pet.bundle.js`).
    - `CT100 (192.168.0.100)` : injection docker dans `lbg-frontend:/usr/share/nginx/html/vrm/` avec cache-buster `?v=mecha_v20`.
- 2026-10-21 : **Rendu Métallique Mecha Master v15 (Suppression des rayures & Lustre Lisse Harmonisé) — validé & déployé** —
  - **Correction des rayures** : Élimination complète des formules de micro-brossage sinusoïdal et des biseaux 1-pixel qui généraient un aspect de rayures / griffures sur les plaques du torse et de l'abdomen.
  - **Harmonisation Plaques ↔ Bras/Jambes** : Texture 2D rétablie sur une surface parfaitement lisse et soyeuse, identique au galbe des bras et des jambes, permettant au MatCap Chrome HD 512×512 Three.js de glisser avec un lustre miroir continu et homogène sur l'ensemble de la carrosserie.
  - **Préservation intégrale des détails** : Sangles en X au centre bas, échancrures de hanches, carénage pelvien aiguillonné, ongles bicolores magenta/cyan et phalanges mécatroniques.
  - **Proportions Chibi** : Tête à +24% (`scale.set(1.24, 1.24, 1.24)`), coupure d'ombre cel-shade mecha (`shadingToonyFactor = 0.95`).
  - **Déploiement multi-surfaces synchronisé** :
    - `Desktop SDS .10` : synchronisé avec succès et overlay Electron redémarré (PID 45908).
    - `N:\Upload\IA\` : `body_skin_android.png`, `metallic_matcap.png`, `vrm_pet.bundle.js` synchronisés.
    - `CT100 (192.168.0.100)` : injecté dans `lbg-frontend:/usr/share/nginx/html/vrm/` avec cache-buster `?v=mecha_v15`.
- 2026-10-19 : **Refonte Torse Mecha Cyborg & Alignement 360° Parfait Dos/Ventre — validé & déployé** —
  - **Analyse & Résolution du désalignement dorsal** : Identification mathématique des sommets de couture du dos dans `Compagnon.vrm` (`X=495` à gauche, `X=1552` à droite avec `dy=0` exact). Résolution des écarts et décalages verticaux historiques (150 px d'écart éliminés) grâce à une règle de symétrie miroir pixel-à-pixel absolue `(495+dx) <-> (1552-dx)` sur toute la hauteur du dos.
  - **Reproduction fidèle de la référence mecha-musume** :
    - *Buste* : Dômes pectoraux bleu cobalt métallisé galbés avec liserés néon cyan émissifs (`#00f5d4`), sternum central vertical et rivets supérieurs.
    - *Sous-mammaire* : Arche rigide continue avec gros rivets concentriques 3D sous les seins.
    - *Abdomen* : Carapace segmentée en 4 anneaux bombés d'un seul tenant arqués vers le haut avec ombrage cylindrique 3D (pas de découpes carrées artificielles).
    - *Flancs* : Creux de taille sombre avec câbles musculaires synthétiques striés accentuant la taille de guêpe.
    - *Pelvis* : Bouclier V central avec contour complet néon cyan émissif, grandes carapaces de hanches galbées avec encoche mécanique et câbles d'aine.
    - *Dos* : Continuité exacte des anneaux lombaires et de la bande sous-scapulaire, colonne vertébrale à modules vertébraux bombés et canal neural cyan sans rupture.
  - **Déploiement multi-surfaces validé** :
    - `N:\Upload\IA\` : `Compagnon.vrm`, `body_skin_android.png`, `face_skin_android.png`, `hair_android.png` mis à disposition via l'agent Windows (`.10:5005`).
    - `Desktop SDS .10` : synchronisation locale dans `C:\Agent_IA\compagnon-desktop\overlay\vrm\` et redémarrage propre de l'overlay (PID vérifié).
    - `CT100 (192.168.0.100)` : injection docker dans `lbg-frontend:/usr/share/nginx/html/vrm/`.
- 2026-10-22 : **Cuisson intégrale (Baking) des Textures Mecha & Tête Chibi dans le binaire `Compagnon.vrm` — validé & déployé** —
  - **Problème initial** : Les textures cyber (`body_skin_android.png` v26, `face_skin_android.png`, `hair_android.png`) et le grossissement de la tête chibi (+68%) étaient appliqués uniquement au runtime dans Three.js (`vrm_pet.js`). Lors de l'import dans un logiciel 3D externe (Blender via le plugin VRM), le binaire contenait encore les anciennes textures de base et les proportions d'origine.
  - **Reconstruction et injection dans le conteneur glTF/GLB binaire** :
    - Image 11 (`Body_00_SKIN`) : remplacée directement dans le buffer GLB par la texture finale mecha v26 (plaques titane mecha, cuisses jointes sans couture, néons cyan `#00f5d4`, rotules et rivets).
    - Image 5 (`Face_00_SKIN`) : injectée avec le visage cyber.
    - Images 13 et 15 (`Hair`) : injectées avec la texture de chevelure cyber.
    - Squelette humanoïde : node 10 (`J_Bip_C_Head`) nativement mis à l'échelle `[1.68, 1.68, 1.68]` (+68%) pour reproduire les proportions Chibi directement dans le rig.
    - Reconstruction binaire propre avec alignement 4-octets glTF (taille finale : 14.1 MB).
  - **Synchronisation immédiate sur `N:\Upload\IA\Compagnon.vrm`** :
    - Fichier `Compagnon.vrm` mis à jour sur le partage de travail `N:\Upload\IA\` (prêt pour import immédiat dans Blender avec toutes les dernières évolutions visibles).
    - Fichiers `.vroid` d'origine (`model_Compagnon.vroid`, `model_Compagnon_Bhead.vroid`, etc.) également confirmés présents sur `N:\Upload\IA\`.
- 2026-10-22 : **Pack de Danses 1 & Recadrage Comportement Compagnon (anti-questionnaire) — validé & déployé live** —
  - **Correction du bug d'animation VRM ("avatar figé qui sautille")** :
    - *Cause racine identifiée* : `VRMA_MAP` contenait des alias vers des fichiers `dance_*.vrma` inexistants. En mode SPA Nginx, les requêtes 404 étaient servies en 200 avec la page HTML, provoquant l'échec de `GLTFLoader` et bloquant le mixer three.js. De plus, `mixer.stopAllAction()` n'était pas exécuté de façon synchrone, ce qui laissait les os figés dans la dernière frame du mixer pendant que seul le rebond Y s'exécutait.
    - *Résolution* : `VRMA_MAP` épuré des fichiers fantômes, `stopVRMA(0)` synchrone avec `mixer.stopAllAction()`, libérant 100 % du squelette pour la cinématique procédurale 60 FPS.
    - Rebuild et redéploiement effectués sur CT100 (`192.168.0.100`) et Windows SDS (`.10`).
  - **Recadrage du comportement du Compagnon (posture pair studio façon Antigravity)** :
    - *Suppression du piège Campus* : `team_proxy.py` délesté des mots-clés de conversation courante (`créer`, `creer`) qui déclenchaient une fausse mission Campus au lieu de dialoguer.
    - *Éradication du questionnaire marketing* : Interdiction formelle dans `router_prompts.py` des questionnaires de coaching creux (« Cible ? Valeur ? »). Obligation pour le Compagnon de répondre avec une vision studio concrète et technique (avatar VRM, bureau Windows .10, OBS/streaming, Lost Heaven) et d'avancer en force de proposition.
- 2026-10-12 : **rejeu feeling humain Compagnon (O-FEEL-1 / O-FEEL-2) — validé & clôturé** —
  - Déploiement CT 100 actualisé avec le build atomique `1.0.0+40e38c0` (`baf1f65b13777595…`, 36 fichiers).
  - Exécution du script [`tools/smoke_rejeu_humain_d6_5174.sh`](../tools/smoke_rejeu_humain_d6_5174.sh) sur `:5174` : 7 tours exécutés sans aucune rupture ni fuite ops.
  - Verdict 100 % vert : `C1=PASS`, `C2=PASS`, `PLAN=PASS`, `GO_AHEAD=PASS` (`SMOKE_REJEU_HUMAIN_D6_OK`, conversation `rejeu-humain-d6-3fa2fffd`).
  - Salutations et suivi sans template rigide, avis franc collègue studio en causerie, plan d'action structuré markdown et absence de piège sur le go-ahead.
- 2026-11-07 : **Unification de la synchronisation Windows SDS .10 & Hygiène Workspace** —
  - *Outillage unifié (`tools/sync_client_to_win.py`)* : Script unique avec support `--client swg|prime|all`, `--dry-run`, gestion fine des erreurs et découverte des cibles. Wrappers de compatibilité `sync_swg_client_to_win.py` et `sync_prime_client_to_win.py` préservés.
  - *Tests & CI* : 152/152 tests Cortex backend PASS, 505/505 tests orchestrateur PASS (0 échec), 18/18 suites Godot headless PASS. Copie de travail `main` 100% propre.
- 2026-11-06 : **SWG Pre-CU 3D : Volets 3, 5, 4 et 1 (Factions GCW, Flourishes, PCD Datapad, Housing POB Entrable) Validés & Déployés** —
  - *Volet 3 — Guerre Civile Galactique (GCW)* : Système d'alignement (`swg_faction_system.gd`) et bureau de recrutement (`swg_faction_dialog.gd`), statuts Civilian/On-Leave/Special Forces (PvP actif mondial), points de faction, garnisons Est (Lieutenant Kren, Stormtroopers, tourelle impériale) et Sud-Ouest (Capitaine Vao, Soldats rebelles, tourelle de l'Alliance).
  - *Volet 5 — Spectacle Cantina & Flourishes* : Commandes `/flourish 1..8`, observation active `/watch` et concert `/listen`, étincelles scéniques, montée de la jauge d'inspiration et octroi du buff de clarté mentale (+250 Mental).
  - *Volet 4 — PCD Datapad Montures & Véhicules* : Gestion dans le Datapad `[P]` des cartes de contrôle (PCD) pour Landspeeder X-34, Moto-Jet Swoop Bike et Dewback Dressé de Selle, invocation `/call` et rangement `/store` directs.
  - *Volet 1 — Housing Posable 3D & Bâtiments Entrables (POB)* : Maison creuse `build_swg_enterable_player_house` avec pas de porte franchissable, salon meublé (table, banquette cuir, coffre sécurisé de maison) et Vendeur PNJ personnel (`Daran`). Commande `/house` ou `/placehouse` pour ériger une maison libre à partir d'un Deed.
  - *Validation & Déploiement* : Selftest headless `swg_client_3d_selftest.gd` 100% vert (9/9 suites) ; 13 fichiers synchronisés vers `J:\swgemu\clients\swg-client` sur Windows SDS `.10`.
- 2026-11-06 : **SWG Pre-CU 3D : Volet 2 — Nids de Créatures (Creature Lairs), Vagues & Missions de Destruction Validé & Déployé** —
  - *Composant `swg_creature_lair_3d.gd`* : Monticules procéduraux de bêtes avec jauge de santé HAM (1400 à 1800 PV), alerte d'aggro de meute coordonnée, vagues de renforts furieux à 75%, 50% et 25% de vie.
  - *Destruction & Décombres* : Effondrement du monticule à 0 PV, transformation en `[DÉCOMBRES DE NID]`, pillage via menu radial avec ressources rares (Œufs fossilisés, Chitine pure de reine, viandes alpha) et crédits.
  - *Contrats de Terminal & Missions* : Nouveaux contrats `mis_lair_chacals` (Tumulus Ouest, 1250 cr) et `mis_lair_scarabees` (Canyon Est, 1600 cr) connectés au Waypoint GPS et validés automatiquement dès l'effondrement du nid.
  - *Validation & Déploiement* : Selftest headless `swg_client_3d_selftest.gd` 100% PASS ; synchronisé sur machine Windows `.10` (`J:\swgemu\clients\swg-client`).
- 2026-11-06 : **Intégration & Raccordement SWG Pre-CU dans Prime Client 2D Topdown (`packages/prime-client`) — Validé & Déployé** —
  - *Composants portés et connectés* :
    - `scripts/swg_target_frame.gd` : Cadre de ciblage unifié 2D (`Vector2.distance_to / 32.0`) & 3D, jauges HAM directes (Santé rouge, Action verte, Mental bleue), badges `[HOSTILE]`, `[CITOYEN]`, `[CADAVRE]`.
    - `scripts/swg_chat_box.gd` : Chat défilant avec saisie `[Entrée]`, commandes Slash (`/dance`, `/kneel`, `/prone`, `/stand`, `/camp`, `/harvester`, `/clone`, `/shout`, `/help`) et verrouillage focus clavier.
    - `scripts/swg_crafting_panel.gd` : Atelier d'artisanat SWG fonctionnel avec contrôle des stocks, consommation des ingrédients d'inventaire et génération d'objets.
    - `scripts/swg_inventory_paperdoll.gd` : Sac à dos 40 slots & Papier-Doll 6 slots, gestion sécurisée off-tree, consommation de consommables (Stimpack Bacta, Rations, Lait Bleu) répercutée sur les jauges.
    - `scripts/swg_audio_synthesizer.gd` : Synthétiseur audio procédural en pur GDScript (blasters, bips droïde, navette, quête, soins).
  - *Contrôles clavier et boucle de jeu 2D* :
    - Raccourci `[Tab]` : cycle de ciblage d'entités avec bip sonore droïde.
    - Raccourci `[Entrée]` : focus boîte de chat.
    - Raccourcis `[I]` (Inventaire/Papier-Doll) et `[T]` (Artisanat).
  - *Validation & Déploiement* :
    - Selftest `packages/prime-client/tools/client_modular_selftest.gd` 100% vert sous Godot 4.6.3.
    - Déploiement automatisé sur Windows SDS `.10` (`J:\swgemu\clients\prime-client`).
- 2026-10-12 : **ticket 5.2 Outillage Ruff & tests headless Godot CI — validé & clôturé** —
  - Configuration [`ruff.toml`](../ruff.toml) et [`pyproject.toml`](../pyproject.toml) racine pour le linting Python ; `ruff check .` passe à 100 % vert.
  - Runner headless Godot [`tools/ci_godot_headless.sh`](../tools/ci_godot_headless.sh) intégré : sim, nav et db/économie (18/18 checks) exécutés en ~3 s (< 10 s DoD) sans dépendance réseau LAN.
  - Le plan d'évolutions `PLAN_PROPOSITIONS_EVOLUTIONS` est officiellement **100 % réalisé** (10/10 tickets DONE).
- 2026-11-02 : **Alignement Lore PNJ, Garde-fous Compagnon & Délégation Directe Cline (`ActionProposal`)** —
  - *Délégation directe Compagnon ➔ Cline* : Extension du routeur [`action_proposal.py`](../packages/cortex/orchestrator/services/action_proposal.py) (`_propose_run_cli_agent`) pour reconnaître toutes les formulations naturelles de délégation (« confie à cline », « demande à cline de », « délègue à cline », « fais écrire par cline ») et extraire automatiquement le mandat ciblé. Injection du flag `gatekeeper` (revue diff + CI requises). Suite de tests orchestrateur enrichie et 100 % passante (30/30 OK).
  - *Garde-fous & Conscience Compagnon* ([`router_prompts.py`](../packages/cortex/compagnon_ui/server_overlay/router_prompts.py)) : Règle anti-divagation mise à jour pour que le Compagnon formalise le mandat exact et propose activement de le déclencher via Cline (carte Agir ou commande directe), tout en annonçant le contrôle superviseur.
  - *Ancrage PNJ Habitué Cantina* : Prise en compte immédiate des volontés de lore dans le projet MMO — mise à jour de `npc:habitue_cantina` dans [`npc_registry.json`](../packages/prime-hub/data/npc_registry.json) (summary, goals de recherche d'alliances avec les Joueurs, surveillance caravanes Al-Khali / convois Zalem, suggestion templates) et [`hub_dialogue.gd`](../packages/prime-hub/scripts/hub_dialogue.gd) (greetings, default moves et répliques contextuelles).
  - *Validation CI* : 146/146 tests pytest Cortex backend verts, 30/30 tests action proposal orchestrateur verts, ruff check vert, tests Godot headless validés.
- 2026-10-12 : **ticket 3.2 Convergence de la mémoire relationnelle jeu ↔ bureau — validé & clôturé** —
  - Module [`relation_memory.py`](../packages/cortex/compagnon_ui/server_overlay/relation_memory.py) connecté à `prime-hub` (`GET /v1/relation-memory` et `POST /v1/relation-memory/append` sur `:8787`).
  - Ancrage prompt système ([`character_layer.py`](../packages/cortex/compagnon_ui/server_overlay/character_layer.py)) injectant les liens de Teome (Jax, Nix, Daan, pourboires, quêtes) dans la conscience du Compagnon.
  - Détection d'intention `wants_relation_memory` branchée dans [`llm_chat_phase.py`](../packages/cortex/compagnon_ui/server_overlay/llm_chat_phase.py) pour restituer l'état relationnel.
  - Endpoints proxy/append dans [`core.py`](../packages/cortex/compagnon_ui/server_overlay/core.py) et méthodes `fetchRelationMemory`/`appendRelationMemory` dans [`useApi.js`](../packages/cortex/compagnon_ui/src/composables/useApi.js).
  - 6/6 tests unitaires passants dans [`test_relation_memory.py`](../packages/cortex/compagnon_ui/server_overlay/tests/test_relation_memory.py) ; packaging atomique CT 100 validé (`overlay.map` + `pyproject.toml`, 36 fichiers).
  - Axe 3 du plan d'évolutions 100 % achevé.
- 2026-10-12 : **ticket 3.1 Live World Stream Hub → Compagnon — validé & clôturé** —
  - Module [`world_stream.py`](../packages/cortex/compagnon_ui/server_overlay/world_stream.py) connecté au flux `prime-hub` (`GET /v1/world/stream` sur `:8787`) avec timeout 1.5 s, cache mémoire et fallback dégradé silencieux.
  - Salutations sociales ([`router_prompts.py`](../packages/cortex/compagnon_ui/server_overlay/router_prompts.py) / `short_social_reply`) enrichies avec le dernier fait marquant de Lost Heaven (ex. boss abattu, chute de ferraille, escorte Nix).
  - Contexte LLM ([`character_layer.py`](../packages/cortex/compagnon_ui/server_overlay/character_layer.py)) injectant les derniers événements du monde dans le prompt système du Compagnon.
  - Route proxy / cache `GET /world/stream` dans [`core.py`](../packages/cortex/compagnon_ui/server_overlay/core.py) et méthode `fetchWorldStream` dans [`useApi.js`](../packages/cortex/compagnon_ui/src/composables/useApi.js).
  - Suite de tests unitaires dédiée [`test_world_stream.py`](../packages/cortex/compagnon_ui/server_overlay/tests/test_world_stream.py) 100 % passante (7 tests) ; packaging atomique CT 100 validé (`overlay.map` + `pyproject.toml`).
  - Débloque le ticket 3.2 (Mémoire relationnelle).
- 2026-10-12 soir : **L3 DONE** confirmé live (`days_ok=3/3`, `status=done`, `last_ok_day=2026-10-11`) · backlog [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md) réécrit (feeling + 3.1 + clos L3/D6.5).
- 2026-10-12 soir : **fil gaps agentiques A–F2 / revue 7j clos** (`O-GAPS-1`) · suites reportées : `O-OPS-1` smoke LAN · `O-OPS-2` agrégat métriques Fleet · `O-OPS-3` F3 O2 hors plan.
- 2026-10-12 : **ticket 2.2 Découpage modulaire des méga-scripts — validé & clôturé** —
  - Volet client `packages/prime-client/scripts/main.gd` (initialement 2 406 L) ramené à **707 L** et scindé en 4 modules spécialisés < 800 L : `client_gameplay_ops.gd` (529 L, salvage, hunt, combat density, trade, wiki), `client_quest_ops.gd` (281 L, craft M10, board, Echo Hammat, initiation), `client_net_world.gd` (675 L, WebSocket, handoff, zone_state, synchronisation entités), `client_ui_dialogue.gd` (506 L, raccourcis, hotbar, chat hub, pont dialogue PNJ). Preuve : selftest headless `packages/prime-client/tools/client_modular_selftest.gd` 100 % vert sous Godot 4.6.3.
  - Volet serveur `packages/prime-hub/scripts/hub_sim.gd` (initialement 1 669 L) ramené à **771 L** et scindé en 5 modules < 800 L (`hub_combat.gd` 447 L, `hub_presence.gd` 185 L, `hub_sim_ambient.gd` 196 L, `hub_sim_views.gd` 142 L, `hub_sim_defs.gd` 103 L). Preuve : selftest headless `packages/prime-hub/tools/sim_selftest.gd` 100 % vert.
  - Résultat : 100 % des scripts GDScript du jeu et du serveur sous le seuil canonique des 800 lignes. Ticket 2.2 marqué `done`.
- 2026-10-12 : **ticket 2.1 Persistance transactionnelle SQLite hub_player_store validé & clôturé** — couche SQLite threadée non-bloquante `packages/prime-hub/scripts/hub_db.gd` (mode WAL, queue asynchrone `BEGIN IMMEDIATE … COMMIT` sans impact sur le tick de frame) ; couche d'abstraction `hub_player_store.gd` pour les positions joueurs avec auto-migration JSON et export miroir périodique ; résilience validée par selftest (`packages/prime-hub/tools/db_selftest.gd`) et smoke crash-safety `kill -9` sans corruption (`tools/smoke_sqlite_prime_hub.sh`) ; ticket 2.2 (découpage modulaire `hub_sim.gd`) débloqué.
- 2026-10-11 : **ticket 1.3 Modularisation Pilot Web vérifié & clôturé** — monolithe `pilot.js` historique (~8 500 L) découpé en 17 modules ES fonctionnels <1 000 L à la racine de `pilot_web/` ; génération chunks `src/chunks/` via `tools/gen_chunks.mjs` synchronisée et vérifiée (`--check` OK) ; build production Vite `dist/` exécuté avec succès en 957ms ; tests static backend `pytest backend/tests/test_pilot_static.py` 100 % passants.
- 2026-10-11 : **ticket 1.2 Streaming SSE vérifié & validé** — route `POST /ask/stream` live sur CT100 (`:5174`, vérifiée par curl `text/event-stream` start+ping+delta+done) ; intégration front `useApi`/`useChat`/`ChatFlow`/`askStream` avec réflexion progressive ≥300 ms et curseur de streaming ; tests unitaires Python (`test_sse_ask.py` 3/3 OK) et Node (`askStream.test.js` 2/2 OK) tout verts ; `PLAN_PROPOSITIONS_EVOLUTIONS.md` mis à jour.
- 2026-10-11 : **ticket sonde AD traité & clos** (arbitrage : absence d'AD actée dans le LAN). Neutralisation des faux-positifs `ad_agent_down` dans `orchestrator/services/proactive.py` (`_infra_signals`, `infra_objective`) et `hybrid_proactive_agent/engine.py` ; recadrage sur `desktop_agent_down` (`.10:5005`) ; mise à niveau des libellés UI `compagnon_ui/src/lib/initiativeQuota.js`, `compagnon-desktop/main.js`, `pilot_web/pilot_orch.js` ; tests unitaires alignés (`initiativeQuota.test.js`) ; handoff `docs/handoff_antigravity_sonde_ad.md` marqué RÉSOLU.
- 2026-10-11 : **ticket 2.3 navmesh livré** — `packages/prime-hub/scripts/hub_nav.gd` (`NavigationServer3D`, bake 193 polys / 16 empreintes ~0.6 s, `map_force_update` synchrone) ; `PATH_BUDGET_PER_TICK=2` supprimé (`budget_per_tick=0`) ; A* grille conservé en fallback hors bornes. Preuves : self-test `packages/prime-hub/tools/nav_selftest.gd` (40/40 entités/tick, ~34 µs/entité) + `tools/smoke_navmesh_prime_hub.sh` ; `/healthz` expose `navmesh`, endpoints `/v1/navmesh` + `/v1/dev/navmesh/probe`. Débloque 2.1.
- 2026-10-09 : bootstrap continuité Antigravity (`.agents/rules/`, `~/.gemini/GEMINI.md`, ce fichier).
- WIP locaux non commités observés au bootstrap : `FOCUS_COMPAGNON.md`, `spawn_team_campus_conductor_job.py`, `compagnon_ui/nginx.conf`, `chat_intent.py` — ne pas écraser sans vérifier le diff.

---

## Prompt de démarrage (coller dans Antigravity)

```
Repo : LBG_Studios. Réponses en français.
Lis dans l’ordre : AGENTS.md → docs/SESSION_EN_COURS.md → docs/PRIORITES_ACTUELLES.md
→ le handoff @docs/handoff_…md si cité.
Confirme en ≤10 lignes : objectif, contraintes, prochain pas — avant toute édition.
En fin de session : mets à jour docs/SESSION_EN_COURS.md.
```
