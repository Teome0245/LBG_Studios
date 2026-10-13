# ADR 0025 — Mains code `.143` (`run_cli_agent`)

**Statut** : accepté (amendé 2026-10-06)  
**Date** : 2026-10-05  
**Complète** : ADR [`0023`](0023-catalogue-outils-ide-second-avis.md) · [`0020`](0020-dsh-greffe-peripherique.md) · [`ecosystem_dev_143.md`](../ecosystem_dev_143.md) · [`lbg_agentic_os.md`](../lbg_agentic_os.md) § 6.1

## Contexte

Le chemin nominal « sans Cursor » ouvre VS Code + Cline sur Omarchy **`.143`**, mais **Plan→Act
reste manuel**. L’humain ne doit plus prendre la main sur la VM pour un patch L1/L2 borné :
Compagnon / Team doivent commander des **mains code** headless sur `.143`.

Contraintes ADR 0023 :

- Cortex / Team / Pilot / Compagnon restent le **cerveau** ;
- Cline / Claude Code / Continue = **outils IDE**, pas personas Campus ;
- pas de computer-use UI (clics Plan→Act) comme chemin critique.

## Décision

1. **Figer** une capability / kind **`run_cli_agent`** sur le worker `linux_agent` `.143:5005`.
2. **Cline n’est pas un agent Campus** : outil UI IDE (`open_app`) + éventuel CLI plus tard.
3. **Exécutant headless nominal (2026-10-06)** : **OpenCode CLI**
   (`opencode run -m opencode/big-pickle …`) — smoke live OK sur `.143`.
4. **Claude Code CLI** : allowlist **expérimentale** — hang / modèle Ollama non catalogué
   (v2.1.x) ; garder UI / second avis ; réessayer après fix settings / version.
5. **Cline CLI** : installé `.143` (`~/.local/bin/cline`, 2026-10-11) en **second avis**
   via Ollama **`.110`** (coûts locaux). **Amendement 2026-10-13 (O-IDE-1..3)** : smoke live
   confirmé bout-en-bout (`E4b-qat`). L'exécution CPU sans VRAM sur `.110` (`size_vram: 0`, >350 s)
   impose de maintenir **OpenCode CLI comme nominal** de production pour la vélocité Team.
   Cline CLI reste disponible en second avis / opt-in 0 € API. Voir [`cline/CLI_SECOND_AVIS.md`](../cline/CLI_SECOND_AVIS.md).
6. **Branchement Team** : Iris (`dev_godot`), Dédale (`dev_game`), Pygmalion
   (`infographiste_ia`), **Métis** (`dev_studio`) via `context.ide_cli=true`.
7. **Rôle hors-jeu** : `dev_studio` (persona **Métis**) — Cortex / Compagnon / Pilot /
   docs studio, pas le client Godot ni Core3.

## Rôles — état 2026-10-06

| Persona | Rôle technique | Scope code |
|---------|----------------|------------|
| Iris / Hermès | `dev_godot` | Client Godot / gateway |
| Dédale | `dev_game` | Gameplay / content / Core3 |
| Pygmalion | `dev_game` + flag infographiste | Assets / pipeline |
| **Métis** | **`dev_studio`** | Cortex · Compagnon · Pilot · docs studio |
| Héphaïstos / Atlas / Thémis | `ops` / `admin_infra` / `pm` | Infra / LLM / jalons |

## Contrat `run_cli_agent`

```json
{
  "kind": "run_cli_agent",
  "app": "opencode",
  "prompt": "mandat court…",
  "cwd": "/home/lbg/projects/LBG_Studios",
  "timeout_s": 300
}
```

| Garde-fou | Valeur |
|-----------|--------|
| Worker | `LBG_LINUX_CLI_AGENT_ENABLED=1` |
| Team | `LBG_TEAM_IDE_CLI_ENABLED=1` |
| Dry-run | défaut **on** (`desktop_dry_run` / soft-confirm Agir) |
| Approbation | policy desktop (soft-confirm LAB / token) |
| Apps | `opencode` (nominal) · `cline` (second avis, Ollama `.110`) · `claude` (expérimental) |
| Modèle OpenCode | `LBG_LINUX_CLI_AGENT_MODEL` (défaut `opencode/big-pickle`) — **pas Ollama** |
| Modèle Cline | `LBG_LINUX_CLINE_MODEL` (défaut `huihui_ai/gemma-4-abliterated:E4b-qat` @ `.110`, plancher qualité) |
| cwd | sous `/home/lbg/projects/` |
| Timeout | `LBG_LINUX_CLI_AGENT_TIMEOUT_S` (défaut **1200**, max 3600) — **auto-bump** si prompt long (~60 s / 500 car.) ; orch HTTP `LBG_DESKTOP_CLI_AGENT_HTTP_TIMEOUT_S` ≥ agent + 120 s |
| Audit | JSONL linux_agent + trace Team |

## Flux

```text
Compagnon / Lyra
  → tâche Iris|Dédale|Pygmalion|Métis (context.ide_cli=true)
    → ide_cli_workflow → agent.desktop (target=omarchy)
      → POST :5005/invoke  kind=run_cli_agent
        → opencode run -m opencode/big-pickle "…"  (cwd monorepo)
          → stdout/stderr → Team result
```

Cline UI reste via `open_app`. Cursor Cloud Agent (L2) = alternative cloud, pas nominal `.143`.

## Alternatives rejetées

| Alternative | Pourquoi |
|-------------|---------|
| Cline = persona Campus | Contredit ADR 0023 |
| Computer-use (clics Plan→Act) | Fragile ; hors kinds Linux |
| Remplacer Team par harness IDE | Second OS |
| Claude CLI comme nominal (2026-10) | Hang headless vs Ollama local |
| Cline CLI obligatoire | Non installé ; OpenCode suffit |

## Conséquences

- Smoke : `infra/scripts/smoke_ide_cli_143.sh`
- Agir : `lance opencode sur omarchy pour …` (défaut) · `lance claude …` (expérimental)
- Amendement Claude → nominal seulement après smoke live stable

## Références

- Impl : `linux_agent/Agent_IA/core.py` · `team/ide_cli_workflow.py`
- Smoke : `infra/scripts/smoke_ide_cli_143.sh`
