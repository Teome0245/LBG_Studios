# ADR 0021 — Slack canal ops (Element / Matrix en backup)

**Statut** : accepté  
**Date** : 2026-08-26  
**Décideurs** : Pilote  
**Complète** : ADR 0018 (Matrix canal externe, shelf P03)  
**Réf.** : [`lbg_agentic_os.md`](../lbg_agentic_os.md) § 6.1 · `lbg_agents.ops_notify`

---

## Contexte

1. Element / Matrix est le canal ops actuel (alertes Atlas, `matrix_notify`, CR spawn, bridge HITL).
2. La team veut un canal plus confortable au quotidien (**Slack**), sans perdre Element.
3. Politique produit : greffe **périphérique** — jamais substituer Conductor / bus Team / file SQLite.

## Décision

1. **Canal primaire cible** : Slack (`#lbg-ops` au MVP).
2. **Backup** : Element / Matrix reste branché en parallèle (`LBG_OPS_NOTIFY_BACKEND=both`).
3. **Abstraction unique** : `lbg_agents.ops_notify.send_text()` — fan-out matrix / slack / both.
4. **MVP** : alerte-only (webhook Incoming). HITL (boutons Approve / slash) = phase 2.
5. **Cutover Element** : optionnel plus tard (`backend=slack`) ; pas de suppression du code Matrix tant que backup utile.

## Architecture

```text
Atlas / spawn / notify  →  ops_notify.send_text
                              ├─ matrix (Element)  ← backup
                              └─ slack webhook     ← primaire cible
```

## Variables (MVP)

| Variable | Rôle |
|----------|------|
| `LBG_OPS_NOTIFY_BACKEND` | `matrix` \| `slack` \| `both` (défaut **`both`**) |
| `LBG_SLACK_WEBHOOK_OPS` | Incoming Webhook `#lbg-ops` |
| `LBG_SLACK_BOT_TOKEN` | Bot `xoxb-…` — HITL poll + Block Kit |
| `LBG_SLACK_CHANNEL_OPS` | Channel id `#lbg-ops` |
| `LBG_SLACK_ALLOWLIST` | User IDs autorisés Approve/Reject |
| `LBG_OPS_NOTIFY_DISABLE` | `1` = coupe tous les backends |
| `LBG_MATRIX_*` | inchangé (homeserver, token, room) |

## Phases

| Phase | Contenu |
|-------|---------|
| **S0** | ADR + `ops_notify` + dual-run call sites alertes |
| **S1** | Webhook configuré en prod 140 ; smoke message test |
| **S2** | HITL Slack : poll texte + Block Kit + endpoints `/v1/pilot/slack/*` |
| **S2b** | Digest équipe horaire sur Slack (fan-out `matrix_notify` → `ops_notify`) |
| **S3** | Cutover optionnel `backend=slack` ; Element off ops |

## Non-objectifs

- Remplacer Pilot / Cockpit / Team bus.
- Chat libre Slack = orchestrateur au MVP.
- Secrets Slack dans Git.

## Conséquences

- Dual-run = anti-régression ops (si Slack down, Element continue).
- Dépendance SaaS Slack acceptée pour le confort ; souveraineté = backup Matrix.
