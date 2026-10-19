# Handoff Pygmalion (Infographiste_IA) — Textures Châssis Androïde Mascotte Compagnon

**Date** : 2026-10-19  
**Auteur** : Antigravity (Pôle O1 Compagnon)  
**Destinataire** : Agent Pygmalion (`Infographiste_IA`)  
**Cible** : `Compagnon.vrm` (`packages/compagnon-desktop/overlay/vrm/Compagnon.vrm` & `packages/cortex/compagnon_ui/public/vrm/Compagnon.vrm`)  
**Statut** : Prêt pour prise en charge

---

## 1. Contexte & Choix d'Architecture

- **Identité mascotte** : Androïde Chibi Cyber inspirée de l'illustration officielle (cheveux carrés bleu nuit indigo, optiques néon cyan émissives, carrosserie métallique élégante).
- **Nombre de bras — Règle stricte** : **2 bras uniquement**.
  - *Arbitrage validé* : Les 4 bras supplémentaires de l'illustration mascotte ne sont pas modélisés afin de préserver l'intégralité du squelette humanoïde standard VRM 1.0 et la compatibilité totale avec les 17 animations VRMA officielles (`walk`, `lookaround`, `relax`, `crossArms`, `sit`, `thinking`, etc.).
- **Mission Pygmalion** : Réaliser le texturage 2D/3D haute résolution (2048×2048) en peignant directement les détails mécaniques, plaques d'armure et rotules en trompe-l'œil 3D sur le patron UV existant du modèle.

---

## 2. Spécifications Graphiques & Palette Canon

| Élément | Couleur / Hex | Rôle & Traitement |
|---|---|---|
| **Châssis principal (Base)** | `#28426b` / `#243d63` | Bleu nuit métallique satiné / carrosserie androïde |
| **Ombre châssis (Shade)** | `#121e33` / `#0b1320` | Teinte d'ombrage profond MToon |
| **Circuits & Liserés actifs** | `#00f5d4` | Lignes luminescentes cyan néon (émissif) |
| **Rotules & Connecteurs** | `#061320` / `#1a2636` | Métal sombre / carbone pour les articulations |
| **Reflets d'arête (Rim)** | `#00f0ff` | Liseré de contour lumineux le long des plaques |
| **Chevelure** | `#182846` & `#00e5ff` | Indigo profond avec mèches aux reflets cyan |

---

## 3. Découpage des Textures à Produire (2048×2048 PNG RGBA)

### A. Texture Corps : `Body_00_SKIN` (`body_skin_android.png`)

Emplacement cible : `packages/compagnon-desktop/overlay/vrm/textures/body_skin_android.png`

1. **Plaques Pectorales** :
   - Deux plaques d'armure sculptées sur le torse, avec chanfrein biseauté et reflets métalliques.
   - Rainure centrale en Y descendant vers le sternum avec liseré lumineux néon cyan `#00f5d4`.
2. **Rotules & Articulations Mécaniques (Trompe-l'œil 3D)** :
   - Épaules, coudes, poignets, hanches et genoux : peindre des anneaux circulaires concentriques simulant des jointures à rotule mécanique intégrées au châssis.
   - Centre de la rotule avec rivet métallique sombre `#061320` et dégradé d'ombre périphérique.
3. **Segmentation Abdominale** :
   - 3 segments horizontaux biseautés façon armure mecha/chibi.
   - Éclairage néon cyan discret dans les interstices.
4. **Encolure Mécanique** :
   - Jonction du cou sombre simulant un col mécanique cylindrique avec rainures verticales.
5. **Jambes & Pieds** :
   - Plaques tibiales renforcées et semelles magnétiques plates sans détail humain (pas d'orteils, sabot/semelle robotique nette).

### B. Texture Visage : `Face_00_SKIN` (`face_skin_android.png`)

1. **Teint de peau** :
   - Bleu nuit cyber lisse `#28426b` parfaitement raccroché à la teinte de l'encolure.
2. **Lignes de démarcation androïde** :
   - Fines gravures techniques (1 à 2 pixels) partant sous les yeux vers les tempes ou le long de la mâchoire pour marquer le visage mécanique.

### C. Texture Cheveux : `Hair_00_HAIR`

1. **Nuances de mèches** :
   - Dégradé indigo profond `#182846` vers des pointes éclairées d'un dégradé néon cyan `#00e5ff`.

---

## 4. Outils & Pipeline d'Intégration

- **Modèle source** : `packages/compagnon-desktop/overlay/vrm/Compagnon.vrm`
- **Injection des textures dans le binaire VRM (glTF/GLB)** :
  - Script automatisé disponible dans `scratch/inject_textures.py` ou outil `glTF-Transform`.
  - Image index 11 pour `Body_00_SKIN` et Image index 8 pour `Face_00_SKIN`.
- **Validation** :
  - Déploiement automatique via `scratch/build_and_deploy_walk.py` vers Windows SDS `.10` pour test in-situ sur la barre des tâches.
  - Vérification du rendu avec les matériaux Three.js MToon (`@pixiv/three-vrm`).
