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
3. **Redémarrer la session et tout exécuter** → copier le bloc sous les `====` (sortie cellule 5)
4. WSL : `source packages/cortex/infra/secrets/lbg.ephemeral.env` (fichier local, non git)
5. Option Studio `.140` : drop-in `infra/systemd/lbg-orchestrator.ephemeral-colab.conf.example` + `/etc/lbg-ephemeral.env` — voir doc

## Kaggle

1. New Notebook → Accelerator **GPU** · Internet **On**
2. Import `lbg_reason_ephemeral_ollama.ipynb`
3. Run All → même `export …`

## Lightning AI

Studio GPU → install Ollama + pull qwen3.5-abliterated:9b + cellules proxy/tunnel (voir doc).

## Modèle

Défaut notebook / `lbg.env.example` : `huihui_ai/qwen3.5-abliterated:9b` (`LBG_COLAB_MODEL`).  
PoC validé aussi : `huihui_ai/qwen3-abliterated:8b-v2`.

## Smoke sans cloud GPU

```bash
cd packages/cortex
python tools/colab/validate_ephemeral_notebook.py
```
