# ADR 0001 — Repo étoile LBG_Studios (B+C)

**Date** : 2026-07-31  
**Statut** : accepté

## Contexte

Plusieurs dépôts actifs (`LBG_IA_MMORPG`, `new_mmo`, Infographiste, avatar) et du legacy diluaient le focus. `new_mmo` ~13 Go rend un monorepo naïf irréaliste.

## Décision

1. **B** — Dépôt méta `LBG_Studios` = source de vérité objectifs, registre, outils.
2. **C** — Extraction chirurgicale snapshot : `packages/cortex`, `packages/prime-client` (+ launchpad sources).
3. Priorité produit : **Studio (O1) puis Jeu (O2)**.
4. Anciens repos = **upstream legacy** (historique), pas suppression immédiate.

## Conséquences

- Développement neuf dans `packages/*` de ce repo.
- Deploy LAN met à jour chemins progressivement (`/opt/LBG_IA_MMO` peut encore recevoir un rsync depuis `packages/cortex`).
- Infographiste / avatar restent liés hors Git monorepo (poids assets).
