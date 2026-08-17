# Face Rig 2D — Orch UI (:5174) + Pilot + MMO

**Statut** : FaceRig sous **Lyra — Personnalisation** sur http://192.168.0.100:5174/ ; stub aussi dans Pilot `#/assistant`.  
**Brief art** : `Infographiste_IA/pipelines/face_parts/BRIEF_lyra_face_rig.md`  
**Jauges** : `docs/lyra_gauges_homeostasie.md`

## Cibles UI

| Surface | Emplacement | Lien |
|---------|-------------|------|
| **Orch UI (priorité visuelle)** | Colonne droite `LyraPanel` | http://192.168.0.100:5174/ |
| Pilot | `#/assistant` carte humeur | http://192.168.0.140:8080/pilot/#/assistant |
| Prime MMO | portraits dialogue (bake) | `assets/ui/portraits/` |

## Pourquoi une pierre deux coups

| Consommateur | Ce qu’il utilise | Où |
|--------------|------------------|-----|
| **Orch / Pilot** | Calques live + jauges Lyra | `face_rig/` |
| **Prime Client** (MMO) | PNG plein visage / expression | `assets/ui/portraits/` |

Même vocabulaire d’expressions, même Infographiste, refs `N:\…\MMORPG\Expressions`.

## API JS

```js
FaceRig.init(hostElOrId, { characterId: "lyra_assistant" });
FaceRig.setMood("curious");
FaceRig.setExpression("happy");
FaceRig.say("Bonjour");
```

Sans PNG : fallback CSS.

## Hors scope

- Remplacer l’avatar Three.js Pilot (complémentaire)
- Sprites overhead 2D monde
