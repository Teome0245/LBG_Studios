# Personnalisation Compagnon (Gemma-4 abliterated)

## Contexte

- Base **canon** : `huihui_ai/gemma-4-abliterated:E4b-qat`
- Mémoire / faits = **RAG** ; ce dossier = **ton / personnalité**
- `.111` / `.110` = serveurs Ollama **sans GPU**
- `.10` = poste train (petit GPU) quand dispo
- Ancien tag Modelfile : `lbg-compagnon-e2b-v1` (rollback)

## v1 — Modelfile (actif)

```bash
python3 packages/cortex/infra/llm_persona_e2b/build_modelfile.py
bash packages/cortex/infra/scripts/create_compagnon_e2b_persona_111.sh --activate
```

Tag : `lbg-compagnon-e4b-v1`  
Env : `LBG_COMPAGNON_LAB_CHAT_MODEL=lbg-compagnon-e4b-v1`

## v2 — QLoRA sur `.10` puis déploiement

Guide run : **[RUN_ON_10.md](./RUN_ON_10.md)** · Playbook : **[PLAYBOOK_FT_10.md](./PLAYBOOK_FT_10.md)**

```bash
# Sur la machine GPU .10 uniquement
bash packages/cortex/infra/llm_persona_e2b/setup_venv_ft_10.sh
source packages/cortex/infra/llm_persona_e2b/.venv-ft/bin/activate
cd packages/cortex/infra/llm_persona_e2b
python train_qlora_e4b.py --data dataset/compagnon_style_v1.jsonl --out runs/e4b-v2-smoke --max-steps 30
```

Rollback Modelfile : `lbg-compagnon-e2b-v1` ou recréer `e4b-v1`.

Ne pas fine-tuner pour « mémoriser » le studio.
