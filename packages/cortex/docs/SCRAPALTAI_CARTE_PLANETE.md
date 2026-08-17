# Scrapaltai — carte planétaire (canon géographique)

**Statut** : canon produit (2026-08-13)  
**Image de référence** : [`assets/scrapaltai_carte_planete_reference.png`](assets/scrapaltai_carte_planete_reference.png)  
**Image annotée** (LH + capitale + grille) : [`assets/scrapaltai_carte_planete_annotee.png`](assets/scrapaltai_carte_planete_annotee.png)  
**Données machine** : [`assets/scrapaltai_planet_map.json`](assets/scrapaltai_planet_map.json)  
**Complément hub local** : [`GEOGRAPHIE_SCRAPALTAI.md`](GEOGRAPHIE_SCRAPALTAI.md)

---

## Planète vs ville vs shard jouable

| Échelle | Taille | Exemple |
|---------|--------|---------|
| **Planète Scrapaltai** | Ø **10 465 km** · **344 M km²** | Carte steampunk (référence) |
| **Capitale** | Metropole | **Zalem** — centre pentagone |
| **Lost Heaven** | **Petite ville** | 8ᵉ cadran (gauche→droite), 3ᵉ (bas→haut) |
| **Shard Core3 `tatooine`** | **13 × 13 km** (±6500 m) | Zone Godot / Prime où le joueur marche aujourd’hui |

Lost Heaven **n’est pas la capitale**. C’est l’**avant-poste joueur** sur la planète, relié par route à **Zalem**.

---

## Grille de la carte (12 × 4)

Origine : **coin inférieur gauche**. Colonnes numérotées **1 → 12** (gauche → droite). Lignes **1 → 4** (bas → haut).

```
  row 4  [ 60°N ─────────────────────────────────────────── 60°N ]
  row 3  [  0°  · · · · · ★ · ●LH · ○ · · ]  ← Lost Heaven (col 8)
  row 2  [ 30°S · · · · · · · · · · · · ]
  row 1  [ 60°S ─────────────────────────────────────────── 60°S ]
         col:  1   2   3   4   5   6   7   8   9  10  11  12

  ★ = Zalem (capitale, col ~6, carrefour pentagone)
  ●LH = Lost Heaven (col 8, row 3) — petite ville hub LBG
  ○ = bassin lac NE (cols 9–11)
  Grand Rift = cols 1–4 (ouest)
```

### Placement Lost Heaven (validé Teome 2026-08-13)

| Paramètre | Valeur |
|-----------|--------|
| Cadran | **Col 8**, **row 3** (3ᵉ en partant du bas) |
| Bande latitudinale | **0° → 30°N** (équateur nord) |
| Région | **Mer de dunes est** — lisière sud-est du bassin lac NE |
| Environnement | Désert ouvert, route rouge vers le Nexus, montagnes à l’ouest |
| Échelle lore | **Petite ville** (~500 m hub + palissade), pas métropole |

---

## Macro-régions (lore)

| Région | Cadrans | Trait dominant |
|--------|---------|----------------|
| **Grand Rift occidental** | cols 1–4, rows 2–4 | Canyon profond, convois le long des parois |
| **Cœur de Zalem** | cols 5–7, rows 2–3 | **Capitale Zalem**, nœud routes rouges |
| **Mer de dunes est** | cols 7–9, rows 2–3 | Dunes, avant-postes — **Lost Heaven** |
| **Bassin du lac NE** | cols 9–12, rows 3–4 | Cratère / caldeira, lac bleu, crêtes |

---

## Zalem (capitale)

| Champ | Valeur |
|-------|--------|
| Rôle | **Capitale planétaire** Scrapaltai |
| Position carte | Pentagone central (~col 6) — calage **`map_uv`** `{u:0.488,v:0.515}` |
| Statut gameplay | **Non jouable v1** — lore, shuttles futurs, factions |
| Visuel carte | Icône pentagonale multicolore, convergence routes rouges |
| Ton lore | **Métropole verticale** de ferraille / scrap — cité suspendue au-dessus du désert, carrefour des convois. Référence structurelle *Gunnm* (Zalem), **univers et visuels LBG** (space western, pas d’IP tierce en surface joueur). |

### Alternatives écartées (référence)

| Nom | Pourquoi |
|-----|----------|
| **Zalem** | **Retenu** — verticalité, scrap, lien émotionnel Gunnm |
| *Ferraille-Cœur* | Trop descriptif, moins de personnalité |
| *Tour-Scrap* / *Spire* | Évoque la forme mais pas la société |
| *Nexus Ferraille* | Placeholder technique (2026-08-13), remplacé par Zalem |

---

## Lost Heaven (hub joueur)

| Champ | Valeur |
|-------|--------|
| Rôle | **Seule ville hub gameplay LBG** (spawn, POI, trainers) |
| Échelle | **Petite ville** avant-poste |
| Position planète | Col **8**, row **2** (3ᵉ bande depuis le bas sur l’art) — **`map_uv`** `{u:0.655,v:0.31}` |
| Anchor Core3 | `(4749, -737)` — shard local 13 km |
| Cantina | **La Perle de Scrapaltai** (POI lore, pas capitale) |

Le shard Core3 actuel (`±6500 m`) = **vue microscope** d’un coin de la cellule (8, 3), pas la planète entière.

---

## Routes et réseau

| Type | Carte | Lore |
|------|-------|------|
| **Rouge** | Artères | Nexus ↔ bassins ↔ Rift — commerce lourd |
| **Jaune** | Secondaire | Pistes locales, mines, avant-postes |

Lost Heaven est sur une **artère rouge** secondaire vers le bassin NE, pas au centre du réseau.

---

## Legacy technique (invisible joueur)

| Lieu | Statut |
|------|--------|
| Mos Eisley vanilla | Même shard Core3 que LH (~4 km) — **deprecated** lore |
| Zone id `tatooine` | Id moteur — affichage **Scrapaltai** |

---

## Utilisation équipe

1. **Nouveau lieu planétaire** → placer sur grille 12×4 + région dans `scrapaltai_planet_map.json`.
2. **Contenu gameplay v1** → rester dans le shard LH (coords Core3).
3. **Dialogue / LLM** : Lost Heaven = petite ville ; capitale = **Zalem** (lointaine, verticale).
4. **Godot Ctrl+M** : texture `prime-client/assets/maps/scrapaltai_planet.jpg` + `scrapaltai_planet_map.json` (marqueurs Zalem / Lost Heaven, grille **G**).

---

## Fichiers liés

| Fichier | Rôle |
|---------|------|
| `docs/assets/scrapaltai_carte_planete_reference.png` | Art steampunk source |
| `docs/assets/scrapaltai_planet_map.json` | Grille + settlements |
| `prime-client/assets/maps/tatooine_map_config.json` | Shard local ±6500 m |
| `docs/world/BIBLE_MMO.md` | Vérités lore V10–V13 |
