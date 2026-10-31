---
trigger: always_on
description: Protocole de délégation de code à Cline (génération) et contrôle par Antigravity (supervision/revue)
---

# Protocole de Cocréation : Cline (Codeur) ↔ Antigravity (Superviseur)

À la demande de l'utilisateur, la génération de code est déléguée à **Cline** (local 0 € via Ollama `.110`), et **Antigravity** assure le rôle de superviseur et contrôleur qualité.

## 1. Rôles et responsabilités

- **Cline (`huihui_ai/qwen2.5-coder-abliterate:14b` sur `.110`)** :
  - Reçoit les mandats de code ciblés (fichiers explicites, jamais tout le monorepo).
  - Écrit / édite le code source sur la machine `.143`.
  - Peut être déclenché soit par Antigravity en CLI (`cline -P ollama ...`), soit par l'utilisateur via l'extension VS Code.

- **Antigravity (Superviseur & Gatekeeper)** :
  - **Cadrage** : Prépare et formule le prompt / mandat pour Cline avec les contraintes exactes.
  - **Inspection** : Analyse le `git diff` et les fichiers modifiés par Cline.
  - **Revue critique** : Vérifie la robustesse, les fuites mémoires, les types, les null/undefined, et le respect des canons LBG (`AGENTS.md`, O1/O2/O3, pas de mutations LLM libres).
  - **Validation / CI** : Lance les tests automatiques (`ruff check`, `pytest backend/tests`, `tools/ci_godot_headless.sh`).
  - **Rapport** : Présente un résumé clair des modifications, des points de vigilance et de l'état des tests à l'utilisateur.

