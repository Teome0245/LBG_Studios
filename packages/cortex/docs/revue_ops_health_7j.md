# Revue métriques — pilote Ops Health (LAN 140)

**Date** : 2026-10-08  
**Périmètre** : plan gaps A–F2 + tick mission L3  
**Verdict** : **GO conditionnel** Phase F (F1/F2 déjà livrés) — mission L3 à clôturer (jour 3) ; F3 O2 jeu **hors** ce plan.

## Snapshot live (2026-10-08 ~10h)

| Indicateur | Valeur |
|------------|--------|
| Ops health | `healthy` · 6/6 requis · 245 `[OFF]` optionnel · 246 `:8787/healthz` OK |
| Timer | `lbg-ops-health-pilot-job` live (`DRY_RUN=0`, `NOTIFY=1`) · cooldown 3 h |
| Mission L3 | `days_ok=2/3` · `last_ok_day=2026-10-08` · `consecutive_red=0` · retries 1/5 |
| Fleet L2 pending | 0 Team · 0 jobs `waiting_approval` |
| Jobs | 117 total · done 110 · queued 4 · failed 3 |
| Lessons | 104 entrées · path `knowledge/lessons_learned.json` |
| Soft-links | Vulcan↔Vex · Hermès↔Tess (présence OK ; Fleet passthrough corrigé 2026-10-08) |

## DoD global (§6 plan) — statut

| Critère | Statut |
|---------|--------|
| ≥1 run pilote auto/jour (vert ou KO géré) | **OK** — timer 3 h ; journal 7j : healthy + remediate (245 requis puis corrigé) |
| Remédiations via L2 | **OK** — spawn L2 + HITL Slack sur KO live |
| Clôture KO → lesson | **OK** — playbook + pont jobs→lessons |
| Chat NL ops → job (opt-in) | **OK** — `LBG_CHAT_AGENTIC` allowlist |
| Vue Fleet agents + L2 | **OK** — `#/team/fleet` |
| Pas d’outil hors allowlist / pas de shell L1 libre | **OK** — garde-fous C |
| Métriques smoke / escalade / latence | **Partiel** — décisions + `elapsed_ms` en state/journal ; pas encore dashboard 7j agrégé |

## Chronologie utile

1. **Avant 2026-10-07** : faux positifs remediate (245 requis) → bruit Slack.
2. **2026-10-07 soir** : 245 optionnel · sonde 246 → `:8787/healthz` · tick mission sur timer · `days_ok=1`.
3. **2026-10-08 matin** : `days_ok=2` · périmètre vert · deadline mission trop courte → **extend** (marge jours restants).

## Soft-links (ADR 0004)

| Studio | Pont IG | Login |
|--------|---------|-------|
| Vulcan (`studio_dev_vulcan`) | Vex (`player_bridge_vex`) | `vulcan_bridge` |
| Hermès (`godot_dev_hermes`) | Tess (`player_bridge_tess`) | `hermes_bridge` |

Fleet expose désormais `mmo_player` / `bridge_agent_id` / `linked_studio_*` (plus seulement dans presence).

## Go / no-go

| Décision | |
|----------|--|
| **GO** | Conserver le pilote live ; terminer mission 3/3 ; F1/F2 restent le cadre assets/PM |
| **NO-GO** | Ne pas ouvrir F3 O2 jeu depuis ce plan (priorités P3–P5 séparées) |
| **À faire** | Demain : tick → `days_ok=3` → `done` · optionnel : agrégat métriques 7j dans Fleet |

## Commandes

```bash
curl -s http://192.168.0.140:8010/v1/team/fleet | jq '.metrics,.smoke_lan_mission.mission'
curl -s -X POST http://192.168.0.140:8010/v1/team/smoke_lan_mission/extend -H 'Content-Type: application/json' -d '{}'
curl -s http://192.168.0.140:8010/v1/team/smoke_lan_mission
```

Voir [`runbook_ops_health_pilot.md`](runbook_ops_health_pilot.md) · [`plan_combler_gaps_agentiques.md`](plan_combler_gaps_agentiques.md).
