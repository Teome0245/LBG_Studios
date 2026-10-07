# Spike 48 h — runtime Godot-first (hors Core3)

**Date** : 2026-10-06 · **ADR** : [`0026-runtime-hors-core3.md`](../packages/cortex/docs/adr/0026-runtime-hors-core3.md)  
**Objectif** : prouver qu’un humain + un bot IA marchent dans Lost Heaven **sans** Core3 246.  
**Owners** : Iris (Godot) · Hermès (serveur mince / WS) · Chœur (contrat C10/C11)

---

## Done quand (go)

- [x] Godot `prime-client` se connecte à un serveur **non-Core3** (WS ou local).
- [x] Entité joueur humain se déplace (ZQSD) ; position répliquée.
- [x] ≥1 bot (`Nix` ou stub) marche vers un POI hub (plaza / marché) de façon **visible**.
- [x] `GET`-équivalent catalog / tick-matrix (réutilise `lbg_agents.agent_catalog`) répond free vs mutation.
- [x] Core3 **éteint** ou ignoré pendant la démo (pas de SOE, pas de `pending.jsonl`).

---

## Hors scope (48 h)

- Craft / quêtes Core3 live, inventaire transactionnel complet  
- Multi-zones, scale, Agones  
- Lore / assets SWG  
- Remplacer tout O2 d’un coup  

---

## Architecture spike

```
┌──────────────────┐     lbg-ws/2 (ou stub)     ┌─────────────────────────┐
│  prime-client    │ ◄────────────────────────► │  lbg-hub-runtime (mince)│
│  Godot 4.x      │   zone_state + move_to     │  Python FastAPI ou      │
│  SnapshotBridge  │   entities[]               │  Godot headless        │
│  (déjà patch IA) │                            │  + TickGate C11         │
└──────────────────┘                            └───────────┬─────────────┘
                                                            │
                                                            ▼
                                                   agent_catalog (C10/C11)
                                                   POI Lost Heaven JSON
```

**Réutiliser** : `packages/prime-client` · `lbg_agents.agent_catalog` · `scrapaltai_pois` / buildings · contrat SpaceMolt.  
**Ne pas réutiliser** : `ia_bridge_screenplay.lua`, SOE handshake, Core3 enqueue.

---

## Découpage temps

### J0 — Socle (≈ 8–12 h)

| # | Tâche | Owner |
|---|--------|--------|
| S1 | Skeleton `packages/cortex/tools/hub_runtime/` (ou `packages/prime-hub/`) — HTTP health + WS zone_state | Hermès |
| S2 | Boucle tick 100–200 ms : positions dict player_id → x,z | Hermès |
| S3 | Godot : flag `use_hub_runtime=1` → NetworkBridge/WS pointe vers hub_runtime (localhost) | Iris |
| S4 | Spawn local human + bot stub si pas d’entité | Iris |

### J1 — Mouvement visible + contrat (≈ 8–12 h)

| # | Tâche | Owner |
|---|--------|--------|
| S5 | Humain : input → `move` / velocity sur serveur mince | Iris + Hermès |
| S6 | Bot : AI triviale `move_to` POI plaza (lerp ou pas fixes) | Hermès |
| S7 | Brancher `GET /catalog` `/guide` `/tick-matrix` (dispatch existant) | Hermès |
| S8 | Mutations bot = TickGate (`http_post_tick_guard` ou équivalent in-proc) | Hermès |
| S9 | Smoke script + capture : 2 sprites bougent 30 s | Argus / Chœur |

### Buffer

- Lerp client (`Entity.move`) si updates trop saccadés  
- Désactiver inject gateway Teome si encore branché par erreur  

---

## Emplacement code suggéré

```
packages/cortex/tools/hub_runtime/
  README.md
  server.py          # FastAPI + WS
  sim.py             # positions + bot walk
  smoke_hub_runtime.sh
packages/prime-client/
  config/hub_runtime.json   # url ws, flag
  scripts/…                 # branchement minimal
```

---

## Critères no-go

- Impossible de faire bouger 2 entités sans retomber sur Core3 en &lt; 48 h efficaces.  
- WS Godot trop cassé pour un stub (alors documenter blocage M12, pas « Core3 obligatoire »).

---

## Après go

1. ADR 0026 → statut **go spike** + collision hub AABB (`hub_collision.py`).  
2. Peel inventaire/quêtes → **fait** sur hub_runtime `:8787` (Godot `HubRuntimeCfg`).  
3. Core3 246 = lab data only (comme PreCU 245) — ops maintenance, pas nouvelle feature tick Lua.  
4. Nav / clamp plus fin (porteaux, props) si AABB insuffisant · persist inventaire disque.

---

## Réfs

- ADR 0026 · ADR 0017 · `AGENT_SKILL_MMO.md` §2–3 · `design_c10_c11_catalog_tick.md`  
- Incident ops 2026-10-06 : pending flood + tick Lua mort + bots figés  
