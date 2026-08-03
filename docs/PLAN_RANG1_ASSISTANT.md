# Plan traction Rang 1 — Assistant PC / infra

**Date** : 2026-08-03  
**Réf.** : [`RESTAURATION_PRODUIT.md`](RESTAURATION_PRODUIT.md)

Ordre d’exécution (enchaînement) :

| Étape | Parcours | Critère done | Prérequis |
|-------|----------|--------------|-----------|
| **A** | `open_url` réel (allowlist host) | Worker ouvre `https://example.org` hors dry-run | Jetons alignés, host allowlist |
| **B** | `search_web_open` | Dry-run OK puis réel DDG | `LBG_DESKTOP_WEB_SEARCH=1` (déjà) |
| **C** | `session_summary` → pont API | `export` + `mmo-bridge` HTTP 200, patch fusionnable | Pilot Cortex |
| **D** | `notepad_append` (proxy dictée) | Append texte sous `C:\Users\Public` | file allowlist |
| **E** | `mail_imap_preview` | Flag + secrets IMAP — sinon doc « à activer » | `LBG_DESKTOP_MAIL_ENABLED` off aujourd’hui |

Garde-fous inchangés : dry-run / allowlists / audit / approval inject.
