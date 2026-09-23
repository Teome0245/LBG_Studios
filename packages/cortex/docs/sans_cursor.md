# Sans Cursor — éditeur + Compagnon LBG

**Date** : 2026-09-21  
**But** : coder et piloter le studio **sans** Cursor IDE.

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
- `ouvre vghd sur mon pc` → `.10`
- `ouvre chromium sur omarchy` → `.143` Hyprland
- `vérifie la session sur omarchy` / `répare session 0…` → heal agent

Prérequis Windows une fois (déjà fait si tâches présentes) :

```powershell
Get-ScheduledTask -TaskName 'LBG-AgentIA-*'
# Si fix-session0 absente :
powershell -File C:\Agent_IA\install_fix_session0_task.ps1   # Admin
```

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
