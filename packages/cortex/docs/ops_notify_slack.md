# Canal ops — Slack + Element (backup)

**ADR** : [`adr/0021-slack-canal-ops-element-backup.md`](adr/0021-slack-canal-ops-element-backup.md)  
**Code** : `lbg_agents.ops_notify` · `slack_hitl` · `slack_notify` · `slack_hitl_poll`

## Objectif

Alertes + **HITL L2** + **digest équipe horaire** sur **Slack `#lbg-ops`**, Element / Matrix en backup (`backend=both`).

## S1 — Webhook alertes

```bash
LBG_OPS_NOTIFY_BACKEND=both
LBG_SLACK_WEBHOOK_OPS=https://hooks.slack.com/services/...
LBG_SLACK_CHANNEL_OPS=C0BSV3LE48J
LBG_OPS_NOTIFY_MAX_CHARS=12000   # digests équipe (défaut 5500 alertes courtes)
```

Smoke : `python -c "from lbg_agents.ops_notify import send_text; print(send_text('smoke'))"`

## S1b — Digest équipe horaire (miroir Element)

Le watchdog P03 `matrix_notify` pousse le même digest que Element (`📬 Équipe — HH:15`) via `ops_notify.send_text` :

- **Index** : toutes les tâches ✅ / ❌ / 🔔 du créneau
- **Détail** : résumé humain + revue (commandes `approve` / `task` adaptées au canal)
- **Planning** : créneaux **toutes les 3 h** à `:15` — `07:15`, `10:15`, `13:15`, `16:15`, `19:15` (silence 22h–05h30). Vars : `LBG_MATRIX_NOTIFY_INTERVAL_H=3`, `LBG_MATRIX_NOTIFY_HOUR_OFFSET=1`.
- **Annulées** : ignorées si &gt; **72 h** (`LBG_MATRIX_NOTIFY_CANCELLED_MAX_AGE_H`) ; tombstones persistantes → pas de re-push après purge d’état

Sur **140**, le script `run_matrix_notify_watchdog.sh` charge aussi `/etc/lbg-ia-mmo.env` et appelle `ops_notify` via le venv cortex (`LBG_CORTEX_PYTHON`).

Timer : `lbg-p03-matrix-notify.timer` (P03). Complète `lbg-slack-notify.timer` (L2 pending toutes les 15 min).

## S2 — HITL L2 (Approve / Reject)

### Prérequis bot Slack (une fois)

1. [api.slack.com/apps](https://api.slack.com/apps) → Create App (ou réutiliser celle du webhook).
2. **OAuth & Permissions** → Bot Token Scopes :
   - `chat:write`
   - `channels:history`
   - `channels:read`
   - `commands` (optionnel slash)
3. Install to workspace → copier **Bot User OAuth Token** `xoxb-…`
4. Inviter le bot dans `#lbg-ops` (`/invite @Bot`).
5. Dans `lbg.env` :

```bash
LBG_SLACK_BOT_TOKEN=xoxb-…
LBG_SLACK_CHANNEL_OPS=C0BSV3LE48J
LBG_SLACK_ALLOWLIST=U0BLV3859NY
LBG_SLACK_HITL=1
LBG_TEAM_APPROVAL_TOKEN=…   # déjà présent
```

6. Push secrets + activer services sur 140 :

```bash
bash infra/scripts/push_secrets_vm.sh
# sur 140 :
sudo cp infra/systemd/lbg-slack-*.service infra/systemd/lbg-slack-notify.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now lbg-slack-hitl-poll.service
sudo systemctl enable --now lbg-slack-notify.timer
```

### Usage

| Dans `#lbg-ops` | Effet |
|-----------------|--------|
| `approve <id>` / `valider <id>` | approve + run Team L2 |
| `reject <id>` / `annuler <id>` | cancel tâche |
| Boutons **Approve** / **Reject** | idem (si bot + Interactivity) |
| **Ouvrir Pilot** | lien Pilot `#/team` (marche déjà via webhook) |

Push auto L2 pending : timer `lbg-slack-notify` (15 min) → Block Kit + texte.

### Boutons Approve / Reject (Socket Mode)

1. App Slack → **Socket Mode** → Enable.
2. App-Level Token `xapp-…` (scope `connections:write`) → `LBG_SLACK_APP_TOKEN`.
3. **Interactivity & Shortcuts** → On (Request URL vide OK en Socket Mode).
4. Sur 140 :

```bash
sudo systemctl enable --now lbg-slack-hitl-socket.service
```

Poll texte (`lbg-slack-hitl-poll`) reste en secours pour `approve <id>`.

## Call sites alertes

| Source | Fonction |
|--------|----------|
| Atlas périmètre KO | `admin_infra_element.send_element_message` |
| Atlas bench watchdog | `atlas_bench_watchdog.send_element_alert` |
| Spawn phases | `team_spawn_phases.push_element_text` |
| L2 pending | `slack_notify` / `ops_notify.send_l2_pending` |
| Digest équipe horaire | `matrix_notify.send_team_digest` → `ops_notify.send_text` |
