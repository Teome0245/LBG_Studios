# Retail City Layout

## Décision — référence spatiale Lost Heaven (2026-08-13)

**Oui : la carte positionnement retail est la référence d’implantation densités / emprises.**

| Couche | Fichier | Rôle |
|--------|---------|------|
| **Référence spatiale** | `assets/maps/retail/scrapaltai/lost_heaven_retail_layout.json` | Gabarit Mos Eisley décalé sur ancre LH `(4749, -737)` — 72 emprises + markers |
| Overlay jeu | `RetailLayoutLayer` (Ctrl+Shift+R) | Carrés verts = cette référence |
| POI lore LH | `lost_heaven_buildings.json` (12 bâtiments) | Labels LBG (La Perle, porte, marché…) — art / quêtes, **pas** la densité rue |
| Props / chemins | `lost_heaven_props.json` | Plaza, palissade, props (Ctrl+H) |

Ne pas écraser les x/z des POI lore avec le gabarit ME sans revue (noms SWG vs Bible LBG).  
Les `size_m` retail peuvent alimenter les POI LH (script `apply_mos_eisley_gabarit_lost_heaven.py`).

### Échelles (vérifiées — 2026-08-14)

| Élément | Formule | Exemple |
|---------|--------|---------|
| Jeton entité | `2 m × SCALE(0.5) × READABILITY(8)` | **8 px** |
| Emprise hub / collision | `size_m × SCALE × mul` | **mul = 1.0** |

**Règle** : `lost_heaven_buildings.json` → `size_m` = mètres Core3 **réels** (rendu **et** collision `ZoneLayers`).  
`world_render.building_size_multiplier` = **1.0** (plus de décalage visuel/physique).  
POI écartés ×**1.35** puis **organiques** (désalignement medium, rues ≥ ~26 m). Rempart élargi en conséquence.

Hub lore ON par défaut ; gabarit retail = Ctrl+Shift+R (référence densités ME, pas la collision hub).

Bbox hub lore (après écartement) ≈ **780 × 480 m** Core3 (+ rempart).

## PNJ serveur (snapshot gateway)

Dernière MAJ équipe LH CODE (2026-07-27).

- HTTP : `http://192.168.0.246:8765/v1/world/npcs_near?anchor_x=4749&anchor_z=-737&radius_m=800`
- Export client : `tools/retail/export_server_npcs_lost_heaven.sh`
- Carte : `tools/retail/build_prime_position_map.sh`
- Triangles **cyan** = entités fusionnées depuis le serveur (`retail_layout_layer`).

## Habillage Lost Heaven (pipeline art)

Checklist (2026-07-27).

- Pipeline : `tools/retail/habillage_lost_heaven.sh`
- Sprites overhead : copie `units_overhead` si NAS/B: indisponible → copie manuelle documentée.
- ComfyUI : pas de régression ; coordonner Iris (markers carte).

## Contrôles

- **Ctrl+Shift+R** — toggle overlay retail (référence)
- **Ctrl+H** — toggle sol / bâtiments lore / props hub
