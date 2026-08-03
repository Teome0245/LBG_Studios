# Plan traction Rang 1 — Assistant PC / infra

**Date** : 2026-08-03  
**Réf.** : [`RESTAURATION_PRODUIT.md`](RESTAURATION_PRODUIT.md)

| Étape | Parcours | Critère done | État 2026-08-03 |
|-------|----------|--------------|-----------------|
| **A** | `open_url` réel | `https://example.org` hors dry-run | **OK** |
| **B** | `search_web_open` | DDG réel | **OK** (`WEB_SEARCH=1`) |
| **C** | `session_summary` | `export` + `mmo-bridge` | **OK** (Pilot `:8080`) |
| **D** | `notepad_append` | Append sous `C:\Users\Public` | **OK** |
| **E** | `mail_imap_preview` | IMAP lecture | **OK** — user `sdesharches` @ `.51` INBOX (port 143 `NO_SSL` ; TLS 993 + `INSECURE_SSL` après restart worker admin) |
| **F** | Dictée micro → STT | Audio → texte → notepad | **reporté** (pas urgent) |

Garde-fous inchangés : dry-run / allowlists / audit / approval inject.

## Suite

1. ~~Mail IMAP~~ — OK 2026-08-03.
2. Dictée : plus tard (Whisper local / API).
3. Rang 2 : voir [`PLAN_RANG2_PERSONA.md`](PLAN_RANG2_PERSONA.md).
4. Optionnel : redémarrer `C:\Agent_IA\run_agent.cmd` **en admin** pour basculer IMAP 993 + `INSECURE_SSL=1`.
