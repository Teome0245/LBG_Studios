# Plan d'Intégration VRM 3D — Écosystème LBG (Compagnon & MMO)

> **Statut** : Cadrage & Feuille de route technique  
> **Date** : 2026-10-16  
> **Acteurs** : Antigravity · Pygmalion (Infographiste IA) · Dédale (Godot Dev) · Compagnon O1 / MMO O2  

---

## 1. Vision & Principe Unifié

L'avatar 3D du **Compagnon** et les personnages du **MMO (Lost Heaven / Scrapaltai)** partagent désormais un socle géométrique commun : **le standard VRM Humanoid (GLTF 2.0 / VRM 1.0)**.

L'objectif est d'assurer la continuité absolue de l'identité visuelle entre :
1. **Le Bureau Windows** : Compagnon desktop (`compagnon-desktop`, overlay Three.js / three-vrm).
2. **Le Web Studio** : Interface Compagnon CT100 (`compagnon_ui`, port `:5174`).
3. **Le Client MMO** : Client Godot 4 (`packages/prime-client`).

```
                    ┌───────────────────────────────┐
                    │  Conception Base VRoid / 3D   │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │    Infographiste_IA (LoRA)    │
                    │   Textures thématiques MMO    │
                    └───────────────┬───────────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  ▼                 ▼                 ▼
          ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
          │  Compagnon   │   │  Compagnon   │   │  MMO Client  │
          │ Desktop .10  │   │  Web CT100   │   │   Godot 4    │
          │ (Three.js)   │   │ (Three.js)   │   │ (godot-vrm)  │
          └──────────────┘   └──────────────┘   └──────────────┘
```

---

## 2. Intégration dans le MMO Godot 4 (`prime-client`)

### Phase A — Aperçu Personnage & Dialogue (Court terme, sans risque)
- **HUD / Fiche Personnage** : Intégration d'un `SubViewport3D` dans l'UI du client Godot 4 (`prime-client`).
- Le modèle 3D du joueur (ou du PNJ ciblé) est rendu en temps réel dans le cadre de la feuille de personnage et dans la boîte de dialogue des quêtes.
- **Lip-sync & Morphs** : Branchement des blendshapes de parole (`aa`, `ih`, `ou`) lors des dialogues audio.

### Phase B — Pions Joueur & PNJ In-Game (Moyen terme)
- Intégration de l'addon officiel **`godot-vrm`** dans `packages/prime-client`.
- Mapping automatique du squelette Humanoid VRM sur le `Skeleton3D` de Godot 4.
- Application de l'arbre d'animation (`AnimationTree` / `AnimationNodeStateMachine` : idle, walk, run, combat, emotes).
- Physique secondaire native via **SpringBones** (mouvement automatique des cheveux, capes et robes lors des déplacements).

---

## 3. Feuille de Route pour l'Infographiste (`Infographiste_IA` / Pygmalion)

### Workstream 1 — Bibliothèque de Textures & Apparences Factionnelles
Pygmalion utilise le pipeline ComfyUI / Stable Diffusion (`../Infographiste_IA`) pour générer les atlas de textures adaptés au lore de Scrapaltai :
1. **Habits de Lost Heaven** : style aventurier / cuir patiné / mécanos.
2. **Tenues Nomades du Ksar** : étoffes du désert, voiles protecteurs contre les tempêtes de sable, teintes ocres et turquoises.
3. **Uniformes Avant-poste Zalem** : tenues militaires légères, insignes de la garde de Zalem.

### Workstream 2 — Banque d'Animations Humanoid Standardisées
1. **Mixamo Pipeline** : Téléchargement et conversion d'un pack d'animations essentielles :
   - *Social / Emotes* : Salut (`wave`), Danse (`dance_hiphop`, `dance_twist`), Colère (`angry_gesture`), Approbation (`nod`), Révérence (`bow`), Célébration (`cheer`).
   - *Locomotion* : Marche (`walk`), Course (`run`), Repos assis (`sit_chair`, `sit_ground`).
2. **Format de distribution** : Export en fichiers `.vrma` (VRM Animation) utilisables à la fois dans Three.js (Web/Desktop) et convertibles en `AnimationLibrary` Godot.

---

## 4. Plan d'Exécution Immédiat

- [x] Modèle unique `Compagnon.vrm` calé de face (rotation `y = 0`) et nettoyé de tout sélecteur parasite.
- [x] Pose de salut (`wave`) fiabilisée avec animation fluide du poignet et tilt de tête.
- [ ] Création du dossier d'assets animations `packages/prime-client/assets/vrm/` et benchmark d'import via `godot-vrm`.
- [ ] Lancement du premier lot de textures thématiques par l'Infographiste dans `Infographiste_IA`.
