# ECC (Everything Claude Code) sur `.143`

**Statut** : parké (2026-09-28) — plugin installé, **désactivé**.  
**ADR** : [`adr/0022-ecc-greffe-peripherique.md`](adr/0022-ecc-greffe-peripherique.md).

Greffe **périphérique** Claude Code sur Omnarchy `.143` uniquement.
Pas sur 140, pas d’adaptateur Cursor dans le monorepo.

## Prérequis

- Claude Code CLI sur `.143` (`claude --version` ≥ 2.1)
- Node.js (marketplace / cache plugin)
- LLM : aujourd’hui Ollama `.110` via `~/.claude/settings.json`
  (`ANTHROPIC_BASE_URL=http://192.168.0.110:11434`)

## État courant

```bash
ssh lbg@192.168.0.143 'claude plugin list'
# ecc@ecc 2.2.2 — Status: disabled
```

Config user typique (`~/.claude/settings.json`) :

- `extraKnownMarketplaces.ecc` → `https://github.com/affaan-m/ECC.git`
- `enabledPlugins["ecc@ecc"]=false`
- `pluginConfigs["ecc@ecc"].options` → `hooks_enabled=false`, `hook_profile=minimal`

## Install (déjà fait ; pour rejouer)

```bash
# Un seul chemin : plugin natif Claude Code (pas d’install manuelle en plus)
claude plugin marketplace add https://github.com/affaan-m/ECC --scope user
claude plugin install ecc@ecc --scope user -y \
  --config hooks_enabled=false \
  --config hook_profile=minimal
claude plugin disable ecc@ecc   # nominal tant que LLM local léger
```

Sources officielles uniquement : repo `affaan-m/ECC`, plugin `ecc@ecc`, npm `ecc-universal`.

## Smoke

### Avec ECC enabled (attendu : FAIL sur LLM local actuel)

```bash
claude plugin enable ecc@ecc
cd ~/projects/LBG_Studios/packages/cortex
claude -p --permission-mode bypassPermissions --allowed-tools '' \
  --permission-prompts none --output-format text \
  'Réponds UNIQUEMENT: ECC_SMOKE_OK'
# Observé 2026-09-28 : Prompt is too long
claude plugin disable ecc@ecc
```

### Pourquoi ça casse

| Facteur | Observé |
|---------|---------|
| Always-on ECC | ~30k tokens (skills/agents inventaire) |
| Gemma 12b via Ollama | `context_length` **4096** |
| Hooks même en `minimal` | tempête `pre:observe` (bloquant) |
| Inférence `.110` | CPU (`size_vram=0`) au moment du smoke |

**Conclusion** : utilisable seulement avec un modèle à **gros contexte** (cloud Claude ou Ollama GPU `num_ctx` ≫ 30k), hooks restant **off** au premier essai.

## Rollback / désinstall

```bash
claude plugin disable ecc@ecc
# ou retrait complet :
claude plugin uninstall ecc@ecc
claude plugin marketplace remove ecc
```

## Hors scope

- `./install.sh --target cursor` dans `LBG_Studios`
- Capability Team / Pilot sur 140
- Remplacement de Cline / Continue / Compagnon
