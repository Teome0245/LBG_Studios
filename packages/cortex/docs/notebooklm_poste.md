# NotebookLM — greffe poste (POC)

**Date** : 2026-09-28  
**Statut** : POC poste Teome — **hors** Cortex / Team / `.140`  
**Outil** : [`notebooklm-mcp-cli`](https://github.com/jacob-bd/notebooklm-mcp) (`nlm` + MCP `gemini-notebook-mcp`)

## Principe

Même règle que Colab / DSH / ECC : **périphérie de recherche**, pas substitution de la mémoire Studio (Team SQLite, `knowledge/`, RAG local prévu).

| OK | Interdit |
|----|----------|
| Cursor / CLI sur le poste | Daemon / capability Team sur `.140` |
| Notebooks « bible / design / docs » | Auth cookie dans secrets LAN |
| Query / audio overview / sources | Chemin critique Lyra / Pilot / smokes |

## Install (déjà fait sur ce poste)

```bash
# uv + CLI (PATH : ~/.local/bin)
uv tool install notebooklm-mcp-cli
nlm setup add cursor        # Cursor
nlm setup add claude-code   # Claude Code CLI
nlm setup add cline         # Cline CLI (~/.cline/…)
# Continue : fichiers ~/.continue/mcpServers/gemini-notebook*.{yaml,json}
```

| Client | Config | Statut poste |
|--------|--------|--------------|
| Cursor | `~/.cursor/mcp.json` (+ `Projets/.cursor/mcp.json`) | branché |
| Claude Code | `~/.claude.json` | branché |
| Claude Desktop | app non installée | — |
| Cline CLI | `~/.cline/data/settings/cline_mcp_settings.json` | branché |
| Cline (VS Code) | `~/.config/Code/.../saoudrizwan.claude-dev/settings/cline_mcp_settings.json` | branché |
| Continue | `~/.continue/mcpServers/` (+ `Projets/.continue/mcpServers/`) | branché (mode **Agent**) |

## Auth (une fois — à faire dans un terminal **local** Hyprland)

Le login ouvre Chromium et attend la connexion Google (~5 min max). À lancer **toi-même** dans Kitty/foot (pas depuis un agent headless) :

```bash
export PATH="$HOME/.local/bin:$PATH"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
nlm login
nlm login --check
nlm notebook list
```

Puis amorcer les docs canons :

```bash
bash packages/cortex/tools/notebooklm/seed_lbg_docs.sh
```

Re-auth si `nlm doctor` indique auth *stale* : `nlm login` (ou `--force` / `--clear` pour changer de compte).

**Attention** : API non officielle (cookies Google). ToS / casses possibles. Compte perso OK pour le POC ; pas de compte prod Studio.

## Usage typique

```bash
# Créer un notebook de recherche Studio
nlm notebook create "LBG — bible & design"

# Ajouter des sources (URL ou fichiers locaux)
nlm source add <NOTEBOOK_ID> --url "https://..."
nlm source add <NOTEBOOK_ID> --file docs/world/BIBLE_MMO.md

# Query grounded
nlm notebook query <NOTEBOOK_ID> "Résume les piliers lore Scrapaltai"

# Depuis Cursor (après restart) : outils MCP notebook_list, source_add, notebook_query, …
```

Script d’amorçage docs canons → notebook : `tools/notebooklm/seed_lbg_docs.sh`.

## Hors scope (volontaire)

- Pas d’Enterprise GCP tant que le POC poste ne prouve pas la valeur.
- Pas de branchement OpenClaw / Team / Open WebUI `.100`.
- Pas de sync H24 docs repo → NotebookLM.

## Vérif

```bash
nlm doctor
nlm setup list
```

Redémarrer **Cursor** après `nlm setup add cursor` pour charger le MCP.
