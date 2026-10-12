# Sans Cursor — éditeur + Compagnon LBG

**Date** : 2026-09-23  
**But** : coder et piloter le studio **sans** Cursor IDE — avec **Compagnon**, la **Team** et Cline sur **`.143`**.

Boucle complète : [`ecosystem_dev_143.md`](ecosystem_dev_143.md).

---

## 0. Qui développe

| Acteur | Sur `.143` / lab |
|--------|------------------|
| **Compagnon** | Propose Agir · ouvre VS Code/Cline · initiatives Self |
| **Team** | Plans / tâches L1 · smokes · leçons (Pilot `#/team`) |
| **Humain** | L2, intention, review |
| **Cline** | Plan 9b / Act 12b sur le monorepo |

---

## 1. Éditeur (VS Code + Continue + Cline)

Déjà sur le poste `.10` :

| Outil | Rôle | Config |
|-------|------|--------|
| **VS Code** | IDE | Microsoft VS Code |
| **Continue** | chat / edit / autocomplete | `%USERPROFILE%\.continue\config.yaml` → matrice 110/111 |
| **Cline** | agent Plan/Act (proche Cursor Agent) | extension `saoudrizwan.claude-dev` |

### Cline (une fois)

Sur **`.10` (Windows)** *ou* **`.143` (Omarchy Hyprland)** — même matrice Ollama :

1. Ouvrir VS Code → Extensions → **Cline** (installé).
2. Settings Cline → API Provider **Ollama** :
   - **Act** : Base `http://192.168.0.110:11434` · Model `huihui_ai/gemma-4-abliterated:12b` (ou `:e2b` si interactif)
   - **Plan** : Base `http://192.168.0.110:11434` · Model `huihui_ai/qwen3.5-abliterated:9b` (triage only : `.111` `2B` / `0.8B`)
3. Features → **Preferred Language: Français** · **Use Compact Prompt** ON · **Plan/Act separate models** ON.
4. Snippets JSON : `packages/cortex/docs/cline/providers.*.json` · smoke `docs/cline/SMOKE.md`.

Install automatisé :
- Windows `.10` : `infra/scripts/install_editor_alt_windows.ps1`
- Omarchy `.143` : `bash infra/scripts/install_editor_alt_omarchy_143.sh` (depuis le LAN)

### Continue

Recharger la fenêtre VS Code après `config.yaml` (modèles LBG Act / Plan / Forge).  
Choisir **LBG Act 12b** pour le chat code ; autocomplete = **0.8B** sur `.111`.

---

## 2. Compagnon (ops / AGIR — sans éditeur)

| Surface | URL |
|---------|-----|
| Compagnon | http://192.168.0.100:5174/ |
| Pilot | http://192.168.0.140:8080/pilot/ |

Actions utiles (jeton desktop auto-sync LAN) :

- `regarde mes mails récents` → IMAP
- `fais mon brief du matin` → brief Self / proactive / infra (RO)
- `ouvre vghd sur mon pc` → `.10`
- `ouvre chromium sur omarchy` → `.143` Hyprland
- `ouvre code sur omarchy` → VS Code + Cline
- `mets à jour vscode sur omarchy` → dry-run puis confirm (**pas** pendant Cline critique)
- `vérifie la session sur omarchy` / `répare session 0…` → heal agent

Deploy / smoke MAJ éditeur (écosystème) :

```bash
bash packages/cortex/infra/scripts/deploy_update_vscode_ecosystem.sh
bash packages/cortex/infra/scripts/smoke_update_vscode_143.sh
```

Prérequis Windows une fois (déjà fait si tâches présentes) :

```powershell
Get-ScheduledTask -TaskName 'LBG-AgentIA-*'
# Si Agent_IA en Session 0 (apps invisibles) — Admin session bureau :
irm http://192.168.0.100:8765/APPLY_SESSION0_FIX.ps1 | iex
# Ou si fichiers déjà à jour :
powershell -File C:\Agent_IA\install_fix_session0_task.ps1   # Admin
```

Détail Session 0 / `open_app` : `packages/cortex/windows_agent/Agent_IA/README.md` · `docs/desktop_hybride.md`.

---

## 3. Smoke rapide

```bash
# Ollama
curl -sS http://192.168.0.110:11434/api/tags | head
curl -sS http://192.168.0.111:11434/api/tags | head
# Compagnon / agents
curl -fsS http://192.168.0.100:5174/ >/dev/null && echo OK_compagnon
curl -fsS http://192.168.0.10:5005/healthz | head -c 200; echo
curl -fsS http://192.168.0.143:5005/healthz | head -c 200; echo
```

Détail éditeur : `cline_local_llm.md` · matrice : `local_llm_route_matrix.md`.
