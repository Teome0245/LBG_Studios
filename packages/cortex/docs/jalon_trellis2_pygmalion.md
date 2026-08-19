# Jalon TRELLIS.2 — renforcement Pygmalion (image → GLB PBR)

**Date** : 2026-08-19  
**Statut** : **R&D** — hooks Team + worker Infographiste_IA ; **désactivé par défaut** (`LBG_MESH_GEN_ENABLED=0`)  
**Complète** : [`jalon_infographiste_ia.md`](jalon_infographiste_ia.md) · [`clients_2d_3d.md`](clients_2d_3d.md) (3D pause produit)

## Pourquoi

| | TripoSR (legacy) | TRELLIS.2 |
|--|------------------|-----------|
| Textures | Bake basique | **PBR** (base color, roughness, metallic, alpha) |
| Topologie | Limitée | Surfaces ouvertes, structures internes |
| Intégration | Scripts PS manuels | **Worker HTTP + Team Pygmalion** |
| GPU | 1050 Ti (4 Go) | **≥ 24 Go** (officiel) / 16 Go+ low-VRAM communautaire |

Pygmalion garde ComfyUI 2D sur `.10` ; le mesh tourne sur un **backend configurable**.

## Backends

| Backend | Var `LBG_MESH_GEN_BACKEND` | Coût | GPU | Notes |
|---------|---------------------------|------|-----|-------|
| **HuggingFace Space** | `huggingface` (défaut) | **0 €** | Aucun (distant) | Space Gradio Microsoft, 512³ max, gratuit |
| Worker self-hosted | `trellis2` | Électricité | RTX 3090+ | `trellis2_worker.py` dans Infographiste_IA |
| API tierce | `api` | Variable | Aucun | 3D AI Studio, EmpirioLabs, etc. |

## Architecture

```
Pilot preset « Mesh 3D »
    ↓
infographiste_workflow (140)
    ├─ infographiste_probe → gaps GLB
    ├─ comfyui_media → PNG concept (2D, .10:8188)
    └─ mesh_media → GLB PBR
           ├─ backend=huggingface → Space Gradio (0€)
           ├─ backend=trellis2   → Worker GPU :8190
           └─ backend=api        → API tierce
           ↓
    simplify_mesh (~8k tris) → NAS exports_3d/
```

Référence upstream : [TRELLIS.2](https://microsoft.github.io/TRELLIS.2/) · [GitHub](https://github.com/microsoft/TRELLIS.2)

## Fichiers livrés

| Zone | Fichier |
|------|---------|
| Orchestrateur | `orchestrator/team/mesh_media.py` |
| Workflow | `infographiste_workflow.py` (chaîne ComfyUI → mesh si flag) |
| Déclaration | `agents/declarations/studio_infographiste_pygmalion.json` |
| Tests | `orchestrator/tests/test_mesh_media.py` |
| Infographiste_IA | `scripts/trellis2_worker.py`, `scripts/image_to_3d_trellis2.sh`, `pipelines/3d/README.md` |

## Variables (`lbg.env.example`)

```bash
# LBG_MESH_GEN_ENABLED="0"          # 1 quand worker GPU prêt
# LBG_MESH_GEN_BASE_URL="http://192.168.0.10:8190"
# LBG_MESH_GEN_BACKEND="trellis2"
# LBG_MESH_GEN_RESOLUTION="512"     # 512 L1 ; 1024+ → L2 Pilot
# LBG_MESH_GEN_TARGET_TRIS="8000"
# LBG_MESH_GEN_TIMEOUT_S="900"
```

Worker (machine GPU) :

```bash
TRELLIS2_ROOT=/opt/TRELLIS.2
TRELLIS2_PYTHON=/opt/TRELLIS.2/.venv/bin/python
LBG_MESH_OUTPUT_DIR=/mnt/nas_lbg/Infographiste_IA/exports_3d
LBG_MESH_WORKER_PORT=8190
```

## Usage Team / Pilot

1. Preset **Mesh 3D (TRELLIS)** → `context.pygmalion_mesh=true`
2. Ou objectif NL : *« prototype mesh 3D trellis pour gap GLB human_male_base »*
3. Activer `LBG_MESH_GEN_ENABLED=1` sur **140** une fois le worker reachable

Résultat workflow : champs `mesh_probe`, `mesh_generation`, `mesh_glb` dans la réponse.

## Autonomie

| Action | Niveau |
|--------|--------|
| Sonde manifest + ComfyUI 2D | L1 |
| Image→mesh 512³ | L2 (token) tant que GPU rare |
| Deploy GLB → prime-client | L2 |

## Prérequis hardware (PoC)

1. **Linux** + NVIDIA **≥ 24 Go VRAM** (3090/4090, A100, ou cloud)
2. Install upstream : `setup.sh` Microsoft (CUDA 12.4, conda)
3. Worker Infographiste : `pip install -r requirements-mesh.txt && python scripts/trellis2_worker.py`
4. Smoke : `./scripts/image_to_3d_trellis2.sh concept.png test_prop`

**Ne pas** tenter sur GTX 1050 Ti 4 Go.

## Prochaines étapes

1. PoC sur GPU dédié (poste, VM Proxmox GPU passthrough, ou cloud)
2. `LBG_MESH_GEN_ENABLED=1` sur 140 + smoke depuis preset Pilot
3. Timer optionnel `lbg-team-mesh-3d-job` (hebdo, gaps manifest only)
4. Reprise 3D produit → brancher `exports_3d/` → `prime-client/assets/`

## Références

- [`jalon_infographiste_ia.md`](jalon_infographiste_ia.md)
- [`architecture_tri_backend_hybride.md`](architecture_tri_backend_hybride.md)
- Infographiste_IA : `pipelines/3d/README.md`, `BACKLOG_robot01.md`
