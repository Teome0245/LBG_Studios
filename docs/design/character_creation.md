# Création de personnage — L'Amas

> *« Tu n'étais rien. Puis le désert a tremblé, et quelque chose s'est condensé. »*
> — Daan Oth, à un nouveau venu

**Statut** : Draft v1 — 2026-08-19
**Priorité** : O2 Gameplay
**Dépendances** : `prime-client` (UI Godot), `cortex/backend` (API), `cortex/agents` (joueur IA)

---

## 1. Concept narratif : l'Amas

### Qu'est-ce qu'un Amas ?

Dans l'univers LBG, aucun être ne « naît » au sens classique. Sur Scrapaltai, l'énergie vitale
résiduelle — celle qui suinte des lignes telluriques, des vestiges du Nexus-Arbre, des poches
de mana fossile enfouies dans le sable — se **condense** parfois spontanément.

Ce phénomène s'appelle un **Amas** : une grappe d'énergie et de matière qui se noue sans prévenir
(d'où le nom — un amas, au sens propre).

Un Amas est une **sphère instable d'énergie et de matière brute**, lumineuse, crépitante,
qui apparaît sans prévenir — souvent dans le désert aux abords de Lost Heaven, parfois dans
les ruines, parfois au cœur d'une tempête de sable. Les habitants de Lost Heaven connaissent
le phénomène. Certains le guettent. D'autres le craignent.

Un Amas **n'a pas encore de forme**. Il n'est ni humain, ni Fel'Rani, ni Mechari. Il est
du **potentiel pur** — une graine de conscience flottant dans un cocon de particules.

### Comment un Amas devient un être ?

L'Amas se cristallise sous l'effet de trois forces :

1. **L'intention** — le désir diffus de devenir *quelque chose* (choix du joueur)
2. **L'empreinte** — l'écho d'un être existant qui l'attire (copie d'un PNJ)
3. **Le milieu** — le biome, la proximité d'une faction, l'énergie ambiante

La cristallisation prend entre quelques secondes (narrativement : quelques heures) et se
déroule en trois phases visibles.

### Pourquoi c'est important

- Justifie narrativement l'apparition de nouveaux personnages sans « stork delivery »
- Explique pourquoi un joueur IA peut aussi créer un personnage (l'IA simule l'intention)
- Permet un onboarding progressif au lieu d'un menu froid
- Donne un moment mémorable et partageable (d'autres joueurs peuvent *voir* un Amas se former)
- Unifie joueurs humains et joueurs IA : même processus, même lore

### Un compte, un Noyau — les six faces du même Amas

Quand un compte crée son **premier** personnage, l'Amas laisse une trace : une **Particule
d'origine** (ou *Noyau Amas*) — un grain lumineux unique, invisible aux autres joueurs mais
visible sur chaque perso du compte (marque subtile : reflet dans les yeux, pulsation sous la
peau/carapace, halo au crépuscule).

Chaque personnage suivant (jusqu'à 6) est une **cristallisation différente** du **même Noyau**.
Ils ne sont pas des clones : races, archétypes et histoires divergent. Mais ils partagent :

- la même Particule d'origine (cosmétique + identifiant lore compte)
- la capacité d'**invoquer** l'un l'autre en session (§10)
- une résonance narrative : « *Tu me reconnais. On vient du même éclat.* »

> Ce n'est **pas** le Chœur du monde (joueurs IA autonomes). Les échos Amas n'ont pas de
> volonté propre — ils obéissent au perso actif ou restent en veille.

---

## 2. Flow de création

### 2.1 Phase 1 — Émergence (l'Amas apparaît)

**Ce que voit le joueur** : un écran sombre. Des particules de lumière convergent lentement
vers un point central. Une sphère instable se forme — pulsante, changeante. Autour, le son
du vent de Scrapaltai.

**Ce que voit le joueur IA** : un payload API. Même résultat, même lore.

**Interaction** : le joueur (humain ou IA) choisit une **direction d'émergence** puis
**personnalise la cristallisation** (sans faction — abordée plus tard en initiation in-game) :

| Étape (phase 1) | Contenu |
|-----------------|---------|
| **Mode** | Archétype · Empreinte · Chaos |
| **Sélection** | Archétype / PNJ / rien (chaos) |
| **Personnalisation** | Race (si archétype, parmi suggestions) · palette couleurs (aperçu Amas) |

| Mode | Description | Résultat |
|------|-------------|----------|
| **Archétype** | Choisir parmi 6 archétypes + race suggérée + palette | Stats + silhouette + affinités |
| **Empreinte** | Copier un PNJ connu du monde | Stats + silhouette du PNJ, variation ±10% |
| **Chaos** | Laisser l'Amas se cristalliser seul | Stats + race aléatoires |

> **Faction** : aucune à la création. Le choix (ou l'absence de choix) intervient dans la
> **phase d'initiation in-game** (Guide des Éclos, quêtes de quartier) — pas au Amas.

#### Les 6 Archétypes

Inspirés des 8 starters (arbres talents Pre-CU) mais condensés en 6 directions
narrativement ancrées :

| Archétype | Identité | Stats dominantes | Race suggérée | Arbre starter |
|-----------|----------|------------------|---------------|---------------|
| **Le Forgeur** | Bâtisseur, réparateur, créateur | Intelligence, Force | Tinkling, Mechari | Artisan |
| **Le Traqueur** | Éclaireur, survivant, pisteur | Agilité, Endurance | Fel'Rani, Varkoon | Prospecteur |
| **Le Soigneur** | Guérisseur, herboriste, chimiste | Intelligence, Esprit | Fae-Lume, Humain | Médecine |
| **La Voix** | Performer, négociateur, espion social | Esprit, Agilité | K'Miri, Humain | Scène |
| **Le Poing** | Combattant corps-à-corps, garde | Force, Endurance | Varkoon, Mogrul | Poing |
| **L'Œil** | Tireur, sniper, observateur | Agilité, Intelligence | Pykrel, Fel'Rani | Visée |

> Les archétypes ne sont **pas des classes**. Ils déterminent le point de départ. La
> progression par usage permet de bifurquer librement ensuite.

#### Le mode Empreinte (copier un PNJ)

L'Amas, attiré par l'écho d'un être existant, prend sa forme comme modèle.

- Le joueur choisit un PNJ parmi ceux **qu'il a déjà rencontrés** (ou, pour un premier
  personnage, parmi une liste de PNJ « notoires » de Lost Heaven)
- Le personnage hérite de la **race, taille, corpulence et stats de base** du PNJ
- Une **variation aléatoire de ±10%** est appliquée (l'Amas n'est pas un clone parfait)
- L'apparence est **similaire mais distincte** (palette décalée, traits légèrement différents)
- Le PNJ source est noté dans la fiche du personnage (lore : « né de l'empreinte de... »)

PNJ notoires disponibles au premier personnage :

| PNJ | Race | Archétype implicite |
|-----|------|---------------------|
| Jax Moro | Humain | La Voix |
| Kisreudi Teste | Fel'Rani | Le Soigneur |
| Kell Asa | Tinkling | Le Forgeur |
| Talen Ress | Humain | La Voix |
| Daan Oth | Humain | Le Traqueur |
| Odo Merr | Mogrul | Le Soigneur |

#### Le mode Chaos

L'Amas n'a pas de direction. Il se cristallise aléatoirement.

- Race, stats, taille : **entièrement aléatoires** dans les bornes jouables
- L'archétype starter est déduit des stats dominantes
- Un trait spécial **« Né du Chaos »** est attribué (bonus mineur aléatoire, cosmétique unique)
- Narrativement : « *L'Amas a vibré sans guide. Ce qui en est sorti... personne ne s'y attendait.* »

### 2.2 Phase 2 — Cristallisation (nom)

L'Amas prend forme selon les choix de l'émergence. La silhouette apparaît progressivement
(particules → contour → corps solide).

**Phase 2 = nom uniquement (V1)** :

- **Nom** (unique, filtre injures, pas de nom PNJ réservé)

Les couleurs et la race ont déjà été fixées en phase 1. Traits distinctifs et corpulence → V2.

### 2.3 Phase 3 — Éveil (entrée dans le monde)

Le personnage ouvre les yeux. Il est debout dans le **Champ des Amas** — une zone juste
à l'extérieur de la palissade est de Lost Heaven, parsemée de cristaux éteints (anciens
Amas qui n'ont pas pris forme).

**Séquence d'éveil** :

1. Caméra : vue subjective floue → netteté progressive
2. Quête d'initiation **« L'Éclat qui se divise »** — Ryn Solh présente la Particule (§12)
3. Tutoriel organique : marcher, inventaire (via le Guide)
4. Le joueur est libre après ~3–5 minutes

> Pour un joueur IA, la phase 3 est instantanée (skip cinématique, entrée directe en zone).

---

## 3. Joueur IA — Création de personnage

### Principe

Un joueur IA (agent autonome) peut créer un personnage **exactement comme un joueur humain**,
via la même API. La différence est uniquement dans l'interface :

| Aspect | Joueur humain | Joueur IA |
|--------|---------------|-----------|
| Interface | UI Godot (écran Amas) | API REST |
| Choix | Interactif (clic, slider) | Payload JSON |
| Phase Éveil | Cinématique jouée | Skippée (flag `skip_awakening`) |
| Lore | Identique | Identique |
| Résultat | Identique | Identique |

### Stratégies de l'IA pour choisir

L'agent IA peut :

1. **Archétype dirigé** — l'orchestrateur décide d'un archétype selon un objectif
   (ex : « l'écosystème manque de soigneurs » → Le Soigneur)
2. **Empreinte PNJ** — l'IA copie un PNJ pour « jouer un rôle similaire » dans le monde
3. **Chaos** — pour de la diversité, l'IA peut lancer un personnage aléatoire
4. **Directive narrative** — l'orchestrateur peut spécifier un brief narratif
   (ex : `"brief": "un traqueur solitaire qui évite Lost Heaven"`)

### Contraintes IA

- Un joueur IA a les **mêmes limites** qu'un joueur humain (max personnages par compte, cooldown)
- Le personnage IA est **flaggé `is_ai: true`** dans la base (visible dans le cockpit Studio,
  invisible pour les autres joueurs in-game)
- L'IA doit fournir un **nom** (peut utiliser un générateur de noms par race)

---

## 4. API — `POST /v1/characters`

### Endpoint

```
POST /v1/characters
Authorization: Bearer <token>
Content-Type: application/json
```

### Request body

```json
{
  "mode": "archetype | empreinte | chaos",

  "archetype": "forgeur | traqueur | soigneur | voix | poing | oeil",

  "race_id": "race:varkoon",

  "empreinte_pnj_id": "kisreudi_teste",

  "customization": {
    "name": "Kael",
    "colors": {
      "skin": "#8B6914",
      "eyes": "#00CED1",
      "accent": "#FF6B35"
    },
    "traits": ["cicatrice_joue_gauche"],
    "corpulence": 0.6
  },

  "skip_awakening": false,

  "ai_brief": "un traqueur solitaire, méfiant, qui préfère le désert à la ville"
}
```

> `archetype` requis si `mode: "archetype"`.
> `race_id` optionnel si `mode: "archetype"` (défaut = 1re race suggérée).
> `empreinte_pnj_id` requis si `mode: "empreinte"`.
> `ai_brief` optionnel, utilisé par l'orchestrateur pour enrichir le background du personnage.

### Response (201 Created)

```json
{
  "character_id": "chr_a7f3...",
  "name": "Kael",
  "race": "Fel'Rani",
  "archetype_starter": "traqueur",
  "stats": {
    "force": 45,
    "agilite": 72,
    "intelligence": 58,
    "hp": 100,
    "endurance": 85,
    "esprit": 40
  },
  "origin": {
    "mode": "archetype",
    "amas_location": "champ_des_amass_est",
    "born_at": "2026-08-19T09:34:12Z"
  },
  "is_ai": false,
  "noyau_id": "noyau_a1b2c3d4",
  "particule_seed": "p7e4f2a9"
}
```

> `noyau_id` et `particule_seed` sont **identiques pour tous les persos d'un compte**
> (créés au 1er Amas, réutilisés ensuite).

### Validations

| Règle | Détail |
|-------|--------|
| Nom unique | 409 Conflict si doublon |
| Nom filtré | 422 si injure / nom PNJ réservé |
| Max persos/compte | 403 si limite atteinte (défaut: **6**, humain et IA partagent le quota) |
| Race archétype | 422 si `race_id` hors suggestions de l'archétype |
| Cooldown | 429 si création trop récente humain (300 s) · aucun pour IA |
| Race valide | 422 si race pas dans le catalogue jouable |
| PNJ valide | 404 si `empreinte_pnj_id` inconnu |

---

## 5. Données — Catalogue jouable V1

### Races jouables au lancement

| Race | Planète d'origine | Tailles (cm) | Silhouette Core3 | Disponible V1 |
|------|-------------------|--------------|-------------------|---------------|
| Humain | Terre-One | 155–200 | `human` | Oui |
| Fel'Rani | Arvandor | 140–180 | `human` | Oui |
| Varkoon | Arvandor | 150–190 | `wookiee` | Oui |
| Mechari | Mecha-Prime | 160–190 | `moncal` | Oui |
| Tinkling | Mecha-Prime | 30–50 | `sullustan` | Oui |
| Mogrul | Aetherion | 90–120 | `ithorian` | Oui |
| Pykrel | Arvandor | 20–30 | `rodian` | V2 |
| K'Miri | Khar'Zuun | 25–40 | `zabrak` | V2 |
| Fae-Lume | Arvandor | 35–45 | `twilek` | V2 |

> 6 races V1 = suffisant pour couvrir tous les archétypes.

### Stats de base par archétype

| Stat | Forgeur | Traqueur | Soigneur | Voix | Poing | Œil |
|------|---------|----------|----------|------|-------|-----|
| Force | 65 | 50 | 35 | 30 | 80 | 40 |
| Agilité | 40 | 75 | 45 | 65 | 45 | 80 |
| Intelligence | 70 | 55 | 75 | 60 | 30 | 65 |
| HP | 100 | 100 | 100 | 100 | 100 | 100 |
| Endurance | 60 | 70 | 50 | 55 | 75 | 55 |
| Esprit | 45 | 40 | 70 | 65 | 35 | 40 |

> Les stats de base sont modifiées par un **bonus racial** (±5 à ±15 selon la race).

---

## 6. Le Champ des Amas (lieu d'apparition)

### Description

Zone de ~200m², à l'est de la palissade de Lost Heaven. Terrain de sable durci parsemé de
**cristaux éteints** — des Amas qui n'ont jamais pris forme, fossilisés en structures
translucides de 30cm à 2m.

Ambiance : vent constant, lueur résiduelle bleue/orange dans les cristaux au crépuscule.
Quelques restes de campement (le Guide des Éclos vit ici).

### Fonctions gameplay

- **Zone de spawn** pour tous les nouveaux personnages
- **Zone sûre** (pas de mobs, pas de PvP)
- Les autres joueurs peuvent voir les Amas se former (événement visuel public)
- Un Amas en cristallisation émet de la lumière et du son — effet social naturel

### Le Guide des Éclos (nouveau PNJ)

| Champ | Valeur |
|-------|--------|
| Nom | **Ryn Solh** |
| Race | Humain (vieux, barbe grise, peau tannée) |
| Rôle | Accueillir les nouveaux, tutoriel, première quête |
| Personnalité | Patient, laconique, légèrement amusé. A vu des centaines de Amas. |
| Localisation | Champ des Amas, assis sur un cristal éteint |
| Dialogue d'accroche | *« Encore un. Le désert continue de rêver. Bienvenue, petit éclat. »* |

---

## 7. Événement monde : Amas Majeur

Environ 1 fois par semaine (temps réel), un **Amas Majeur** apparaît — plus grand, plus
lumineux, plus instable. Ce n'est pas un joueur qui se crée : c'est un événement monde.

- **Visible** à longue distance (colonne de lumière dans le ciel)
- Les joueurs proches peuvent **influencer** la cristallisation (apporter des ressources,
  jouer de la musique, combattre les mobs attirés)
- Le résultat : un **PNJ unique** est engendré, avec une personnalité et un rôle déterminés
  par les actions des joueurs présents
- Ce PNJ s'installe à Lost Heaven et enrichit le monde de façon permanente

> C'est le mécanisme par lequel le monde grandit organiquement. Les joueurs IA peuvent
> aussi participer à un Amas Majeur.

---

## 8. Roadmap d'implémentation

| Phase | Contenu | Dépendance |
|-------|---------|------------|
| **V1-data** | Catalogue races jouables JSON, stats archétypes, table PNJ empreinte | Fait |
| **V1-api** | `POST /v1/characters`, validations, persistance | Fait |
| **V1-ui** | Écran Amas dans prime-client (3 phases, minimal) | Fait |
| **V1-ia** | L'orchestrateur peut appeler `POST /v1/characters` | Fait (API) |
| **V2** | **Écho Amas** (switch, invocation, échanges inter-persos), personnalisation étendue | V1 |
| **V3** | Amas Majeur (événement monde), Guide des Éclos quêtes complètes | V2 |

---

## 9. Décisions produit (V1)

| Question | Décision V1 |
|----------|-------------|
| Limite persos/compte | **6 total** (humain + IA partagent le quota → tester les 6 archétypes en parallèle) |
| Multi-personnage actif | **V2 — Écho Amas** (§10) : switch + invocation sans déco/reco |
| Suppression perso | **V2** — dissipation lore |
| Faction | **Aucune par défaut** — initiation in-game (Guide des Éclos, progression) |
| Mode Empreinte | PNJ notoires au 1er perso ; autres après rencontre |
| Joueurs IA visibles | Rien in-game ; flag cockpit Studio |
| Cooldown création | 5 min humain · aucun IA |
| Personnalisation Émergence | Mode + sélection + **race** (archétype) + **palette** ; phase 2 = nom |

---

## 10. Écho Amas — multi-personnage sans déco (V2, canon solo)

**Décision** : Option B retenue. Un joueur contrôle **1 perso actif** + **1 écho invoqué**
(max 2 entités visibles en zone). Switch et renvoi/invocation **in-game** — pas de déconnexion
pour échanger entre les 6 archétypes du compte.

### 10.1 Lore — fragment, pas PNJ

L'**Écho** est le second corps du **même Noyau Amas** (§1). Ce n'est pas :

- un PNJ du Chœur du monde
- un bot autonome avec quêtes / dialogue libre
- un second joueur humain connecté

C'est un **fragment condensé** : assez de matière pour marcher et aider, pas assez de
conscience pour agir seul. Narrativement, Ryn Solh dirait : *« Ton écho te suit. Ne lui demande
pas son avis — il n'en a qu'un, et c'est le tien. »*

**Marque visible** : tous les persos d'un compte portent la **Particule d'origine** (grain
cyan-orange, pulse lent). Quand l'écho est invoqué, la Particule **pulse en synchronie** entre
actif et écho — signal visuel que ce sont des faces du même Amas.

### 10.2 Boucle gameplay — actif, écho, switch, renvoi

```
┌─────────────────────────────────────────────────────────┐
│  Compte (6 persos max, 1 Noyau Amas partagé)          │
│                                                         │
│   [Perso A — ACTIF]  ←──switch──→  [Perso B — ÉCHO]    │
│        │                              follow + support   │
│        │  « Renvoyer l'écho »                            │
│        ↓                                                 │
│   [Perso B disparaît en particules]                       │
│        │  « Invoquer… » (liste des 5 autres persos)     │
│        ↓                                                 │
│   [Perso C — ÉCHO]                                       │
└─────────────────────────────────────────────────────────┘
```

| Action | Effet | Cooldown suggéré |
|--------|-------|------------------|
| **Invoquer un écho** | 2e perso apparaît près de l'actif, mode follow | 30 s (hors combat) |
| **Switch actif ↔ écho** | Contrôle bascule ; l'ancien actif passe en follow | 5 s (hors combat) |
| **Renvoyer l'écho** | L'écho se dissipe en particules, disparaît de la zone | immédiat |
| **Invoquer un autre** | Choisir un perso du compte (non présent) comme nouvel écho | 30 s |

**Échanges inter-persos** : le joueur peut transférer objet / crédits entre actif et écho
via un menu « Échange Amas » (proximité < 3 m, les deux entités présentes). Pas besoin de
se déconnecter ni de repasser par l'écran login.

> En combat : switch bloqué ou rallongé ; renvoi d'écho autorisé (fuite tactique lore :
> *« Retourne dans le Noyau. »*).

### 10.3 Comportement de l'écho (non-autonome)

| Comportement | Détail |
|--------------|--------|
| **Follow** | Maintien 2–4 m, évite obstacles, ne aggro pas seul |
| **Combat** | Attaque / soin **uniquement** si le perso actif le déclenche (hotkey « Ordre écho ») |
| **Dialogue** | Silence — pas de lignes propres ; le actif parle pour les deux si besoin |
| **Quêtes** | Progression **actif uniquement** ; l'écho est spectateur |
| **IA** | State machine simple (follow → idle → ordre → regroup) — **pas** d'orchestrateur LLM |

### 10.4 Soutiens légers par archétype (ordre écho)

Un bouton / hotkey déclenche l'aide de l'écho selon **son** archétype (pas celui de l'actif) :

| Archétype écho | Soutien (cooldown ~60 s) |
|----------------|--------------------------|
| **Forgeur** | Répare l'arme/outil actif (+5 % durabilité stub) |
| **Traqueur** | Ping ressource / danger à 20 m pendant 10 s |
| **Soigneur** | Soin léger (+10 % HP) sur l'actif |
| **Voix** | Buff social (+5 % réputation quartier, 5 min) |
| **Poing** | Taunt 3 s sur la cible visée par l'actif |
| **Œil** | Marque cible (+5 % précision actif, 15 s) |

### 10.5 Switch — ce qui se passe techniquement

1. Le client envoie `switch_echo` au gateway (actif_id ↔ echo_id).
2. Le serveur **transfère le contrôle** : input → nouvelle entité actif.
3. L'ancien actif passe en mode écho (AI follow sur l'autre).
4. Caméra, hotbar, inventaire **suivent le nouveau actif**.
5. Position : les deux entités restent à leur place (pas de teleport).

Inventaires **séparés** par perso ; échange via menu proximité (§10.2).

### 10.6 Limites (strict)

- **Maximum 2 entités simultanées** en zone : **1 actif + 1 écho**. Jamais 3.
- **1 seule invocation** à la fois — impossible d'invoquer un 2e écho tant que le premier
  n'est pas renvoyé.
- Les **4 autres persos** du compte (sur 6 max) restent en veille, non matérialisés.
- Pour changer d'écho : **renvoyer** puis **invoquer** un autre (pas de swap direct écho↔écho).
- Switch = bascule contrôle **actif ↔ écho** uniquement.

### 10.7 Annexe — double connexion (LAN / équipe, non prioritaire)

Deux sessions Launchpad sur le même compte restent possibles en **LAN** pour coop réelle
(deux humains, un compte). Hors scope solo V2. Si activé : cap 2 sessions, pas d'écho en
parallèle (les entités sont déjà deux joueurs autonomes).

---

## 11. Specs techniques V2 (Écho — à implémenter)

| Composant | Responsabilité |
|-----------|----------------|
| `prime-client` | UI switch / invoquer / renvoi ; menu échange ; sync caméra + hotbar |
| Gateway Prime | Messages WS `invoke_echo`, `dismiss_echo`, `switch_active`, `amas_trade` |
| Cortex (optionnel) | Persistance Noyau Amas (`noyau_id`, `particule_seed`) à la création perso — **fait V1** |
| `prime-client` | Panel **H** — prototype invoke / switch / dismiss (stub local + WS) |

Messages WS proposés :

```json
{"type": "invoke_echo", "character_id": "chr_…"}
{"type": "dismiss_echo"}
{"type": "switch_active"}
{"type": "echo_order", "order": "soin|forge|…"}
{"type": "amas_trade", "items": [...], "credits": 0}
```

---

## 12. Quête d'initiation — « L'Éclat qui se divise »

**ID** : `lh_init_particule_echo`  
**Donneur** : Ryn Solh (Guide des Éclos), Champ des Amas est  
**Déclencheur** : auto au **1er personnage** du compte, ~1 s après entrée en zone  
**Persistance** : `user://initiation_quest.json` (client Godot V1)

### Objectif pédagogique

1. Présenter la **Particule d'origine** / Noyau Amas (visuel + `noyau_id` / `particule_seed`)
2. Expliquer le **pouvoir d'invocation** (max 2 simultanés : actif + écho)
3. Inviter à **créer le 2e personnage in-game** (sans déco/reco)
4. Faire **expérimenter** invoke / switch / renvoi via panel **H**

### Étapes

| # | ID | Contenu | Action joueur |
|---|-----|---------|---------------|
| 1 | `accueil` | Ryn accueille au Champ des Amas | Continuer |
| 2 | `particule` | Révélation Particule + Noyau | Affichage cosmétique |
| 3 | `pouvoir` | Lore invocation (2 max, 1 écho) | Continuer |
| 4 | `second_eclat` | « Cristallise un second éclat ici » | **Ouvre écran Amas in-game** |
| 5 | `invocation` | « Invoque ton écho (H) » | Ouvre panel Écho |
| 6 | `complete` | Clôture + accès libre Lost Heaven | Terminer |

### Création 2e perso in-game

- Même flow Amas que login (`CharacterCreationPanel`, flag `in_game=true`)
- API `POST /v1/characters` — même `noyau_id` / `particule_seed` que le 1er
- Roster compte mis à jour sans déconnexion
- Quête reprend automatiquement à l'étape invocation

### Fichiers

| Fichier | Rôle |
|---------|------|
| `content/world/quests_lbg_templates.json` | Template sidecar / board |
| `prime-client/config/initiation_quest_particule.json` | Script quête client |
| `scripts/initiation_quest_controller.gd` | État + progression |
| `scripts/initiation_quest_panel.gd` | UI dialogue Ryn Solh |

### Reset (debug)

Supprimer `user://initiation_quest.json` pour rejouer l'initiation.


