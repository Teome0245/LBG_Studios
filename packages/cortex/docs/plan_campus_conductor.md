# Plan — Campus Conductor (Lyra)

**Date** : 2026-08-03  
**Statut** : V2 + Vague 4 clôture mission  
**Voir aussi** : `docs/lbg_agentic_os.md`, `docs/adr/0019-team-plan-llm-bus.md`

## Problème

Le bureau Team montre ~10 personas ; souvent peu de `busy` et beaucoup `idle` / café.  
C’est **normal** (miroir), mais la file et le café méritent un conducteur qui **décide**.

## Livré

| Version | Contenu |
|---------|---------|
| V0 | Drain `queued` L1 + rapport idle |
| V1 | Coffee fill (spawn utiles si café plein) |
| V2 | `act` selon état + mission NL + score utilité café + UI Pilot |
| V4 | **Clôture mission** auto (smoke vert / file terminée) + bouton Pilot |

## Qu’est-ce qu’une « mission » Lyra ?

1. Tu saisis un objectif NL sur `#/team/office` → **Mission**.
2. Lyra appelle `plan` → crée des tâches Team taguées `_campus_mission_id`.
3. Elle **conduit** (`act`) : drain la file, mode `mission_drive`.
4. Avant Vague 4, la mission restait `open`/`driving` **pour toujours** (même si tout est vert).
5. **Maintenant** : quand toutes les tâches de la mission sont terminales :
   - QA présent et `result.ok` → statut `closed` (smoke vert)
   - **A2** (`LBG_TEAM_MISSION_BLOCK_CLOSE_ON_SMOKE_FAIL=1`, défaut) : QA/owner smoke rouge → **pas closable** (mission reste ouverte)
   - sinon failed sans block → `closed_failed`
   - encore des `queued`/`running` → pas de clôture
   - missions Godot / `owner_smoke_bundle` : QA + `owner_smokes.ok` requis (voir `docs/PLAN_MMO_O2.md`)
6. Mode `mission_close` dans `decide_action` → `act` appelle `maybe_close_mission`.
7. Manuel : bouton **Clôturer** (double-clic = `force`).

## Modes (`decide_action` → `act`)

| Mode | Quand | Action |
|------|-------|--------|
| `triage_failed` | agents failed | drain |
| `mission_close` | mission ouverte + file terminée | clôture auto |
| `mission_drive` | mission ouverte + file | drain |
| `drain` | queued en attente + slots | prefill |
| `coffee_fill` | café ≥ min + utilité OK | spawn L1 |
| `observe` | rien d’urgent / cap plein | idle Lyra (+ tentative close) |

## Env

```bash
LBG_TEAM_CAMPUS_CONDUCTOR_ENABLED=1
LBG_TEAM_CAMPUS_MISSION_AUTO_CLOSE=1   # Vague 4
LBG_TEAM_CAMPUS_CONDUCTOR_MAX_BUSY=4
LBG_TEAM_CAMPUS_CONDUCTOR_MAX_STARTS=2
```

## API / UI

- `GET /v1/team/campus/status` (+ `mission_closure`)
- `GET /v1/team/campus/mission/closure`
- `POST /v1/team/campus/mission/close` `{force?, reason?}`
- `POST …/act` · `POST …/mission` · `POST …/conduct`
- Pilot `#/team/office` : Conduire / Mission / **Clôturer**

## Hors scope

- Scoring LLM des playbooks

## Persistance multi-reboot (Vague 4+)

Fichier JSON : `LBG_TEAM_MISSION_PATH` ou colocalisé `campus_mission.json` à côté de `LBG_TEAM_DB_PATH`.  
Chargé au premier `last_mission()`, écrit à chaque `_set_mission` (y compris clôture).
