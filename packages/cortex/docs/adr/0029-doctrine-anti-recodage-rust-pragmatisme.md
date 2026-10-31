# ADR 0029 — Doctrine Anti-Recodage Global (Rust & Hype vs Pragmatisme Produit)

**Statut** : **Accepté**  
**Date** : 2026-10-31  
**Contexte** : Interrogation récurrente issue des tendances du web et des réseaux sociaux (ex. mouvance *« Rewrite everything in Rust »*) sur l'opportunité de réécrire l'intégralité du projet en Rust.  
**Références** : ADR 0017 (Anti-techno-tourisme & conservation de la sim existante), ADR 0026 (Runtime joueur Godot-first), [`OBJECTIVES.md`](../../../OBJECTIVES.md).

---

## 1. Contexte & Diagnostic du « Piège du Big Bang »

Le projet **LBG Studios** est structuré autour de trois piliers opérationnels :
- **O1 Compagnon** : Backend Python FastAPI, orchestration multi-agents, dialogue LLM local/hybride, interface Web Vue 3 et bureau Electron Three.js / VRM.
- **O2 MMO (banc d'essai)** : Moteur Godot 4 headless (`prime-hub` sur `.246:8787`), client Godot (`prime-client`), simulation spatiale, navigation 3D et persistance SQLite.
- **O3 Joueurs IA** : Agents autonomes portables opérant dans l'univers de jeu.

La tentation de « tout réécrire en Rust » pour des motifs de pureté académique ou de performances théoriques se heurte aux réalités concrètes de l'ingénierie logicielle :

### A. Pilier O1 (IA & Dialogue) : le goulot n'est pas le langage
- 99 % de l'écosystème IA mondial (PyTorch, GGUF, bindings Ollama, tokenizers, transformers) est natif ou interfacé en Python.
- Le temps de réponse du Compagnon est dominé à 98 % par l'inférence matérielle des modèles de langage (CPU/GPU). Remplacer FastAPI par un serveur Rust ferait gagner 2 millisecondes sur une requête où le LLM met plusieurs secondes à inférer.
- Une réécriture détruirait l'agilité d'itération, la glue de données et la compatibilité avec les bibliothèques d'agents sans aucun gain perceptible pour l'utilisateur.

### B. Pilier O2 (Jeu & Simulation) : l'effet « réinvention de la roue »
- Godot 4 fournit nativement et gratuitement : le moteur physique et les collisions, le `NavigationServer3D` (pathfinding PNJ), l'importateur GLTF/VRMA, l'éditeur de scènes visuel, la gestion des animations squelettiques 53 os et la pile réseau WebSocket.
- Réécrire en Rust pur (ex. Bevy ou moteur custom) exigerait de réimplémenter un moteur de jeu complet à la main. Cela immobiliserait l'équipe pendant 18 à 24 mois sans livrer la moindre quête, PNJ ou fonctionnalité de jeu supplémentaire.
- **Loi de Spolsky** : les réécritures complètes *from scratch* sont la première cause d'abandon des projets indépendants.

---

## 2. Doctrine Retenue : L'Approche « Scalpel » (Rust Ciblé)

Rust n'est pas banni du projet, mais son adoption est soumise à un **cadre strict d'intervention chirurgicale** :

| Rôle dans le projet | Technologie nominale | Justification |
| :--- | :--- | :--- |
| **Orchestration IA & Dialogue (O1)** | **Python (FastAPI)** | Écosystème IA dominant, flexibilité, glue multi-modèles. |
| **Moteur Monde & Rendu (O2)** | **Godot 4 (GDScript / C#)** | Outils intégrés (physique, navigation, UI, formats 3D). |
| **Optimisation ultra-haute performance** | **Rust (Scalpel)** | Réservé aux micro-briques goulot, isolées et démontrées. |

### Cas d'usage autorisés pour Rust :
1. **Godot GDExtension (`godot-rust / gdext`)** : si un benchmark formel démontre qu'une boucle interne de simulation (ex. calcul de foule de 1 000+ PNJ, raycasting massif) sature le thread GDScript.
2. **Micro-passerelle réseau (Relay haute fréquence)** : micro-service isolé (Axum/Actix) si un jour le flux binaire temps réel sature l'I/O réseau.
3. **Outillage CLI offline lourd** : compilation d'assets, conversions de maillages volumineux ou traitement de textures.

---

## 3. Règle de Décision (Gatekeeper)

Toute proposition d'introduction de code Rust doit satisfaire deux conditions préalables :
1. **Preuve par profilage / benchmark** : existence d'un goulet d'étranglement mesuré sur la stack existante, impossible à optimiser en GDScript/Python.
2. **Modularité sans rupture** : intégration sous forme de plugin (GDExtension) ou de micro-service découplé, **sans jamais déclencher de réécriture globale** du code applicatif ou du contenu produit.

---

## 4. Statut & Clôture

- **Refus formel du Big Bang Rewrite en Rust**.
- Maintien du triptyque pragmatique : **Python (cerveau) + Godot (corps/espace) + Rust (scalpel optionnel sur benchmark)**.

