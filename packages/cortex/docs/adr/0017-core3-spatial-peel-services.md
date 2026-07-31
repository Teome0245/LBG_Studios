# ADR 0017 — Core3 garde spatial + peel services (anti techno-tourisme)

## Statut

**Accepté** — 2026-07-28  
**Décideurs** : Pilote  
**Complète** : ADR 0002 (autorité jeu), ADR 0005 (Core3 Prime), ADR 0016 (axe LBG talents/artisanat), ADR 0015 (tri-backend équipe)

---

## Contexte

1. **Prime 246** : Core3 = autorité monde (spawns, tick, PNJ, joueurs IA, sim de vie).
2. **Client** : `prime-client` Godot — affiche le monde ; **ne définit pas** Lost Heaven.
3. Tentation « next-gen » (Agones, Unity/Unreal MMO Kit, Nakama seul, Rust custom) : remplacer le monolithe spatial par idéal architectural.
4. Réalité produit : hub Lost Heaven, IA vivante, multiplons, Godot déjà branché — **sim spatiale fonctionnelle** qu’on ne doit pas jeter.

---

## Question centrale

> Conserve-t-on Core3 comme serveur Prime spatial, ou migre-t-on vers une stack Agones / zone custom / Unity ?

**Réponse retenue (A + B + peel)** : **oui, on conserve Core3** (A) ; **non au big bang next-gen** (B) ; modernité = **services à côté**. Migration monde = **B′ conditionnel** (Phase 2–3 seulement).

---

## Argumentaire A — pourquoi **garder Core3** (phase actuelle)

### Ce que Core3 apporte déjà

| Actif | Pourquoi ça compte |
|--------|-------------------|
| Monde vivant | Spawns, pathing, multiplons, scripts Lua, joueurs IA — déjà en prod 246 |
| Autorité unique | Pas de double écriture monde (ADR 0002) |
| Contenu / ops | Fork `server-core3`, patches `content/core3/`, runbooks, équipe |
| Coût | Réécrire sim + inventaire + IA + zone = **années**, pas un sprint |
| Client Godot | Déjà découplé du rendu SWG — le serveur n’a plus besoin d’être « le client » |

### Ce que « next-gen » décrit vraiment (trois problèmes)

1. **Sim spatiale** (zones, PNJ, collisions, tick) → Core3 est fort ici.  
2. **État joueur transactionnel** (inventaire, talents, économie) → à **sortir** du monolithe.  
3. **Orchestration scale** (Agones / K8s) → seulement quand N shards.

La bonne réponse n’est pas « tout jeter », c’est **éplucher** (2) puis éventuellement (3).

### Quand Core3 devient une prison (seuils, pas slogans)

- Objectif **zéro** protocole SOE / TRE / structures SWG côté runtime.  
- Inventaire / craft / quêtes exigent un modèle que Lua+Core3 ne tient plus.  
- Scale horizontal (beaucoup de zones) sans monolithe zone.  
- Équipe capable de maintenir un backend Go/Rust + sim custom **en parallèle** du produit jouable.

**Aujourd’hui** : Lost Heaven, IA, Godot, M9/M10 avancent **sur** Core3 — on n’est **pas** à ces seuils.

### Recommandation produit (A)

> **Oui, on garde Core3 comme serveur Prime** pour la géographie, les PNJ, les joueurs IA et la sim de vie.  
> **Non**, on ne reconstruit pas ça dans Unity/Unreal/Agones maintenant.  
> **Oui**, on **sort progressivement** inventaires / talents / social vers des services (déjà amorcé `:8791`) ; Godot parle à ces services **et** au monde Core3.

---

## Argumentaire B — pourquoi **pas** de migration totale immédiate

| Option « catalogue » | Risque pour LBG |
|--------------------|-----------------|
| **Agones + micro-zones** | Ops K8s lourde ; aucun gain tant que 1 galaxie / 1 hub |
| **Unity / Unreal MMO Kit** | Client cible = **Godot** ; double client = perte de focus |
| **Nakama seul** | Excellent inventaire/social ; **pas** une sim monde — il faudrait quand même un zone server |
| **Rust custom** | Perf max, **tout à construire** (PNJ, quêtes, outils) |

Migrer « pour être next-gen » = **perdre** la sim de vie déjà définie — exactement ce qu’on refuse.

*(La feuille de route Phase 2–4 ci-dessous est le **seul** chemin autorisé si B devient nécessaire.)*

---

## Décision

### 1. Garder Core3 comme **calculateur spatial + vie**

| Core3 fait (garder) | Core3 ne doit plus être la source de vérité (peel) |
|---------------------|-----------------------------------------------------|
| Qui est où | Inventaire transactionnel |
| Qui interagit / combat (tick) | Talents / skills persistés |
| Scripts IA proximité (faim, soif, patrouilles, multiplons) | Craft / schémas hors TRE si possible |
| Géographie / spawns / zone | Social, matchmaking, comptes (cible) |

**Règle d’or produit** : le serveur (Core3 tant qu’il reste) **définit** Lost Heaven et la vie des PNJ/IA ; **Godot affiche** (coords, interpolation, rendu). Pas d’ancrages client qui figent la sim.

### 2. Architecture hybride cible (Phase 0–1)

```
Godot ──WS / snapshots / move──► Core3 Prime (246)     # spatial + comportement
     └──HTTP/gRPC────────────────► Sidecar LBG (:8791+) # inventaire, talents, craft
```

Le jour où un **go/no-go** valide le remplacement du bloc spatial, on substitue Core3 par un **zone server** Go/Rust qui expose **la même API spatiale** ; inventaire + Godot changent peu.

### 3. Anti-patterns rejetés (immédiat)

| Idée | Verdict |
|------|---------|
| Rewrite monde « pour être next-gen » | **Non** — piège MMO indé |
| Agones / K8s multi-zones maintenant | **Non** — trop tôt (1 hub / 1 shard) |
| Remplacer Godot par Unity/Unreal | **Non** — client cible déjà Godot |
| Nakama **seul** comme sim monde | **Non** — excellent transactionnel, pas un zone server |
| Figer les PNJ côté Godot (`apply_visual_override` comme modèle) | **Non** — casse la vie serveur |

### 4. Phrase à graver

> **Core3 reste le serveur Prime spatial et « vivant » tant qu’il délivre.  
> Godot affiche.  
> Les systèmes transactionnels (inventaire, talents, quêtes) migrent hors monolithe.  
> On ne remplace le monde Core3 que sur critères mesurés — pas sur catalogue techno.**

---

## Feuille de route

### Phase 0 — 0–3 mois (focus immédiat) — **Keep + discipline**

| Priorité | Livrable |
|----------|----------|
| P0 | Tuer le mock talents : sidecar `:8791` réel (`/v1/catalog/skills` + inventaire) |
| P0 | Godot discipliné : pos Core3 → interpolation → affichage ; pas de vérité spatiale client |
| P0 | Spawns Lost Heaven corrigés **sur 246** ; locomotion / multiplons conservés |
| P0 | Doc ops : moteur Core3 ≠ univers LBG |

**Critère de sortie** : hub jouable Godot + talents/inventaire live + PNJ vivants visibles sans override client.

### Phase 1 — 3–6 mois — **Peel transactionnel**

- Inventaire / craft / talents : service LBG (Go/Rust + Redis/SQL) ; transactions hors crash zone Core3 / TRE.
- Quêtes : service dédié dès réimplantation (même contrat client).
- Contrats API stables : spatial (WS) vs transactionnel (HTTP/gRPC).

**Critère** : bug item / talent ne dépend plus d’un crash zone Core3.

### Phase 2 — jalon **go/no-go** moteur spatial

Scorecard (0–5) :

1. Frein protocole SOE pour features LBG  
2. Coût Lua / TRE pour contenu non-SWG  
3. Perf / stabilité zone sous charge IA  
4. Capacité équipe à tenir un zone-server custom  
5. Besoin réel multi-shards  

- Score **bas** → rester Core3 + peel.  
- Score **haut** → Phase 3.

### Phase 3 — migration monde (seulement si go) — **6–18 mois**

Ordre imposé :

1. Services transactionnels matures (Nakama-like ou équivalent Go).  
2. Zone server LBG (Go/Rust) — même API spatiale que le pont Godot actuel.  
3. Dual-run / shard test.  
4. Bascule Godot.  
5. **Agones / K8s** seulement si N zones à scaler.  
6. Éteindre Core3 + ADR de supersession.

### Phase 4 — cutover

Inventaire + monde + login hors Core3 ; archivage TRE/Lua runtime.

---

## Matrice de décision rapide

| Objectif | Choix |
|----------|--------|
| Avancer Lost Heaven + IA + Godot **maintenant** | **Garder Core3** |
| Inventaires / talents propres | **Sidecar / service** à côté |
| Scale 10+ zones | Plus tard : zone custom **puis** Agones |
| Monde 100 % non-SWG runtime | Phase 3 si Phase 2 le dit |
| Client 3D AAA | Programme **orthogonal** (pas une raison de jeter Core3 aujourd’hui) |

---

## Conséquences

| Acteur | Action |
|--------|--------|
| Ops / Héphaïstos | Spawns & stabilité 246 ; pas de cluster K8s « pour le plaisir » |
| Dev game / Dédale | Contenu + Lua vie PNJ/IA ; multiplons ; pas de redesign spatial Godot |
| Dev Godot / Iris–Hermès | Miroir spatial ; UI branchée sidecar pour M10+ |
| Sidecar `:8791` | Devenir **vérité** inventaire/talents (Phase 0–1) |
| Équipe / Element | Toute proposition « on remplace Core3 » → citer ce ADR + scorecard Phase 2 |

---

## Liens

- ADR [`0002-mmo-autorite-pont.md`](0002-mmo-autorite-pont.md) — autorité jeu Core3  
- ADR [`0005-new-mmo-core3-coexistence.md`](0005-new-mmo-core3-coexistence.md) — Core3 Prime unique  
- ADR [`0016`](../../../../new_mmo/lbg-mmo/docs/adr/0016-prime-axe-lbg-talents-artisanat.md) — produit LBG talents/artisanat (chemin relatif monorepo → `new_mmo`)  
- Tâches spawn Lost Heaven Core3 (run `b1760be2eb38`) — spawns 246 sans figer locomotion  

---

## Historique

| Date | Événement |
|------|-----------|
| 2026-07-28 | Accepté — hybride Core3 spatial + peel ; Phase 0 focus ; anti techno-tourisme |
| 2026-07-28 | Enrichissement : **argumentaire A** + **B** ; réponse formalisée **A + B + peel** ; Pilote **GO Phase 0** |
