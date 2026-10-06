# AGENT_SKILL_MMO — manuel joueurs IA (C9)

**Date** : 2026-10-06 · **Statut** : Vague B (manuel + pointeurs C1–C3)  
**Ticket** : [`BOITE_IDEES_GAMEPLAY.md`](../../../docs/world/BOITE_IDEES_GAMEPLAY.md) §14 **C9**  
**Inspiré** : SpaceMolt [`skill.md`](https://spacemolt.com/skill.md) — mapping [`CONCURRENTS_IA_MMO_2026-10.md`](../../../docs/world/CONCURRENTS_IA_MMO_2026-10.md) §6  
**Canon** : [`BIBLE_MMO.md`](../../../docs/world/BIBLE_MMO.md) (V20–V24, V30–V35, V40–V42, V50–V54)

Ce document est le **manuel unique** pour les agents qui **jouent** le MMO (bots sidecar + Chœur). Ce n’est **pas** un prompt MJ freeform : seules les actions du catalogue et les Vérités Bible s’appliquent.

---

## 1. Rôle et personas

| Acteur | Rôle | Ce qu’il ne fait pas |
|--------|------|---------------------|
| **Lia / Nix / Mira** | Joueurs IA Core3 sur **246** — boucles hub (quêtes, craft, chasse, scène) via sidecar `:8791` | Narrateur omniscient, inventaire de lieux, attribution de métiers hors registry |
| **Chœur du monde** (`studio_player_ia_choeur`, V50) | Garant **runtime** : probe, smoke écarts Bible / M10 / inventaire PNJ ; ticks autonomie **L2** avec approbation | MJ improvisé ; contredire V40–V42 ; progression bots hors catalogue M10 (V52) |

**Onboarding cible** (SpaceMolt → LBG) : humain Godot → **1 compagnon visible** (C3) → flotte Chœur / bots.

Réfs : [`studio_player_ia_choeur.json`](../agents/declarations/studio_player_ia_choeur.json) · [`quest_hub_bot_autonomy.py`](../agents/src/lbg_agents/quest_hub_bot_autonomy.py)

---

## 2. Transports — un catalogue, trois surfaces

Même **contrat d’actions** (noms + schémas JSON) sur :

| Transport | Usage | Notes |
|-----------|--------|--------|
| **HTTP Pilot / sidecar** | `:8791` — quêtes, enqueue bot, snapshots | Chemin actuel des bots Lia/Nix |
| **WebSocket Godot** | `prime-client` — `move`, `say`, `interact` (`lbg-ws/2`) | Joueur humain + miroir futur bot |
| **MCP Studio** (futur) | Tools découverts pour Team / agents externes | Aligner sur C10 |

Les implémentations diffèrent ; **les noms d’action et les champs obligatoires ne divergent pas** sans ADR.

---

## 3. Queries gratuites vs mutations tickées

**Principe** (SpaceMolt → LBG, C11) : lectures = sans coût tick ; changements monde = **mutation** (file, cooldown, ou tick Chœur).

### Queries (read-only, pas de commit monde)

- `catalog` — `skills` \| `recipes` \| `npcs` \| `poi` (C10)
- `get_guide` — playstyle hub (`prospecteur` \| `artisan` \| `scene` \| `medecin` \| `scout`)
- `snapshot` / `self/status` — position, intérieur, quêtes actives
- `quests/board`, `quests/status`
- `inventory/list`, `skills/list` (joueur courant)
- `relation_memory/list` — entrées C2 pour injection `world_hint`
- `npc/registry` — `summary`, `goals`, `constraints` (V40)

### Mutations (tick / POST, effet persistant ou sidecar)

- `move_to` — déplacement bot (marche visible hub, pas teleport mission)
- `quests/accept`, `quests/progress`, `quests/complete`
- `craft/start`, `craft/complete` — station + schematic M10 (V31)
- `survey/execute` — prospection / gisement validé
- `hunt/engage` — chasse hors palissade (ex. chacals)
- `tip_stage` — pourboire scène cantina
- `talk_npc` — dialogue **borné** (suggestions C1 + texte ; commit via C12)
- `trade/offer` — négociation marchand bornée (C7, futur)
- `salvage/loot` — pile scrap → inventaire (C8)
- `relation_memory/append` — dette, rencontre, don, lien quête (C2)

---

## 4. Actions autorisées — hub Lost Heaven

Périmètre **couche A** : Scrapaltai / **Lost Heaven** uniquement (V10–V13). POI figés V12 ; cantina = **La Perle de Scrapaltai** (V13).

| Action | But hub | Ancrage data |
|--------|---------|--------------|
| `survey` | Prospection dunes / gisement | `lh_survey_dunes`, boxes prospecteur M10 |
| `talk_npc` | Dialogue registry + suggestions | `npc_registry.json`, V20–V22 |
| `craft` | Kit, pièce, conso au banc / atelier | `m10_skills_catalog.json`, V30–V31 |
| `tip_stage` | Spectacle cantina, XP scène stub | `lh_show_perle` |
| `hunt` | Meute chacals hors porte | `poi:lh_hunt_chacal`, bestiaire Scrapaltai |
| `accept_quest` / `progress_quest` | Board Daan Oth | `quests_lbg_templates.json` |
| `escort` / `deliver` / `enquete` | Templates hub existants | idem board |
| `move_to` | Trajet POI visible | `lost_heaven_buildings.json` / POI V12 |

Interdit en action agent : ouvrir Zalem jouable, factions « Mondes Brisés », magie surface, combat Poing/Visée comme boucle centrale (V34).

---

## 5. Anti-dérive Bible (obligatoire)

Avant toute réponse ou mutation, respecter :

- **V40** — `world_hint` + registry = seule source de faits ; pas de villes / planètes inventées.
- **V41** — Interdits nommés (Willowdale, Mos Eisley, Tatooine, …).
- **V42** — Registre muet → « je ne sais pas » / renvoi guide, scribe, rumeur — **pas d’invention**.
- **V20–V24** — Rôle PNJ fixe (ex. Kisreudi ≠ danse ; trainers scène = triplon / Talen Ress, V21–V22).
- **V50–V54** — Chœur vérifie ; Scribe = chronique in-world (C5), pas doublon ops.

En cas d’écart détecté : rapporter `world_truth_guard` (statut cible Chœur), ne pas « corriger » le lore en prose.

---

## 6. Playstyles hub (guides M10)

Guides **`get_guide(playstyle)`** = data réelle, pas hallucination (SpaceMolt → C10).

| Playstyle | Profession M10 | Boucle hub typique |
|-----------|------------------|-------------------|
| **Prospecteur** | `prospecteur` | survey dunes → ressources → vendeur / craft |
| **Artisan** | `artisan` | atelier → schematic novices → kit / pièce |
| **Scène** | `scene` | Talen / Perle → danse ou tip → réconfort moral |
| **Médecine** | `medecin` | clinique → kits terrain → escort blessé (backlog) |
| **Scout** | alias prospecteur / piste | chasse légère, camp, faune portes |

Catalogue canon : [`content/m10/m10_skills_catalog.json`](../content/m10/m10_skills_catalog.json) · arbres : [`ARBRES_TALENTS_PRECU.md`](../../../docs/world/ARBRES_TALENTS_PRECU.md)

Mémoire relationnelle (C2) : schéma [`relation_memory_schema.json`](../content/world/relation_memory_schema.json) → injecter dans `world_hint` dialogue.

---

## 7. Livrables C10–C12 (stubs)

| ID | Owner | Done quand | TODO |
|----|-------|------------|------|
| **C10** | Hermès | `catalog(type=…)` read-only sur sidecar ou MCP Studio | Stub ✅ [`design_c10_c11_catalog_tick.md`](design_c10_c11_catalog_tick.md) · `GET /catalog` dialogue HTTP · mirror `:8791` next |
| **C11** | Hermès + WD | Mutations filetées vs queries | Stub ✅ table + flag `tick_cost` / `requires_tick` · middleware tick live next |
| **C12** | Iris | Dual `result` + `structuredContent` | Endpoint dialogue : texte joueur + flags/deltas commit |

**Séquence** : C9 (ce doc) → C10/C11 contrat → C12 dialogue · C2 mémoire avant C1 live suggestions.

Exécution Team : [`FOCUS_CONCURRENTS_TEAM.md`](../../../docs/FOCUS_CONCURRENTS_TEAM.md)

---

## Vague B — statut C1 / C2 / C3

| Ticket | Statut | Pointeur |
|--------|--------|----------|
| **C1** | Design ✅ · impl live **en cours** (Iris + Cline `.143`) | [`design_c1_dialogue_suggestions.md`](design_c1_dialogue_suggestions.md) |
| **C2** | Schéma ✅ · injection `world_hint` **en cours** | [`relation_memory_schema.json`](../content/world/relation_memory_schema.json) |
| **C3** | Stub + design ✅ · wire Godot / sidecar **next Cline** | [`design_c3_companion_spawn.md`](design_c3_companion_spawn.md) · [`companion_spawn_lh.json`](../content/world/companion_spawn_lh.json) |

### Checklist C3 (compagnon joueur-facing)

- [ ] 1 bot (**Nix** défaut) ancré près `poi:player_spawn` (pas hunt yard / Pilot `#/hunt` seul)
- [ ] Nameplate visible pour ce bot même si `hide_npc_nameplates_on_play`
- [ ] Flag `spawn_companion` lu côté Godot ou feed snapshot (stub `companion_spawn_lh.json`)
- [ ] Présence hub : pas de teleport Core3 246 sans doc ; pas toucher PreCU 245
- [ ] Smoke joueur : login → voir nameplate compagnon au shuttleport LH

---

## Historique

| Date | Changement |
|------|------------|
| 2026-10-06 | Vague B — section C1/C2/C3 + checklist C3 |
| 2026-10-05 | Brouillon C9 Vague A — Chœur |
