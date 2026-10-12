# Design C3 — Compagnon IA visible au spawn Lost Heaven

**Ticket** : Boîte §14 **C3** · Epitome + bots LBG  
**Date** : 2026-10-06 · **Owner** : Chœur (+ Iris Godot / Cline `.143`)  
**Statut** : stub data + design — **pas** de spawn live Core3 **246** / PreCU **245**  
**Canon** : Bible V40–V54 · manuel [`AGENT_SKILL_MMO.md`](AGENT_SKILL_MMO.md)

---

## Objectif

Au premier contact hub : **1 bot joueur-facing** (Nix ou Lia) visible près du spawn shuttleport — **nameplate + présence**, pas seulement Pilot `#/hunt` / F1–F3 caméra.

Done : login humain → compagnon à portée visuelle de `poi:player_spawn` avec nameplate forcé.

---

## État actuel (repère)

| Couche | Constat |
|--------|---------|
| **POI spawn** | `poi:player_spawn` = (4749, −537) — [`scrapaltai_pois.json`](../../prime-client/assets/maps/scrapaltai_pois.json) |
| **Hub caméra** | `LOST_HEAVEN_HUB` = (4749, 0, −737) — `main.gd` |
| **Bots feed** | `zone_feed` / snapshots : `player:Nix` souvent ~ (4755, −532) = **déjà près spawn** ; Lia souvent intérieur ailleurs |
| **Nameplates** | `entity.gd` `show_nameplates` ; play mode force off via `human_player.json` → `hide_npc_nameplates_on_play` |
| **Focus bots** | F1/F2/F3 = caméra debug (`FOCUS_BOTS`) — **pas** présence onboarding |
| **Hunt** | `poi:lh_hunt_chacal` hors palissade — hors scope C3 |

**Choix MVP** : **Nix** (position naturelle spawn). Lia = fallback si flag `bot_id`.

---

## 1. Data stub (livré)

[`companion_spawn_lh.json`](../content/world/companion_spawn_lh.json) — flag + ancre + labels.  
`active: false` jusqu’à wire Godot / feed ; **aucune** mutation Core3 depuis ce fichier.

---

## 2. Fichiers à toucher (Cline `.143`)

### Prime Client (Godot) — chemin sûr offline

| Fichier | Rôle |
|---------|------|
| `packages/prime-client/config/human_player.json` | Ajouter `spawn_companion: true`, `companion_bot_id: "Nix"`, `companion_force_nameplate: true` |
| `packages/prime-client/scripts/main.gd` | Après possess / world entry : si flag, assurer entité compagnon (feed live **ou** stub local) + nameplate |
| `packages/prime-client/scripts/entity.gd` | Option : `force_nameplate` par entité (bypass `show_nameplates` global) |
| `packages/prime-client/scripts/snapshot_bridge.gd` | Si bot absent du feed : spawn local depuis stub coords (kind `player`, label Nix) |
| `packages/prime-client/assets/sprites/` | Déjà `player_bot.png` pour Nix/Lia |

### Cortex — optionnel Vague B

| Fichier | Rôle |
|---------|------|
| Sidecar `:8791` enqueue `move_to` vers ancre stub | **Uniquement** si LAN 246 documenté ; sinon skip |
| Commentaire 30 s (toast / say) | Backlog soft — pas bloquant nameplate |

### Hors scope

- PreCU **245** — ne pas modifier
- Teleport / respawn destructeur bots sur **246** sans doc ops
- Follow pathfinding long / combat compagnon
- Flotte Mira+Lia+Nix (reste Chœur Pilot)

---

## 3. Contrat stub → client

```json
{
  "spawn_companion": true,
  "bot_id": "Nix",
  "entity_id": "player:Nix",
  "anchor_poi": "poi:player_spawn",
  "x": 4758.0,
  "z": -545.0,
  "nameplate": "Nix",
  "force_nameplate": true
}
```

Client lit stub (copie sous `prime-client/config/` ou chemin Cortex monté) **ou** miroir dans `human_player.json`.

---

## 4. Séquence implémentation recommandée

1. Flag config + lecture `main.gd` / `_on_world_entered`
2. Si `player:Nix` déjà dans EntityManager (snapshot) → `force_nameplate` + léger offset caméra optionnel
3. Sinon → spawn local stub aux coords (pas Core3)
4. Smoke : Godot play → L optionnel ; nameplate Nix visible sans Pilot
5. (LAN) enqueue `move_to` ancre — doc dans ticket ops, pas silent

---

## 5. Anti-dérive Bible

- Pas de lore inventé sur le compagnon (V40–V42)
- Pas d’attribution métier hors M10 / registry (V52)
- Commentaire 30 s = tip hub borné ou silence — pas MJ freeform

---

## Next step Cline `.143`

Wire `human_player.json` + `force_nameplate` sur entité `player:Nix` au world entry ; fallback spawn local depuis `companion_spawn_lh.json` si feed absent. Smoke login hub — **pas** de script spawn 246.
