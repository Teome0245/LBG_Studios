# Boîte à idées — Gameplay extrait (LBG Prime)

**Date** : 2026-08-04 · **MAJ** 2026-10-05 (§14 veille)  
**Statut** : extrait vivant — **n’écrit pas de Vérité** sans décision datée dans [`BIBLE_MMO.md`](BIBLE_MMO.md)  
**Source** : `LBG_IA_MMORPG/Boite à idées/` (lecture legacy) · veille [`CONCURRENTS_IA_MMO_2026-10.md`](CONCURRENTS_IA_MMO_2026-10.md)  
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
8. Tickets **§14 veille concurrents** (P3 / wahou / agent contract) — *ouvert 2026-10-05*

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
| [`CONCURRENTS_IA_MMO_2026-10.md`](CONCURRENTS_IA_MMO_2026-10.md) | Veille Everwhere / Jenova / Epitome / ClaudeCraft / SpaceMolt |

### Gel explicite (ne pas propager)

Veridian / Nexus-Arbre comme lieux jouables · Terre1 · **Cercle des Arcanes** · Élémentaires / Homonculus / Elfe-Orc fantasy · OTServ · craft hors Pre-CU · inspirations multivers (Gunnm/DBZ/…) en `world_hint`.

---

## 14. Veille concurrents IA/MMO (2026-10) — tickets

**Source** : [`CONCURRENTS_IA_MMO_2026-10.md`](CONCURRENTS_IA_MMO_2026-10.md) · ADR [`../adr/0002-veille-concurrents-ia-mmo.md`](../adr/0002-veille-concurrents-ia-mmo.md) · exécution Team [`../FOCUS_CONCURRENTS_TEAM.md`](../FOCUS_CONCURRENTS_TEAM.md)  
**Règle** : ticket ici = idée priorisée ; promotion Bible / catalogue = décision datée séparée.  
**Spawn** : `LBG_ORCHESTRATOR_URL=http://192.168.0.140:8010 python -m lbg_agents.spawn_team_concurrents_wave_job` (vague A|B|C via `LBG_TEAM_CONCURRENTS_WAVE`).

### P0 — wahou / P3 (prochains)

| ID | Ticket | Origine | Done quand | Owner cible |
|----|--------|---------|------------|-------------|
| **C1** | Dialogue hub : 2–3 **suggestions d’actions** + texte libre | Everwhere | PNJ hub (cantina / board / trainer) expose coups typés + free text ; smoke dialogue | Iris + Chœur · **live hub** 2026-10-08 : Jax trade UI + Guide wiki UI + Daan board · free text panel · smoke `tools/smoke_p3_hub_dialogue.sh` |
| **C2** | **Mémoire relations** (dette, PNJ croisé, objet offert) injectée `world_hint` | Everwhere / Jenova | 1 joueur + 1 PNJ : rappel concret après action (tip / quête / don) | Chœur + Dédale · schéma Vague A · stub Python ✅ · **live hub** 2026-10-08 : `players_state.relation_memory` + `GET /v1/relation-memory` + inject dialogue (`tip`/`accept`/`trade`/`met`) · smoke `tools/smoke_c2_relation_memory_hub.sh` |
| **C3** | **Compagnon IA visible** au spawn Lost Heaven (1 bot : Lia ou Nix) | Epitome + bots LBG | Nameplate + follow court / commentaire 30 s ; pas Pilot-only | Iris + Chœur · **live hub** 2026-10-07 : Nix greet+escort ~28 s + nameplate (`fleet_greet` mono-compagnon) |
| **C4** | **1 event dynamique** board (meute portes **ou** chute scrap **ou** panne starport) | Epitome | Template EventEngine persisté + entrée board Daan ; Chœur peut sonder | WD + Chœur · **live hub** 2026-10-07 : `hub_events` + quest `lh_scrap_fall_salvage` + `GET /v1/events/active` (chute scrap) · stub cortex ✅ Vague A |

### P1 — densité / data

| ID | Ticket | Origine | Done quand | Owner cible |
|----|--------|---------|------------|-------------|
| **C5** | **Chronique session** Scribe (5–10 lignes) + titre cosmétique optionnel | Everwhere journey book / ClaudeCraft deeds | Export après quête hub ou tip scène | Dédale + Chœur · **live hub** 2026-10-07 : `GET /v1/chronicle` + log quête/tip/salvage/craft · dialogue Scribe « chronique » · stub ✅ Vague C |
| **C6** | **Wiki / guide joueur** généré depuis inventaire PNJ + M10 + POI | ClaudeCraft wiki | Page ou panel lisible, drift = fail smoke data | Argus + Iris · **live hub** 2026-10-07 : `GET /v1/wiki` + panel Menu · MVP md [`wiki_hub_lost_heaven_mvp.md`](../../packages/cortex/docs/wiki_hub_lost_heaven_mvp.md) ✅ Vague C |
| **C7** | **Négociation marchand** bornée (delta prix + réputation) | Epitome | 1 vendor hub ; pas LLM libre sur prix | Iris · **live hub** 2026-10-07 : `POST /v1/trade/offer` Jax ±15 % · suggestions dialogue · stub cortex ✅ Vague C |
| **C8** | Boucle **salvage scrap** hors palissade → input craft M10 | SpaceMolt salvage / Scrapaltai | 1 wreck/pile scrap + loots → schematic existant | Dédale · **live hub** 2026-10-07 : `POST /v1/salvage` + hotbar `[1]` près `poi:lh_scrap_pile` → craft `kit_reparation` (T) · stub cortex ✅ Vague A |
| **C13** | **Anneau désert LH** — joueurs IA hors murs (~3 km), pas Scrapaltai entière | Studio (débride explore) | Data `explore_ring_lh.json` + autonomy + clamp `move_to` + skill | Chœur · **MVP** ✅ 2026-10-07 |

### P2 — contrat agents (SpaceMolt → Chœur / bots)

| ID | Ticket | Origine | Done quand | Owner cible |
|----|--------|---------|------------|-------------|
| **C9** | **`AGENT_SKILL_MMO.md`** (manuel unique bots joueurs IA) | SpaceMolt `skill.md` | 1 doc : actions autorisées, Bible, anti-dérive, playstyles hub | Chœur + Thémis · **brouillon** [`AGENT_SKILL_MMO.md`](../../packages/cortex/docs/AGENT_SKILL_MMO.md) ✅ Vague A |
| **C10** | **Catalog tools** read-only (`skills`, `recipes`, `npcs`, `poi`) | SpaceMolt `catalog` / `get_guide` | Endpoint ou MCP Studio ; guides playstyle = data M10 | Hermès · **stub** `GET /catalog` + `/guide` dialogue HTTP ✅ Vague C |
| **C11** | **Tick mutations** vs queries gratuites sur pont joueur IA | SpaceMolt tick model | Mutations craft/quête/tip filetées ; snapshots free | Hermès + WD · **stub** `/tick-matrix` + flag context ✅ Vague C |
| **C12** | Réponses **duales** texte joueur + `structuredContent` commit | SpaceMolt envelope API | Dialogue + commit flags/deltas sans double parse fragile | Iris · **MVP** dual envelope `/invoke` ✅ Vague C |

### Gel explicit (veille)

Text-only MMO · UE5 megaserver · freeform sans Bible · permadeath persona défaut · token Solana · ouverture publique serveur aux LLM internet · galaxy 500 systèmes v1.

---

## Historique

| Date | Changement |
|------|------------|
| 2026-08-04 | Premier extrait Boîte à idées → canon Studios |
| 2026-08-04 | Relecture complète `plan MMMORPG.md` — QuestEngine, MJ IA, archétypes, 75 % civils, params monde |
| 2026-10-05 | §14 tickets veille concurrents + SpaceMolt (ADR 0002, `CONCURRENTS_IA_MMO_2026-10.md`) |
| 2026-10-05 | Vague A docs/stubs : C1 design, C2 schéma, C4/C8 data, C9 `AGENT_SKILL_MMO.md` |
| 2026-10-06 | Vague B code+smoke C1/C2/C3 ; Vague C MVP C5–C7 + C10–C12 |
| 2026-10-07 | **C13** anneau désert LH — explore IA hors murs (`explore_ring_lh.json`) |
| 2026-10-07 | **C4/C5/C8 live** prime-hub `:8787` — event scrap board, chronique Scribe, salvage→craft ; docs [`RUNTIME_GODOT.md`](../RUNTIME_GODOT.md) |
| 2026-10-07 | **C6/C7 live** — wiki `/v1/wiki` + panel ; négo Jax `/v1/trade/offer` |
| 2026-10-08 | **C2 live** — relation_memory persistée hub + dialogue ; **P5a** hotbar chasse client OK |
