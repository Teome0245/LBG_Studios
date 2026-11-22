# 🌌 Direction Artistique & Identité Visuelle de Prime

> **Étoile du Nord de Prime** : *Garder le squelette systémique de SWG + T4C, mais forger une âme visuelle unique et multiverselle.*  
> Ce document est la source de vérité canonique pour « dés-SWG-iser » l'esthétique du jeu et unifier les références du projet dans le moteur **Godot 4.6.3 Full 3D**.

---

## 1. La Synthèse des 3 Piliers de l'Univers

L'univers de **Prime** (planète Scrapaltai, hub de Lost Heaven, et mondes connectés) fusionne 10 grandes inspirations en 3 piliers visuels cohérents :

```
                  ┌────────────────────────────────────────┐
                  │          L'UNIVERS DE PRIME            │
                  └────────────────────────────────────────┘
                                      │
         ┌────────────────────────────┼───────────────────────────┐
         ▼                            ▼                           ▼
┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
│   PILIER 1       │        │   PILIER 2       │        │   PILIER 3       │
│ TECH ORGANIQUE & │        │ ÉNERGIE, CHI &   │        │ TON HÉROÏQUE &   │
│    BRICOLÉE      │        │    ALCHIMIE      │        │ ABSURDE MÉTA     │
├──────────────────┤        ├──────────────────┤        ├──────────────────┤
│ Gunnm            │        │ FMA              │        │ Discworld        │
│ Cyberpunk 2077   │        │ Avatar TLA       │        │ Free Guy         │
│ Firefly          │        │ Dragon Ball Z    │        │ Albator          │
│ Steampunk        │        │ Magie T4C        │        │ Steampunk        │
└──────────────────┘        └──────────────────┘        └──────────────────┘
```

1. **Tech Organique & Bricolée (Gunnm, Cyberpunk, Firefly, Steampunk)** :
   - Ferraille noble, cuivre de Scrapaltai, châssis mécatronique Mechari, implants cybernétiques apparents.
   - Vaisseaux et engins asymétriques avec tuyauteries, câblages visibles, propulseurs plasma et chaudières à vapeur.
   - Interfaces et technologies usées par le sable et le temps, pas de « clean corporate ».

2. **Énergie, Chi & Alchimie (Fullmetal Alchemist, Avatar, Dragon Ball Z, T4C)** :
   - Cercles de transmutation lumineux se déployant sous les pieds lors de l'incantation de sorts.
   - Maîtrise des éléments (Silice/Terre, Plasma/Feu, Éther/Air, Eau/Glace) et auras de ki perceptibles.
   - Ailes karmiques d'énergie pure (Séraphin lumineux / Démon d'obsidienne et flammes).

3. **Ton Héroïque & Absurde Méta (Discworld, Free Guy, Albator)** :
   - PNJ dotés de personnalités décalées, quêtes d'initiation parfois loufoques au milieu d'enjeux cosmiques.
   - Enseignes anachroniques, cantinas avec musique générée et robots philosophes.

---

## 2. Déclinaison par Couche de Jeu (Godot 4 Full 3D)

### A. Silhouettes, Armures & Personnages
* **Base technique** : Rigging humanoïde standard (compatible VRM / glTF 2.0).
* **Direction stylistique** :
  - **Membres cybernétiques** : Remplacement visible de bras/jambes par des prothèses en laiton ou polymère sombre (Gunnm).
  - **Plastrons Alchimiques** : Symboles et cercles gravés dans le métal qui s'illuminent lors de l'utilisation de compétences (FMA).
  - **Tenues d'École & Manteaux** : Manteaux longs en lambeaux flottant au vent désertique, kimonos de combat renforcés (DBZ/Avatar/Firefly).

### B. Hub de Lost Heaven & Environnements (Scrapaltai)
* **Ambiance Lumineuse** : Ciel cuivre/ambre, soleil voilé par la poussière en suspension, horizon bleuté (ACES Tonemapping + SSAO).
* **Architecture** :
  - Placette centrale en alliage composite avec anneaux néon cyan pulsants (`world_ground_3d.gd`).
  - Mât de télécommunications central avec balise lumineuse clignotante.
  - Tuyauteries, réservoirs de vapeur, décharges de ferrailles high-tech, étals de marchands sous toiles de jute.
  - Tempêtes de sable périodiques modifiant la visibilité et la densité du brouillard volumétrique.

### C. Interfaces, HUD & Menus
* **Dés-SWG-isation du HUD** :
  - Barres HAM (Santé, Action, Esprit) stylisées sous forme de conduits de fluide bio-énergétique.
  - Fenêtres avec bordures en cuivre patiné et angles adoucis, rétro-éclairage néon subtil.
  - Livre de sorts T4C orné de glyphes runiques alchimiques.
  - Discrets glitches holographiques lors des alertes critiques ou des transmissions IA (Free Guy / Cyberpunk).

### D. VFX, Sorts & Magie (Particules & Shaders)
* **Incantations** :
  - **Bouclier de Silice** : Hexagones translucides de silice vibrante autour du joueur.
  - **Éclair de Plasma** : Traînées électriques violentes avec rémanence d'arcs cyan.
  - **Cercle de Transmutation** : Décalque lumineux au sol tournant sur lui-même avant l'explosion magique.
  - **Auras de Karma** : Ailes éthérées et lueur volumétrique proportionnelle au rang de karma.

---

## 3. La Trinité des Factions du Multivers

| Faction | Inspirations | Philosophie & Devise | Palette Visuelle | Rangs d'Influence |
|---|---|---|---|---|
| **Convergence Synthetika** | Gunnm, Cyberpunk, Mechari | *« Le silicium sublime la chair. »* | Cyan électrique (`#00e5ff`), Chrome, Violet néon | Initié → Opérateur Câblé → Ingénieur Prothésiste → Commandeur → Archi-Cyborg |
| **Cercle des Arcanes Primordiaux** | FMA, Avatar, DBZ | *« De la terre au cosmos, l'énergie transmute. »* | Or étincelant (`#ffd700`), Améthyste, Blanc pur | Novice Alchimique → Adepte Élémentaire → Canalisateur de Chi → Maître Transmutateur → Grand Alchimiste |
| **Coalition des Mondes Brisés** | Firefly, Albator, Discworld | *« Rouille, liberté et cap sur l'inconnu. »* | Cuivre patiné (`#ff7043`), Cuir tanné, Bronze | Matelot de Rouille → Flibustier → Navigateur → Capitaine du Vide → Corsaire Céleste |

---

## 4. Pipeline IA pour la Génération de Nouveaux Skins

Le Studio de Contenu (`tools/studio_content_engine/`) et les générateurs d'assets exploitent cette matrice de prompts pour alimenter les textures, concepts et modèles :

### Prompts de Concept Art (SDXL / Flux / Midjourney / ComfyUI) :

* **Guerrier Cyber-Alchimiste (Convergence / Arcanes)** :
  > `concept art of a cyber-alchemical warrior, tattered dust coat, mechanical prosthetic arm engraved with glowing transmutation alchemy circles, neon cyan and copper accents, cyberpunk scrapaltai desert background, dynamic dramatic lighting, full body shot, game ready art, artstation trending`

* **Hub de Lost Heaven (Architecture Scrapaltai)** :
  > `game environment concept art, bustling scrap-punk desert outpost, rusty iron pipes, brass steampunk steam boilers, giant holographic neon signs, flying skiffs, dusty copper haze atmosphere, inspired by Firefly and Gunnm, 3rd person perspective, highly detailed`

* **VFX Sort Alchimique (T4C / FMA)** :
  > `visual effects sheet, magical transmutation circle glowing on sand ground, intricate geometric runes, plasma electricity burst, element particles, game ready VFX, top-down isometric view`
