---
name: gladys-self-healing
description: Boucle de méta-régulation et d'auto-réparation Gladys (0€ Cloud). Détecte une anomalie de production, formule un mandat chirurgical, pilote la main ouvrière locale (Qwen 2.5 coder 14B sur Ollama .110), inspecte le diff, valide les tests CI et consigne le résultat.
commands:
  run: tools/test_self_healing_loop.py
---

# Skill Gladys : Boucle d'Auto-Évaluation et Auto-Réparation

## Rôle et Contexte
Gladys assure sa propre résilience opérationnelle via une boucle cybernétique en 5 étapes, 100% autonome et à coût nul (0€ Cloud) :
1. **Détection** : Surveillance et détection d'une anomalie en production.
2. **Formulation du Mandat** : Gladys rédige une consigne chirurgicale avec le bug, la cause racine et les tests à satisfaire.
3. **Exécution Ouvrière Locale** : Délégation à Ollama RTX `.110` (`qwen2.5-coder:14b`).
4. **Supervision & Gatekeeper** : Gladys inspecte le code généré, lance la suite de tests (CI) et refuse toute régression.
5. **Validation & Handoff** : Mise à jour du journal d'incidents et commit propre.

## Commande CLI
```bash
python3 tools/test_self_healing_loop.py
```
