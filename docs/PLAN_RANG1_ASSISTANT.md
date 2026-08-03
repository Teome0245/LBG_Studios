# Plan traction Rang 1 — Assistant PC / infra

**Date** : 2026-08-03  
**Réf.** : [`RESTAURATION_PRODUIT.md`](RESTAURATION_PRODUIT.md)

| Étape | Parcours | Critère done | État 2026-08-03 |
|-------|----------|--------------|-----------------|
| **A** | `open_url` réel | `https://example.org` hors dry-run | **OK** |
| **B** | `search_web_open` | DDG réel | **OK** (`WEB_SEARCH=1`) |
| **C** | `session_summary` | `export` + `mmo-bridge` | **OK** (Pilot `:8080`) |
| **D** | `notepad_append` | Append sous `C:\Users\Public` | **OK** |
| **E** | `mail_imap_preview` | IMAP lecture | **bloqué** — `LBG_DESKTOP_MAIL_ENABLED=1` + secrets dans `desktop.env` |
| **F** | Dictée micro → STT | Audio → texte → notepad | **à faire** (pas de STT worker) |

Garde-fous inchangés : dry-run / allowlists / audit / approval inject.

## Suite

1. Mail : fournir IMAP (host/user/pass) → activer flag worker → smoke `mail_imap_preview`.
2. Dictée : choisir STT (Whisper local / API) → speech → `notepad_append`.
3. Brancher intents NL Cockpit (« cherche X », « note que… ») sur ces actions (déjà partiel via action-proposal).
