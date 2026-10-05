# Contre-pouvoir Compagnon (pas Lyra)

**Date** : 2026-09-22  
**Rôle** : valider décisions / confirmer actions Agir **avant** le Réel.  
**Lyra** = présence / jauges — **pas** ce gate.

## Flux

```
Compagnon propose (action-proposal)
  → POST /v1/companion/review-proposal  (contre-pouvoir)
  → ActionCard : badge + risques
  → auto dry-run si soft / medium
  → Réel : jeton + (si block_real) override humain
```

## Sources de vérité

| Couche | Fichier |
|--------|---------|
| Service | `orchestrator/services/companion_review.py` |
| API orch | `POST /v1/companion/review-proposal` |
| Proxy Pilot | `POST /v1/pilot/companion/review-proposal` |
| UI | `compagnon_ui/src/lib/agir.js` → `reviewProposal` · `ActionCard.vue` |

## Soft-confirm LAB (remplace le jeton)

Sur LAN sécurisé (`LBG_COMPAGNON_LAB=1` ou `LBG_DESKTOP_APPROVAL_MODE=confirm`) :

| Avant | Après |
|-------|--------|
| Coller `LBG_DESKTOP_APPROVAL_TOKEN` | Case **« Je confirme l’exécution réelle »** |
| Secret dans localStorage | Sentinelle `confirmed` + `desktop_confirm: true` |

**Réel auto (lecture seule)** — kinds `mail_imap_preview`, `memory_recall`, `selfcheck`, `network_inventory`, `morning_brief`, sondes… : `auto_real=true` (plus de Dry-run → clic Réel).  
`open_url` / `search_web_open` restent en dry-run auto (effet UI).  
Off : `LBG_COMPANION_AUTO_REAL_SOFT=0`.

Agents (`.10` / `.143`) : même mode via `LBG_DESKTOP_APPROVAL_MODE=confirm` (Windows) ou `LBG_LINUX_APPROVAL_MODE=confirm`.  
Le jeton secret reste accepté en secours. Contre-pouvoir `block_real` + override inchangé.

## Vague Agir 2026-10 (P1–P3)

| # | Sujet | Doc / code |
|---|--------|------------|
| P1 | Mail IMAP + auto-Réel soft | `mail_imap_preview` · `companion_review._AUTO_REAL_KINDS` |
| P2 | Selfcheck LAN + soft-confirm DevOps | `devops_executor` · `LBG_DEVOPS_SOFT_CONFIRM` |
| P3 | Inventaire LAN + timer + Héphaïstos/Atlas + Nest Cast | [`runbook_network_inventory.md`](runbook_network_inventory.md) |

## Smoke

```bash
curl -sS -X POST http://192.168.0.140:8010/v1/companion/review-proposal \
  -H 'Content-Type: application/json' \
  -d '{"actor_id":"ui:compagnon","source_text":"mails","proposal":{"action":{"kind":"mail_imap_preview"},"risk_level":"high"}}'
```
