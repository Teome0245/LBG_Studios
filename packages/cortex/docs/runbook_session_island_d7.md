# Runbook — Présence Agents (D7)

**Date** : 2026-10-09  
**ADR** : [`0027`](adr/0027-session-island-d7.md) · Events : [`session_island_events_v1.md`](session_island_events_v1.md)

## Flags worker `.143`

```bash
# linux.env / systemd
LBG_SESSION_ISLAND_ENABLED=1
LBG_SESSION_ISLAND_FAIL_OPEN=1
LBG_SESSION_ISLAND_APPROVAL_TIMEOUT_S=60
```

Redémarrer `linux_agent` `:5005` après changement.

## Smoke rapide

```bash
# Status
curl -sS http://127.0.0.1:5005/session/status | jq .

# SSE (autre terminal)
curl -sN http://127.0.0.1:5005/session/stream

# Client minimal
python packages/cortex/linux_agent/Agent_IA/tools/presence_agents_client.py \
  --sse http://127.0.0.1:5005/session/stream
```

Déclencher un `run_cli_agent` **réel** (pas dry-run) → events `session.start` / `prompt` / `stop|error`.

## Electron `.10`

`packages/compagnon-desktop/config.json` :

```json
"sessionIsland": {
  "enabled": true,
  "streamUrl": "http://192.168.0.143:5005/session/stream",
  "decisionUrl": "http://192.168.0.143:5005/session/decision"
}
```

Opt-in off par défaut. Relancer Compagnon Desktop.

## Rollback

1. `LBG_SESSION_ISLAND_ENABLED=0` + restart worker  
2. `sessionIsland.enabled: false` sur Electron  
3. Aucun impact Agir / D6 si flags off

## Notes Team

Les tâches `ide_cli` en **dry-run** ne livrent pas de code — exiger `ide_cli_live=true` + `desktop_approval` pour un passage réel.
