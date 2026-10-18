# Session en cours — LBG Studios

**Mis à jour** : 2026-10-16  
**Branche** : `main`  
**Outil** : partagé Cursor ↔ Antigravity — **lire au démarrage, mettre à jour avant de partir**.  
**Backlog non traité** : [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md)  
**Fil** : canon O1/O2/O3 + D8 avatar bridge Desktop — **documenté** ; suite = feeling / adapters externes.

---

## Objectif actuel

Continuité multi-outils : même canon **O1 Compagnon / O2 MMO banc / O3 Joueurs IA** ([`OBJECTIVES.md`](../OBJECTIVES.md)).  
Travail produit : Compagnon D6 vert + hub Godot P3–P5 sans rouvrir le legacy.  
**2026-10-14** : polish O2 ESCORT + SHOW + HOTBAR **clos** · hygiène contexte **clos** · Mods→Compagnon **clos** · **canon O1/O2/O3** · **D8 avatar bridge** (SSE `:8765` + overlay VRM) **préparé**.

## Snapshot priorités (voir détail dans PRIORITES_ACTUELLES)

| Rail | État |
|------|------|
| **O1 Compagnon** | D0–D6 OK ; D8 avatar bridge **préparé** — `FOCUS_COMPAGNON.md` · `avatar_presence_events_v1.md` |
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
25. **Backlog ouvert** : 0 sujet ouvert dans [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md).

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
- 2026-10-12 : **rejeu feeling humain Compagnon (O-FEEL-1 / O-FEEL-2) — validé & clôturé** —
  - Déploiement CT 100 actualisé avec le build atomique `1.0.0+40e38c0` (`baf1f65b13777595…`, 36 fichiers).
  - Exécution du script [`tools/smoke_rejeu_humain_d6_5174.sh`](../tools/smoke_rejeu_humain_d6_5174.sh) sur `:5174` : 7 tours exécutés sans aucune rupture ni fuite ops.
  - Verdict 100 % vert : `C1=PASS`, `C2=PASS`, `PLAN=PASS`, `GO_AHEAD=PASS` (`SMOKE_REJEU_HUMAIN_D6_OK`, conversation `rejeu-humain-d6-3fa2fffd`).
  - Salutations et suivi sans template rigide, avis franc collègue studio en causerie, plan d'action structuré markdown et absence de piège sur le go-ahead.
- 2026-10-12 : **ticket 5.2 Outillage Ruff & tests headless Godot CI — validé & clôturé** —
  - Configuration [`ruff.toml`](../ruff.toml) et [`pyproject.toml`](../pyproject.toml) racine pour le linting Python ; `ruff check .` passe à 100 % vert.
  - Runner headless Godot [`tools/ci_godot_headless.sh`](../tools/ci_godot_headless.sh) intégré : sim, nav et db/économie (18/18 checks) exécutés en ~3 s (< 10 s DoD) sans dépendance réseau LAN.
  - Le plan d'évolutions `PLAN_PROPOSITIONS_EVOLUTIONS` est officiellement **100 % réalisé** (10/10 tickets DONE).
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
