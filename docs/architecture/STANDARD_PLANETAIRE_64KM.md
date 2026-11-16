# STANDARD PLANÉTAIRE MMO — 64 KM × 64 KM (TOROÏDE FERMÉ)

> **Document d'Architecture Technique & Gameplay**  
> **Date de révision** : 16 Novembre 2026  
> **Mise à niveau** : Standard 64 km × 64 km ($4\,096\text{ km}^2$), validé sur Scrapaltai.  
> *(Note d'anticipation : réserve 128 km × 128 km pour une future mégaplanète).*

---

## 1. Vue d'ensemble

Toutes les planètes ouvertes du MMO (Scrapaltai, Corellia, etc.) adoptent le standard sphérique projeté / toroïdal :
- **Dimensions d'un hémisphère / planisphère complet** : **64 000 m × 64 000 m** ($64\text{ km} \times 64\text{ km}$).
- **Surface totale arpentable** : **$4\,096\text{ km}^2$** (équivalent à 256 maps SWG classiques de $16\text{ km}^2$, 100 fois Skyrim, ou 4 fois Just Cause 3).
- **Repère cartésien mondial** :
  - $X \in [-32\,000\text{ m}, +32\,000\text{ m}]$ (Ouest $\leftrightarrow$ Est)
  - $Z \in [-32\,000\text{ m}, +32\,000\text{ m}]$ (Nord $\leftrightarrow$ Sud)
  - Centre de projection planétaire : $(0, 0)$.

---

## 2. Règle de Rotation Torique (World Wrap)

Pour simuler une planète sans mur invisible (« Terre Ronde ») :
- En franchissant la frontière Est ($X \ge +32\,000$), le joueur et les entités réapparaissent en continu à l'extrême Ouest ($X \to -32\,000$).
- En franchissant la frontière Nord ($Z \le -32\,000$), le joueur boucle au Sud ($Z \to +32\,000$).
- Implémentation mathématique Godot & Hub :
  ```gdscript
  const WORLD_MIN: float = -32000.0
  const WORLD_SPAN: float = 64000.0

  func wrap_world_pos(pos: Vector3) -> Vector3:
      var wx: float = fposmod(pos.x - WORLD_MIN, WORLD_SPAN) + WORLD_MIN
      var wz: float = fposmod(pos.z - WORLD_MIN, WORLD_SPAN) + WORLD_MIN
      return Vector3(wx, pos.y, wz)
  ```
- **Exception (« Terre Plate »)** : Si une planète ou lune spécifique est désignée comme « Terre Plate / Fragment d'astéroïde », le wrap est désactivé et un champ de confinement ou abîme bloque les déplacements aux bordures.

---

## 3. Cycle Jour / Nuit Progressif (Fuseaux Horaires Planétaires)

Sur un monde de 64 km, la lumière solaire n'est pas uniforme :
- **Heure solaire locale** :
  $$\text{Heure locale} = \text{Heure méridienne centrale} + \left(\frac{X}{64\,000} \times 24\text{ h}\right)$$
  *(Chaque tranche de 2 667 mètres en longitude correspond à 1 heure solaire).*
- **Terminateur solaire** : Affiché sur la carte régionale (`planet_map_panel.gd`) sous la forme d'un gradient crépusculaire lissé (128 bandes) se déplaçant d'Est en Ouest.
- **Ambiance 2D au sol** : La pénombre et l'éclairage ambiant au sol (`canvas_of_kings_atmosphere.gd`) réagissent directement à la longitude $X$ de la caméra.

---

## 4. Répartition Géographique Régionale Canonique (Scrapaltai 64 km)

Les sites, villes et POIs sont harmonieusement répartis sur les 4 quadrants de la planète ($X, Z \in [-32\,000, +32\,000]$) :

| Secteur / Région | Site | Coordonnées $(X, Z)$ | Rôle / Description |
| :--- | :--- | :--- | :--- |
| **Bassin Central-Est** | **Lost Heaven** | `(+4 749, -737)` | Hub Joueur, Spatioport & Cantina La Perle |
| | **Ferme Lars-Val** | `(+4 500, -8 000)` | Station d'humidité centrale |
| **Grand Désert du Sud** | **Ksar Nomade** | `(+6 000, -18 000)` | Grande Oasis sacrée du Sud & Bazar de troc |
| | **Canyon des Épaves** | `(+11 000, -15 000)` | Débris du convoi Zalem & squelette Krayt |
| **Frontière Orientale** | **Oasis d'Al-Khali** | `(+18 000, -10 000)` | Étape caravanière des dunes de l'Est |
| | **Guet des Dunes** | `(+24 000, -5 000)` | Vigie orientale & épave du cargo Ikaros |
| **Massif Septentrional (Nord)** | **Anchor-Ridge** | `(+7 000, +16 000)` | Cité minière de duracier, falaises du Nord |
| | **Lac d'Améthyste** | `(+14 000, +22 000)` | Cratère d'impact géodique & réserve d'eau |
| **Plateau Industriel (Ouest)** | **Avant-poste Zalem** | `(-7 000, -1 000)` | Garnison de la passe & péage autoroutier |
| | **Zalem (Mégalopole)** | `(-18 000, +3 000)` | Capitale industrielle, 10 mégastructures |
| **Grand Rift Occidental** | **Mos Espa Bazar** | `(-14 000, -4 000)` | Marché franc à la sortie du Grand Rift |
| | **Camp des Ferrailleurs**| `(-18 000, -9 000)` | Terriers & ateliers des ferrailleurs Jawas |
| | **Gouffre du Dragon Krayt**| `(-22 000, +12 000)` | Fosse rocheuse colossale du Nord-Ouest |

---

## 5. Précision Numérique & Métriques de Déplacement

- **Précision Float32 à 64 km** :
  - L'incrément minimal à $64\,000\text{ m}$ est de $7{,}6\text{ mm}$ (sub-centimétrique).
  - Zéro vibration de caméra (*jitter*).
- **Temps de parcours** :
  - **À pied** ($18\text{ km/h}$) : tour du monde en ~3h30.
  - **En speeder bike** ($140\text{ km/h}$) : ~27 minutes d'un bout à l'autre.
  - **Navette orbitale / voyage rapide** : liaisons inter-cités en quelques secondes.

---

## 6. Réserve Future : Mégaplanète 128 km × 128 km ($16\,384\text{ km}^2$)

Pour une future planète continentale dédiée au vol spatial libre et atmosphérique :
- $X, Z \in [-64\,000, +64\,000]\text{ m}$.
- Précision Float32 toujours < $8\text{ mm}$ à $64\,000\text{ m}$.
- Nécessite du pavage dynamique de tuiles cartographiques (quadtree) pour le zoom `Ctrl+M`.
