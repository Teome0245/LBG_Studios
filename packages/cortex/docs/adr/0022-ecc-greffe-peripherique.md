# ADR 0022 — Everything Claude Code (ECC) en greffe périphérique

**Statut** : accepté (spike `.143` — **parké**, plugin désactivé)  
**Date** : 2026-09-28

## Contexte

[Everything Claude Code (ECC)](https://github.com/affaan-m/everything-claude-code)
est un système d’optimisation de harness agentique (skills, agents, hooks, review,
mémoire, AgentShield). Cible principale : **Claude Code** ; adaptateurs limités
pour Cursor, OpenClaw, etc. (`ecc-universal` npm, plugin `ecc@ecc`).

Sur Omnarchy **`.143`**, Claude Code est déjà un composant IDE (Ollama `.110`/`.111`),
aux côtés de Cline et Continue — voir [`ecosystem_dev_143.md`](../ecosystem_dev_143.md).

Politique produit (`lbg_agentic_os.md` § 6.1) + même ligne que
[ADR 0020 (DSH)](0020-dsh-greffe-peripherique.md) :
**greffer en périphérie — ne pas substituer Cortex / Team / Pilot.**

## Décision

1. **Ne pas remplacer** Cortex / Team / Pilot / Cline par ECC.
2. **Autoriser** une greffe **poste `.143` uniquement** (scope Claude Code `user`),
   hors 140 / hors monorepo git (pas d’adaptateur Cursor full dans `LBG_Studios`).
3. **Parké après smoke 2026-09-28** : ECC **installé mais désactivé** tant que le
   LLM local n’offre pas un contexte compatible avec le coût always-on ECC (~30k tok).
4. **Ne pas** empiler install plugin + install manuelle / Cursor adapter
   (consigne upstream : un seul chemin par harness).

## Spike `.143` (2026-09-28)

### Install (faite)

```bash
# Sur lbg@192.168.0.143
claude plugin marketplace add https://github.com/affaan-m/ECC --scope user
claude plugin install ecc@ecc --scope user -y \
  --config hooks_enabled=false \
  --config hook_profile=minimal
```

| Élément | Valeur |
|---------|--------|
| Host | `lbg-omarchy` / `192.168.0.143` |
| Plugin | `ecc@ecc` **2.2.2** |
| Scope | `user` (`~/.claude/`) — monorepo non touché |
| Claude Code | `2.1.281` → Ollama `.110` (Gemma 12b / Qwen 9b) |

### Smoke

| Test | Résultat |
|------|----------|
| Plugin list / details | OK — skills/agents ECC visibles |
| Session avec ECC **enabled** | **FAIL** — `Prompt is too long` (toujours-on ECC vs fenêtre locale) |
| Hooks `minimal` | Tempête `pre:observe` (runners standard/strict) ; session bloquée |
| Ollama `.110` au moment du smoke | CPU (`size_vram=0`) ; Gemma ctx **4096** ; Qwen ctx 32768 |
| Session avec ECC **disabled** | Baseline lente (CPU) ; pas de rejet immédiat « prompt too long » |

Détail opérationnel : [`ecc_claude_code_143.md`](../ecc_claude_code_143.md).

### État laissé

```bash
claude plugin disable ecc@ecc   # état nominal actuel
# Réactivation future (si ctx LLM suffisant) :
# claude plugin enable ecc@ecc
```

## Alternatives rejetées (pour l’instant)

| Alternative | Raison |
|-------------|--------|
| ECC full + hooks standard sur `.143` | Charge contexte + hooks incompatibles Ollama local actuel |
| `./install.sh --target cursor` dans le monorepo | Risque de collision avec `AGENTS.md` / rules LBG ; hors scope spike |
| Brancher ECC dans Team / Pilot sur 140 | Substitution du bus interne ; hors greffe périphérique |
| Désinstaller complètement | Conservé pour réessai rapide quand le backend LLM change |

## Risques

| Risque | Mitigation |
|--------|------------|
| Réactiver ECC casse Claude Code local | Garder `enabledPlugins.ecc@ecc=false` ; doc smoke avant enable |
| Doublon vs Cline / Team | ECC = outillage coding poste ; pas de capability Team tant que park |
| Upstream change marketplace / slug | Sources officielles uniquement (`affaan-m/ECC`, `ecc@ecc`, `ecc-universal`) |

## Conséquences

- Aucun changement runtime 140 / orchestrateur / Pilot.
- Doc + ADR versionnés ; config machine `~/.claude/` hors git.
- Réessai pertinent si : Claude cloud, ou Ollama GPU avec `num_ctx` ≫ 30k + hooks off.

## Références

- [`ecc_claude_code_143.md`](../ecc_claude_code_143.md)
- [`adr/0020-dsh-greffe-peripherique.md`](0020-dsh-greffe-peripherique.md)
- [`ecosystem_dev_143.md`](../ecosystem_dev_143.md) · [`omarchy_vm_143.md`](../omarchy_vm_143.md)
- [`lbg_agentic_os.md`](../lbg_agentic_os.md) § 6.1
- https://github.com/affaan-m/everything-claude-code · https://github.com/affaan-m/ECC
