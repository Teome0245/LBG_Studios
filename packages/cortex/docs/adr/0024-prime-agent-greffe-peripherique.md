# ADR 0024 — Prime Agent (PrimeIntellect) en greffe périphérique

**Statut** : accepté (spike `.143` — **lab OK**, daemon off)  
**Date** : 2026-10-05

## Contexte

[Prime Agent](https://github.com/PrimeIntellect-ai/prime-agent) (PrimeIntellect, MIT) est un
harness coding / recherche open-source bâti autour de deux abstractions :

1. **RLM** (Recursive Language Model) — contexte comme variables et outils / subagents comme
   appels Python dans un REPL IPython persistant.
2. **Continual Harness** — prompts, mémoires, descriptions de skills et specs de subagents
   durables, raffinables via `/refine` (snapshots + rollback), scope local par défaut.

Fork enrichi de **Pi** (`~/.prime/agent/` vs `~/.pi/agent/`). Fichier de modèles :
`~/.prime/agent/models.json` — providers OpenAI-compat dont **Ollama**.

Sur Omnarchy **`.143`**, le chemin nominal IDE reste Cline / Continue / Claude Code
(ADR [`0023`](0023-catalogue-outils-ide-second-avis.md)).

Politique produit (`lbg_agentic_os.md` § 6.1) + même ligne que
[ADR 0020 (DSH)](0020-dsh-greffe-peripherique.md) et [ADR 0022 (ECC)](0022-ecc-greffe-peripherique.md) :
**greffer en périphérie — ne pas substituer Cortex / Team / Pilot / Compagnon.**

**Collision de nom** : le monorepo a déjà `packages/prime-client` (jeu Godot O2).
Dans toute doc / ADR LBG, écrire **Prime Agent (PrimeIntellect)** ou `prime-agent`,
jamais « Prime » seul.

## Décision

1. **Ne pas remplacer** Cortex / Team / Pilot / Compagnon / Cline par Prime Agent.
2. **Autoriser** une greffe **poste `.143` (et miroir `.10`)** uniquement — config user
   `~/.prime/`, hors 140 / hors monorepo git (pas de fork upstream dans `LBG_Studios`).
3. **Statut catalogue** : expérimentation (ADR 0023) — **au plus une** greffe d’xp active
   (ne pas empiler avec DSH / ECC enabled / OpenCode always-on).
4. **LLM** : Ollama LAN `.110` / `.111` via `models.json` (matrice
   [`local_llm_route_matrix.md`](../local_llm_route_matrix.md)) — pas de cloud obligatoire
   pour le spike Studio.
5. **Capability Team** `prime_agent_headless` : **non** pour l’instant (même barre que DSH P2) ;
   évaluer seulement si le spike coding poste apporte une leçon nette vs Cline.
6. **Patterns à importer** (sans dépendance runtime) : `/refine`-style lessons,
   context-as-variable, skills Python importables — vers `lessons_learned` / playbooks Team.

## Spike `.143` (2026-10-05)

### Install

```bash
# Sur lbg@192.168.0.143 (ou miroir .10)
curl -fsSL https://app.primeintellect.ai/prime-agent/install.sh | sh
```

Provider Ollama LAN — `~/.prime/agent/models.json` :

```json
{
  "providers": {
    "ollama-lan": {
      "baseUrl": "http://192.168.0.110:11434/v1",
      "api": "openai-completions",
      "apiKey": "ollama",
      "compat": {
        "supportsDeveloperRole": false,
        "supportsReasoningEffort": false
      },
      "models": [
        { "id": "huihui_ai/gemma-4-abliterated:e2b" },
        { "id": "huihui_ai/gemma-4-abliterated:12b-qat" },
        { "id": "huihui_ai/qwen3.5-abliterated:9b" },
        { "id": "lbg-cline-plan:9b" }
      ]
    }
  }
}
```

```bash
prime-agent --model ollama-lan/huihui_ai/gemma-4-abliterated:e2b
# ou 12b-qat pour batch patient (CPU .110)
```

| Élément | Valeur |
|---------|--------|
| Host | `lbg-omarchy` / `192.168.0.143` |
| Version | **0.9.8** (`~/.local/share/prime-agent/` + symlink `~/.local/bin/prime-agent`) |
| Scope | user (`~/.prime/`) — monorepo non touché |
| LLM | Ollama `.110:11434/v1` (tags réels : `e2b`, `12b-qat`, `9b`) |

### Smoke (2026-10-05)

| Test | Résultat |
|------|----------|
| Install `install.sh` + kernel Python | **OK** (~20 s) |
| `prime-agent --version` → `0.9.8` | **OK** |
| `prime-agent doctor` (aucun service) | **OK** |
| Chat `-p` e2b, no-tools, token `PRIME_AGENT_SMOKE_OK` | **OK** (~93 s CPU `.110`) |
| `prime-agent shutdown --force` | **OK** (daemon démarré pendant le run, arrêté après) |
| Runtime sur `.140` | **N/A** — rien déployé |

Commande smoke rejouable :

```bash
cd /tmp/prime-agent-smoke
prime-agent --offline -p --no-session --no-tools --no-skills --no-extensions \
  --no-prompt-templates --no-context-files \
  --model 'ollama-lan/huihui_ai/gemma-4-abliterated:e2b' --thinking off \
  'Réponds UNIQUEMENT avec exactement ce token: PRIME_AGENT_SMOKE_OK'
```

Détail opérationnel : [`prime_agent_143.md`](../prime_agent_143.md).

**Statut après smoke** : greffe **vivante** en lab (installée, provider OK, chat OK). Pas de promotion vers « autorisé ». Pas de capability Team. Daemon **arrêté** après le smoke (ne pas laisser always-on).

## Alternatives rejetées (pour l’instant)

| Alternative | Raison |
|-------------|--------|
| Remplacer Cline par Prime Agent | Chemin nominal ADR 0023 = Cline |
| Deploy daemon Prime Agent sur `.140` | Substitution bus / second OS |
| Fork upstream dans `packages/cortex` | Hors greffe périphérique ; collision sémantique avec `prime-client` |
| Capability Team headless dès le jour 1 | Même discipline que DSH — spike poste d’abord |
| Empiler avec Pi / Oh My Pi + Prime Agent | Un seul fork Pi-family à la fois |

## Risques

| Risque | Mitigation |
|--------|------------|
| Confusion `prime-client` (jeu) vs `prime-agent` | Nommage explicite « PrimeIntellect » partout |
| Shell / Python modèle = pas un sandbox | Worktree jetable ; pas de secrets ; repos trusted only |
| Contention `.110` (`MAX_LOADED=1`) | Une greffe xp à la fois ; préférer e2b pour interactif |
| Always-on harness / gros system prompt | Smoke court ; park si `Prompt too long` (leçon ECC) |
| Daemon background oublié | `prime-agent shutdown` en fin de spike |

## Conséquences

- Aucun changement runtime 140 / orchestrateur / Pilot.
- Doc + ADR versionnés ; config machine `~/.prime/` hors git.
- ADR 0023 amendé : ligne catalogue *Expérimentation* + second avis CLI possible.
- Réessai / promotion seulement après smoke + leçon (ADR amendé + checklist).

## Références

- [`prime_agent_143.md`](../prime_agent_143.md)
- [`adr/0020-dsh-greffe-peripherique.md`](0020-dsh-greffe-peripherique.md)
- [`adr/0022-ecc-greffe-peripherique.md`](0022-ecc-greffe-peripherique.md)
- [`adr/0023-catalogue-outils-ide-second-avis.md`](0023-catalogue-outils-ide-second-avis.md)
- [`local_llm_route_matrix.md`](../local_llm_route_matrix.md) · [`ecosystem_dev_143.md`](../ecosystem_dev_143.md)
- [`lbg_agentic_os.md`](../lbg_agentic_os.md) § 6.1
- https://github.com/PrimeIntellect-ai/prime-agent · https://www.primeintellect.ai/blog/rlm
