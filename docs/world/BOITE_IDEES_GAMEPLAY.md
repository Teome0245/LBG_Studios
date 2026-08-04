# Boîte à idées — Gameplay extrait (LBG Prime)

**Date** : 2026-08-04  
**Statut** : extrait vivant — **n’écrit pas de Vérité** sans décision datée dans [`BIBLE_MMO.md`](BIBLE_MMO.md)  
**Source** : `LBG_IA_MMORPG/Boite à idées/` (lecture legacy)  
**Canon produit** : Bible · [`ARBRES_TALENTS_PRECU.md`](ARBRES_TALENTS_PRECU.md) · [`INVENTAIRE_PNJ.md`](INVENTAIRE_PNJ.md) · catalogue M10  
**Réf. Pre-CU runtime** : 245 lecture seule (V4)

---

## 0. Périmètre

| In | Out |
|----|-----|
| Hub Scrapaltai / Lost Heaven (couche A) | Fantasy Terre1 / magie explicite (couche D) |
| Structure talents Pre-CU + craft/social | OTServ / Unity / Unreal comme client |
| Races D1-10-A, bestiaire désert | Admin Studio, prompts Antigravity, assets seuls |
| PNJ à objectifs, quêtes LBG | Factions « Mondes Brisés » / Veridian comme lieux jouables |

Règle : une idée reprise ici se **recopie** vers Bible / catalogue / registry — on ne joue pas depuis la Boîte à idées.

---

## 1. Boucle centrale (enrichit V2)

Sources : `plan MMMORPG.txt` §4–5 · `20260527_rappel_objectif_mmo.txt`

| Principe | Reprise LBG |
|----------|-------------|
| Professions Pre-CU, dépendance entre métiers | Arbres M10 / ADR 0016 — **déjà** |
| On ne privilégie pas le combat ; craft + social | V34 combat hors vitrine courte |
| Pas de « niveau » unique : skills par usage + réputation | Progression box Pre-CU, pas XP flat fantasy |
| Boucles courte / moyenne / longue | Quête hub → housing/relations → influence (backlog) |

---

## 2. Hub Lost Heaven — tone (enrichit V10–V13)

Sources : `mmmorpg_ambiance.txt` · `20260426-1500.txt`

### Tone hub (proposé → ancre N10)

**« Patchwork. Récup’. Élégante désolation. »**

| Filtre | Application Scrapaltai / LH |
|--------|------------------------------|
| Look | Métal oxydé, cuir usé, objets jamais neufs, accents bleu électrique pâle / orange cuivré |
| Objets | Assemblages d’époques (réparation, scrap, pièce shuttle) |
| Dialogue | Concret, jargon technique léger — **pas** métaphore arcanique / magie |
| « Magie » | Interdite en surface ; « science oubliée / calibration » OK en couche B seulement |

**Mapper** : ancienne « Veridian » (ville patchwork) = **ambiance visuelle de Lost Heaven**, pas un 2ᵉ hub.  
**Cantina** : La Perle de Scrapaltai (V13).

---

## 3. Talents & craft (V30–V35)

Sources : rappel objectif · `MMO_LBG_Guides_suite_3.txt` (craft)

- Reprendre : recettes + stations + skills liés.
- **Ne pas** créer un skill flat `lbg_crafting_novice` qui court-circuite les boxes Pre-CU.
- Toute recette → `requires_skill` / `requires_box` catalogue M10 (V31).
- Référence boxes originales : **PreCU 245** (V4), puis miroir `precu_skill_id`.

---

## 4. Économie & quêtes (N5)

Sources : plan §5 · Guides suite_3 · **`plan MMMORPG.md` §5 (QuestEngine)**

### Types de quêtes (plan §5.1 → LBG)

| Type plan | Reprise Lost Heaven |
|-----------|---------------------|
| Statiques | Arcs hub / factions (plus tard) |
| Dynamiques locales | Templates déjà data (`quests_lbg_templates.json`) |
| Systémiques | Crise ressources, panne starport, faune aux portes — backlog Conductor/Chœur |

Templates QuestEngine du plan : escort, livraison, enquête, réparation, hack → **escort + enquête** ajoutés ; rituel/magie **gelés**.

### Templates quêtes LBG (remplacent stubs fantasy)

| Template | Exemple Lost Heaven | Giver |
|----------|---------------------|--------|
| Survey / prospection | Relever un gisement hors palissade | Scout trainer / Daan Oth |
| Livraison | Colis starport → marché | Guide / Daan |
| Escorte | Convoyer un civil porte → clinique | Sergent / Guide |
| Enquête | Disparition au marché → rumeuriste + scribe | Daan / Scribe |
| Réparation | Kit pour Jax (La Perle) ou atelier | Kell Asa / Jax |
| Rumeur | Info cantina → scribe | Habitué / Rumeuriste |
| Spectacle | Assister / tipper Artiste de scène | Talen (formation) / Artiste |
| Chasse faune | Meute Chacal / Scarabée | Sergent / Scout |
| Médecine | Venin → clinique | Odo Merr |

### Économie minimale hub (à data-iser)

Ressources déjà stub M10 : ferraille, ruban, grain, capsule d’eau, plaque, tampon.  
À étendre depuis bestiaire désert (carapace, venin, cristal sable…) → inputs artisan.

---

## 5. Races jouables (V23 — D1-10-A)

Source : `D1-10-A START.core3-selection.txt` (déjà partiellement dans `races.json`)

| Race LBG | Origine | Rôle MMO | Fit hub |
|----------|---------|----------|---------|
| Fel'Rani | Arvandor | éclaireur | Kisreudi (T1) |
| Tinkling | Mecha-Prime | artisan | atelier LH |
| Mechari | Mecha-Prime | technicien | voyageurs N8 |
| K'Miri | Khar'Zuun | espion désert | **fort** Scrapaltai |
| Murrik / Pykrel / Fae-Lume / Varkoon | Arvandor | variés | voyageurs |
| Plimp | Thalassia | amphibie | rare au désert |
| Mogrul | Aetherion | mineur | prospecteur |

---

## 6. Bestiaire Scrapaltai (désert) — P0

Source : `20260429_mmmorpg_bestiaire..txt` (biome Desert)

| Id proposé | Nom | Comportement | Danger | Loot → craft |
|------------|-----|--------------|--------|--------------|
| `beast:scorpion_titan` | Scorpion-Titan | embuscade | 4 | venin, carapace |
| `beast:serpent_sable` | Serpent de Sable | sous sable | 5 | écailles dorées |
| `beast:chacal_dore` | Chacal Doré | meute | 2 | fourrure dorée |
| `beast:scarabee_obsidien` | Scarabée Obsidien | blindé | 2 | obsidienne |
| `beast:marcheur_dunes` | Marcheur des Dunes | colosse lent | 4 | os géants |
| `beast:fennec_mirage` | Fennec Mirage | fuite / tromperie | 1 | poussière mirage |

Data : `packages/cortex/content/world/bestiaire_scrapaltai.json`.  
Schematics liés : `bandage_antivenin` (venin), `plaque_carapace`, `lame_obsidienne` — catalogue M10.  
**Gel** : Djinn Mineur (fantasy).

---

## 7. PNJ vivants & dialogue (V20, V40–V42)

Sources : **`plan MMMORPG.md` §6 + architecture PNJ** · `note de gemini.txt` · dialogue orchestrateur

| Idée plan | Reprise LBG |
|-----------|-------------|
| Identité procédurale (traits, métier, famille) | Registry + inventaire ; génération lourde = backlog |
| Cycle de vie (naissance→mort→succession) | Vision long terme — pas P0 hub |
| Routines adaptatives (stock, crime, métier) | GOAP léger roster LH |
| Objectifs C/M/L | Déjà `goals` registry — enrichir |
| Économie PNJ (produire / consommer / échanger) | Vendors hub + craft M10 |
| Relations sociales | Réputation ville (T*) |
| 3 niveaux sim + ticks sociaux | Actif LH / semi zone / passif stats |
| **MJ IA** (événements, incohérences, assist) | **Chœur + World Director / Campus** — pas un PNJ cantina |
| Joueurs IA | Chœur V50–V54 (Lia/Nix…) |
| Guardrails dialogue | **Bible only** — pas Gunnm/DBZ/Discworld en prompt joueur |

Lyra = IA incarnée **Studio / monde** (étoile du nord) — **pas** un PNJ cantina (≠ Kisreudi).

---

## 8. Factions / réputation (T3 ouvert)

Source : **`plan MMMORPG.md`** (3 factions officielles + 75 % civils)

| Idée plan | Adaptation Scrapaltai |
|-----------|------------------------|
| **75 % civils** | Défaut Lost Heaven — opinions / réputation ville |
| Coalition des Mondes Brisés (neutre, craft, récup’) | Culture **civils Lost Heaven** — label T* à trancher |
| Convergence Synthetika | Voyageurs **Mechari / Tinkling** (Mecha-Prime) — pas empire tech en hub |
| Cercle des Arcanes | **Gelé** (magie / couche D) |
| Flotte Libre / Empire / Néant / Tisseurs | Lore couche B ou rumeurs La Perle — pas surface joueur |

---

## 9. Archétypes modulaires → arbres M10

Source : plan §3.1 (classes = builds, pas cages)

| Archétype plan | Arbre / profession LBG |
|----------------|------------------------|
| Combat | Poing / Visée (P2 UI) |
| Support | Médecine + Scène (soin morale) |
| Artisanat | Artisan de rue (+ survey artisan) |
| Exploration | Prospecteur / Pilotage shuttle |
| Social / Économie | Citoyen de quartier + vendors |

---

## 10. Paramètres monde (backlog Scrapaltai)

Source : plan §3.2 / GDD 4.4 — **à trancher**, pas Vérité encore

| Paramètre | Proposition plan | Note |
|-----------|------------------|------|
| Jour/nuit | 6 h | Optionnel LH |
| Orbite / saison | ~91 j | Couche B |
| Lunes / marées | Effets | Hors désert sauf events |
| Housing | Persistant | Après M10 B2B |
| Vol / nage | Physique simplifiée | Après hub stable |
| Langages | Raciaux / planétaires | Backlog social |

---

## 11. Backlog hors hub (vision plan)

Housing, vol, nage, cartes sphériques, Terre plate, multivers planètes, 30k–60k PNJ simulés — **vision** `plan MMMORPG.md` Phases 2–5.  
Priorité O2 actuelle : M10 craft B2B + persona + hub LH + Chœur.

---

## 12. Priorités d’exécution (ordre proposé)

1. Ancre **N10 tone** Scrapaltai + **N11** bestiaire — *fait*
2. Loots → schematics M10 — *fait*
3. Templates quêtes LBG (+ escort/enquête) — *fait / enrichi*
4. Enrichir **goals/routines** trainers hub (GOAP léger)
5. Faction civils hub (label T*) + T3 pilotes
6. Spawns désert autour LH — sans toucher 245
7. MJ IA / events systémiques via Chœur (plan §6.3)

---

## 13. Index sources

| Fichier | Rôle |
|---------|------|
| `…/plan MMMORPG.md` | **GDD complet** — lu en structure (§1–10 + factions + QuestEngine + PNJ) |
| `…/plan MMMORPG.txt` | Variante condensée |
| `…/20260527_rappel_objectif_mmo.txt` | Étoile MMO Pre-CU + PNJ IA |
| `…/Detail du projet_v3_20260409.txt` | Vision globale (Studio + MMO) |
| `…/mmmorpg_ambiance.txt` | Tone bio-mécanique / patchwork |
| `…/D1-10-A START.core3-selection.txt` | 10 races Core3→LBG |
| `…/20260429_mmmorpg_bestiaire..txt` | Bestiaire + JSON |
| `…/MMO_LBG_Guides_suite_3.txt` | Quêtes / éco / craft Core3 |
| `…/20260428_1220_on ce recentre.txt` | Priorité IA desktop puis MMO |
| `…/20260624.txt` | Client Godot / Prime |

### Gel explicite (ne pas propager)

Veridian / Nexus-Arbre comme lieux jouables · Terre1 · **Cercle des Arcanes** · Élémentaires / Homonculus / Elfe-Orc fantasy · OTServ · craft hors Pre-CU · inspirations multivers (Gunnm/DBZ/…) en `world_hint`.

---

## Historique

| Date | Changement |
|------|------------|
| 2026-08-04 | Premier extrait Boîte à idées → canon Studios |
| 2026-08-04 | Relecture complète `plan MMMORPG.md` — QuestEngine, MJ IA, archétypes, 75 % civils, params monde |
