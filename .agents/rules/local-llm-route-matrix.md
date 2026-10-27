---
trigger: model_decision
description: Matrice LLM locale 110 heavy / 111 light, routage Ollama Compagnon et Team — appliquer dès qu’on touche reason_llm, Ollama, Colab, ou modèles compagnon
---

# Matrice LLM locale

Source exécutable : `packages/cortex/orchestrator/team/reason_llm.py` → `reason_route_matrix()`.
Source lisible : `packages/cortex/docs/local_llm_route_matrix.md`.

- **`.110` heavy (CPU only)** : `huihui_ai/qwen2.5-coder-abliterate:14b` (code/patchs), `huihui_ai/gemma-4-abliterated:12b-qat` (PM/dialogue, alias `:12b`), `huihui_ai/gemma-4-abliterated:E4b-qat` (chill/philo/interactif/forge). Interactif : préférer E4b/9b/2B. Pas de 27B routé. `e2b` retiré.
- **`.111` light** : `huihui_ai/qwen3.5-abliterated:2B` (router/json / Compagnon LAB), `huihui_ai/qwen3.5-abliterated:0.8B` (fast), `huihui_ai/gemma-4-abliterated:E4b-qat` (causerie/chill). Pas de `gemma4:e2b` legacy ni `e2b`.
- **Colab éphémère** : défaut `huihui_ai/qwen3.5-abliterated:9b` (`LBG_REASON_EPHEMERAL_*` / `LBG_COLAB_MODEL`).
- Qwen : `think: false` (`LBG_REASON_OLLAMA_THINK` / `LBG_DIALOGUE_LLM_OLLAMA_THINK`).
- Ne pas réintroduire `gemma3:4b` ni `gemma4:e2b` (censuré) sur 111. Préférer tags Ollama `huihui_ai/*`.
