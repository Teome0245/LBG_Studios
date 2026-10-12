# Lancer le FT **sur `.10`** (GPU)

> Depuis l’agent Cursor actuel (`lbg-omarchy`) : **pas de `nvidia-smi`**, **pas de SSH** vers `.10`.  
> Tout le train se fait sur la session GPU `.10`.

## 0. Prérequis

```bash
nvidia-smi   # ≥8 Go confort pour E4B QLoRA
# monorepo dispo (nfs / git pull / rsync)
cd ~/Projets/LBG_Studios   # ou ton chemin
```

HF base (alignée Ollama `E4b-qat`) :

`huihui-ai/Huihui-gemma-4-E4B-it-abliterated`

## 1. Setup

```bash
bash packages/cortex/infra/llm_persona_e2b/setup_venv_ft_10.sh
source packages/cortex/infra/llm_persona_e2b/.venv-ft/bin/activate
```

## 2. Dataset

Seed : `dataset/compagnon_style_v1.jsonl` (à enrichir vers 80–300 lignes).  
Style only — pas de dumps ops.

## 3. Train (smoke court)

```bash
cd packages/cortex/infra/llm_persona_e2b
python train_qlora_e4b.py \
  --data dataset/compagnon_style_v1.jsonl \
  --out runs/e4b-v2-smoke \
  --max-steps 30 \
  --batch 1 --grad-accum 8
```

Run complet (quand le smoke est OK) :

```bash
python train_qlora_e4b.py \
  --data dataset/compagnon_style_v1.jsonl \
  --out runs/e4b-v2 \
  --epochs 2 \
  --merge
```

## 4. GGUF → `.111`

Convertir `runs/e4b-v2/merged` avec llama.cpp (`convert_hf_to_gguf.py` + quant Q4_K_M), puis :

```bash
bash packages/cortex/infra/scripts/deploy_compagnon_e2b_ft_to_111.sh \
  --tag lbg-compagnon-e4b-v2 \
  --gguf /chemin/lbg-compagnon-e4b-v2-q4_k_m.gguf \
  --activate
```

Rollback : `lbg-compagnon-e4b-v1` (Modelfile déjà actif).

## Si Gemma-4 / Unsloth casse

1. Mettre à jour `transformers` / `unsloth` au jour J  
2. Ou FT uniquement via fallback `transformers+peft` (déjà dans le script)  
3. Vérifier `LBG_FT_HF_MODEL=…` si tu changes de checkpoint
