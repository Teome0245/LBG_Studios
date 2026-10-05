# Mémoire → seed d’évolution STUDIO (P5 vague Agir)

**Date** : 2026-10-05  
**But** : après `memory_recall`, extraire **1** `evolution_seed` scorée et la proposer via STUDIO  
(Team L1 / En parler / Ignorer) — **pas** un dump des 443 leçons, **pas** d’auto-promo.

## Flux

```
Agir « montre ce que tu retiens »
  → memory_recall (Self + leçons)
  → extract_evolution_seed (thèmes Jobs L2 > LAN > mails > infra)
  → studio_offer dans le payload
  → ActionCard : panneau STUDIO
       ├ Team L1  → spawn qa lecture seule + feedback accept (seed)
       ├ En parler → message discuss + feedback accept
       └ Ignorer   → feedback dismiss (pas de seed)
```

`auto_promote: false` à l’extraction. Une promotion Self n’arrive que si l’humain
accepte et que le score seed atteint le seuil spontanéité (`LBG_SPONTANEITY_PROMOTE_SCORE`).

## Scoring thèmes

| Thème | Exemples leçons | Poids |
|-------|-----------------|-------|
| `jobs_l2` | waiting_approval, HITL | 0.92 |
| `lan` | inventaire, freebox, apparus | 0.88 |
| `mail` | IMAP, inbox | 0.84 |
| `infra` | selfcheck, healthz, disk | 0.78 |
| `compagnon` | Agir, spontané | 0.72 |

## Fichiers

| Couche | Chemin |
|--------|--------|
| Extraction | `agents/src/lbg_agents/memory_recall.py` |
| UI STUDIO | `compagnon_ui/src/components/ActionCard.vue` |
| Extract client | `compagnon_ui/src/lib/agir.js` → `extractStudioOffer` |
| Feedback | `POST /spontaneity/feedback` (`evolution_seed`) |

## Accept P5

- [x] 1 seed scorée après recall (pas dump)
- [x] Visible STUDIO : Team L1 / En parler / Ignorer
- [x] Pas d’auto-promo à l’affichage
- [x] Smoke + tests unitaires

## Smoke

```bash
cd packages/cortex/agents && .venv/bin/python -m pytest tests/test_memory_recall.py -q
# Live .140
PYTHONPATH=agents/src .venv/bin/python -c \
  'from lbg_agents.memory_recall import run_memory_recall; \
   o=run_memory_recall(actor_id="p5", text="mémoire", context={}); \
   print(o["status"].get("evolution_seed")); print(o["status"].get("studio_offer",{}).get("intents"))'
```

Sur `:5174` : **Ma mémoire** → Réel → bandeau violet STUDIO.
