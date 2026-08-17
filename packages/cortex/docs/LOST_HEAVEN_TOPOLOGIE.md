# Lost Heaven — topologie ville (concept art → POI)

**Statut** : mapping validé pour itération (2026-08-13)  
**Art** : [`lost_heaven_town_concept.png`](assets/lost_heaven_town_concept.png) · annoté [`lost_heaven_town_concept_annote.png`](assets/lost_heaven_town_concept_annote.png)  
**Données** : [`prime-client/assets/maps/lost_heaven_town_topology.json`](../../prime-client/assets/maps/lost_heaven_town_topology.json)

---

## Décision

| Question | Choix |
|----------|--------|
| Adapter l’art à LH, ou LH à l’art ? | **Les deux, à doses** : **forme** (ovale, 2 portes, plaza) → concept art ; **coords POI Core3** restent la vérité gameplay pour l’instant |
| Style visuel | Toits médiévaux = **référence spatiale seulement** — en jeu : scrap / désert / patchwork (Bible N10) |
| Gabarit ME rectangulaire | Devient **secondaire** ; le concept ovale guide la palissade v2 |

---

## Lecture de la carte concept

```
        N
        ↑
   Porte OUEST ───────────── enceinte ovale ───────────── Porte EST
   (→ Zalem)                                              (→ désert)
        │                                                      │
        │     [logements]   [auberge/clinique/hall]           │
        │              ╲         │         ╱                   │
        │               ╲   PLAZA TRIANGLE ╱                    │
        │                ╲_______╱_______╱                     │
        │     [banque/mairie]  │  [cantina/artisan]            │
        │                      │                               │
        │                 [marché]  [port]                     │
```

---

## Mapping POI (existant → districts art)

| POI LBG | Rôle | District art | Coords Core3 actuelles |
|---------|------|--------------|------------------------|
| Plaza | Cœur | Triangle central | `(4749, -737)` |
| Port shuttle | Arrivée | Sud-est | `(4809, -802)` |
| La Perle | Cantina | Est | `(4939, -802)` |
| Banque | Civique | Ouest (grand bâtiment) | `(4679, -802)` |
| Mairie | Civique | Ouest / SO | `(4679, -932)` |
| Auberge | Nord | Nord plaza | `(4809, -672)` |
| Clinique | Nord | Nord-ouest plaza | `(4679, -672)` |
| Hall entraînement | Nord | Nord-est plaza | `(4939, -672)` |
| Marché | Sud | Sud plaza | `(4809, -932)` |
| Bureau missions | Sud | Sud-est plaza | `(4939, -932)` |
| Atelier artisan | Est | Est | `(5069, -802)` |
| Logements PNJ | Ouest | Près porte ouest | `(4549, -802)` |
| Porte (legacy sud) | Sortie | → **devient porte est** | `(4809, -1062)` |

---

## Écarts à combler (actuel vs concept)

| Actuel (gabarit ME) | Concept art | Action |
|---------------------|-------------|--------|
| **1 porte sud** puis **2 portes** (P1) | Enceinte **ovale** + anneau (P2) | **Fait** — emprises `size_m` = collision ; POI écartés (rues) ; rempart élargi ; portes sur le mur |
| **1 porte sud** | **2 portes** (O / E) | P1 — `gate:west_zalem` + `gate:east_wilds` |
| Routes en croix | Anneau + organique | **Fait** (P2) — chemins courbes + `path:lh_inner_ring` |
| Overlay verts retail | Carte ville lisible | P3 — texture concept + `map_uv` |

---

## Phases

1. **P0** — art + JSON mapping (**fait**)
2. **P1** — deux portes dans `lost_heaven_props.json` (ouest = route Zalem, est = wilds) — **fait** (2026-08-13)
3. **P2** — palissade ovale + anneau plaza (collision `ZoneLayers`) — **fait** (2026-08-13)
4. **P3** — mini-carte Godot (Ctrl+H / panneau ville) branchée sur `map_uv`

---

## Ce qu’on ne fait **pas**

- Remplacer le lore scrap par une ville « médiévale fantasy » (V1 / N10)
- Déplacer massivement les POI Core3 sans smoke PNJ / bots
- Effacer Mos Eisley vanilla (hors sujet)

---

## Prochaine étape proposée

Appliquer **P3** — overlay / mini-carte ville (texture concept + `map_uv`).
