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

- `lost_heaven_buildings.json` — POI bâtiments
- `lost_heaven_props.json` — chemins + meubles
- `lost_heaven_npc_anchors.json` — placement PNJ (override visuel)

## Contrôles

- **H** — recentrer caméra hub (4749, -737)
- **Ctrl+H** — toggle sol + bâtiments + props hub (art LH)
- **Ctrl+C** — toggle collisions / palissade debug (zone_layers)
- **L** — nameplates entités (off par défaut)
- **F9** — panneau debug

## Joueur humain

Voir `docs/HUMAN_PLAYER.md` — packet `cn` UDP `:12345`.
