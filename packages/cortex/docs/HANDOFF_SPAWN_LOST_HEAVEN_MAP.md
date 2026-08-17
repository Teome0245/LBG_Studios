# Handoff spawn — Lost Heaven / carte / PNJ serveur

> Lot **one-shot**. Pas un preset Pilot.

## Contexte

- Client : `packages/prime-client` (runtime 140 : `/opt/new_mmo/prime-client`)
- Gateway : `192.168.0.246` — HTTP `:8765`, WS `:50000`
- Lost Heaven : sortie sud OK, carte retail + triangles PNJ serveur (cyan) branchés côté client

## Enchaînement Dry-run → Contrôle → Réel (Element)

| Étape | Commande | Effet |
|-------|----------|--------|
| **0 — Aperçu** | `.../spawn_team_lost_heaven_map.sh --dry-run` | Affiche les objectifs, **sans** orchestrateur |
| **1 — Dry** | `... --phase=dry --notify-element` | Tâches équipe avec `devops_dry_run`, sondes, pas d’effet serveur |
| **2 — Contrôle** | `... --phase=control --notify-element` | Tâche **Argus** : compte rendu `go/no-go`, supervisor + curl 246 |
| **3 — Réel** | `... --phase=real --notify-element` | `ops` + `dev_game` en **L2** ; Godot/QA exécutés ; DevOps réel si token OK |

**Tout d’un coup** (dry → contrôle → réel, création L2 sans auto-run réel) :

```bash
bash LBG_IA_MMORPG/LBG_IA_MMO/infra/scripts/spawn_team_lost_heaven_map.sh --phase=all --notify-element
```

État des runs : `LBG_TEAM_SPAWN_STATE` (défaut `/tmp/lbg_spawn_lh_state.json`).

### Compte rendu Element

- **`--notify-element`** : message synthèse phase dans la salle **LBG Pilot LAN** + passage du watchdog `matrix_notify` (✅ Terminé / 🔔 L2 / ❌ Échec).
- Prérequis Matrix (core **140** ou poste avec secrets) : `LBG_MATRIX_*`, `LBG_P03_BACKEND_URL`, `LBG_PILOT_API_TOKEN` — voir ADR 0018, `LBG_Project_03/lbg_agents/matrix_notify.py`.
- Commandes salle : `pending`, `task <id>`, **`valider <id>`** (phase réel ops/dev_game), `status`.

Pilot **`#/team`** = détail ; Element = suivi mobile.

### Phase réelle — L2

- `ops` et `dev_game` sont créés avec `approval_required=true` (pas de run auto sauf `LBG_TEAM_SPAWN_AUTO_RUN_REAL=1` + `LBG_TEAM_APPROVAL_TOKEN`).
- Sur 140, **`LBG_DEVOPS_DRY_RUN=0`** peut être nécessaire pour que le contexte `devops_dry_run: false` soit effectif.

### Spawn CODE (docs + deliverables)

```bash
bash LBG_IA_MMORPG/LBG_IA_MMO/infra/scripts/spawn_team_lost_heaven_code.sh --dry-run
bash .../spawn_team_lost_heaven_code.sh
```

Workflow orchestrateur : `orchestrator/team/lost_heaven_code_workflow.py` (`write_files=1`).

### Pipeline complet depuis WSL → VM 140 (Element)

```bash
bash LBG_IA_MMORPG/LBG_IA_MMO/infra/scripts/run_lost_heaven_pipeline_ssh_140.sh
```

En fin de run : **rsync auto** `140:/opt/new_mmo/prime-client/docs/` → WSL `new_mmo/prime-client/docs/` (désactiver : `LBG_LH_SYNC_DOCS_BACK=0`). Avant sync, backup des `*.md` locaux dans `docs/.lh_sync_backup_<ts>/`.

Sur **140** directement :

```bash
bash /opt/LBG_IA_MMO/infra/scripts/spawn_team_lost_heaven_full_pipeline_140.sh
```

État dry ids : `LBG_TEAM_SPAWN_STATE=/var/lib/lbg/spawn_lh_state.json` (évite « aucun id dry enregistré » en contrôle).

## Lancer (simple)

```bash
bash LBG_IA_MMORPG/LBG_IA_MMO/infra/scripts/spawn_team_lost_heaven_map.sh --dry-run
bash .../spawn_team_lost_heaven_map.sh --phase=dry --notify-element
bash .../spawn_team_lost_heaven_map.sh --phase=control --notify-element
bash .../spawn_team_lost_heaven_map.sh --phase=real --notify-element
bash .../spawn_team_lost_heaven_map.sh --only=ops,dev_game --phase=real
bash .../spawn_team_lost_heaven_map.sh --list-phases
```

**Prérequis** : `LBG_ORCHESTRATOR_URL` (défaut `http://192.168.0.140:8010`).

Variables : `LBG_PRIME_CLIENT_ROOT`, `LBG_PRIME_VM`, `LBG_GATEWAY_HTTP`, `LBG_PROJECT_03_ROOT`.

## Rôles

| Rôle | Focus |
|------|--------|
| ops | Déploiement gateway 246 + healthz + npcs_near |
| dev_game | Spawns PNJ LH sur Core3 |
| dev_godot (Hermès) | Export PNJ, Launchpad/WSL |
| dev_godot (Iris) | Retail layout, doc carte |
| qa | Smoke E2E LH + API (+ tâche **contrôle** dédiée en `--phase=control`) |
| dev_godot (habillage) | Sprites / habillage_lost_heaven |

## Clôture tâche

`deliverables[]`, `blockers[]`, `status` dans l’output orchestrateur → push Element via `matrix_notify`.
