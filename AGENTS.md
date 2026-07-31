# AGENTS.md — LBG Studios

Réponses en français (voir `CLAUDE.md`). Priorité **O1 Studio** (`packages/cortex`) puis **O2 Jeu** (`packages/prime-client`). Ne pas réintroduire le legacy `/mmo/`, `mmo_server`, `mmmorpg_server`, `web_client`.

## Cursor Cloud specific instructions

Le script d'update (au démarrage du VM) crée `packages/cortex/.venv` et installe les 3 packages Python en editable (`backend`, `orchestrator`, `agents`). Toolchain préinstallé : Python 3.12, Node 22. Pas de `uv`, pas de binaire Godot.

### Produit O1 exécutable : Cortex (backend + Pilot UI)

- **Backend API** (FastAPI, port **8000**) : sert aussi l'UI **Pilot** en statique sous `http://127.0.0.1:8000/pilot/`. C'est le produit O1 démontrable de bout en bout dans cet environnement.
- Lancement (activer d'abord `source packages/cortex/.venv/bin/activate`) :
  - `cd packages/cortex/backend && LBG_ORCHESTRATOR_URL=http://127.0.0.1:8010 uvicorn main:app --host 0.0.0.0 --port 8000`
- Commandes de run/smoke standard : voir `packages/cortex/pilot_web/README.md` (§ Commandes) — ne pas dupliquer ici.

### Gotchas non évidents

- **Lancer les services depuis le dossier du package**, pas depuis `packages/cortex`. Les imports sont *plats* (`from api...`, `from router...`, `from shared_registry`), donc `cd backend && uvicorn main:app` (comme systemd), **pas** `uvicorn backend.main:app` (échoue : `ModuleNotFoundError`). Idem pour l'orchestrateur (`cd orchestrator && uvicorn main:app`).
- **L'orchestrateur (port 8010) ne démarre PAS tel quel dans ce monorepo.** `orchestrator/services/proactive.py` et `orchestrator/lbg_sa/memory_store.py` importent `hybrid_proactive_agent`, un package **legacy jamais extrait** ici (absent du repo, absent de PyPI). `uvicorn main:app` de l'orchestrateur échoue donc en `ModuleNotFoundError: No module named 'hybrid_proactive_agent'`. Le backend fonctionne **seul** ; les endpoints qui proxifient l'orchestrateur (`/v1/pilot/route`, `/capabilities`, `/action-proposal`, …) renvoient une erreur *gracieuse* (`/v1/pilot/status` → `"orchestrator":"error"`). Les endpoints backend autonomes (ex. `/healthz`, `/v1/pilot/assistant/session-summary/export` et `.../mmo-bridge`) fonctionnent sans orchestrateur.
- **Tests** : rootdir = `packages/cortex` (`pytest.ini`). Depuis le venv : `python -m pytest backend/tests` → **64/64 verts**. La suite globale (`python -m pytest --continue-on-collection-errors`) montre de nombreux échecs/erreurs de collecte dans `orchestrator/tests` et `agents/tests` : ils dépendent des modules/données legacy absents (`hybrid_proactive_agent`, `mmo_server`, `mmmorpg_server`, catalogues core3). **C'est attendu**, pas une régression introduite par le setup.
- **Pas de linter configuré** (aucun `ruff`/`flake8`/`black`/`mypy`). La porte qualité du repo est **pytest**.

### O2 (hors périmètre exécutable ici)

- `packages/prime-client` : projet **Godot 4.6** (pas de binaire Godot dans le VM, GUI requise) + serveur de jeu « 246 » externe. Voir `packages/prime-client/SMOKE.md`.
- `packages/launchpad` : lanceur **Electron** (cibles de build Windows uniquement). Si besoin : `cd packages/launchpad && npm install && npm start` (nécessite une GUI + serveur 246). Non inclus dans le script d'update (lourd, hors O1).
