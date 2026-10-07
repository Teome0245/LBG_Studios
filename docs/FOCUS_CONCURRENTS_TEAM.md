# Focus — Veille concurrents → exécution Team (C1–C12)

**Date** : 2026-10-05 · **MAJ** 2026-10-06 (Vague A ✅ → Vague B lancée)  
**Canon** : [`world/BOITE_IDEES_GAMEPLAY.md`](world/BOITE_IDEES_GAMEPLAY.md) §14 · [`world/CONCURRENTS_IA_MMO_2026-10.md`](world/CONCURRENTS_IA_MMO_2026-10.md) · ADR [`adr/0002-veille-concurrents-ia-mmo.md`](adr/0002-veille-concurrents-ia-mmo.md)  
**Pilot** : `#/team/office` · spawn : `python -m lbg_agents.spawn_team_concurrents_wave_job`  
*(tâches L1 explicites par vague — plus fiable que le plan NL coffee-fill seul)*  
**Édition code** : Cline Plan→Act sur `.143` (ADR 0023) — pas Cursor Cloud sauf L2 explicite.

**Mission Vague B** : `concurrents_wave_B_1791268990` ✅ close  
**Mission Vague C** : `concurrents_wave_C_1791269685` (queued)

| Vague C | task_id | Ticket |
|---------|---------|--------|
| Hermès | `556d342c…` | C10_C11 |
| Iris | `6755f873…` | C12 |
| Dédale | `b0df2cca…` | C5_C7 |
| Argus | `b78a1150…` | smoke_C |

## Contraintes

- **O1 D6** (Compagnon) reste gate stratégique ; ces tickets = **préparation O2 / P3** en parallèle doc+data, code jeu borné.
- `max_tasks≤4` par vague · L1 only · **pas** de Cloud Agent · Bible = anti-dérive.
- Une vague = une mission Lyra ; clôturer avant la suivante (smoke Argus si code Godot).

## Parallelisme (3 vagues)

```text
Vague A (docs / design) ──┬── Thémis plan 72h
                          ├── Chœur C9 outline + C2 schéma mémoire
                          ├── Iris C1 design suggestions dialogue
                          └── Dédale C4 event + C8 salvage data stub
                                    │
Vague B (code .143) ──────┬── Iris C1+C2 (dialogue + world_hint)
                          ├── Iris/Chœur C3 compagnon spawn visible
                          ├── Chœur C9 AGENT_SKILL_MMO.md final
                          └── Argus smoke dialogue / hunt
                                    │
Vague C (contrat + densité) ┬── Hermès C10 catalog + C11 tick
                            ├── Iris C12 dual response
                            ├── Dédale C5 chronique + C7 marchand
                            └── Argus/Iris C6 wiki data
```

**Séquentiel forcé** : C2 avant C1 live (mémoire alimente suggestions) · C9 avant C10/C11 · C3 après smoke hunt existant.

---

## Vague A — Mission NL (à coller / spawn)

```
Mission veille concurrents Vague A — docs only, max 4 tâches L1.
@Thémis : 5 lignes next 72h — ordre C1–C12 + owners + ce qui bloque O1 D6.
@Chœur : brouillon AGENT_SKILL_MMO.md (C9) + schéma mémoire relations C2 (JSON) — lire CONCURRENTS_IA_MMO_2026-10 + Bible V40–V54 — pas de code Core3.
@Iris : design C1 suggestions dialogue hub (coups typés + free text) — endpoints/UI Godot listés, pas d’implémentation.
@Dédale : stub data C4 (1 event Scrapaltai) + C8 (1 pile scrap POI) sous content/ — schema JSON, pas spawn live 246.
Argus : smoke doc-only = fichiers présents + JSON valid — pas godot_login.
Réfs : docs/world/BOITE_IDEES_GAMEPLAY.md §14 · docs/world/CONCURRENTS_IA_MMO_2026-10.md
```

## Vague B — Mission NL (après A closed)

```
Mission veille concurrents Vague B — code L1 + Cline .143 si write hors allowlist.
@Iris : implémenter C1 suggestions + C2 world_hint mémoire (1 PNJ hub).
@Chœur : C3 compagnon visible spawn LH (Lia ou Nix) + finaliser C9 AGENT_SKILL_MMO.md.
@Argus : smoke dialogue + #/hunt / inventory si touché — block close si rouge.
Hors scope : P4 SOE, UE5, freeform sans Bible.
```

## Vague C — Mission NL (après B)

```
Mission veille concurrents Vague C — contrat agents SpaceMolt-style.
@Hermès : C10 catalog read-only + C11 tick mutations vs queries (design+stub :8791).
@Iris : C12 dual result/structuredContent sur 1 endpoint dialogue.
@Dédale : C5 chronique Scribe + C7 négociation marchand bornée (1 vendor).
@Argus+Iris : C6 wiki généré inventaire+M10 (MVP markdown ou panel).
```

## Done Vague A

| Ticket | Livrable |
|--------|----------|
| **C9** | [`packages/cortex/docs/AGENT_SKILL_MMO.md`](../packages/cortex/docs/AGENT_SKILL_MMO.md) |
| **C2** schéma | [`packages/cortex/content/world/relation_memory_schema.json`](../packages/cortex/content/world/relation_memory_schema.json) |
| **C1** design | [`packages/cortex/docs/design_c1_dialogue_suggestions.md`](../packages/cortex/docs/design_c1_dialogue_suggestions.md) |
| **C4** event stub | [`packages/cortex/content/world/events/event_lh_scrap_fall_or_meute.json`](../packages/cortex/content/world/events/event_lh_scrap_fall_or_meute.json) |
| **C8** salvage POI | [`packages/cortex/content/world/poi_lh_scrap_pile.json`](../packages/cortex/content/world/poi_lh_scrap_pile.json) |
| Plan 72 h | [`PLAN_72H_CONCURRENTS.md`](PLAN_72H_CONCURRENTS.md) |

**Next** : Vague B en cours — C3/C9 stub ✅ · C1+C2 code en cours · Argus smoke après.

### Done Vague B (partiel)

| Ticket | Livrable |
|--------|----------|
| **C9** final | section Vague B dans [`AGENT_SKILL_MMO.md`](../packages/cortex/docs/AGENT_SKILL_MMO.md) |
| **C3** stub | [`design_c3_companion_spawn.md`](../packages/cortex/docs/design_c3_companion_spawn.md) · [`companion_spawn_lh.json`](../packages/cortex/content/world/companion_spawn_lh.json) |
| **C1** MVP | templates registry + `suggested_moves` invoke + boutons Godot (tests unitaires C1 verts) |
| **C2** MVP | [`relation_memory.py`](../packages/cortex/agents/src/lbg_agents/relation_memory.py) + stub example → `memory_hint` |

**Reste Vague B** : ~~deploy 140 · smoke dialogue live · wire C3 Godot · open_mission_board~~ ✅ 2026-10-06 (`SMOKE_C1_OK`). LLM model Pilot 404 = hors scope (infra).

### Done Vague C

| Ticket | Livrable |
|--------|----------|
| **C12** | dual `result` / `structuredContent` sur `/invoke` (tests verts) |
| **C5** | [`scribe_chronicle_session_stub.json`](../packages/cortex/content/world/scribe_chronicle_session_stub.json) |
| **C6** | [`wiki_hub_lost_heaven_mvp.md`](../packages/cortex/docs/wiki_hub_lost_heaven_mvp.md) + générateur |
| **C7** | [`design_c7_vendor_negotiation.md`](../packages/cortex/docs/design_c7_vendor_negotiation.md) · [`vendor_negotiation_jax.json`](../packages/cortex/content/world/vendor_negotiation_jax.json) |
| **C10** | [`design_c10_c11_catalog_tick.md`](../packages/cortex/docs/design_c10_c11_catalog_tick.md) · `GET /catalog` `/guide` live `.140:8020` |
| **C11** | `/tick-matrix` + flag context · [`agent_catalog.py`](../packages/cortex/agents/src/lbg_agents/agent_catalog.py) |

**Vague C** : livrables MVP ✅ 2026-10-06 (11 tests catalog verts · catalog live 140).  
**Suite G5+** : catalog/tick/dialogue sur **`prime-hub` `:8787`** (TickGate C11 Godot + smoke `tools/smoke_p3_hub_dialogue.sh`) · MCP Studio stdio OK · sidecar `:8791` = legacy.

## Surfaces humaines

| Action | Où |
|--------|-----|
| Suivre / clôturer | Pilot `http://192.168.0.140:8080/pilot/#/team/office` |
| Compagnon toast Team | `http://192.168.0.100:5174/` — « Mission … » |
| Édition | `ouvre code sur omarchy` → VS Code + workspace + Cline Plan→Act |
| Deploy après merge | `tools/deploy_cortex_140.sh` + smokes owner |

## Done global

Tickets C1–C12 cochés dans Boîte §14 **ou** reportés avec raison datée.  
Aucune Vérité Bible inventée sans décision séparée.
