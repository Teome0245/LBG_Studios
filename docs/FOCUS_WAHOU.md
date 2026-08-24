# Focus — recentrage + effet wahou

**Date** : 2026-08-24  
**Règle** : un pari visible, Team L1, **pas** de Cloud Agent ni de 27b × N.

Pilot : `#/team/office` (mission) · Cour de chasse déjà là : `#/hunt`.

## Archivé (ne plus rouvir)

| Sujet | Pourquoi c’est clos |
|-------|---------------------|
| Client SWG / TRE joueur | Godot only |
| Serveur Godot dédié / rewrite Core3 | ADR 0017 — Core3 spatial + peel |
| Comparaison NeL vs Core3 | Cadré : CDB = contrat, pas XML |
| P0–P1, M9–M12 login/WS/move | Fait |
| P5a cour de chasse sandbox | Fait (code `main`, Pilot `#/hunt`) |
| P2 overlay inventaire Core3 | Fait (dump Lua si online) — **deploy 246 OK 2026-08-24** (`core3_live: true`) |
| Face rig Lyra, TRELLIS, méta-Team L3 | Livré O1 |
| Bac Python `/mmo/` | Gelé |

Legacy `new_mmo` / `LBG_IA_MMORPG` / stash : **lecture**, pas de feature.

## Ce qui manque (le wahou)

**Pari** : les **30 premières secondes** à Lost Heaven.

Le joueur (ou toi en Pilot) doit sentir *un monde vivant*, pas un hub technique.

| Couche | Wahou | Pas wahou |
|--------|--------|-----------|
| **Studio** | `#/hunt` + bureau Team qui **conduit** | Encore un audit LLM |
| **Entités IA** | Lia / Nix / Mira **jouables** (chasse ou hub) | Stats `inventory_count` |
| **Lore** | Un battement (chasse, Palissade, Perle) | Bible relue |
| **Gameplay** | Board chasse / forage dans Godot | Encore un stub HTTP |
| **UI** | Sac **Core3 live** + nameplates | Points gris Tatooine |

## Team — économie de tokens

- Mission **@mentions** (plan heuristique, **0** appel plan LLM).
- `max_tasks=4` · L1 only · **pas** Cursor Cloud · **pas** `player_ia` think.
- Coffee-fill existant (scores playbooks) ; pas de spawn parallèle.
- 27b réservé au dialogue PNJ / 1 brief PM, pas à 4 agents.

### Mission en cours (2026-08-24)

id `7164b000-138c-4127-acd5-e8a8a611f1be` — Pilot `#/team/office`.

Objectif unique : **rendre le wahou visible**, pas élargir le scope.

1. **Thémis** — 5 lignes : next 72 h (deploy inventaire 246 ✅, chasse dans Godot, 1 battement Chœur).
2. **Iris** — scène hub → palissade / board chasse (`godot_dev_track: hunt_hub`, **pas** M9).
3. **Dédale** — 1 POI lore « hors palissade » (`poi:lh_hunt_chacal`) branché board.
4. **Argus** — smoke `#/hunt` ✅ + `GET :8791/v1/inventory` (`source=core3_lua_inventory`, `core3_live=true`).

Hors mission : P4 `soe_handshake`, DSH `.10`, LoRA portraits (Pygmalion **après** le battement joueur).
