# Prime Agent (PrimeIntellect) sur `.143`

**Statut** : lab OK (2026-10-05) — installé, smoke chat vert, **daemon arrêté**.  
**ADR** : [`adr/0024-prime-agent-greffe-peripherique.md`](adr/0024-prime-agent-greffe-peripherique.md).

Greffe **périphérique** sur Omnarchy `.143` (miroir `.10` OK).  
Pas sur 140, pas de fork dans le monorepo, pas de capability Team tant qu’une leçon nette vs Cline n’existe pas.

> Ne pas confondre avec **`packages/prime-client`** (client Godot O2).

## Prérequis

- Accès LAN Ollama **`.110:11434`**
- Matrice : [`local_llm_route_matrix.md`](local_llm_route_matrix.md)
- Catalogue : ADR [`0023`](adr/0023-catalogue-outils-ide-second-avis.md) — **au plus 1 greffe xp active**

## Install (faite 2026-10-05)

```bash
curl -fsSL https://app.primeintellect.ai/prime-agent/install.sh | sh
# → 0.9.8 dans ~/.local/share/prime-agent/
# → symlink ~/.local/bin/prime-agent
# → kernel Python ~/.prime/agent/kernel-venv/
prime-agent --version   # 0.9.8
prime-agent doctor
```

## Provider Ollama LAN

Fichier : `~/.prime/agent/models.json` (tags **réels** sur `.110` au smoke) :

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

Interactif CPU `.110` : **e2b**. Batch patient : **12b-qat**.

## Smoke

### Chat minimal (rejouable)

```bash
mkdir -p /tmp/prime-agent-smoke && cd /tmp/prime-agent-smoke
prime-agent --offline -p --no-session --no-tools --no-skills --no-extensions \
  --no-prompt-templates --no-context-files \
  --model 'ollama-lan/huihui_ai/gemma-4-abliterated:e2b' --thinking off \
  'Réponds UNIQUEMENT avec exactement ce token: PRIME_AGENT_SMOKE_OK'
# Attendu : PRIME_AGENT_SMOKE_OK
prime-agent shutdown --force
```

### Continual Harness (pas encore smoke)

`/refine` + memory locale — à faire en session TUI quand utile ; hors chemin critique.

## Résultats smoke

| Date | Host | Modèle | Test | Résultat | Note |
|------|------|--------|------|----------|------|
| 2026-10-05 | `.143` | `e2b` | install + doctor + `-p` chat | **OK** | ~93 s CPU ; daemon stoppé après |

## Rollback / désinstall

```bash
prime-agent shutdown --force
rm -f ~/.local/bin/prime-agent
rm -rf ~/.local/share/prime-agent ~/.prime
```

## Hors scope

- Capability Team / Pilot sur 140
- Remplacement de Cline / Continue / Claude Code / Compagnon
- Install concurrente Pi / Oh My Pi + Prime Agent
- Daemon always-on (contention `.110` + second cerveau)

## Liens

- Upstream : https://github.com/PrimeIntellect-ai/prime-agent
- RLM : https://www.primeintellect.ai/blog/rlm
- ADR 0020 DSH · ADR 0022 ECC · ADR 0023 catalogue · ADR 0024
