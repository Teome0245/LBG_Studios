# Hub Lost Heaven — monde visible

## Couches (WorldMap, bas → haut)

| Couche | Rôle |
|--------|------|
| HubBuildingsLayer | POI lore LH (12 bâtiments) — ON par défaut ; Ctrl+H |
| HubPropsLayer | Chemins + rempart ovale + **allées de seuil** + épines E–O/N–S |
| HubGroundLayer | Sol / plaza (optionnel) |
| **RetailLayoutLayer** (verts) | Gabarit ME → LH — **off** par défaut (Ctrl+Shift+R) |

Échelles : `size_m` = mètres Core3 (collision = rendu) ; `building_size_multiplier` **1.0**.  
Portes : champ `door` (face / width / depth / apron) — rendu + vestibule walkable. Doc : `docs/RETAIL_CITY_LAYOUT.md`.

## Data

- `scrapaltai_map_config.json` — config planète (id moteur `planet: tatooine`, affichage Scrapaltai)
- `scrapaltai_pois.json` / `scrapaltai_zones.json` — POI / zones debug
- `scrapaltai.svg` — texture shard ; `scrapaltai_planet.jpg` — carte lore Ctrl+M
- `retail/scrapaltai/` — layouts retail (Lost Heaven + gabarits)
- `lost_heaven_buildings.json` — POI bâtiments
- `lost_heaven_props.json` — chemins + meubles
- `lost_heaven_npc_anchors.json` — placement PNJ (override visuel)

Compat lecture seule : symlinks `tatooine_map_config.json` → `scrapaltai_map_config.json` (idem pois/zones).
Nouveaux scripts/outils doivent utiliser les chemins `scrapaltai_*`.

## Contrôles

- **H** — recentrer caméra hub (4749, -737)
- **Ctrl+H** — toggle sol + bâtiments + props hub (art LH)
- **Ctrl+W** — toggle eau debug (polygones `scrapaltai_zones.json`, vide depuis migration LH)
- **Ctrl+C** — toggle collisions / palissade debug (zone_layers + emprises LH). Clôture hub **off** par défaut (sortie libre).
- **Ctrl+B** — toggle objets retail Mos Eisley (`mos_eisley_ws.json`, off par défaut)
- **L** — nameplates entités (off par défaut)
- **F9** — panneau debug

## Joueur humain

Voir `docs/HUMAN_PLAYER.md` — packet `cn` UDP `:12345`.
