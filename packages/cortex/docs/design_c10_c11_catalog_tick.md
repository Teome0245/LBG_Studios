# Design C10 + C11 — Catalog read-only & tick mutations

**Tickets** : Boîte §14 **C10** / **C11** · veille **SpaceMolt** ([`CONCURRENTS_IA_MMO_2026-10.md`](../../../docs/world/CONCURRENTS_IA_MMO_2026-10.md) §6)  
**Date** : 2026-10-06 · **Owner** : Hermès (+ WD pour middleware tick live)  
**Manuel** : [`AGENT_SKILL_MMO.md`](AGENT_SKILL_MMO.md) §3 / §7  
**Statut** : design + stub dialogue `:8020` + **wire sidecar `:8791`** (GET catalog/guide/tick-matrix)

---

## Objectif

Exposer un **catalogue unique** machine-readable (`skills` \| `recipes` \| `npcs` \| `poi`) et un **contrat tick** : lectures gratuites vs mutations filetées — pattern SpaceMolt, sans ouvrir Core3 ni inventer du lore.

---

## C10 — Catalog read-only

### Contrat

| Param | Valeurs | Source data |
|-------|---------|-------------|
| `type=skills` | professions + boxes M10 | `content/m10/m10_skills_catalog.json` → `professions` / `skills` |
| `type=recipes` | schematics craft | même fichier → `schematics` |
| `type=npcs` | résumé registry (id, name, role, zone) | `agents/.../npc_registry.json` |
| `type=poi` | POI hub LH + stubs content | `prime-client/.../scrapaltai_pois.json` + `content/world/poi_*.json` |
| `get_guide(playstyle)` | guides hub | playstyles §6 AGENT_SKILL + id profession M10 |

Réponse type :

```json
{
  "ok": true,
  "type": "skills",
  "count": 4,
  "items": [],
  "tick_cost": "free",
  "requires_tick": false,
  "context": {
    "tick_cost": "free",
    "requires_tick": false,
    "kind": "query",
    "action": "catalog"
  }
}
```

### Surfaces (ordre Vague C)

| Surface | Statut Vague C | Notes |
|---------|----------------|-------|
| Module Python `lbg_agents.agent_catalog` | **stub livré** | source de vérité locale |
| `GET` dialogue HTTP `:8020` | **stub livré** | `/catalog?type=…`, `/guide?playstyle=…`, `/tick-matrix` |
| Sidecar Prime `:8791` | **wire live** 2026-10-06 | `GET /catalog` `/guide` `/tick-matrix` (+ `/v1/*`) via `agent_catalog.http_get_dispatch` |
| MCP Studio | futur | mêmes `type` + schémas |

Pas de mutation via ces endpoints — HTTP **GET** uniquement.

---

## C11 — Queries gratuites vs mutations tickées

**Principe** : toute lecture catalogue / snapshot / board = `tick_cost=free` ; tout effet persistant monde ou enqueue bot = `tick_cost=mutation` (`requires_tick=true`).

### Flag context (wire)

À propager dans `context` (dialogue, sidecar, futur MCP) :

| Champ | Type | Sens |
|-------|------|------|
| `tick_cost` | `"free"` \| `"mutation"` | Coût côté contrat agents |
| `requires_tick` | `bool` | Alias booléen (`true` ⇔ mutation) |
| `kind` | `"query"` \| `"mutation"` | Classification |
| `action` | `string` | Nom d’action catalogue (`catalog`, `move_to`, …) |

Erreurs mutation (cible middleware) : `429` / `tick_busy` si file pleine ; `400` si query déguisée en POST monde.

### Table actions (hub Lost Heaven)

| Action | kind | tick_cost | requires_tick | Notes |
|--------|------|-----------|---------------|-------|
| `catalog` | query | free | false | C10 |
| `get_guide` | query | free | false | playstyle hub |
| `snapshot` / `self/status` | query | free | false | position, quêtes actives |
| `quests/board` | query | free | false | lecture board |
| `quests/status` | query | free | false | |
| `inventory/list` | query | free | false | |
| `skills/list` | query | free | false | joueur courant |
| `relation_memory/list` | query | free | false | C2 lecture |
| `npc/registry` | query | free | false | summary/goals |
| `move_to` | mutation | mutation | true | marche hub visible |
| `quests/accept` | mutation | mutation | true | |
| `quests/progress` | mutation | mutation | true | |
| `quests/complete` | mutation | mutation | true | |
| `craft/start` | mutation | mutation | true | station + schematic |
| `craft/complete` | mutation | mutation | true | |
| `survey/execute` | mutation | mutation | true | |
| `hunt/engage` | mutation | mutation | true | |
| `tip_stage` | mutation | mutation | true | Perle |
| `talk_npc` | mutation | mutation | true | commit C12 |
| `trade/offer` | mutation | mutation | true | C7 |
| `salvage/loot` | mutation | mutation | true | C8 |
| `relation_memory/append` | mutation | mutation | true | C2 écriture |

Implémentation machine : `lbg_agents.agent_catalog.classify_action` + `TICK_MATRIX`.

---

## Fichiers

| Fichier | Rôle |
|---------|------|
| `packages/cortex/docs/design_c10_c11_catalog_tick.md` | ce design |
| `packages/cortex/agents/src/lbg_agents/agent_catalog.py` | catalog + tick matrix |
| `packages/cortex/agents/src/lbg_agents/dialogue_http_app.py` | GET mock |
| `packages/cortex/agents/tests/test_agent_catalog.py` | unitaires |

---

## Hors scope Vague C

- Middleware tick live / cooldown partagé bots (mutations)
- Ouverture MCP Studio publique
- Mutations craft/hunt via ce stub
- Changer le manuel C9 hors pointeur done

---

## Done quand

- [x] Design court + table tick + flag context
- [x] Stub catalog read-only (4 types) + `get_guide`
- [x] Tests unitaires verts
- [x] Mirror `:8791` — `GET /catalog|/guide|/tick-matrix` (+ alias `/v1/…`) via `lbg_agents.agent_catalog.http_get_dispatch` (2026-10-06)
