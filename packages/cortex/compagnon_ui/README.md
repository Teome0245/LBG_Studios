# LBG Compagnon UI — chat produit (:5174)

Sources extraites de `_archive/LBG_IA/orchestrateur/frontend` (2026-09-16).  
**Surface canon Compagnon** : http://192.168.0.100:5174/  
Cadrage : [`docs/FOCUS_COMPAGNON.md`](../../../../docs/FOCUS_COMPAGNON.md).

## Dev local

```bash
cd packages/cortex/compagnon_ui
cp .env.example .env   # VITE_API_BASE_URL=http://192.168.0.100:3000 pour LAN
npm install
npm run dev            # http://127.0.0.1:5175 (proxy → API)
```

## Deploy LAN (.100)

```bash
bash packages/cortex/infra/scripts/deploy_compagnon_100.sh
bash packages/cortex/infra/scripts/deploy_compagnon_100.sh --smoke
```

Sync → `/opt/orchestrateur/frontend/` + overlay profils `router_prompts.py` → rebuild Docker `frontend` (+ backend si overlay).

## Poste `.10` (D1 — raccourci)

Voir [`desktop/README.md`](desktop/README.md) :

```powershell
powershell -ExecutionPolicy Bypass -File .\desktop\Install-CompagnonShortcut.ps1
```

Fenêtre app Edge/Chrome (`--app=`) vers `:5174` — épingler à la barre des tâches.

## Suite D2 / D8

App Electron (tray + FaceRig) : `packages/compagnon-desktop`.  
Bridge avatar SSE (VRM / Mate Engine) : [`avatar_presence_events_v1.md`](../docs/avatar_presence_events_v1.md).

## Persona

Profils envoyés à `POST /ask` : `compagnon` (défaut), `jarvis`, `mother`, `kit`, `hal`, …
Côté API Orch : overlay `server_overlay/router_prompts.py` (greffe sur le backend `.100`).

## Vision (analyse d'images)

Joindre ou coller une image dans le chat → `POST /api/pilot/vision-ask` (Cortex Pilot `.140`) → Ollama `.110` (`LBG_VISION_LLM_MODEL`, défaut `llava:latest`). Max 3 images, 4 Mo chacune. Le 27B abliterated reste dispo en override mais est trop lent pour la vision CPU.

## Chat LLM (routage local)

Overlay `server_overlay/routing.json` + `local_llm_provider.py` : priorise Ollama `.110`
(`gemma4:e2b` fast/balanced, `huihui_ai/Qwen3.8-abliterated:27b` smart). Groq `gpt-oss-20b` reste en fallback cloud.

## Desktop + bulles SSE (notes ops)

- **Session 0** (`.10`) : overlay `desktop_dispatch` auto-`fix_session0` puis retry `open_app` ; tâche Windows **AtLogOn** pour les reboots nocturnes. Remède one-shot Admin → `APPLY_SESSION0_FIX.ps1` (voir `windows_agent/Agent_IA/README.md`).
- **Bulles vides** : `useChat.finishStream` / `sse_ask` forcent un contenu de secours ; `ChatFlow` ne peint plus une carte glass vide ; activité → Échec si réponse vraiment vide.
