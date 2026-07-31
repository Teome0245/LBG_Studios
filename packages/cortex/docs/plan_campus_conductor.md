# Plan — Campus Conductor (Lyra)

**Date** : 2026-07-31  
**Statut** : V2 livré (opt-in)  
**Voir aussi** : `docs/lbg_agentic_os.md`

## Problème

Le bureau Team montre ~10 personas ; souvent peu de `busy` et beaucoup `idle` / café.  
C’est **normal** (miroir), mais la file et le café méritent un conducteur qui **décide**.

## Livré

| Version | Contenu |
|---------|---------|
| V0 | Drain `queued` L1 + rapport idle |
| V1 | Coffee fill (spawn utiles si café plein) |
| V2 | `act` selon état + mission NL + score utilité café + UI Pilot |

## Modes (`decide_action` → `act`)

| Mode | Quand | Action |
|------|-------|--------|
| `triage_failed` | agents failed | drain |
| `mission_drive` | mission ouverte + file | drain |
| `drain` | queued en attente + slots | prefill |
| `coffee_fill` | café ≥ min + utilité OK | spawn L1 |
| `observe` | rien d’urgent / cap plein | idle Lyra |

Score café : pas de respawn si succès récent (`COFFEE_UTILITY_S` = 6 h).

## Env

```bash
LBG_TEAM_CAMPUS_CONDUCTOR_ENABLED=1
LBG_TEAM_CAMPUS_CONDUCTOR_MAX_BUSY=4
LBG_TEAM_CAMPUS_CONDUCTOR_MAX_STARTS=2
LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_FILL=1
LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_MIN=3
LBG_TEAM_CAMPUS_CONDUCTOR_COFFEE_UTILITY_S=21600
```

## API / UI

- `GET /v1/team/campus/status` · `POST …/act` · `POST …/mission` · `POST …/conduct`
- Pilot `#/team/office` : barre Lyra (Conduire / Mission)
- Timer 5 min → `/act`

## Hors scope

- Clôture auto mission sur smoke vert
- Scoring LLM des playbooks
