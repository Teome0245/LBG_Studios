# Maturité contenu A / B / C

**Date** : 2026-08-27  
**Canon** : [`docs/world/BIBLE_MMO.md`](../../../docs/world/BIBLE_MMO.md) — vérités **V60–V65**, décision **T8**.  
**Runtime** : `packages/cortex/agents/src/lbg_agents/dialogue_llm.py`

## Principe

- **Canon monde = C** (large : fictionnel sauf illégal).
- **B** puis **A** = filtres de **présentation** selon le joueur (protéger ≠ amputer le lore).
- La policy LBG prime sur le refus « soft » des modèles Ollama.

| Cap | Effet |
|-----|--------|
| **C** | Pas de filtre présentation ; thèmes adultes fictionnels OK |
| **B** | Pas de sexe/nudité explicites ni gore clinique ; sombre évoqué OK |
| **A** | Empile B + ton bienveillant ; variantes soft obligatoires pour arcs sombres |

Interdit **tous paliers** : exploitation sexuelle de mineurs / CSAM, doxxing, harm IRL.

## Contexte dialogue

Passer le plafond au LLM via (premier trouvé gagne) :

1. `context.maturity_cap` (ou `content_maturity` / `maturity`)
2. `context.player.maturity_cap`
3. `context.session_summary.maturity_cap`
4. Env `LBG_DIALOGUE_MATURITY_DEFAULT` (défaut code : **`C`**)

Aliases acceptés : `soft`/`kid` → A, `teen`/`pg13` → B, `mature`/`adult` → C.

Exemple :

```json
{
  "world_npc_id": "npc:innkeeper",
  "maturity_cap": "A",
  "quest_hints": [
    { "text": "Apporte de l'eau au camp", "maturity": "A" },
    { "text": "Scène dure du hangar", "maturity": "C" }
  ]
}
```

Avec `maturity_cap: "A"`, seul le premier hint est injecté dans le system prompt. Listes supportées : `quest_hints`, `maturity_hints`. Un `quest_hint` objet peut aussi porter `maturity`.

## API code

| Fonction | Rôle |
|----------|------|
| `resolve_maturity_cap(context)` | Plafond effectif |
| `format_maturity_guardrails(cap)` | Bloc system prompt |
| `filter_by_maturity(items, cap)` | Filtre listes taguées |
| `maturity_allows(tag, cap)` | Test unitaire A⊂B⊂C |

La clé de cache dialogue inclut `maturity_cap` (défaut `LBG_DIALOGUE_CACHE_CONTEXT_KEYS`).

## Tests

```bash
cd packages/cortex && python -m pytest agents/tests/test_maturity_cap.py -q
```

## Suite (hors ce stub)

- Persistance `maturity_cap` sur le compte joueur / UI réglages.
- Tags `maturity` sur quêtes / assets / variantes soft côté contenu.
- PIN parental / preuve d’âge pour **monter** vers C (V61).
