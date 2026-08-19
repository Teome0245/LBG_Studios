# Face Rig 2D — Lyra Assistant

## Architecture

Le face rig affiche un visage 2D animé composé de calques superposés dans un sprite sheet unique (`face.png`).

### Mode `full_face`

Chaque frame du sprite sheet est un composite pré-assemblé de 4 calques :

| Ordre | Calque | Source | Scale | Position (Y, X offset) |
|-------|--------|--------|-------|------------------------|
| 1 | Base (tête chauve) | Copilot PNG §1 | fill 256px | 0, centré |
| 2 | Yeux | Copilot PNG §3 | 0.275 | 0.40, -28px |
| 3 | Bouche | Code_Generated §2 | 0.20 | 0.70, -15px |
| 4 | Cheveux | Copilot PNG §2 | 1.08 | -40px, -3px |

### Sprite Sheet (`face.png`)

Grille 5 colonnes × 3 lignes, cellules 256×256 px.

| | Col 0 | Col 1 | Col 2 | Col 3 | Col 4 |
|---|---|---|---|---|---|
| Row 0 | neutral | happy | sad | angry | surprised |
| Row 1 | talk_1 (E) | talk_2 (A) | talk_3 (O) | wink | blink |
| Row 2 | tired | squint | angry_talk | happy_talk | sad_talk |

### Émotions → Frames

| Émotion | Frame yeux | Frame bouche |
|---------|-----------|-------------|
| neutral | neutral | m_closed |
| happy | neutral | m_smile |
| sad | sad | m_sad |
| angry | angry | m_grimace |
| surprised | surprised | m_O |
| talking | neutral (cycle) | m_E → m_A → m_O |

## Sources des assets

- **Copilot_20260819_154626.png** (1024×1024, fond noir) : tête chauve, cheveux, yeux expressifs (8 variations)
- **Code_Generated_Image1.png** (1024×1024, fond checker) : bouches/phonèmes (12 variations : closed, A, E, I/S, O, U, smile, F/V, frown, grimace, sad)

Les sources originales sont archivées dans `Infographiste_IA/pipelines/face_parts/outputs/lyra_assistant/`.

## Pipeline de (re)génération

1. Fournir une planche source PNG avec sections : base, cheveux, yeux, bouches
2. Découper les éléments avec `clean_black()` (fond noir) ou `clean_white()` (fond checker)
3. Assembler les composites avec les offsets ci-dessus
4. Générer le sprite sheet 5×3
5. Déployer : `docker cp face.png lbg-frontend:/usr/share/nginx/html/face_rig/assets/lyra_assistant/`

## Frontend

- `face_rig.js` : détecte `mode: "full_face"` dans le manifest, charge `face.png`, applique `background-position` pour chaque émotion
- Cache-buster intégré (`?v=timestamp`) pour forcer le rechargement des PNG
- Fallback CSS si les assets ne chargent pas

## Évolutions prévues

- Planche source mieux proportionnée (éléments à la même échelle)
- Intégration ComfyUI pour génération cohérente via IP-Adapter
- Système de têtes modulaires pour PNJ/joueurs (12 types de base disponibles)
