# AGENTS.md — LBG Studios

Monorepo LBG Studios. Priorité : **O1 Studio** (`packages/cortex`) puis **O2 Jeu** (`packages/prime-client`).
Voir `README.md`, `OBJECTIVES.md`, `docs/REGISTRE.md`. Réponses en français sauf demande contraire.

## Cursor Cloud specific instructions

### Périmètre exécutable dans ce monorepo

Ce dépôt est une **extraction chirurgicale** du legacy `LBG_IA_MMORPG` : certains packages upstream ont été
**volontairement gelés / non importés** (`hybrid_proactive_agent`, `companion_bot`, `mmo_server`, `mmmorpg_server`).
Conséquences concrètes pour le développement local :

- **`packages/cortex/backend` + `pilot_web` = l'application runnable** (point d'entrée Studio documenté).
  Le backend sert le Pilot UI sur `/pilot/` et n'appelle l'orchestrateur qu'en **HTTP** (dégradation propre si absent).
- **`packages/cortex/orchestrator` NE DÉMARRE PAS ici** : `orchestrator/main.py` importe `services/proactive.py` qui fait
  un `import hybrid_proactive_agent` **au chargement** (idem `orchestrator/lbg_sa/memory_store.py`). Ce package legacy
  n'est pas dans le monorepo (gelé, cf. `docs/REGISTRE.md`), donc l'orchestrateur et les endpoints Pilot qui le proxient
  (chat/route, capabilities, jobs, team…) renvoient une erreur tant qu'il n'est pas fourni. Ne pas réintroduire le legacy.
- **`packages/prime-client`** (client Godot 4.6) et **`packages/launchpad`** (launcher Electron, cible Windows) sont
  **hors périmètre E2E ici** : prime-client nécessite le serveur « Prime » externe `192.168.0.246` ; launchpad se build sous Windows.

### Environnement Python (Cortex)

- venv unique : `packages/cortex/.venv` (gitignoré). Activer : `source packages/cortex/.venv/bin/activate`.
- Les 3 packages sont installés en **editable** (`pip install -e ...[dev]`) par le script de mise à jour du VM.
  L'editable install = **hot-reload** direct des sources ; pas besoin de réinstaller après un changement de code Python
  (redémarrer uvicorn suffit). Réinstaller uniquement si les `dependencies` d'un `pyproject.toml` changent.

### Lancer l'application (backend + Pilot UI)

Depuis `packages/cortex`, venv activé :

```bash
export LBG_ORCHESTRATOR_URL="http://127.0.0.1:8010"   # optionnel ; l'orchestrateur n'est pas runnable ici
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Puis : `http://127.0.0.1:8000/pilot/` (UI), `GET /healthz`, `GET /v1/pilot/status` (santé agrégée, calcul serveur).
`GET /v1/pilot/status` affiche normalement `backend: ok` et `orchestrator: error` (attendu, cf. ci-dessus) en Cloud ;
sur LAN 140, orchestrator + agents sont en général **ok**.

Smoke surfaces LAN (Pilot 140, Cockpit/Orch `.100`, Core3 `:8792`) :
`bash tools/smoke_lan_surfaces.sh --functional` — voir `docs/SMOKE_LAN.md`.

### Tests

Lancer **par package** (le venv doit être activé). NE PAS lancer `pytest` à la racine `packages/cortex` :
les suites `backend` / `orchestrator` partagent des noms de modules top-level (`api`, `services`, `models`, `router`)
→ collisions d'import en mode `importlib`, et `conftest.py` référence des packages legacy absents.

- Backend (référence, tout vert) : `cd packages/cortex && python -m pytest backend/tests` → **64 passent**.
- Agents (lib support) : `python -m pytest agents/tests`. Une partie échoue car des **catalogues de données de jeu
  legacy** (Core3 / world content / perform ids) ne sont pas dans le repo (`.gitignore` exclut les assets lourds) — ce
  sont des dépendances de données manquantes, pas un souci d'environnement.
- Orchestrator : non collectable (mêmes imports legacy manquants que ci-dessus).

### Lint

Aucun linter n'est configuré dans le dépôt (pas de ruff/flake8/mypy/black, pas de pre-commit ; seul
`packages/cortex/infra/ci/test_pytest.sh` existe et suppose les packages legacy). Vérif syntaxe rapide :
`python -m compileall backend`.
