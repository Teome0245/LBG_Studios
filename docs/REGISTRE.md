# Registre LBG Studios

**Date** : 2026-09-21 (REASON ephemeral câblé `.140` · Colab Pinggy PoC)  
**Source de vérité** : ce fichier.

**Objectif** : recentrer sur **Studio (Cortex)** puis **Jeu (Prime/Godot)** dans `LBG_Studios`,  
sans perdre l’étoile du nord — [`RESTAURATION_PRODUIT.md`](RESTAURATION_PRODUIT.md).  
**Focus compagnon** : [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) (O1 Studio).  
**Handoff sonde AD (Antigravity)** : [`handoff_antigravity_sonde_ad.md`](handoff_antigravity_sonde_ad.md).  
**Handoff visuel Compagnon (Antigravity)** : [`handoff_antigravity_visuel_compagnon.md`](handoff_antigravity_visuel_compagnon.md).  
**Focus wahou (jeu, archivé)** : [`FOCUS_WAHOU.md`](FOCUS_WAHOU.md).  
**Smoke** : [`SMOKE_LAN.md`](SMOKE_LAN.md).  
**LLM local** : [`packages/cortex/docs/local_llm_route_matrix.md`](../packages/cortex/docs/local_llm_route_matrix.md) · règle Cursor `local-llm-route-matrix.mdc`.  
**Compagnon LLM / morale LAB** : [`packages/cortex/docs/compagnon_llm_moral_policy.md`](../packages/cortex/docs/compagnon_llm_moral_policy.md).  
**GPU éphémère Colab** : [`packages/cortex/docs/reason_ephemeral_colab.md`](../packages/cortex/docs/reason_ephemeral_colab.md) · notebooks `packages/cortex/tools/colab/`.  
**LLM secours free** : [`packages/cortex/docs/reason_cloud_free_fallback.md`](../packages/cortex/docs/reason_cloud_free_fallback.md) · comparatif [`llm_cloud_free_vs_local.md`](../packages/cortex/docs/llm_cloud_free_vs_local.md).  
**Canal ops** : Slack + Element backup — [`packages/cortex/docs/ops_notify_slack.md`](../packages/cortex/docs/ops_notify_slack.md) · ADR 0021.  
**Sprint évolution 7j** (Team, L1 auto / L2 Pilot) : [`packages/cortex/docs/team_evolution_sprint.md`](../packages/cortex/docs/team_evolution_sprint.md).  
**Pont Cloud↔LAN** : [`packages/cortex/docs/pont_cloud_local.md`](../packages/cortex/docs/pont_cloud_local.md).  
**Lore / âme jeu** : [`world/BIBLE_MMO.md`](world/BIBLE_MMO.md) · [`world/INVENTAIRE_PNJ.md`](world/INVENTAIRE_PNJ.md) · [`world/ARBRES_TALENTS_PRECU.md`](world/ARBRES_TALENTS_PRECU.md) · [`world/BOITE_IDEES_GAMEPLAY.md`](world/BOITE_IDEES_GAMEPLAY.md) · maturité A/B/C ([`maturity_content.md`](../packages/cortex/docs/maturity_content.md), V60–V65) · garant runtime **Chœur du monde**.

**Règle** : dépôt **legacy / archive / étagère** = pas de nouvelle feature produit ; correctifs OK.

---

## Chemins et remotes

| Quoi | Chemin / URL |
|------|----------------|
| Monorepo (source de vérité) | `/home/sdesh/projects/LBG_Studios` — GitHub `Teome0245/LBG_Studios` |
| Workspace Cursor | `LBG_Studios.code-workspace` |
| Deploy runtime Cortex | `.140` → **`/opt/LBG_IA_MMO`** (rsync, pas de `git clone`) |
| Env prod | `.140` `/etc/lbg-ia-mmo.env` (depuis `packages/cortex/infra/secrets/lbg.env`) |
| Client Windows | Launchpad → `J:\swgemu\dist\` ; Godot `J:\swgemu\clients\prime-client` |

### Client Godot (deux chemins — ne pas les confondre)

| Rôle | Chemin |
|------|--------|
| **Source Git** (dev, ce repo) | `packages/prime-client` |
| **Runtime 140** (env actuel) | `/opt/new_mmo/prime-client` (`LBG_PRIME_CLIENT_ROOT`) |
| Copie Studios sur 140 | `/opt/LBG_Studios/packages/prime-client` (pas encore l’env par défaut) |
| Joueur Windows | `J:\swgemu\clients\prime-client` (sync depuis le package) |

Nouvelles features client → **Git Studios**. Deploy / sondes VM → respecter `LBG_PRIME_CLIENT_ROOT` jusqu’à unification.

---

## Actif — monorepo `LBG_Studios`

| Package | Rôle | Point d’entrée |
|---------|------|----------------|
| **`packages/cortex`** | Studio : orchestrateur, Team, Pilot, agents | `http://192.168.0.140:8080/` |
| **`packages/prime-client`** | Jeu : client Godot Prime | Launchpad / Godot → 246 |
| **`packages/launchpad`** | Lanceur Electron (sources) | build Windows → `J:\swgemu\dist\` |

Serveurs jeu (runtime, hors Git) :

| Hôte | Rôle | Accès |
|------|------|-------|
| **`192.168.0.246:8792`** | **Prime** — monde LBG produit (écriture / features) | http://192.168.0.246:8792/ |
| **`192.168.0.245:8792`** | **PreCU** — **référence SWG Pre-CU** (lecture seule ; ne pas modifier) | http://192.168.0.245:8792/ |
| **`192.168.0.246:8080`** | Patches Prime | http://192.168.0.246:8080/patches/prime/manifest.json |

**Règle 245** : modèle le plus proche de l’original Pre-CU pour consulter arbres / craft / datatables. Toute feature LBG = **246** + monorepo. Voir Bible **V4**.

## LAN — hôtes (Atlas / ops)

| IP | Rôle | Notes |
|----|------|-------|
| **`.10`** | Poste Teome | Cursor, ComfyUI, pilotage humain — plus l’executor LAN |
| **`.100`** | Cockpit / Orch UI / Simple Chat | `:8093` Cockpit · `:3000` API · `:5174` SPA chat · `:3080` Open WebUI lab |
| **`.110`** | Ollama **heavy** | `:11434` **CPU only** — `gemma-4-abliterated:12b` + `e2b` (+ `qwen3.5-abliterated:9b` disque) ; pas de 27B routé |
| **`.111`** | Ollama **light** | `:11434` — `qwen3.5-abliterated:2B` (Clean / Compagnon LAB) + `0.8B` (Fast) |
| **`.140`** | Core Studio | Pilot `:8080`, backend `:8000`, orchestrateur `:8010` |
| **`.141`** | CT `lbg-executor` | poll `/v1/team/wsl/*` — `lbg-lan-executor.service` |
| **`.142`** | CT `lbg-hands` | NUC `.200` — `linux_agent` `:6001`, inbox `/var/lib/lbg-hands/inbox` ; voir [`hands_ct_142.md`](../packages/cortex/docs/hands_ct_142.md) |
| **`.143`** | VM `lbg-omarchy` | NUC `.200` — lab Omarchy (Arch/Hyprland) ; voir [`omarchy_vm_143.md`](../packages/cortex/docs/omarchy_vm_143.md) |
| **`.200` / `.201`** | Proxmox | `.200` = NUC (hôte CT 111 / 142 / VM 143) · `.201` = R720 (CT 110 / 141) |
| **`.51`** | NAS Synology | `N:` = raccourci SMB ; **pas** OneDrive ; uptime irrégulier (~6 mois) |
| **`.245`** | PreCU | lecture seule `:8792` |
| **`.246`** | Prime | monde produit `:8792` + sidecar IA |

LLM : `think: false` (Qwen). `.110` = 24 Go RAM **sans GPU** — interactif → 2B/9b ; 12b = batch ; PoC GPU → Colab (`reason_ephemeral_colab.md`).

## Actif — remotes liés (hors Git monorepo)

| Chemin local | Rôle |
|--------------|------|
| `../Infographiste_IA` | Pipeline assets / LoRA |
| **Cockpit P03** (runtime) | Ops infra LAN — http://192.168.0.100:8093/pilot/#/cockpit (sources `_shelf/LBG_Project_03`) |
| **Orchestrateur UI / Compagnon** | SPA Vue chat produit — http://192.168.0.100:5174/ ; sources **`packages/cortex/compagnon_ui`** ; deploy `packages/cortex/infra/scripts/deploy_compagnon_100.sh` ; API `:3000` |
| **Compagnon Desktop** | Electron tray + avatar — `packages/compagnon-desktop` (poste `.10`) |

## Étagère

| Dépôt | Motif |
|-------|--------|
| `_shelf/LBG_Project_03` | Sources Cockpit / LangGraph — runtime actif sur `.100:8093` ; pas de nouvelles features majeures ici (lien depuis Pilot Ops) |

## Archive / legacy upstream

| Dépôt | Motif |
|-------|--------|
| `_archive/avatar_app` | Bac avatars web Three.js — gelé |
| `_archive/mmmorpg` | Pivot Core3 / sandbox WS gelée |
| `_archive/LBG_IA` | Sources SPA Orchestrateur Vue — runtime `:5174` en **redirect Pilot** (P3) ; API `:3000` active |
| `../LBG_IA_MMORPG` | **Upstream legacy** Cortex (avant extraction) |
| `../new_mmo` | **Upstream legacy** jeu (Core3 + historiques) |

### Composants gelés (ne pas réimporter)

`mmo_server`, `mmmorpg_server`, `web_client`, `pilot_web/mmo`, `lbg_client_godot` 3D phase 0, `avatar_app`.

---

## Matrice

```mermaid
flowchart LR
  subgraph studios["LBG_Studios"]
    CX["packages/cortex"]
    PC["packages/prime-client"]
    LP["packages/launchpad"]
  end
  subgraph linked["Liés"]
    INFO["Infographiste_IA"]
    CK["Cockpit .100:8093"]
    ORCH["Orch 5174 → Pilot"]
  end
  subgraph lan["LAN runtime"]
    H110["Ollama 110 heavy"]
    H111["Ollama 111 light"]
    H140["Core 140"]
    H141["Executor 141"]
    H142["Hands 142"]
  end
  subgraph game["Serveurs jeu"]
    P246["Prime 246:8792"]
    P245["PreCU 245:8792"]
  end
  subgraph arch["Archive"]
    AVA["avatar_app"]
    MMM["mmmorpg"]
    LIA["LBG_IA"]
  end
  subgraph legacy["Legacy"]
    MMO["LBG_IA_MMORPG"]
    NM["new_mmo"]
  end
  INFO --> PC
  CX -.->|"upstream"| MMO
  PC -.->|"upstream"| NM
  CX --> H140
  H140 --> H110
  H140 --> H111
  H140 --> H141
  H140 --> H142
  LP --> P246
  PC --> P246
```

---

## Jalons récents (O1 / O2)

| Date | Jalon | Où |
|------|--------|-----|
| 2026-08-24 | Recentrage wahou : aboutis archivés, pari 30 s Lost Heaven, mission Team L1 | [`FOCUS_WAHOU.md`](FOCUS_WAHOU.md) |
| 2026-08-18 | Pilot : modules ES + Vite, Three.js npm (`three@0.128`), import map uvicorn | `packages/cortex/pilot_web` |
| 2026-08-18 | Orchestrateur démarrable sans legacy : stub local `hybrid_proactive_agent` | `packages/cortex/orchestrator` |
| 2026-08-18 | Backend : `pydantic-settings`, `response_model` Pilot, `trace_id` E2E | `packages/cortex/backend` |
| 2026-08-18 | O2 : pipeline assets Prime + persistance inventaire/quêtes via bridge Core3 | `packages/prime-client` |
| 2026-09-20 | LLM secours free (Groq/OpenRouter) + comparatif Colab/Kaggle + smoke notebooks | `docs/reason_cloud_free_fallback.md`, `docs/llm_cloud_free_vs_local.md` |
| 2026-09-21 | REASON ephemeral câblé sur `.140` (drop-in `/etc/lbg-ephemeral.env`) + doc PoC Colab/Pinggy | `docs/reason_ephemeral_colab.md`, `infra/systemd/lbg-orchestrator.ephemeral-colab.conf.example` |
