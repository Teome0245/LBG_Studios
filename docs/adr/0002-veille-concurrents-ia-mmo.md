# ADR 0002 — Veille concurrents IA / MMO (2026-10)

**Date** : 2026-10-05  
**Statut** : accepté (cadre de veille — **pas** de pivot produit)

## Contexte

Plusieurs produits proches (MJ texte, MMO « AI NPCs », MMO browser construit par IA, MMO joué par agents) offrent des idées réutilisables. Sans cadre, on risque soit de tout ignorer, soit de dériver hors Bible / rail O2.

Sources passées en revue : Everwhere, Jenova Roleplay GM, Epitome, World of ClaudeCraft, **SpaceMolt**.

## Décision

1. La veille vit dans [`docs/world/CONCURRENTS_IA_MMO_2026-10.md`](../world/CONCURRENTS_IA_MMO_2026-10.md) (extrait vivant).
2. Les tickets actionnables sont listés dans [`docs/world/BOITE_IDEES_GAMEPLAY.md`](../world/BOITE_IDEES_GAMEPLAY.md) §14 — **pas** de Vérité Bible sans décision datée.
3. **Pas de pivot** : client Godot + Core3 Prime + canon Scrapaltai / Lost Heaven restent la cible (OBJECTIVES O2, PLAN_MMO_O2).
4. Priorité d’inspiration :
   - **Court** : UX dialogue (suggestions + mémoire), compagnon IA hub, 1 event dynamique.
   - **Moyen** : wiki data-driven ; **contrat agent** type SpaceMolt (`skill` + catalog + tick mutations) pour Chœur / bots.
5. Explicite **hors scope** : text-only MMO, UE5 rewrite, freeform sans Bible, tokens web3, ouverture publique du serveur aux LLM internet.

## Conséquences

- Thémis / Chœur / Iris peuvent reprendre §14 sans relire les sites.
- Toute idée promue en Vérité → entrée datée dans `BIBLE_MMO.md`.
- SpaceMolt influence surtout le **pont joueurs IA** (manuel + outils), pas le look Godot.
