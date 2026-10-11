# Cline CLI — second avis local (`.143`)

**Statut** : installé 2026-10-11 · OpenCode reste **nominal** Team (ADR 0025).

## Pourquoi

OpenCode Team utilise `opencode/big-pickle` (catalogue OpenCode) — **pas Ollama**, coûts/quotas peu visibles.
Cline CLI pointe vers **Ollama `.110`** → coûts = infra locale (maîtrisés).

## Install (déjà fait)

```bash
npm install -g --prefix "$HOME/.local" cline   # → ~/.local/bin/cline
export PATH="$HOME/.local/bin:$PATH"
```

## Modèle

| Usage | Host | Model |
|-------|------|--------|
| Act / code (défaut CLI, **minimum**) | `.110` | `huihui_ai/gemma-4-abliterated:E4b-qat` |
| Plan / rapide (secours) | `.110` | `huihui_ai/qwen3.5-abliterated:9b` |
| Qualité max (optionnel) | `.110` | `huihui_ai/gemma-4-abliterated:12b-qat` |

Env agent : `LBG_LINUX_CLINE_PROVIDER=ollama` · `LBG_LINUX_CLINE_MODEL=huihui_ai/gemma-4-abliterated:E4b-qat`

## Smoke

```bash
cline -y --json --thinking none -P ollama -m huihui_ai/gemma-4-abliterated:E4b-qat \
  -c /home/lbg/projects/LBG_Studios -t 300 \
  "Réponds PONG sans modifier de fichiers"
```

Smoke 2026-10-11 : CLI → Ollama `.110` OK. Défaut Cline = **E4b-qat** (plancher qualité). Sur CPU (`size_vram: 0`) rester patient ; ne pas redescendre sous E4b sans override explicite.

## Via Team (second avis)

Contexte tâche : `"ide_cli_app": "cline"` (défaut toujours `opencode`).

```json
{ "ide_cli": true, "ide_cli_app": "cline", "ide_cli_live": true, "desktop_dry_run": false }
```

Ou Agir : `lance cline sur omarchy pour …`

**ADR 0023** : ne pas lancer OpenCode + Cline en écriture parallèle sur le même cwd.

## Coûts

| Chemin | Backend | Coût tokens |
|--------|---------|-------------|
| OpenCode headless | `opencode/big-pickle` | catalogue OpenCode (limites compte) |
| Cline CLI / UI | Ollama `.110` | **0 € API** — charge GPU/CPU LAN |
