---
trigger: always_on
description: Rituel démarrage / fin de session — lire SESSION_EN_COURS et handoffs avant de coder
---

# Continuité session (Cursor ↔ Antigravity)

## Au démarrage d’une tâche non triviale

1. Lire `docs/SESSION_EN_COURS.md` (état vivant).
2. Lire `docs/PRIORITES_ACTUELLES.md` si l’objectif n’est pas déjà clair.
3. Si un handoff Antigravity est cité dans la session → le lire entièrement avant toute édition.
4. Confirmer en ≤10 lignes : objectif, contraintes, prochain pas — puis seulement coder.

## Avant de quitter / changer de sujet

Mettre à jour `docs/SESSION_EN_COURS.md` : objectif, fichiers touchés, bloquants, 3 prochaines actions, lien handoff.

## Handoffs dédiés

- `docs/handoff_antigravity_*.md` = tickets isolés (prompt collable + DoD).
- Ne pas mélanger deux handoffs dans la même session sauf demande explicite.
