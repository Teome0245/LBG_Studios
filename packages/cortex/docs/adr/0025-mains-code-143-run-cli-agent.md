# ADR 0025 — Mains code `.143` (`run_cli_agent`)

**Statut** : accepté  
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
2. **Cline n’est pas un agent Campus** : c’est (ou sera) une app cible du kind (`app=cline|claude|opencode`).
3. **Exécutant préféré slice-1** : **Claude Code CLI** (`claude -p …`) — déjà autorisé ADR 0023,
   scriptable. Cline CLI / OpenCode = allowlist opt-in une fois smoke OK.
4. **Branchement Team** : personas **Iris** (`dev_godot`), **Dédale** (`dev_game`),
   **Pygmalion** (`dev_game` + `infographiste_ia`) peuvent poser
   `context.ide_cli=true` → workflow `ide_cli` → `agent.desktop` → `.143`.
5. **Pas de rôle « hors jeu » dédié** pour l’instant (voir § Roles). L’outil est **partagé**.

## Rôles — état 2026-10-05

| Persona | Rôle technique | Scope code |
|---------|----------------|------------|
| Iris / Hermès | `dev_godot` | Client Godot / gateway |
| Dédale | `dev_game` | Gameplay / content / Core3 |
| Pygmalion | `dev_game` + flag infographiste | Assets / pipeline |
| Héphaïstos / Atlas / Thémis | `ops` / `admin_infra` / `pm` | Infra / LLM / jalons — **pas** forge monorepo |

**Pas de `dev_studio` / « hors game »** aujourd’hui. Le code Cortex / Compagnon / Pilot
n’a pas de persona dédiée : quand besoin, une tâche `ide_cli` peut être portée par
`dev_game` (Dédale) ou `ops` **via le même outil** — un futur rôle `dev_studio` est
**hors slice**, ADR amendé si on le crée.

## Contrat `run_cli_agent`

```json
{
  "kind": "run_cli_agent",
  "app": "claude",
  "prompt": "mandat court…",
  "cwd": "/home/lbg/projects/LBG_Studios",
  "timeout_s": 300
}
```

| Garde-fou | Valeur |
|-----------|--------|
| Worker | `LBG_LINUX_CLI_AGENT_ENABLED=1` (défaut **0** jusqu’au smoke) |
| Team | `LBG_TEAM_IDE_CLI_ENABLED=1` (défaut **0**) |
| Dry-run | défaut **on** (`desktop_dry_run` / env) |
| Approbation | même policy desktop (soft-confirm LAB / token) |
| Apps | allowlist `claude` · `cline` · `opencode` |
| cwd | sous `/home/lbg/projects/` (ou allowlist env) |
| Timeout | `LBG_LINUX_CLI_AGENT_TIMEOUT_S` (défaut 300) |
| Audit | JSONL linux_agent + trace Team |

## Flux

```text
Compagnon / Lyra
  → tâche Iris|Dédale|Pygmalion (context.ide_cli=true)
    → ide_cli_workflow → agent.desktop (target=omarchy)
      → POST :5005/invoke  kind=run_cli_agent
        → claude -p "…"  (cwd monorepo)
          → stdout/stderr → Team result
```

Cline UI reste disponible via `open_app` pour observation / second passage humain.
Cursor Cloud Agent (L2) reste l’alternative cloud — **pas** le chemin nominal `.143`.

## Alternatives rejetées

| Alternative | Pourquoi |
|-------------|---------|
| Cline = persona Campus | Contredit ADR 0023 |
| Computer-use (clics Plan→Act) | Fragile ; hors kinds Linux |
| Remplacer Team par harness IDE | Second OS |
| Toujours-on Cline + OpenCode + Codex | Règle de charge ADR 0023 |

## Conséquences

- Slice-1 : kind worker + workflow Team + tests dry-run ; enable flags après smoke `.143`.
- Docs : `ecosystem_dev_143.md` + Agir « lance claude sur omarchy pour … ».
- Amendement possible : rôle `dev_studio` si le volume Cortex hors-jeu le justifie.

## Références

- Impl : `linux_agent/Agent_IA/core.py` (`run_cli_agent`) · `team/ide_cli_workflow.py`
- Smoke : à ajouter `infra/scripts/smoke_ide_cli_143.sh` (dry-run)
