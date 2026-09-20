# Colab / Kaggle / Lightning — GPU éphémère LBG

| Fichier | Rôle |
|---------|------|
| [`lbg_reason_ephemeral.ipynb`](lbg_reason_ephemeral.ipynb) | **Canonique** — Pinggy + proxy Bearer |
| [`lbg_reason_ephemeral_ollama.ipynb`](lbg_reason_ephemeral_ollama.ipynb) | **Kaggle / Pinggy bloqué** — tunnel **cloudflared** |
| [`archive_mai_drive_1kyH4rxH.ipynb`](archive_mai_drive_1kyH4rxH.ipynb) | Archive mai (Open WebUI cassé) |
| [`validate_ephemeral_notebook.py`](validate_ephemeral_notebook.py) | Validation + smoke LAN |

Doc : [`docs/reason_ephemeral_colab.md`](../../docs/reason_ephemeral_colab.md)

## Quelle plateforme ?

| Plateforme | Quand | Notebook |
|------------|-------|----------|
| **Colab** | rapide, compte Google | `lbg_reason_ephemeral.ipynb` |
| **Kaggle** | Colab idle/quota/check flaky ; ~30 h/sem | `lbg_reason_ephemeral_ollama.ipynb` |
| **Lightning** | VS Code web, ~22 h/mois | mêmes cellules / terminal Studio |

## Colab

1. Importer `lbg_reason_ephemeral.ipynb` (ou copie Drive)
2. Runtime → **GPU T4**
3. Tout exécuter → copier `export LBG_REASON_EPHEMERAL_*=…`

## Kaggle

1. New Notebook → Accelerator **GPU** · Internet **On**
2. Import `lbg_reason_ephemeral_ollama.ipynb`
3. Run All → même `export …`

## Lightning AI

Studio GPU → install Ollama + pull qwen3.5-abliterated:9b + cellules proxy/tunnel (voir doc).

## Modèle

Défaut : `huihui_ai/qwen3.5-abliterated:9b` (`LBG_COLAB_MODEL`).

## Smoke sans cloud GPU

```bash
cd packages/cortex
python tools/colab/validate_ephemeral_notebook.py
```
