# Pont Cloud ↔ Local (WSL / LAN)

**Date** : 2026-08-12  
**Statut** : mix des 3 approches (pull WSL + push linux_agent + pipeline Cloud→LAN)

Le **Cursor Cloud Agent** tourne sur un VM isolé (pas d’accès `192.168.0.x`).  
L’**infra LBG** vit sur le LAN (`.140`, `.246`, WSL Teome). Ce document décrit comment relier les deux sans exposer le LAN sur Internet.

---

## Vue d’ensemble

```
┌─────────────────────┐     PR / code      ┌──────────────────────┐
│ Cursor Cloud Agent  │ ─────────────────► │ GitHub (allowlist)   │
└─────────┬───────────┘                    └──────────────────────┘
          │ intent cursor: / Team
          ▼
┌─────────────────────┐   file WSL (pull)   ┌──────────────────────┐
│ Orchestrateur .140  │ ◄────────────────── │ WSL executor (poste) │
│ Team + OpenClaw     │                     │ lbg_wsl_executor.sh  │
└─────────┬───────────┘                     └──────────┬───────────┘
          │ skills :18790 (VM)                        │ SSH / smokes
          ▼                                             ▼
┌─────────────────────┐                     ┌──────────────────────┐
│ OpenClaw bridge     │                     │ Prime .246 / diag    │
│ (sur .140)          │                     │ depuis WSL           │
└─────────────────────┘                     └──────────────────────┘

Option push (linux_agent sur WSL) :
  .140 ──HTTP──► WSL:6001/linux_agent (desktop_action / futur run_skill)
```

| Couche | Rôle | Où ça tourne |
|--------|------|----------------|
| **Cloud** | Code, PR, refactor multi-fichiers | VM Cursor |
| **Orchestrateur** | Team, missions, routage | `.140:8010` |
| **Pull WSL** | Smokes / diag LAN depuis le poste | WSL Ubuntu Teome |
| **OpenClaw :18790** | Skills bash sur la VM core | `.140` loopback |
| **linux_agent push** | Actions poste (fichiers, apps) | WSL ou Windows |

---

## 1. Pull WSL (recommandé — implémenté)

### API Team (orchestrateur)

| Méthode | Route | Rôle |
|---------|-------|------|
| `GET` | `/v1/team/wsl/health` | Santé + allowlist skills |
| `POST` | `/v1/team/wsl/tasks` | Enqueue une tâche WSL |
| `POST` | `/v1/team/wsl/poll` | Claim atomique `queued → running` |
| `POST` | `/v1/team/wsl/tasks/{id}/complete` | Rapport `done` / `failed` |

Auth optionnelle : header `X-LBG-WSL-TOKEN` si `LBG_WSL_EXECUTOR_TOKEN` est défini sur `.140`.

### Skills allowlistés

| `wsl_skill` | Script |
|-------------|--------|
| `diag_godot_supervisor` | `infra/scripts/diag_godot_supervisor_wsl.sh` |
| `smoke_godot_m11_login` | `infra/scripts/smoke_godot_m11_login_lan.sh` |
| `smoke_godot_m12_ws` | `infra/scripts/smoke_godot_m12_ws_lan.sh` |
| `smoke_godot_owners` | `infra/scripts/smoke_godot_owners.sh` |
| `smoke_lan_surfaces` | `tools/smoke_lan_surfaces.sh` |
| `smoke_cursor_agent` | `infra/scripts/smoke_cursor_agent_lan.sh` |

### Depuis WSL

```bash
cd ~/projects/LBG_Studios/packages/cortex

# une passe
bash infra/scripts/lbg_wsl_executor.sh --once

# daemon (poll 30s)
bash infra/scripts/lbg_wsl_executor.sh --loop

# enqueue manuel
bash infra/scripts/lbg_wsl_executor.sh --enqueue diag_godot_supervisor "Diag post-merge O2"

# diag direct (sans file Team)
bash infra/scripts/diag_godot_supervisor_wsl.sh
```

### Enqueue depuis l’orchestrateur / Cloud follow-up

```bash
curl -s -X POST http://192.168.0.140:8010/v1/team/wsl/tasks \
  -H 'Content-Type: application/json' \
  -H "X-LBG-WSL-TOKEN: ${LBG_WSL_EXECUTOR_TOKEN}" \
  -d '{
    "wsl_skill": "smoke_godot_owners",
    "objective": "Smoke O2 après PR Cursor",
    "actor_id": "cursor:followup"
  }'
```

Puis l’executor WSL en `--loop` sur le poste Teome consomme la tâche.

### Déploiement `.140`

```bash
# Depuis le monorepo (WSL)
bash tools/deploy_wsl_bridge_140.sh
# optionnel : LBG_WSL_EXECUTOR_TOKEN='secret' bash tools/deploy_wsl_bridge_140.sh
```

Smoke :

```bash
bash packages/cortex/infra/scripts/smoke_wsl_executor_lan.sh
```

---

## 2. Push linux_agent (complément desktop)

Pour des actions **sur le poste** (fichiers, apps, navigateur) sans poll :

```bash
# WSL — worker Linux
cd packages/cortex/linux_agent/Agent_IA
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 6001
```

Sur `.140` (si WSL joignable depuis le LAN) :

```bash
LBG_AGENT_LINUX_URL=http://<ip-wsl>:6001
```

Flux identique au **desktop hybride Windows** : `POST /v1/pilot/route` → `agent.desktop` → worker HTTP.  
Voir [`desktop_hybride.md`](desktop_hybride.md).

**Limite** : IP WSL stable + routage `.140` → poste. Le pull WSL évite ce problème.

---

## 3. Pipeline Cloud → LAN (bout-en-bout)

Séquence cible après une mission `cursor:` :

1. **Cloud** : PR sur `Teome0245/LBG_Studios` (allowlist).
2. **Team** : tâche `dev_game` ou merge manuel + deploy `.140`.
3. **Enqueue WSL** : `POST /v1/team/wsl/tasks` avec `smoke_godot_owners` ou `diag_godot_supervisor`.
4. **WSL executor** : exécute, `complete` → mission Campus peut clôturer si QA verte.
5. **OpenClaw** (sur `.140`) : skills ops qui n’ont pas besoin du poste (sync VM, healthz local).

Exemple mission Orch :

```text
team: mission Smoke O2 après changement client — enqueue wsl smoke_godot_owners puis brief PM
```

(Le plan heuristique QA + enqueue WSL explicite via API reste le chemin fiable aujourd’hui.)

---

## 4. OpenClaw sur `.140` (EXEC VM — déjà en place)

- Bridge HTTP : `http://127.0.0.1:18790` (`lbg_skill_bridge.py`)
- Consommé par `team/openclaw_adapter.py` (Héphaïstos, Argus)
- **Ne remplace pas** le WSL executor : pas d’SSH vers `.246` depuis le poste opérateur pour certains diag

---

## 5. CT Proxmox `lbg-executor` (remplace WSL `.10`)

Sur un CT Debian (ex. `.141`) :

```bash
# Création CT Proxmox (R720, CTID=141) + bootstrap user lbg
bash packages/cortex/infra/scripts/create_lbg_executor_ct_proxmox.sh

# Install executor (rsync scripts + systemd)
LBG_EXECUTOR_HOST=192.168.0.141 bash packages/cortex/infra/scripts/install_lbg_executor_ct.sh --remote

# Ou sur la cible après clone/rsync monorepo dans /opt/LBG_IA_MMO
sudo bash infra/scripts/install_lbg_executor_ct.sh
```

Unité : `lbg-lan-executor.service` — poll `lbg_wsl_executor.sh --loop`.

Le poste **`.10`** ne sert plus qu'à ComfyUI + pilotage humain.

---

## Sync GitHub → infra

| Cible | Méthode actuelle |
|-------|------------------|
| `.140` `/opt/LBG_IA_MMO` | **rsync** (`tools/deploy_wsl_bridge_140.sh`, `tools/deploy_infra_fixes_140.sh`) — pas de clone git |
| GitHub | Source de vérité — `commit` + `push` depuis poste dev, puis deploy script |

Workflow recommandé :

```bash
git add … && git commit -m "…" && git push
bash tools/deploy_infra_fixes_140.sh
```

Pour migrer `.140` vers `git pull` : initialiser clone une fois sur la VM, puis remplacer rsync par `git pull` dans les scripts deploy (hors scope immédiat).

---

## Garde-fous

| Risque | Mitigation |
|--------|------------|
| Exposer le LAN | Pas de tunnel entrant ; **pull** WSL uniquement |
| Exécution arbitraire | Allowlist `wsl_skill` côté API + scripts |
| Token volé | `LBG_WSL_EXECUTOR_TOKEN` + LAN seulement |
| Double exécution | Claim atomique SQLite `queued → running` |
| Cloud ≠ LAN | Cloud = code ; WSL = smokes/diag ; ne pas mélanger |

---

## Fichiers

| Fichier | Rôle |
|---------|------|
| `orchestrator/team/wsl_executor.py` | Logique file WSL |
| `orchestrator/router/routes/team.py` | Routes `/v1/team/wsl/*` |
| `infra/scripts/lbg_wsl_executor.sh` | Daemon / CLI pull |
| `infra/scripts/diag_godot_supervisor_wsl.sh` | Diag Godot via SSH `.140` |
| `infra/openclaw/lbg_skill_bridge.py` | EXEC sur VM |
| `linux_agent/Agent_IA/` | Push desktop Linux |

---

## Voir aussi

- [`plan_cursor_cloud_agent.md`](plan_cursor_cloud_agent.md) — Cloud Agent (PR)
- [`desktop_hybride.md`](desktop_hybride.md) — worker Windows/Linux
- [`architecture_tri_backend_hybride.md`](architecture_tri_backend_hybride.md) — REASON / EXEC / MEDIA
- [`SMOKE_LAN.md`](../../docs/SMOKE_LAN.md) — surfaces jeu
