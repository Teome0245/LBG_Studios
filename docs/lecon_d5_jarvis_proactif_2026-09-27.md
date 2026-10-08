# Leçon — Fil Jarvis / D5 proactif + soft-confirm (2026-09-27 → clôture 2026-10-08)

**Discussion** : Compagnon « plus que Jarvis » (demande un mandat, propose sans qu’on lui demande)  
**Surfaces** : `:5174` · Pilot `#/jobs` · Accueil `#/`  
**Statut** : **clôturé** — code en main + deploy lab ; pas de dirty tree lié à ce fil (2026-10-08).

---

## Intention produit

Jarvis exécute ce qu’on demande. On voulait un Compagnon qui :

1. **demande** ce qu’il peut veiller (mandat) ;
2. **propose** des actions non sollicitées (Garde / Opportunité / Studio) ;
3. **n’auto-exécute jamais** le Réel L2.

## Livré

| Élément | Où | Notes |
|---------|-----|--------|
| **D5** Garde / Mandat / Opportunité / Studio | `mandate.js` · `initiativeQuota.js` · toast | Voir [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) § D5 |
| Empty state chips Mandat | `ChatFlow.vue` | Si mandat non confirmé |
| Soft-confirm LAB | `ActionCard` + `_SOFT_KINDS` | `open_url`, `mail_imap_preview`, sondes → Réel sans case |
| Jobs prérempli | `pilot_web/index.html` | Plus de « cherche Cursor AI » |
| Actions utiles | `usefulAgirActions.js` | Plus d’entrée Recherche web / Cursor |
| Accueil | `pilot_web/index.html` | Carte doublon « Chat produit (Orch) » retirée |
| Routes Accueil / Bureau | `pilot_router` hide-all `.pilot-page` | Fuites Accueil sur `#/team/office` corrigées |

Commit de référence (soft-confirm / initiatives) : `5a0cb68` et suivants sur la branche O1.

## Pièges

| Sujet | Leçon |
|-------|--------|
| Deploy smoke | `POST /api/ask` peut pendre (LLM lent) alors que UI + Agir sont OK — ne pas bloquer le deploy dessus |
| Soft-confirm | Côté UI **et** `companion_review` (`block_real=false`) ; sinon la case disparaît mais Réel reste verrouillé |
| Accueil | « Beaucoup de lignes Accueil » = souvent routeur partiel, pas des liens morts |

## Suite (hors ce fil)

Ce fil ne rouvre plus D5. La suite Studio/Jeu est ailleurs :

1. **Feeling D6** — rejeu humain C2 encore partiel — [`smoke_humain_d6_2026-10-08.md`](smoke_humain_d6_2026-10-08.md)  
2. **Présence zone entraînement** — Phase C livrée ; reste rejeu humain + L3 — [`PLAN_PRESENCE_ZONE_ENTRAINEMENT.md`](PLAN_PRESENCE_ZONE_ENTRAINEMENT.md)  
3. **Priorités** — [`PRIORITES_ACTUELLES.md`](PRIORITES_ACTUELLES.md)

## Ne pas recommencer

- Remettre une recherche Cursor dans Jobs / actions utiles  
- Redemander confirmation pour `open_url` / mail preview en LAB soft-confirm  
- Absorber Team/Jobs dans un clone de `:5174`
