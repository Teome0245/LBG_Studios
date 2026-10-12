# Présence Agents — contrat events v1

**Produit** : Présence Agents (D7)  
**Date** : 2026-10-09  
**Statut** : figé P0 (aligné [`SESSION_ISLAND_D7_DECISIONS.json`](../../../docs/SESSION_ISLAND_D7_DECISIONS.json))  
**ADR** : [`0027`](adr/0027-session-island-d7.md)

## Bus (P1)

| Canal | Où | Endpoint / path |
|-------|-----|-----------------|
| HTTP SSE | workers `:5005` | `GET /session/stream` |
| Décision | workers `:5005` | `POST /session/decision` |
| Unix socket | Omarchy `.143` | `$XDG_RUNTIME_DIR/lbg-presence-agents.sock` |
| Named pipe | Windows `.10` | `\\.\pipe\lbg-presence-agents` |

Les deux familles (HTTP + IPC) émettent / consomment le **même** JSON newline-delimited.  
Opt-in : `LBG_SESSION_ISLAND_ENABLED=1`. Fail-open : `LBG_SESSION_ISLAND_FAIL_OPEN=1` (défaut).  
Timeout Allow/Deny : **60 s** (`approval_timeout_s`).

## Envelope

```json
{
  "v": 1,
  "event": "session.start",
  "session_id": "cli-opencode-20261009-abcdef",
  "agent": "opencode",
  "persona": "metis",
  "ts": "2026-10-09T14:00:00Z",
  "summary": "≤80 caractères, sans secrets",
  "detail": {},
  "approval_id": null
}
```

| Champ | Règle |
|-------|--------|
| `agent` | Outil IDE (`opencode`, `claude`, …) — **pas** persona Campus |
| `persona` | Optionnel — Métis/Iris seulement pour audit |
| `summary` | Truncate ; jamais token / clé / `.env` |
| `approval_id` | Non-null seulement sur `session.approval_needed` |

## Events

| `event` | Effet UI | Callback |
|---------|----------|----------|
| `session.start` | Pill apparaît | — |
| `session.prompt` | Ticker prompt | — |
| `session.tool_pre` | Ticker outil / fichier | — |
| `session.tool_post` | Ticker résultat court | — |
| `session.approval_needed` | Carte Allow / Deny / Always-session | `POST /session/decision` |
| `session.stop` | Finished ~5 s | — |
| `session.error` | État erreur | — |

## Exemple — `session.start`

```json
{
  "v": 1,
  "event": "session.start",
  "session_id": "cli-opencode-20261009-a1b2c3",
  "agent": "opencode",
  "persona": "metis",
  "ts": "2026-10-09T14:00:00Z",
  "summary": "OpenCode · packages/cortex",
  "detail": { "cwd": "/home/lbg/projects/LBG_Studios/packages/cortex", "kind": "run_cli_agent" },
  "approval_id": null
}
```

## Exemple — `session.approval_needed`

```json
{
  "v": 1,
  "event": "session.approval_needed",
  "session_id": "cli-opencode-20261009-a1b2c3",
  "agent": "opencode",
  "persona": "metis",
  "ts": "2026-10-09T14:00:12Z",
  "summary": "Réel run_cli_agent — jeton desktop requis",
  "detail": { "kind": "run_cli_agent", "app": "opencode" },
  "approval_id": "appr-9f3e2c1a"
}
```

Décision client :

```json
{
  "v": 1,
  "approval_id": "appr-9f3e2c1a",
  "decision": "allow",
  "scope": "once",
  "ts": "2026-10-09T14:00:20Z"
}
```

`decision` ∈ `allow` | `deny` · `scope` ∈ `once` | `session` (Always-allow = `allow` + `session`).

Si aucune décision avant **60 s** → fail-open (policy desktop / deny-safe selon kind).

## Exemple — `session.stop`

```json
{
  "v": 1,
  "event": "session.stop",
  "session_id": "cli-opencode-20261009-a1b2c3",
  "agent": "opencode",
  "persona": "metis",
  "ts": "2026-10-09T14:05:01Z",
  "summary": "Session terminée · exit 0",
  "detail": { "exit_code": 0 },
  "approval_id": null
}
```

## Cibles UI P1

- Electron `.10` : `compagnon-desktop` overlay (`sessionIsland.*`)
- Omarchy `.143` : client minimal (SSE et/ou socket)
- Pilot Fleet : miroir **best-effort** (ne bloque pas le close MVP)
