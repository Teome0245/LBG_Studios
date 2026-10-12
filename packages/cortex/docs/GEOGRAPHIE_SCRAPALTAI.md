# Géographie Scrapaltai — référence équipe

**Statut** : canon produit (2026-08-13)  
**ADR** : [`adr/0009-scrapaltai-lost-heaven.md`](adr/0009-scrapaltai-lost-heaven.md)  
**Carte planète** : [`SCRAPALTAI_CARTE_PLANETE.md`](SCRAPALTAI_CARTE_PLANETE.md) · image [`assets/scrapaltai_carte_planete_reference.png`](assets/scrapaltai_carte_planete_reference.png)

---

## Vocabulaire (ne pas confondre)

| Terme | Rôle | Id technique |
|-------|------|--------------|
| **Scrapaltai** | Planète entière (Ø 10 465 km) | Affichage lore ; zone Core3 locale : `tatooine` |
| **Zalem** | **Capitale planétaire** (métropole verticale, pentagone central carte) | Lore — **non jouable v1** |
| **Lost Heaven (LH)** | **Petite ville** — hub gameplay LBG | Cadran **col 8 / row 3** · Core3 `(4749, -737)` |
| **Shard Core3** | Patch jouable **13 × 13 km** autour de LH | `half_size: 6500` — pas la planète entière |
| **Mos Eisley (ME)** | Legacy vanilla — hors lore | `(3520, -4800)` dans le même shard |
| **La Perle de Scrapaltai** | Cantina de LH (pas la capitale) | POI `(4939, -802)` |

Règle d’or : **gameplay v1 = Lost Heaven** (petite ville). **Capitale = Zalem** (lointaine). ME = purge.

---

## Étendue planétaire

**Trois échelles** (voir [`SCRAPALTAI_CARTE_PLANETE.md`](SCRAPALTAI_CARTE_PLANETE.md)) :

1. **Planète** — carte steampunk 12×4 cadrans, Ø 10 465 km  
2. **Lost Heaven** — petite ville, **col 8 / row 3**, route vers **Zalem**  
3. **Shard Godot/Core3** — carré ±6500 m (zoom local où le client affiche verts + entités)

```
  Planète (carte)                    Shard Core3 (jeu actuel)
  ┌─── 12 cols ───┐                  ┌─ 13 km ─┐
  │  … ★ Zalem …  │                  │ LH ●    │
  │  …   ●LH  ○   │  ── contient ──► │    ME ■ │
  └───────────────┘                  └─────────┘
  ★ capitale                         ● hub (~500 m)
  ●LH col8 row3                      ■ legacy vanilla
```

| Paramètre | Valeur | Source |
|-----------|--------|--------|
| Planète (diamètre) | **10 465 km** | Carte référence / `scrapaltai_planet_map.json` |
| Lost Heaven (carte) | **Col 8, row 3** (petite ville) | `SCRAPALTAI_CARTE_PLANETE.md` |
| Capitale | **Zalem** (col ~6) | idem |
| Shard jouable (client) | **±6500 m** (13×13 km) | `scrapaltai_map_config.json` |
| Distance LH ↔ ME (shard) | **~4240 m** | Δ coords Core3 |
| Rayon PNJ live (gateway) | **800 m** autour LH | map config |

**Le carré dézoom max Godot** = le **shard local** ±6500 m, pas la planète entière (voir carte planète pour l’échelle globale).

---

## Lost Heaven — POI hub (coords Core3 outdoor)

Ancre : `(4749, -737, z≈32)`. Référence : `packages/cortex/content/core3/locations/lost_heaven_hub.json`, `packages/prime-client/assets/maps/lost_heaven_buildings.json`.

| POI | x | y (plan) | Rôle |
|-----|---|----------|------|
| Place / hub | 4749 | −737 | Centre plaza |
| Port shuttle | 4809 | −802 | Spawn joueur cible |
| **La Perle** (cantina) | 4939 | −802 | Barman Jax, spectacle |
| Banque | 4679 | −802 | |
| Marché | 4809 | −932 | |
| Hall entraînement | 4939 | −672 | Trainers combat |
| Atelier artisan | 5069 | −802 | Trainer artisan |
| Porte est | 5155 | −900 | Sortie désert (ex porte sud) |
| Porte ouest | 4450 | −760 | Route vers Zalem |

Cellules intérieures LH : **TBD** tant que les POI `world_poi` ne sont pas posés IG (World Editor). En attendant : **posts outdoor** `cell=0`.

**Concept ville (ovale, 2 portes)** : [`LOST_HEAVEN_TOPOLOGIE.md`](LOST_HEAVEN_TOPOLOGIE.md) — P1 portes + **P2 palissade ovale** actifs.

---

## Calques debug Prime Client (Godot)

| Calque | Raccourci | Couleur | Signification |
|--------|-----------|---------|---------------|
| `RetailLayoutLayer` | Ctrl+Shift+R | **Vert** | Référence spatiale LH (gabarit ME **décalé** sur ancre LH) |
| `HubBuildingsLayer` / props | Ctrl+H | Tuiles + palissade | POI lore LBG (12 bâtiments) |
| `ZoneLayers` | toujours si activé | Bleu = eau, rouge = collision | Polygones hub / terrain |
| `PoiLayer` | — | Pastilles | POI actifs (ME deprecated = masqué) |
| `PlanetBackdrop` | dézoom max | Carré sable + cercles | **Planète entière** ±6500 |

**Vert ≠ Scrapaltai entier.** Vert = emprises de référence **Lost Heaven** uniquement.

**Bleu en bas de carte dézoomée** = zone **Mos Eisley vanilla** (entités serveur / retail ME), pas LH.

---

## Mos Eisley — statut LBG

| Élément | Statut |
|---------|--------|
| Mesh / ville vanilla Core3 | Existe encore (non supprimable facilement) |
| Spawns LBG / PNJ catalogue | **Migration → LH** (script `migrate_npc_catalog_me_to_lh.py`) |
| Cantina cell `1082877` | Legacy — `housing_enter cantina` à remplacer par La Perle |
| `locations/mos_eisley_*.json` | `deprecated: true` |
| POI client | `deprecated: true` dans `scrapaltai_pois.json` |

On **décommissionne** ME pour le gameplay ; on ne **rase** pas la ville vanilla du moteur.

---

## Migration PNJ ME → LH (2026-08-13)

**Phase 1 (actuelle)** : posts **outdoor** `cell=0` aux POI LH. Roster ids inchangés (`roster:mos_*`) pour compat Lua — coords mises à jour.

| Roster | Ancien lieu | Nouveau post LH |
|--------|-------------|-----------------|
| `roster:mos_eisley_cantina_barman` | ME cantina 1082877 | La Perle `(4939, -802)` |
| `roster:mos_entertainer_trainer` | ME training 1189634 | `(4939, -802)` |
| `roster:mos_trainer_*` | ME training cells | Hall `(4939, -672)` ± offsets |
| `roster:mos_trainer_artisan` | ME 1189639 | Atelier `(5069, -802)` |
| `roster:mos_eisley_quest_giver` | ME outdoor 3488 | Plaza `(4809, -737)` |

**Phase 2** : cellules intérieures La Perle / halls après pose POI `world_poi` — mettre à jour `building_cell` dans `locations/lost_heaven_*.json`.

Appliquer :

```bash
python3 packages/cortex/infra/scripts/migrate_npc_catalog_me_to_lh.py
# Puis copier catalogue + locations vers VM (246) et restart autonomie population
```

Voir aussi [`GEOGRAPHIE_SCRAPALTAI.md`](GEOGRAPHIE_SCRAPALTAI.md) — référence équipe.

---

## Fichiers source de vérité

| Domaine | Fichier |
|---------|---------|
| Carte planète | `docs/SCRAPALTAI_CARTE_PLANETE.md` |
| Grille + settlements | `docs/assets/scrapaltai_planet_map.json` |
| Image référence | `docs/assets/scrapaltai_carte_planete_reference.png` |
| Image annotée | `docs/assets/scrapaltai_carte_planete_annotee.png` |
| Hub serveur | `packages/cortex/content/core3/locations/lost_heaven_hub.json` |
| Catalogue PNJ | `packages/cortex/content/core3/core3_npc_catalog.json` |
| POI export | `content/core3/world_poi/scrapaltai.json` |
| Carte client | `packages/prime-client/assets/maps/scrapaltai_map_config.json` |
| Gabarit spatial | `packages/prime-client/docs/RETAIL_CITY_LAYOUT.md` |

---

## Checklist alignement équipe

- [ ] Lost Heaven = **petite ville** (col 8 / row 3), pas la capitale.
- [ ] Capitale lore = **Zalem** (centre carte) — pas confondre avec LH.
- [ ] Nouveau PNJ / quête → coords LH, pas ME.
- [ ] Godot : verts = référence LH ; bleu bas de carte = ME legacy.
- [ ] Déployer catalogue migré après changement JSON.
- [ ] Phase 2 : noter `building_cell` La Perle dès pose IG.
