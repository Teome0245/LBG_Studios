# ADR 0027 — Présence Agents (D7 Compagnon Desktop)

**Statut** : **accepté**  
**Date** : 2026-10-09  
**Accepté le** : 2026-10-09 (clarifs Compagnon + GO humain ; P0 figé hors short-circuit Team docs_only)  
**Nom produit** : **Présence Agents** (ex. « Session Island »)

**Complète** :

- [`docs/PLAN_SESSION_ISLAND_D7.md`](../../../../docs/PLAN_SESSION_ISLAND_D7.md)
- [`docs/SESSION_ISLAND_D7_COMPAGNON_CLARIFS.md`](../../../../docs/SESSION_ISLAND_D7_COMPAGNON_CLARIFS.md)
- [`docs/SESSION_ISLAND_D7_DECISIONS.json`](../../../../docs/SESSION_ISLAND_D7_DECISIONS.json)
- Contrat events : [`session_island_events_v1.md`](../session_island_events_v1.md)
- ADR [`0023`](0023-catalogue-outils-ide-second-avis.md) · [`0025`](0025-mains-code-143-run-cli-agent.md)
- [`FOCUS_COMPAGNON.md`](../../../../docs/FOCUS_COMPAGNON.md) (rail D0–D6 → D7)
- Gap **G5** : [`plan_combler_gaps_agentiques.md`](../plan_combler_gaps_agentiques.md)
- Inspiration (idées MIT, pas fork) : [Louis-CFM/coucou](https://github.com/Louis-CFM/coucou)

## Contexte

Les mains code headless (ADR 0025, `run_cli_agent` / OpenCode sur `.143`) sont **efficaces mais opaques** pendant l’exécution. Le HITL L2 (tokens, Pilot, Slack) couvre les jobs Team, mais **pas** une UX poste « Allow / Deny au moment de l’outil ».

Le Compagnon Desktop (`packages/compagnon-desktop`) a déjà tray + overlay avatar + initiatives (D2/D3). Il manque un **bandeau session live** + carte d’approbation inline.

## Décision

1. **Greffer** **Présence Agents** (D7) comme extension de `compagnon-desktop` (+ client minimal Omarchy) — pas un produit Coucou parallèle, pas Tauri, pas Godot.
2. **Cerveau inchangé** : Cortex / Team / Pilot / Compagnon `:5174` restent la source de vérité. L’island est une **peau poste**.
3. **Contrat events v1** : voir [`session_island_events_v1.md`](../session_island_events_v1.md).
4. **Bus V1 dual** : HTTP SSE (`GET /session/stream`, `POST /session/decision`) **et** IPC (Unix socket `.143` / named pipe `.10`) en parallèle dès P1.
5. **Fail-open** : timeout Allow/Deny **60 s** ; `LBG_SESSION_ISLAND_FAIL_OPEN=1` par défaut.
6. **Opt-in** : `LBG_SESSION_ISLAND_ENABLED=0` par défaut ; config Electron `sessionIsland.enabled`.
7. **Pills = outils IDE** (`opencode`, `claude`, …), jamais personas Campus (ADR 0023).
8. **Jobs Team `waiting_approval`** restent Pilot + Slack — **hors** island V1.
9. **Cibles UI P1** : Electron `.10` + client minimal Omarchy `.143`.
10. **Miroir Pilot Fleet** : best-effort P1 ; reporter P2 si ça met le MVP en danger (ne bloque pas le close).
11. **Always-allow** : scope **session** uniquement.
12. **Secrets** : jamais tokens / clés dans les events ; chemins tronqués ; audit JSONL worker.

## Alternatives rejetées

| Alternative | Pourquoi |
|-------------|---------|
| Fork Coucou (Tauri + Mochi) | Stack déjà Electron ; marque tierce ; scope explosé |
| Island dans Godot / prime-hub | O2 hors focus D7 |
| Remplacer Slack/Pilot HITL | Island = complément poste, pas cockpit ops |
| SSE seul sans IPC | Rejeté en clarifs — dual bus P1 |
| Auto-Allow silencieux global | Contre-pouvoir Compagnon |
| Chat multi-LLM dans l’island | Chat = `:5174` |

## Conséquences

- Jalon **D7 Présence Agents** dans `FOCUS_COMPAGNON.md`.
- Spawn Team : `python -m lbg_agents.spawn_team_session_island_d7_job` (vague `P0` docs / `P1` code).
- Runbook : `packages/cortex/docs/runbook_session_island_d7.md` (à créer en P1).
- Amendement ADR 0025 : instrumentation `run_cli_agent` → emitter (réf. croisée, pas conflit).

## Critères d’acceptation P1

Voir plan §10. Résumé : opt-in off = no-op ; events start/stop ; overlay ticker ;
Allow/Deny sur réel approval ; fail-open 60 s ; pas de régression D6/Agir.

## Références d’implémentation (P1)

- `packages/compagnon-desktop/overlay/`
- Client minimal Omarchy (à créer, léger)
- `packages/cortex/linux_agent/Agent_IA/session_emitter.py` (NEW)
- `packages/cortex/linux_agent/Agent_IA/core.py` (`run_cli_agent`)
- `packages/cortex/orchestrator/services/action_policy.py` (réutiliser, ne pas dupliquer)
