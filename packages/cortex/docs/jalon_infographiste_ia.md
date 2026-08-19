# Jalon Infographiste IA — intégration équipe virtuelle

**Date** : 2026-07-11  
**Statut** : **en cours** (pipeline GLB, pas de blocage produit)  
**Persona équipe** : **Pygmalion** (`dev_game` + sous-projet `infographiste_ia`)

---

## Rôle dans la réunification

| Élément | Détail |
|---------|--------|
| Sous-projet | `infographiste_ia` — registre `/v1/team/meta` |
| Owner technique | `dev_game` (Dédale) |
| Affichage Pilot | **Pygmalion (infographiste_ia)** sur les tâches dédiées |
| Lié | `client_godot`, `docs/pipeline_assets_swg_godot.md` |

L'Infographiste n'est pas un rôle API séparé : c'est une **piste dev_game** avec persona et sonde dédiée, comme Godot/lbg-ws/2.

---

## Ce que fait la Team

### Sonde L1 (`infographiste_probe`)
- Lit `packages/prime-client` manifests avatars/world (plus `lbg_client_godot`)
- Compte les `.glb` attendus vs présents sur disque
- Vérifie `docs/pipeline_assets_swg_godot.md`
- **OK structurel** même si 0 GLB (phase en cours)

### Workflow (`infographiste_workflow`)
- Brief PM focalisé sous-projet
- `action_proposal` forge (pipeline assets / export Blender)
- Résultat : `kind: infographiste_workflow`

### Superviseur Godot
- Piste `infographiste_assets` incluse en mode `full` (timer 6h)

### Timer dédié
- `lbg-team-infographiste-job` — **12 h**, actor `system:team_infographiste`

### Pipeline LoRA (`infographiste_lora_workflow`)
- Vision Ollama par lots sur `unclassified` → `prepare-styles --from-sorted` → queue train LoRA
- Timer : `lbg-team-infographiste-lora-job` — **2 h**, actor `system:team_infographiste_lora`
- Styles cibles : `mmorpg_general` (`mmorpg_insp_lora`), `prime_sprite_2d` (`prime_sprite_2d_lora` / `lbg_sprite2d`)
- État : `/var/lib/lbg/team_infographiste/lora_pipeline.json`

```bash
# VM 140
bash infra/scripts/install_team_infographiste_lora_job_vm.sh

# Entraînement GPU (poste dev WSL — déclenché depuis 140)
LBG_INFOGRAPHISTE_LORA_TRAIN_ENABLED=1
LBG_INFOGRAPHISTE_LORA_TRAIN_REMOTE=1
LBG_LAN_HOST_DESKTOP=192.168.0.10
LBG_INFOGRAPHISTE_WSL_SSH_PORT=2222
LBG_INFOGRAPHISTE_WSL_SSH_USER=sdesh
LBG_LORA_TRAIN_DEPLOY=1
cd Infographiste_IA && ./scripts/train_lora_by_style.sh --style mmorpg_general --deploy

# Setup initial (une fois) :
bash infra/scripts/setup_wsl_lora_train_wsl.sh
powershell -ExecutionPolicy Bypass -File infra/scripts/setup_wsl_lora_train_portproxy.ps1   # admin Windows
bash infra/scripts/activate_wsl_lora_train_remote.sh   # tout-en-un
```

Variables LoRA :
```bash
LBG_INFOGRAPHISTE_IA_ROOT=/opt/Infographiste_IA
LBG_LORA_VISION_UNCLASSIFIED_TARGET=200
LBG_LORA_VISION_BATCH_LIMIT=100
OLLAMA_BASE_URL=http://192.168.0.110:11434
OLLAMA_VISION_MODEL=llava
LBG_INFOGRAPHISTE_LORA_TRAIN_ENABLED=0   # 1 sur poste GPU
```

---

## Usage Pilot `#/team`

1. Raccourci **Infographiste IA** → **Lancer**
2. Ou plan NL : *« audit pipeline assets glb infographiste »*
3. Filtre liste : `actor: system:team_infographiste`

---

## Variables

```bash
LBG_TEAM_INFOGRAPHISTE_JOB_ENABLED=1
LBG_TEAM_INFOGRAPHISTE_JOB_ACTOR_ID=system:team_infographiste
LBG_INFOGRAPHISTE_GODOT_ROOT=/opt/LBG_Studios/packages/prime-client  # défaut : resolve_prime_client_root()
```

Install timer :
```bash
bash infra/scripts/install_team_infographiste_job_vm.sh
```

---

## Prochaines étapes (humain / forge)

1. **Sprites 2D top-down** — Infographiste_IA → Prime Client (`pipelines/2d/`, `deploy_sprites_to_prime.sh`)
2. **Mesh 3D TRELLIS.2** — worker GPU + `mesh_media.py` ([`jalon_trellis2_pygmalion.md`](jalon_trellis2_pygmalion.md)) ; **off par défaut**
3. Premier export `human_male_base.glb` (Blender ou TRELLIS) — pause 3D
4. Cantina bloc GLB — pause 3D

---

## Références

- [`pipeline_assets_swg_godot.md`](pipeline_assets_swg_godot.md)
- [`equipe_autonome_godot.md`](equipe_autonome_godot.md)
- [`runbook_promotion_prototype_core3.md`](runbook_promotion_prototype_core3.md)
- [`jalon_trellis2_pygmalion.md`](jalon_trellis2_pygmalion.md) — image→GLB PBR (TRELLIS.2)
