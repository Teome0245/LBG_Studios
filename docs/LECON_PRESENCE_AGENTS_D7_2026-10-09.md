# Leçon — Présence Agents (D7) · clôture conversation 2026-10-09

**Statut** : **clôturé côté conception + code monorepo** · **deploy / Team live incomplets**  
**Produit** : Présence Agents (ex. Session Island)  
**Inspiration** : Coucou (MIT, idées seulement — pas de fork)

## Livré dans le monorepo

| Artefact | Chemin |
|----------|--------|
| Plan Team | [`PLAN_SESSION_ISLAND_D7.md`](PLAN_SESSION_ISLAND_D7.md) |
| Clarifs Compagnon | [`SESSION_ISLAND_D7_COMPAGNON_CLARIFS.md`](SESSION_ISLAND_D7_COMPAGNON_CLARIFS.md) |
| Décisions (gate spawn) | [`SESSION_ISLAND_D7_DECISIONS.json`](SESSION_ISLAND_D7_DECISIONS.json) |
| ADR 0027 **accepté** | [`packages/cortex/docs/adr/0027-session-island-d7.md`](../packages/cortex/docs/adr/0027-session-island-d7.md) |
| Contrat events v1 | [`packages/cortex/docs/session_island_events_v1.md`](../packages/cortex/docs/session_island_events_v1.md) |
| Runbook | [`packages/cortex/docs/runbook_session_island_d7.md`](../packages/cortex/docs/runbook_session_island_d7.md) |
| Spawn Team P0/P1/P1B | `lbg_agents.spawn_team_session_island_d7_job` |
| Emitter + SSE + socket | `linux_agent/Agent_IA/session_emitter.py` + routes `/session/*` |
| Instrumentation CLI | `linux_agent/Agent_IA/core.py` (`run_cli_agent`) |
| Overlay Electron | `packages/compagnon-desktop` (`sessionIsland.*`, opt-in **off**) |
| Client Omarchy minimal | `linux_agent/Agent_IA/tools/presence_agents_client.py` |
| Tests | `linux_agent/Agent_IA/tests/test_session_emitter.py` (4/4) |

## Décisions produit (clarifs)

- **GO** Phase 0–1  
- Bus dual : SSE HTTP + IPC (socket `.143` / pipe Windows prévu)  
- UI : Electron `.10` + client minimal `.143`  
- Pilot Fleet : best-effort P1  
- Nom : **Présence Agents**  
- Timeout Allow/Deny : **60 s** · Always-allow = scope session  

## Leçons Team / ops

1. **`docs_only` / dry-run** : les tâches Team se sont souvent clôturées sans livrable réel (Thémis docs_only générique ; Métis `ide_cli` dry-run).  
2. **Live OpenCode** exige `ide_cli_live` + **jeton** `desktop_approval` aligné avec `LBG_LINUX_APPROVAL_TOKEN` sur `.143` — le token `desktop.env` Windows **ne matche pas**.  
3. **Argus trop tôt** : smoke LAN générique avant emitter → `failed` ; préférer verify ciblé `session/status`.  
4. **`.143` non sync** : `/session/status` encore **404** sur le worker live au moment de la clôture.

## Suite ouverte (hors cette conversation)

1. Aligner / injecter le bon `LBG_LINUX_APPROVAL_TOKEN` pour les mains code live.  
2. Déployer `linux_agent` Agent_IA sur `.143` + `LBG_SESSION_ISLAND_ENABLED=1`.  
3. Activer `sessionIsland.enabled` sur Electron `.10`.  
4. Smoke runbook + (optionnel) miroir Pilot.

## Hors scope confirmé

- Fork Coucou / Mochi / iPhone  
- Godot / O2  
- Greffe REA (rétro-ingénierie) — refusée ; reconstitution clean-room seulement si besoin futur  

## Réf. jalon

[`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) § Desktop D7.
