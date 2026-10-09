---
trigger: always_on
description: Canon LBG Studios — O1 Studio puis O2 Jeu, runtime hub Godot, legacy hors features
---

# LBG Studios (Antigravity)

- Source de vérité : ce dépôt — `OBJECTIVES.md`, `docs/REGISTRE.md`, `docs/PRIORITES_ACTUELLES.md`, `docs/SESSION_EN_COURS.md`.
- Priorité : **O1 Studio** (`packages/cortex`) puis **O2 Jeu**.
- **O2 runtime (G5, 2026-10-07)** : autorité joueur = `packages/prime-hub` Godot sur `.246:8787` (HTTP+WS). Client = `packages/prime-client` + Launchpad ≥2.1.4. Ops : `docs/RUNTIME_GODOT.md`.
- **Interdit chemin joueur** : Core3, gateway `:8765`/`:50000`, spike Python `hub_runtime` — **OFF** (`packages/cortex/infra/scripts/stop_core3_and_spike_246.sh`).
- Feature Studio → `packages/cortex`. Feature jeu → `prime-client` / `prime-hub` (pas Core3, pas spike).
- Ne pas réintroduire le client web legacy `/mmo/` ni `mmo_server` / `mmmorpg_server`.
- Repos `LBG_IA_MMORPG` et `new_mmo` = upstream legacy (lecture / sync), pas cible de nouvelles features.
- Réponses en **français** sauf demande contraire. Réponses courtes ; lire les docs canons avant d’explorer au hasard.
