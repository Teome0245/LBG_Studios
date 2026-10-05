# Playbook — Fine-tune E4b-qat sur `.10` → déployer sur `.111` / `.110`

## But

Personnaliser **le ton / la personnalité** Compagnon (pas la mémoire studio).  
Entraîner sur **`.10` (petit GPU)**, servir sur **`.111`** (causerie) ou **`.110`** (forge).

Base Ollama : **`huihui_ai/gemma-4-abliterated:E4b-qat`**  
(Prérequis mémoire : **RAG**. Ne pas FT pour « apprendre » les leçons.)

## Prérequis `.10`

```bash
nvidia-smi   # noter modèle + VRAM
# Objectif : ≥8 Go pour QLoRA E4b ; 6–8 Go = serré ; <6 Go → rester Modelfile
```

Stack : **Unsloth** (simple) ou Axolotl.

Aligner le checkpoint HF sur la lignée Gemma-4 E4B abliterated / QAT (voir `docs/local_llm_route_matrix.md`). Valider le style après merge.

## Dataset (style only)

Fichier : `infra/llm_persona_e2b/dataset/compagnon_style_v1.jsonl`

- **Oui** : ton collègue, fierté sobre, refus « en tant qu’IA »
- **Non** : dumps ops, secrets, état Team inventé
- Volume v1 : **80–300** tours de qualité

## Entraînement (esquisse Unsloth)

QLoRA 4-bit, `r=8|16`, seq 1024–2048, batch 1 + accum 8–16, 1–3 epochs.  
Sortie : LoRA → merge → **GGUF**.

## Export → Ollama

```bash
# SYSTEM via build_modelfile.py (base E4b-qat)
python3 packages/cortex/infra/llm_persona_e2b/build_modelfile.py

# Puis FROM ./lbg-compagnon-e4b-v2-q4_k_m.gguf + SYSTEM collé
ollama create lbg-compagnon-e4b-v2 -f /tmp/Modelfile.v2
```

## Déployer vers `.111`

```bash
bash packages/cortex/infra/scripts/deploy_compagnon_e2b_ft_to_111.sh \
  --tag lbg-compagnon-e4b-v2 \
  --gguf /chemin/lbg-compagnon-e4b-v2-q4_k_m.gguf \
  --activate
```

## Rollback

```text
LBG_COMPAGNON_LAB_CHAT_MODEL=lbg-compagnon-e4b-v1   # Modelfile
# ou
LBG_COMPAGNON_LAB_CHAT_MODEL=lbg-compagnon-e2b-v1   # ancien e2b
```

## Checklist smoke

- [ ] GPU `.10` OK
- [ ] Dataset sans secrets
- [ ] Tag `e4b-v2` sur `.111` ; `e4b-v1` toujours là
- [ ] Causerie Compagnon + RAG intact sur questions mémoire
