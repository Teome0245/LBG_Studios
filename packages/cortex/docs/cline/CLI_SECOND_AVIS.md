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

## Coûts & Décision nominale (ADR 0025)

| Chemin | Backend | Coût tokens | Latence observée | Statut Team |
|--------|---------|-------------|------------------|-------------|
| **OpenCode headless** | `opencode/big-pickle` | catalogue OpenCode | ~5–15 s | **Nominal (Défaut)** |
| **Cline CLI** | Ollama `.110` (`E4b-qat`) | **0 € API** (LAN) | >350 s (`size_vram: 0` CPU) | **Second avis / Opt-in** |

## Mesure de charge & Smoke live (2026-10-13 — O-IDE-1..3)

1. **Preuve bout-en-bout (O-IDE-1)** :
   - Déclenchement live vérifié : Team/Orch (`:8010`) → worker `.143:5005` (`run_cli_agent app=cline`) → binaire user `/home/lbg/.local/bin/cline` → Ollama `.110:11434`.
2. **Diagnostic performance Ollama (O-IDE-2)** :
   - L'inspection `ollama ps` sur `.110` confirme `size_vram: 0` (exécution 100 % RAM CPU, sans GPU) avec un contexte de 32 768 tokens.
   - Sur CPU non accéléré, la latence de traitement dépasse les 350 s, déclenchant le timeout HTTP interne du client Cline (`durationMs: 357164` → `Error: The operation timed out`).
   - Règle de plancher : interdiction de redescendre sous `E4b-qat` pour coder (seuil qualité minimum). L'accélération nécessite un hôte Ollama avec VRAM allouée.
3. **Décision formelle ADR 0025 (O-IDE-3)** :
   - **OpenCode** est **maintenu comme exécutant nominal** pour toute la production Team (Métis, Iris, Dédale, Pygmalion).
   - **Cline CLI** reste un **outil de second avis / analyse locale à la demande**, sans bloquer les workflows studio.

