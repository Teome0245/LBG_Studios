# Session en cours — LBG Studios

**Mis à jour** : 2026-11-13  
**Branche** : `main`  
**Outil** : partagé Cursor ↔ Antigravity — **lire au démarrage, mettre à jour avant de partir**.  
**Backlog non traité** : [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md)  
**Fil** : canon O1/O2/O3 — **Organisme Global Lyra & Incarnation Lia — Pilotage Multimodal OS (.10 & .143 via agent-desktop)**.

---

## Dernières actions réalisées (2026-11-13)
1. **Manifeste & Architecture Globale de l'Organisme LBG (`docs/ORGANISME_LBG.md`)** :
   - Formalisation de l'entité cybernétique globale : **Lyra** *(nom de travail)* et de son incarnation relationnelle : **Lia**.
   - Cartographie anatomique des rôles machines :
     - `.10` (Poste Teome) : Interface de symbiose humaine, audio/visuel, et main droite logicielle UIA sans vol de souris.
     - `.143` (Atelier Omarchy) : Usine logicielle et main gauche autonome pour les agents CLI (compute, CI, dev).
     - `.140` / `.110/.111` : Cerveau central, orchestration Cortex, mémoire et inférence locale.
     - `.246` (Lost Heaven `:8787`) : Banc d'entraînement spatial pour les corps virtuels O3.
   - Doctrine d'autonomie et garde-fous : abaissement des micro-confirmations bloquantes avec audit JSONL strict.
   - Référencé dans `OBJECTIVES.md` et `docs/REGISTRE.md`.

2. **Intégration Moteur `agent-desktop` (Vercel Labs) sur Windows (.10) et Linux (.143)** :
   - Intégration de l'accessibilité native OS (UIA sur Windows, AT-SPI sur Linux) dans `packages/cortex/windows_agent` et `packages/cortex/linux_agent`.
   - Primitives implémentées : `ui_snapshot`, `ui_click`, `ui_type`, `ui_press`, `ui_scroll`, `ui_focus`.
   - Actions headless sans vol de souris validées sur Windows.
   - Exposition du statut CLI dans `GET /healthz`.
   - Déploiement live sur le PC `.10` (`192.168.0.10:5005`) et démonstration live validée sur Notepad.exe.
   - Tests unitaires complets : 17 tests Windows, 12 tests Linux, 153 tests Cortex Backend (100% verts).

---

## Actions précédentes (2026-11-12)
1. **Studio Content Engine V2.1 (Dynamisme Vidéo, Motion Design & B-Roll Tech)** :
   - **Sous-titres Karaoké Mot-à-Mot Pop (`voice_engine.py`)** : découpage temporel fin et surlignage mot par mot en jaune néon éclatant (`&H0000FFFF&` avec grossissement pop +14%) au tempo oral exact.
   - **Arrière-plan Cyberpunk en Mouvement Continu (`video_compositor.py`)** : défilement fluide de la grille perspective au sol vers l'avant à 30 FPS + 24 particules néon montantes en permanence (fin de l'écran statique).
   - **Infographies B-Roll Concètes à Droite** :
     - *Phase Alerte* : carte rouge `PIÈGE DES API CLOUD` avec courbe de coût grimpante (`+450€ / mois`).
     - *Phase Solution* : carte cyan `STACK 100% LOCALE` avec tags Godot 4.6 Headless, Ollama RTX, Piper ONNX, SQLite WAL.
     - *Phase Métriques* : carte vert émeraude `BENCHMARKS EN DIRECT` avec jauge 60 ticks/s (100%), RAM 1.2 Go (15%) et 0.00€ Cloud.
     - *Phase Outro* : carte magenta `REPO LBG STUDIOS` avec lien GitHub et bouton d'action.
   - **Composition 2 Tiers & Avatar Réactif** :
     - Cadrage équilibré : Lia sur le tiers gauche de l'écran avec posture/regard tourné vers les infographies de droite.
     - Micro-inclinaisons de tête et buste dynamiques sur les accents de voix (`rms`).
   - **Validation & Test Vidéo HD** : génération complète réussie (`drop_1794489788`, 55.2s, 26.65 Mo, MP4 1080×1920 @ 30 FPS).
2. **Compagnon 3D VRM : Posture & Chorégraphie Live Concert (Storyboard Diva Nexura Domina)** :
   - **Micro 3D Stylisé de Scène (`cyberMicGroup`)** : création d'un mesh 3D procédural (corps noir graphite métallique, capsule micro sculptée, anneaux néon emissive cyan et magenta pulsant au kick 128 BPM) attaché dynamiquement comme enfant direct du bone `rightHand` (`rhNode.add(cyberMicGroup)`), grille orientée au plus près des lèvres/menton.
   - **Naturel Scénique, Biomécanique & Contrapposto Dynamique (Correctif Storyboard)** :
     - **Micro 3D redressé vers la bouche** : correction des angles du bras droit (`rightLowerArm` replié vers le haut et l'intérieur `[-0.22, -0.16, -2.10]`, coude contre le buste `[0.32, 0.35, 0.85]`), et réorientation locale de la capsule (`rotation.set(0.25, 0.15, 0.60)`) pour que la sphère chromée soit dressée directement à 2 cm devant les lèvres au lieu de pointer horizontalement sur le torse.
     - **Jambes déverrouillées & Stance ouverte permanente** : fin des cuisses croisées ou collées en un seul trait ; écartement minimal garanti de `0.26 rad` (~15°), pieds en éventail (25° externe), flexion permanente bien visible (jambe d'appui à `0.25 rad`, jambe libre à `0.55 rad`, et drop de scène à `0.85 rad` ~50°).
     - **Tête & Émotion** : inclinaison arrière accentuée vers le micro (`head: [-0.22, -0.06, 0.08]`) pour restituer la véritable extase vocale du concept art.
   - **Intégration Mocap FBX Complète (195 Fichiers, Tous Dossiers & Sous-Dossiers)** :
     - Rapatriement récursif de l'intégralité des mouvements FBX depuis `O:\OneDrive\Pictures\IA\mouvements` (Packs `Capoeira Pack`, `Female Locomotion Pack`, `Free Test Pack`, `Pro Magic Pack`, et racine) vers `packages/compagnon-desktop/overlay/vrm/fbx_source/` (195 fichiers FBX, 611 Mo de mocap brute).
     - Pipeline de conversion parallèle multi-cœurs (`tools/batch_convert_fbx.py`) avec FBX2glTF + `fbx2vrma-converter.js` : **189 nouveaux convertis, 6 existants, 0 échec** en ~2 minutes.
     - Empreinte disque ultralégère : **90.02 Mo au total** pour les 195 animations VRMA (~450 Ko par animation en moyenne !).
     - Classification et génération du manifest structuré (`manifest.json`) en 8 catégories :
       - *Danses & Grooves* (29 anims : Gangnam Style, Twerk, Can Can, Macarena, Bellydance, Hip Hop 1-3, Jazz 1-3, Samba, Salsa, Disco...).
       - *Capoeira & Arts Martiaux* (40 anims : Armada, Au, Bencao, Chapa, Ginga, Martelo, Meia Lua, Rasteira...).
       - *Locomotion & Déplacements* (25 anims : Catwalk, Happy Walk, Strafes, Sprint, Jump...).
       - *Magie & Incantations* (57 anims : Cast Spell 1H/2H, Magic Area Attacks 01-05, Shield Blocks, Reacts...).
       - *Poses & Silhouettes* (18 anims : Female Dance Pose, Dynamic Pose, Laying, Kneeling...).
       - *Expressions & Réactions* (23 anims : Cheering, Victory, Taunt, Bashful, Thinking, Phone...).
       - *Fitness & Sport* (11 anims : Air Squats, Back Squat, Backflip, Push Up, Kettlebell, Speedbag...).
       - *Général* (17 anims).
     - Résolution dynamique universelle dans `vrm_pet.js` (`VRMA_CATALOG` de 397 clés d'accès direct, `resolveVrmaFile`), dézoom dynamique automatique sur mouvement complet (`isFullBodyAction`), et neutralisation du root-motion in-place.
     - Recompilation du bundle IIFE (`vrm_pet.bundle.js`), synchronisation locale vers l'overlay Windows (`192.168.0.10:5005`) et déploiement Web instantané sur CT 100 (`192.168.0.100:5174`).
     - Test live validé sur desktop overlay avec `send_avatar_command` (`gangnam`, `bellydance`, etc.).
   - **Clip Musical Officiel 60s en Mode Studio Cyberpunk 3D (YouTube Shorts / TikTok HD)** :
     - Élimination totale des éléments de bureau Windows (ni fond d'écran, ni barre des tâches, ni icônes) : immersion 100% scénique.
     - Scène de concert futuriste en Three.js / WebGL hardware (GTX 1050 Ti) :
       * Grille perspective lumineuse cyan au sol défilant vers l'avant à 30 FPS.
       * Spots volumétriques de scène (cyan & magenta) pulsant en temps réel au kick de la musique.
       * 40 particules néon montantes en continu et halo central scénique derrière l'avatar.
       * Carte d'en-tête HUD glassmorphism (style officiel Studio Content Engine) : `LYRA // LIVE 3D CONCERT`, `100% LOCAL • 0€ CLOUD`, `KHOR-UN VAL-KYRA (128 BPM)`.
       * Égaliseur audio 32 bandes en bas de scène réagissant aux fréquences réelles de la piste.
     - Avatar 3D (Lyra androïde) en plein pied au centre de la scène tenant le micro cyber 3D néon, lèvres et regard calés au tempo, enchaînant les danses mocap (Intro Diva -> Couplet Groove -> Bellydance -> Pop Dance -> Gangnam -> Samba -> Finale Idol).
     - Rendu master vidéo 1080×1920 (Vertical 9:16, H.264 High Profile @ 6214 kb/s, 29.98 FPS, Audio AAC 48 kHz stéréo, 44.46 Mo).
     - Fichier délivré sur l'hôte Windows : `O:\OneDrive\Pictures\IA\Contenue\clip_khor_un_val_kyra_studio_60s.mp4`.
3. **Mode Live Concert Virtuel & Déhanché Mocap Aeysa sur Nexura Domina (Clip Complet 158s / 2m38s HD)** :
   - **Déhanché Mocap Pop / Maraschino Step Viral (@aeysamusic)** :
     * Analyse image par image de la référence TikTok virale (`7699001951047961878`) : balancement prononcé du bassin de gauche à droite, cambrure lombaire, flexion alternée des genoux et transfert de poids organique sur jambe d'appui tendue.
     * Intégration du clip mocap officiel `Dancing Maraschino Step.vrma` joué en boucle fluide infinie par l'AnimationMixer Three-VRM.
     * Micro 3D cyber néon solidement tenu en main droite avec anneaux cyan/magenta pulsant au kick 128 BPM.
     * Lipsync vocal synchrone en temps réel et regard scénique habité (yeux mi-clos / extase vocale de diva).
   - **Cadrage Silhouette Complète Dézoomé (`dist = 3.45m`, `lookY = headPos.y - 0.58m`)** :
     * Moins zoomé à la demande utilisateur : plan moyen complet révélant l'avatar des pieds à la tête avec respiration sous le HUD supérieur, bottes mecha posées sur le sol de scène juste au-dessus du visualiseur audio, et toute la dynamique des hanches/cuisses bien visible.
   - **Scénographie Studio Cyberpunk & Capture Sécurisée Hardware** :
     * Dégradé sombre cinématique (`#03050c`), doubles rim lights volumétriques réactives aux basses, particules lentes.
     * HUD concert glassmorphism minimaliste ("✦ NEXURA DOMINA", live pill, equalizer audio 36 barres réactif).
     * Script de capture et muxing automatique `record_studio_nexura_clip.py` exécuté sur Windows via l'agent `:5005` (FFmpeg gdigrab 158s @ 30 FPS avec `-draw_mouse 0`, gardien Win32 TopMost anti-superposition, upscale Lanczos 1080×1920 HD vertical + audio master `Nexura Domina_v1.mp3`).
     * Master vidéo final livré :
       * Version intégrale : `O:\OneDrive\Pictures\IA\Contenue\clip_nexura_domina_v1_studio_full.mp4` (145.65 Mo, 157.6s, 1080×1920 HD).
       * Version compatibilité : `O:\OneDrive\Pictures\IA\Contenue\clip_nexura_domina_v1_studio_60s.mp4`.
     * Frames de contrôle validées : `final_check_30s.png`, `final_check_75s.png`, `final_check_120s.png`.
4. **Clip Musical Officiel 60s avec l'Avatar de Bureau 3D (Lyra Live Performance)** :
     - Enregistrement en direct hardware via FFmpeg `gdigrab` sur le poste Windows (`192.168.0.10`) de l'overlay 3D Three.js réel en exécution (Lyra skin android, micro cyber 3D néon, lipsync et animations mocap).
     - Synchronisation chorégraphique millimétrée sur les 60 secondes de `Khor-un Val-Kyra.mp3` :
       - 0.0s – 8.5s : Intro Diva avec micro en main (`femaledance`)
       - 8.5s – 22.0s : Couplet rythmé & chant passionné (`cyberGroove`)
       - 22.0s – 34.5s : Electro Drop 1 (`bellydance`)
       - 34.5s – 45.0s : Electro Drop 2 / Pop dance (`popdance`)
       - 45.0s – 52.5s : Climax d'énergie (`gangnam`)
       - 52.5s – 57.5s : Célébration festive (`samba`)
       - 57.5s – 60.0s : Final Idol (`fingerHeart` & sourire de victoire)
     - Encodage H.264 / AAC 48 kHz stéréo à 1080×1920 (vertical HD 9:16 pour YouTube Shorts & TikTok, 19.23 Mo).
     - Fichier final délivré sur le disque hôte : `O:\OneDrive\Pictures\IA\Contenue\clip_khor_un_val_kyra_avatar_bureau_60s.mp4`.
     - Rétablissement automatique des dimensions de bureau standard et du mode promenade (`wander: true`).
   - **Clip Musical 60s & Déploiement Pipeline (Khor-un Val-Kyra / Nexura Diva)** :
     - Script de montage cinématographique vertical 1080x1920 30 FPS (`tools/build_clip_khor_un_val_kyra.py`) : 7 plans enchaînés avec zoompan/Ken Burns dynamique et synchronisation complète de la bande son master 60s (`khor_un_val_kyra.mp3`).
     - Rendu vidéo finalisé (`clip_khor_un_val_kyra_60s.mp4`, 9.0 Mo, H.264 / AAC 256k) et copié automatiquement sur le poste Windows dans `O:\OneDrive\Pictures\IA\Contenue\clip_khor_un_val_kyra_60s.mp4`.
   - **Panneau Compagnon Web & Desktop (`LyraPanel.vue`)** :
     - Ajout de 12 boutons de chorégraphies et actions animées : Diva Live, Bellydance, Pop Dance, Gangnam Style, Samba, Hip-Hop, Capoeira Ginga, Robot, Disco, Catwalk, Pirouette, Mini Heart.
     - Déclenchement automatique du plein pied (`fullBodyPoses`) dès le clic.
     - Recompilation Vite et déploiement sur CT 100 (`lbg-frontend`).
   - **Portage des Animations 3D dans le MMO (`prime-client` Godot 4.6)** :
     - Création de `packages/prime-client/assets/animations/{locomotion,combat,dances}/` avec 23 animations prêtes à l'emploi au format GLB standard (walk, run, sprint, jump, strafes, capoeira ginga/armada/esquiva/martelo, sorts magiques 1H/2H, parade bouclier, danses).
     - Tests CI Headless Godot validés (`tools/ci_godot_headless.sh`).
1. **Élévation Graphique 2D Top-Down style *Canvas of Kings* (Prime Client 2D)** :
   - **Moteur d'Ambiance Visuelle & Éclairage Dynamique (`canvas_of_kings_atmosphere.gd`)** :
     - Cycle jour/nuit circadien 2D avec `CanvasModulate` synchronisé directement sur le snapshot réseau `world_clock` du hub (`game_hour`, `is_night`, `light_ambient`).
     - Éclairage solaire et ombres portées douces dynamiques : calcul en temps réel de `_sun_shadow_offset` et `_sun_shadow_alpha` répercutés sur les bâtiments de Lost Heaven (`hub_buildings_layer.gd`) et les entités (`entity.gd`).
     - Éclairage 2D nocturne procédural : 11 lanternes `PointLight2D` avec textures de gradient radial générées en mémoire (Hermite cubique, 0 dépendance asset manquante) et scintillement organique doux.
     - Particules atmosphériques douces de poussière et vent (`CPUParticles2D`) centrées sur la caméra 2D.
     - Ombre de contact au sol et halos lumineux doux sous les terminaux holo, les droïdes et les sabres laser.
2. **Élévation Graphique 3D Spatiale JTL style *PVKK* & *Road to Vostok* (`swg_space_flight_3d.gd`)** :
   - **Post-Processing & Rendu PBR Réaliste (Road to Vostok & Godot 4)** :
     - Tonemapping `ACES` (`tonemap_exposure = 1.15`, `tonemap_white = 1.25`) pour un contraste doux sans brûlures de hautes lumières.
     - Bloom / Glow cinématographique chaud (`glow_bloom = 0.35`, `glow_hdr_threshold = 0.9`, mode SCREEN) pour le rayonnement des étoiles, réacteurs et voyants.
     - Nébuleuse spatiale cosmique (Brouillard de profondeur atmosphérique `fog_enabled = true`).
     - Éclairage directionnel solaire à ombres PBR nettes (`DirectionalLight3D`) doublé d'un contre-jour cosmique bleuté de nébuleuse.
     - Ceinture d'astéroïdes et roches PBR polygonales rugueuses (`metallic = 0.15, roughness = 0.92`) en rotation lente.
   - **Poste de Pilotage & Mode Cockpit PVKK (Première Personne)** :
     - Modélisation du cockpit tactile brutaliste / dieselpunk : montants verrière en acier riveté, console de bord en pan incliné (`roughness = 0.85`), moniteur CRT vectoriel à phosphore vert émissif (radar JTL avec coordonnées et ciblage TIE en direct), voyants LED d'état émissifs (SYS_NOMINAL, SHIELDS_OK, WEAPONS_HOT, WARN_RADAR), et levier de gaz (throttle) qui s'incline avec l'accélération.
     - Bascule fluide double caméra avec la touche **`[V]`** ou le bouton HUD dédié : bascule entre **Cockpit PVKK Immersive** (1ère personne) et **Vue Extérieure 3D** (3e personne).
     - En vue extérieure : 4 réacteurs ioniques de l'X-Wing avec panaches de plasma rose/rouge émissifs qui pulsent et s'étirent selon la vitesse (`current_speed`).
3. **Outillage, Déploiement & Validation** :
   - Ajout des nouveaux fichiers à la synchronisation SDS Windows `.10` (`tools/sync_client_to_win.py`) : 22 fichiers synchronisés avec succès.
   - Validation 100% verte du selftest client Godot headless (`tools/client_modular_selftest.gd`).
   - Déploiement du patch officiel sur le serveur de patch Launchpad (`192.168.0.246:8080`) via `deploy_prime_client_patch_246.sh`.
4. **Éclairage 2D Avancé Canvas of Kings : Entrées de Lost Heaven, Camp Zalem, Ksar Nomade & Caravanes** :
   - **Entrées de Lost Heaven** : 8 lanternes encadrant de chaque côté les piliers et arches d'entrée (Porte Ouest route de Zalem, Porte Est du désert, Porte Sud du shuttleport, Porte Nord palissade).
   - **Camp Avancé de Zalem** : 8 lanternes ambrées de garnison (Checkpoint et barrières Ouest, Poste de commandement Capitaine Vael, Atelier Soren Kray, Caserne Milice, Relais des convois/Inn, Dépôt de ravitaillement, Place d'armes).
   - **Ksar Nomade** : 9 lanternes de campement nomade et oasis (Arches d'entrée Nord et Est, berges de l'Oasis, Grande tente de l'Ancien Nadir, Tente des soins de Miran Sael, Tente de troc, Caravansérail).
   - **Caravanes de Scrapaltai (`entity.gd`)** : détection automatique des membres de caravane (`npc:caravan_*`, nomades), ajout d'une lanterne 2D attachée `PointLight2D` ambrée projetant une lueur mobile et scintillante au sol, dessin des lanternes nomades en laiton et des bâtis/sacoches de bât.
   - **Halte des caravanes d'Al-Khali** : balises et feux de bivouac à mi-chemin entre Lost Heaven et le Ksar.
5. **Studio Content Engine : Voix Officielle Vivienne Neural, 2s Silence & Fix Phonétique ("GitHub")** :
   - **Voix Officielle Sélectionnée (`fr-FR-VivienneMultilingualNeural`)** : élocution vivante, diction ultra-propre et naturelle à 0 € de coût récurrent.
   - **Correction Phonétique Orale (`voice_engine.py`)** : règle automatique transposant "GitHub" en "Guite Heube" pour l'audio sans altérer l'orthographe exacte dans les sous-titres ASS.
   - **Silence Initial de 2.0s & Phrase Signature** : 2 secondes de regard franc avant le démarrage de la présentation *"Bonjour, je suis Lia..."*.
   - **Validation de bout en bout** : génération du drop `drop_1794407604` (33.4s, 4.49 Mo) synchronisé vers `O:\OneDrive\Pictures\IA\Contenue\`.
6. **Compagnon Desktop & Backend Cortex : Intégration de la Voix Vivienne Neural & Dictionnaire Phonétique** :
   - **Backend Cortex (`packages/cortex/backend/services/tts_service.py` & `/v1/tts`)** :
     - Ajout de `fr-FR-VivienneMultilingualNeural` comme voix par défaut du Compagnon (`default_voice`).
     - Application automatique du dictionnaire phonétique oral (`GitHub` -> `Guite Heube`, `open source` -> `opène source`, `Godot` -> `Godo`, `API`, `LLM`, `framework`) pour toutes les répliques du Compagnon.
     - Synthèse audio WAV haute fidélité avec calcul synchronisé des 5 visèmes morph-targets VRM (`aa`, `ih`, `ou`, `ee`, `oh`).
     - Installation des dépendances et déploiement validé sur le serveur `.140:8000` (`lbg-backend.service`).
     - 153 tests unitaires backend verts (`pytest backend/tests`).
   - **Agent Windows .10 (`compagnon_parler`)** :
     - Nouvelle capability installée sur l'agent Windows (`.10:5005`) pour synthétiser et jouer en direct la voix Vivienne Neural sur les haut-parleurs du PC avec notification au pont avatar VRM (`127.0.0.1:8765`).
     - Test d'élocution avec termes techniques ("GitHub", "Godot", "open source") validé avec succès en direct sur Windows .10.
7. **Intégration Computer Use `agent-desktop` (Vercel Labs) sur Windows `.10` et Linux `.143`** :
   - **Moteur d'Accessibilité Natif (`agent_desktop.py`)** :
     - Remplacement des captures d'écran lourdes (`observe_screen` / vision LLM) et de la monopolisation de la souris physique (`pyautogui`) par la lecture directe de l'arbre d'accessibilité de l'OS (UI Automation sur Windows, AT-SPI sur Linux).
     - Actions supportées : `ui_snapshot` (capture d'éléments interactifs avec identifiants `@ref`), `ui_click` (clic headless en tâche de fond), `ui_type` (saisie sécurisée via stdin), `ui_press` (raccourcis), `ui_scroll`, `ui_focus`.
     - Exécution possible en unitaire ou chaînée dans la macro par lot `run_steps`.
   - **Intégration dans `windows_agent` (`packages/cortex/windows_agent/Agent_IA/`)** :
     - Détection de la CLI globale (`agent-desktop`) et exposition du statut dans `GET /healthz` (`agent_desktop.installed`, `agent_desktop.version`).
     - Compatibilité totale avec les garde-fous de sécurité existants (dry-run, approval tokens).
     - Script de déploiement `sync_windows_agent.sh` mis à jour pour copier `agent_desktop.py`.
     - Suite de tests unitaires dédiée `test_agent_desktop.py` (17 tests validés).
     - **Déploiement live sur Windows `.10:5005` validé** : `agent-desktop 1.2.0` installé et actif, premier `ui_snapshot` live exécuté en ~400 ms avec 604 éléments référencés.
   - **Intégration dans `linux_agent` (`packages/cortex/linux_agent/Agent_IA/`)** :
     - Sémantique symétrique pour Omarchy `.143`, exposition dans `/healthz` et tests dédiés `test_agent_desktop_linux.py` (12 tests validés).

---

## Dernières actions réalisées (2026-11-10)
1. **Pipeline de Création de Contenu Automatisé 100% Local / 0 € (`tools/studio_content_engine/`)** :
   - **Génération de Scripts Viraux Tech (`script_generator.py`)** : format court vertical (Hook 3s, Problème/Douleur, Solution architecture 0€, Call to Action) alimenté par Ollama local (`.111:11434` / `.110:11434`) avec repli canonique résilient.
   - **Synthèse Vocale & Audio Engine Fix (`voice_engine.py`)** : correction du bug de décalage d'octets impair (qui causait le bruit blanc et les craquements), ajout de micro-fondus de 8ms aux transitions, normalisation crête à -1.0 dB (0 clipping) et rééchantillonnage 44,1 kHz AAC pour une clarté optimale.
   - **Rendu 3D Avatar Compagnon (`blender_render_keyframes.py`)** : passage sur le modèle canonique `Compagnon.vrm` orienté face caméra, posture naturelle des bras baissés (élimination de la T-pose), avec les shape keys faciales (`Fcl_MTH_A`, `Fcl_MTH_O`, `Fcl_EYE_Close`, `Fcl_ALL_Joy`).
   - **Composition Vidéo & Lip-Sync Dynamique (`video_compositor.py`)** :
     - Synchronisation labiale temps réel sur l'amplitude RMS audio.
     - Clignements d'yeux procéduraux (toutes les 3.6s) et micro-mouvements de respiration.
     - Spectre audio néon réactif (28 barres oscillantes).
     - Dégradé cyberpunk avec grille perspective sci-fi et bandeau d'en-tête LBG Studios.
   - **Orchestrateur & CLI Unifié (`content_bot.py`)** : génération complète en ~30 secondes d'un fichier MP4 1080×1920 (H.264 / AAC, ~3 Mo) prêt pour TikTok, YouTube Shorts et Instagram Reels.
   - **Connecteurs Publication YouTube Shorts & TikTok Studio (`youtube_publisher.py`, `tiktok_publisher.py`)** :
     - **YouTube Data API v3** : authentification OAuth 2.0 officielle 100% connectée à la chaîne officielle **La Boite à Geek (@lbg-p8k, ID: UCqr0ctaojYRPy0kD4rPTBQg)** avec jeton persistant (`tools/studio_content_engine/config/youtube_token.json`).
     - Pont d'authentification automatisé avec ouverture de Firefox sur le poste Windows et proxy loopback local.
     - **Shorts publiés avec succès sur @LBG-p8k** :
       - [`https://www.youtube.com/shorts/WNfoQsOhX-0`](https://www.youtube.com/shorts/WNfoQsOhX-0) (*"Arrête de payer des API Cloud pour tes Agents IA"*).
       - [`https://www.youtube.com/shorts/sRpZn0ONnWU`](https://www.youtube.com/shorts/sRpZn0ONnWU) (*"Pourquoi Godot 4 Headless bat les serveurs traditionnels"*).
     - **TikTok Studio** : capability `preparer_upload_tiktok` sur l'Agent Windows (.10) : ouverture automatique de TikTok Studio Upload, sélection du fichier dans l'explorateur et injection de la légende/hashtags dans le presse-papier Windows.
     - **Automatisation Quotidienne (2 vidéos / jour)** :
       - Timer systemd `lbg-content-daily.timer` actif à **11h30** et **17h30** avec service `lbg-content-daily.service`.
       - Backlog de sujets curatés (`topics_backlog.json`) dépilant les thématiques tech/MMO/Godot/IA sans doublons.
       - Génération automatique du fichier MP4 + publication YouTube Shorts + création d'une fiche mémo texte (`*_tiktok_memo.txt`) dans `O:\OneDrive\Pictures\IA\Contenue\` avec légende et hashtags pour publication manuelle TikTok en 5 secondes.
2. **Pipeline Graphique 3D & World Building Automatisé (Blender Headless + Godot 4)** :
   - **Étape 1 : Blender Headless (`bpy`) & Props Modulaires (`tools/asset_pipeline/blender_prop_builder.py`)** :
     - Installation & activation de Blender 5.2.2 LTS en mode headless (`blender -b`).
     - Générateur procédural de props sci-fi avec biseaux, matériaux PBR émissifs et formes de collision Godot automatiques (`-col`).
     - Génération validée de 3 modèles `.glb` directement utilisables dans `packages/prime-client/assets/models/` (`sci_fi_crate.glb`, `modular_pillar.glb`, `terminal_console.glb`).
   - **Étape 2 : Pipeline Créatures & Personnages Rig/Animé (`tools/asset_pipeline/ai_creature_pipeline.py`)** :
     - Script `blender_creature_processor.py` : nettoyage maillage, centrage, auto-rig squelette (Armature standard), skinning automatique (Bone Heat Weighting), et animation cyclique (Idle de respiration).
     - Génération validée en 2s de créatures exportées en `.glb` avec animations (`alien_beast_crawler.glb`, `gundark_beast.glb`).
   - **Étape 3 : Constructeur de Terrain & Scatter Procédural Godot 4 (`packages/prime-client/scripts/world_terrain_builder.gd`)** :
     - Génération de maillage de terrain dynamique (`ArrayMesh` avec `FastNoiseLite`), vertex coloring par altitude/biome, calcul des normales et tangentes.
     - Collision physique temps réel via `ConcavePolygonShape3D` (`create_trimesh_shape()`).
     - Algorithme de dispersion intelligente de props (scatter) avec analyse du gradient de pente (filtrage des falaises raides).
     - Suite de tests headless `packages/prime-client/tools/terrain_builder_selftest.gd` intégrée dans `tools/ci_godot_headless.sh` (pass en <1s).
   - **Étape 4 : Amélioration du Compagnon Desktop (`packages/compagnon-desktop`)** :
     - **Accessoires 3D modulaires (`tools/asset_pipeline/blender_accessory_builder.py`)** : modélisation et export de 3 accessoires `.glb` (`cyber_visor.glb`, `holo_datapad.glb`, `neural_headset.glb`) attachables dynamiquement aux os VRM (`head`, `leftHand`).
     - **Nouvelles Poses / Emotes procédurales** : `focus` (analyse/scan de code avec posture inclinée et micro-oscillations) et `victory` (bras en V triomphal et célébration).
     - **Amélioration du Rendu 3D** : ajout d'un contre-jour `cyberHaloLight` (lumière cyan d'ambiance à 0x00f5d4) pour découper nettement la silhouette sur n'importe quel fond d'écran Windows.
     - **Intégration Electron & Overlay** : compilation via `bundle-vrm.py`, nouvelles entrées contextuelles dans le menu plateau/clic-droit (`main.js`, `overlay.js`, `preload.js`).
     - **Auto-Sync & Phase Tampon au Démarrage (`main.js`, `Lancer_Compagnon.cmd`)** :
       - Auto-détection de la source (`A:\LBG_Studios\packages\compagnon-desktop` ou partage réseau `\\192.168.0.143`) directement à l'ouverture.
       - Synchronisation automatique transparente des assets et du code (`main.js`, `preload.js`, `overlay/`).
       - Relaunch automatique transparent (`app.relaunch()`) si le code principal a été mis à jour.
       - Entrée manuelle ajoutée dans la barre des tâches : `🔄 Vérifier les mises à jour (A: -> C:)`.
       - Nouveau lanceur Windows rapide `Lancer_Compagnon.cmd` et mise à jour de `Create-DesktopShortcut.ps1`.
       - Raccourcis `Ctrl+R` / `F5` (rechargement sans cache) et `Ctrl+Shift+I` (DevTools) câblés dans `mainWindow` pour l'interface de chat.
       - Protection des modèles VRM perso : remplacement du `/MIR` robocopy par `/E` (sans purge) et sauvegarde automatique des modèles locaux vers le dépôt.
     - **Déploiement Compagnon Web/Chat UI (`packages/cortex/compagnon_ui`) sur CT `.100:5174`** :
       - Bouton `🔄 MAJ` (synchronisation et reload) ajouté dans le header du panneau avatar 3D (`LyraPanel.vue`).
       - Section `👓 Accessoires 3D` (Visière, Datapad, Oreillette) et pose `🔍 Focus` intégrées dans `LyraPanel.vue`.
       - Build Docker frontend & backend déployé sur CT `.100` (`deploy_compagnon_100.sh`).
2. **Enrichissement du Second Brain Lore & Monde LBG (`docs/lore/`)** :
   - Documentation canonique (hors Star Wars, biomes LBG propres inspirés de SWG) des 4 autres planètes majeures :
     - **`arvandor.md`** (Plaines luxuriantes, marbre blanc, cascades, diplomatie) + faction `cercle_diplomates_arvandor.md` + PNJ `bige_coto.md` (danse/arts scéniques).
     - **`khar_zuun.md`** (Lune des arbres titans, canopées géantes, brume dense) + faction `gardiens_canopee.md` + PNJ `mira_kael.md` (chasseresse).
     - **`terre_one.md`** (Berceau naval océanique, chantiers spatiaux) + faction `chantiers_navals_orbitaux.md` + PNJ `garr_vek.md` (instructeur spatial).
     - **`mor_valoth.md`** (Badlands carmin toxiques, bêtes mutantes) + faction `confrerie_brumes_rouges.md` + PNJ `dr_azra_veld.md` (bio-ingénierie dissidente).
   - Validateur `tools/validate_lore_links.py` : 21 nœuds, 147 relations, 0 lien cassé, 0 orphelin.
2. **Connexion Temps Réel de la Topologie au Hub Godot (`.246:8787`)** :
   - Endpoint `GET /v1/pilot/topology` : agrège la base de connaissances et interroge en direct le hub Godot (`/v1/bots`).
   - Injection dynamique des **10 Joueurs IA en direct** (Nix, Lia, Mira, Kael, Renn, Sola, Vex, Ori, Tess, Bram) avec leurs coordonnées temps réel, quête active et mode de jeu.
   - Frontend Pilot (`topology_graph.js`) : filtre `Bots IA 🤖`, badge live, mise à jour glissante continue (polling 4s) et drawer d'inspection enrichi.
   - Compilation Vite et déploiement en production sur la VM `.140` (`lbg-backend.service` actif et validé).
3. **Outil de Revue de Code Automatique Locale LBG (`tools/review_code_llm.py`)** :
   - Audit heuristique instantané (0 ms) des canons LBG et intégration Ollama `.110` / `.111`.
4. **Protocole Risk Gate Déterministe (`docs/design/RISK_GATE_AGENT_PROTOCOL.md`)** :
   - Formalisation canonique du sas étanche validé par la CI Godot headless (19 suites, code 0).

---

## Dernières actions antérieures (2026-11-09)
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
     - **`Mia.vrm`** : Avatar citoyenne de Lost Heaven ➔ Affecté à **Humain** (Terre-One / Corellien).
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
