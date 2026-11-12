# Agent Windows (Agent_IA)

Ce module contient le **worker Windows** (HTTP) exécuté sur le poste utilisateur.

## Chemin cible sur le PC Windows

Déploiement attendu : `C:\Agent_IA\`

## Démarrage

1) Copier le module sur Windows dans `C:\Agent_IA\`
2) Créer `C:\Agent_IA\desktop.env` (voir `desktop.env.example`)
3) Lancer **dans ta session bureau** (pas admin SYSTEM) :

```powershell
# Sans fenêtre (recommandé) — logs : C:\Agent_IA\logs\agent_ia*.log
powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\Agent_IA\start_agent.ps1

# Console visible (debug)
C:\Agent_IA\run_agent.cmd
```

Si l’agent tourne déjà sous **Système / Session 0** (apps ouvertes invisibles) :

```powershell
# Remède one-shot (Admin, session bureau) — tire scripts + main.py depuis le staging LAN :
irm http://192.168.0.100:8765/APPLY_SESSION0_FIX.ps1 | iex

# Ou en local si les fichiers sont déjà à jour dans C:\Agent_IA :
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Agent_IA\fix_session0_admin.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Agent_IA\install_fix_session0_task.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Agent_IA\fix_agent_to_user_session.ps1
```

Vérif LAN (doit afficher `session0_risk=False`, `listener_session_id` > 0) :

```bash
curl -sS -X POST http://192.168.0.10:5005/invoke \
  -H 'Content-Type: application/json' \
  -d '{"actor_id":"diag","text":"agent session status","context":{"desktop_action":{"kind":"agent_session_status"},"desktop_approval":"confirmed"}}'
```

**Compagnon** : avant tout `open_app`, si `session0_risk` → **auto `fix_session0`** puis retry (plus besoin de taper « répare session 0 » chaque matin).  
La tâche `LBG-AgentIA-fix-session0` a un trigger **AtLogOn** (délai 45 s) pour les postes éteints la nuit.  
**Important** : `fix_session0` **poll** le listener et renvoie `ok=false` / `session0_still` si `:5005` reste en Session 0. Log : `C:\Agent_IA\logs\fix_session0.log`.

Cause fréquente de régression : service Windows **`AgentLocalV0`** (`start_agent.bat` en SYSTEM) — à laisser **Disabled**.  
AGIR manuel « répare session 0 » reste dispo (Dry-run → Réel) si besoin de forcer.

Démarrage auto (logon) + redémarrage 08:00 / 20:00 — **toujours en compte utilisateur Interactive** :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Agent_IA\install_agent_ia_scheduled_tasks.ps1
```

- `start_agent.ps1` / `restart_agent.ps1` — arrière-plan, **sans** fenêtre cmd (pas de `cmd.exe`)
- `start_agent.vbs` / `restart_agent.vbs` — même chose **sans flash** (double-clic OK)
- `start_agent.cmd` / `restart_agent.cmd` — wrappers → VBS (quitte tout de suite)
- Refuse de démarrer depuis Session 0 ; remplace un listener hors session courante
- `run_agent.cmd` — **debug console uniquement** (fenêtre volontairement ouverte)

## Endpoints

- `GET /healthz`
- `POST /invoke` (utilisé par `LBG_AGENT_DESKTOP_URL`)
- `GET /capabilities`, `POST /execute`, `POST /install` (historique / expérimental — pas requis pour `desktop_control`)

## Config hot-reload

Le fichier `desktop.env` est relu automatiquement quand il change (pas besoin de relancer uvicorn).

## Computer Use (Windows) — MVP contrôlé

Le worker supporte 2 familles d’actions via `context.desktop_action` :

- **Actions “MVP”** (déjà en place) : `open_url`, `notepad_append`, `open_app`
- **Actions “Computer Use”** (vision + souris/clavier) : `observe_screen`, `click_xy`, `move_xy`, `drag_xy`, `type_text`, `hotkey`, `scroll`, `wait_ms`
- **Macro** : `run_steps` (exécute une liste d’étapes bornée)
- **ComfyUI (API)** : `comfyui_queue`, `comfyui_patch_and_queue`, `comfyui_history`, `comfyui_view`

### Sécurité (important)

- **Désactivé par défaut** : `LBG_DESKTOP_COMPUTER_USE_ENABLED=0`
- **Dry-run** recommandé au début : `LBG_DESKTOP_DRY_RUN=1`
- **Approval token** conseillé en prod : `LBG_DESKTOP_APPROVAL_TOKEN=...`
- **Observation protégée** (par défaut si token activé) : `LBG_DESKTOP_OBSERVE_REQUIRES_APPROVAL=1`
- **Audit JSONL** : `LBG_DESKTOP_AUDIT_LOG_PATH=C:\Agent_IA\desktop_audit.jsonl`
- **ComfyUI** : désactivé par défaut + approval requis (`LBG_DESKTOP_COMFYUI_ENABLED=0`)

### Exemples de payloads (`POST /invoke`)

#### 1) Observe (dry-run)

```json
{
  "actor_id": "ui:desktop",
  "text": "",
  "context": {
    "desktop_dry_run": true,
    "desktop_action": { "kind": "observe_screen" }
  }
}
```

#### 2) Observe réel (avec approval)

```json
{
  "actor_id": "ui:desktop",
  "text": "",
  "context": {
    "desktop_dry_run": false,
    "desktop_approval": "CHANGE-MOI",
    "desktop_action": { "kind": "observe_screen", "region": { "x": 0, "y": 0, "w": 1280, "h": 720 } }
  }
}
```

#### 3) Click + type (dry-run)

```json
{
  "actor_id": "ui:desktop",
  "text": "remplir un champ",
  "context": {
    "desktop_dry_run": true,
    "desktop_action": { "kind": "click_xy", "x": 640, "y": 360, "button": "left", "clicks": 1 }
  }
}
```

### Paramètres supportés (Computer Use)

#### A) Computer Use standard (pyautogui & coordonnées écran)
- `observe_screen`
  - `region` (optionnel) : `{x,y,w,h}`
  - retour contrôlé via `LBG_DESKTOP_SCREENSHOT_RETURN` :
    - `path` (défaut) : écrit dans `LBG_DESKTOP_SCREENSHOT_DIR` et renvoie le chemin
    - `base64` : renvoie aussi `base64` (coûteux)
    - `none` : n’expose pas l’image, audit uniquement
- `click_xy`
  - `x`, `y` (requis), `button` (`left|right|middle`), `clicks` (1..10), `interval_s`
- `move_xy`
  - `x`, `y` (requis), `duration_s` (0..10)
- `drag_xy`
  - `x1`,`y1`,`x2`,`y2` (requis), `duration_s`, `button`
- `type_text`
  - `text` (requis), `interval_s` (0..1), limite via `LBG_DESKTOP_TYPE_MAX_CHARS`
- `hotkey`
  - `keys` (requis) : `["ctrl","l"]`, `["ctrl","shift","i"]`, etc. (max 6)
- `scroll`
  - `clicks` (requis) : -2000..2000
- `wait_ms`
  - `ms` (requis) : 0..60000

#### B) Computer Use via `agent-desktop` (Vercel Labs — Arbre d'accessibilité natif)
> **Recommandé** : lit l'arborescence UI Automation / AT-SPI directement en JSON, sans capture d'écran et sans monopoliser la souris utilisateur.  
> Prérequis sur le poste : `npm i -g agent-desktop` (ou binaire GitHub).

- `ui_snapshot` (alias `desktop_snapshot`, `observe_ui`)
  - `app` (optionnel) : nom du processus / titre de fenêtre (ex: `"notepad"`, `"Slack"`)
  - `interactive` (bool, défaut `true`) : filtre uniquement les éléments interactifs (boutons, champs, liens)
  - `compact` (bool, défaut `true`) : élague les conteneurs superflus
  - `skeleton` (bool, défaut `false`) : vue macro structurelle
  - `root_ref` (optionnel) : sous-arbre ciblé à partir d'un `@ref`
  - *Retourne* : JSON avec `snapshot_id` et la liste des éléments et leurs `@ref` stables.
- `ui_click` (alias `desktop_click`)
  - `ref` (requis) : identifiant d'élément (ex: `"@s8f3k2p9:e3"`)
  - `button` (`left|right|middle`, défaut `"left"`)
  - `clicks` (1..n, défaut 1)
  - `headed` (bool, défaut `false`) : simule un clic matériel si l'application refuse l'accessibilité
- `ui_type` (alias `desktop_type`)
  - `ref` (requis) : identifiant du champ de saisie
  - `text` (requis) : chaîne de texte injectée de manière sécurisée via stdin
  - `headed` (bool, défaut `false`)
- `ui_press` (alias `desktop_press`)
  - `key` (requis) : touche ou raccourci (ex: `"Enter"`, `"Escape"`, `"Ctrl+s"`)
- `ui_scroll` (alias `desktop_scroll`)
  - `ref` (optionnel) : conteneur à faire défiler
  - `direction` (`up|down|left|right`, défaut `"down"`)
  - `amount` (nombre de crans, défaut 3)
- `ui_focus` (alias `desktop_focus`)
  - `ref` (requis) : identifiant de l'élément à focaliser

### ComfyUI (API locale)

Ces actions appellent l’API ComfyUI (typiquement `http://127.0.0.1:8188`) depuis le worker Windows.
Elles sont protégées par :
- `LBG_DESKTOP_COMFYUI_ENABLED=1`
- `context.desktop_approval` (approval token)

Actions :
- `comfyui_queue` : envoie un workflow “API export” (payload `prompt`)
  - `workflow` (requis, objet JSON)
  - `client_id` (optionnel)
- `comfyui_patch_and_queue` : applique un patch simple puis queue
  - `workflow` (requis)
  - `ops` (requis) : liste d’opérations :
    - `set_input`: `{op:"set_input", node:"205", key:"seed", value:123}`
    - `set_inputs`: `{op:"set_inputs", node:"205", values:{...}}`
  - `client_id` (optionnel)
- `comfyui_history`
  - `prompt_id` (requis)
- `comfyui_view` : récupère un fichier depuis `/view`
  - `filename` (requis), `subfolder` (optionnel), `type` (optionnel, défaut `output`)
  - `return` : `path|base64|none` (défaut `path`) ; écrit dans `LBG_COMFYUI_DOWNLOAD_DIR` si `path`
- `comfyui_status` : probe `GET /system_stats` (pas d’approval)
- `comfyui_ensure` : démarre ComfyUI s’il est down (hidden, **sans HITL**) — défaut root `C:\Users\sdesh\ComfyUI`, args `--listen 0.0.0.0 --port 8188 --lowvram`
- `comfyui_restart` : stop process `:8188` puis relance (**approval**)

`desktop.env` : `LBG_COMFYUI_ROOT`, `LBG_COMFYUI_PYTHON`, `LBG_COMFYUI_ARGS`, `LBG_COMFYUI_AUTO_ENSURE=1` (ensure automatique avant `comfyui_queue` / brief Pygmalion si down).

### ComfyUI — démarrage sans fenêtre

Comme Agent_IA, ComfyUI peut tourner en arrière-plan (logs fichier, pas de cmd au premier plan) :

```powershell
# Recommandé — logs : C:\Agent_IA\logs\comfyui_agent.log
powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\Agent_IA\start_comfyui.ps1

# Console visible (debug)
C:\Agent_IA\run_comfyui.cmd
```

- `start_comfyui.ps1` / `restart_comfyui.ps1` — arrière-plan
- `start_comfyui.cmd` / `restart_comfyui.cmd` — wrappers vers les `.ps1`
- `comfyui_ensure` / `comfyui_restart` (via `/invoke`) appellent le même lanceur hidden

### `run_steps` (macro)

Exécute une séquence bornée d’actions (utile côté orchestrateur : un seul appel).

- entrée :
  - `steps` : liste d’objets `{kind: "...", ...}` (les mêmes champs que les actions unitaires)
  - `stop_on_fail` (optionnel, défaut `true`) : si `false`, continue même si une étape échoue
- limites :
  - `LBG_DESKTOP_RUN_STEPS_MAX` (défaut 12)
  - `LBG_DESKTOP_RUN_STEPS_TIMEOUT_MS` (défaut 30000)
- audit :
  - un résumé `event: agents.desktop.audit` (kind=`run_steps`)
  - des sous-événements `event: agents.desktop.step` (un par étape)
- sortie :
  - `step_outputs[]` : sorties détaillées par étape (ex. screenshot `path/mime/bytes`)
  - `errors[]` : erreurs collectées (surtout utile quand `stop_on_fail=false`)

Exemple :

```json
{
  "desktop_action": {
    "kind": "run_steps",
    "steps": [
      { "kind": "open_url", "url": "https://example.org" },
      { "kind": "wait_ms", "ms": 800 },
      { "kind": "observe_screen" }
    ]
  }
}
```

## `import_face_parts`

Opt-in. Sync aussi `face_parts_import_action.py` vers `C:\Agent_IA\`.

```json
{
  "desktop_action": {
    "kind": "import_face_parts",
    "character_id": "lyra_assistant",
    "deploy": false
  }
}
```

`desktop.env` : `LBG_DESKTOP_FACE_PARTS_ENABLED=1` + `LBG_DESKTOP_FACE_PARTS_INBOX` (dossier Expressions / Gemini).

