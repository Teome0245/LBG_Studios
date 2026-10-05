# Brief matinal Compagnon (P4 vague Agir)

**Date** : 2026-10-05 (P0 2026-09-28 → enrichi P4)  
**But** : point studio matinal read-only — Self + Jobs L2 + LAN + suggestions Agir.  
**Contrat** : brief ≤15 lignes · **0 auto-exécution** des `next_agir` (mails / selfcheck / inventaire restent à valider).

Voir aussi : [`ecosystem_dev_143.md`](ecosystem_dev_143.md) · [`runbook_network_inventory.md`](runbook_network_inventory.md).

---

## Contrat `BriefPayload`

```json
{
  "schema_version": 1,
  "kind": "morning_brief",
  "day_key": "2026-10-05",
  "spoken_text": "…",
  "reply": "…",
  "line_count": 12,
  "auto_execute_next": false,
  "signals": { "proactive": {}, "self": {}, "infra": {}, "jobs_l2": {}, "lan": {}, "mail": {} },
  "next_agir": [
    { "id": "jobs_l2", "sourceText": "ouvre http://192.168.0.140:8080/#/jobs dans le navigateur" },
    { "id": "mail", "sourceText": "regarde mes mails récents" }
  ]
}
```

Priorité `next_agir` (max 2) : Jobs L2 waiting → diff LAN → selfcheck KO → mails.

---

## Surfaces

| Surface | Comportement |
|---------|--------------|
| Agir | `fais mon brief du matin` → `morning_brief` (lecture seule, `auto_real` soft OK) |
| Catalogue | `usefulAgirActions` id `morning_brief` |
| Mandat | scope `morning` |
| Initiative | toast 7h–10h, fingerprint `studio:morning:YYYY-MM-DD` |
| Self | `ensure_morning_brief_will()` 1×/jour si fenêtre matin |

---

## Env

| Variable | Défaut | Rôle |
|----------|--------|------|
| `LBG_MORNING_BRIEF_ENABLED` | `1` | Coupe l’envie Self |
| `LBG_MORNING_BRIEF_TZ` | `Europe/Paris` | Fuseau |
| `LBG_MORNING_BRIEF_HOUR_START` | `7` | Début `[start, end)` |
| `LBG_MORNING_BRIEF_HOUR_END` | `10` | Fin |
| `LBG_NETWORK_INVENTORY_STATE` | `/var/lib/lbg/…/state.json` | Diff LAN dans le brief |

---

## Accept P4

- [x] Synthèse Self + Jobs L2 + LAN (+ mails en suggestion)
- [x] ≤15 lignes
- [x] `auto_execute_next: false` — propositions Agir seulement
- [x] Smoke live `.140`

## Hors scope

- Auto-fetch IMAP dans le brief (reste Agir P1)
- TTS Nest Cast (bouche optionnelle, lot séparé)
- Connecteurs devis / ventes / social
