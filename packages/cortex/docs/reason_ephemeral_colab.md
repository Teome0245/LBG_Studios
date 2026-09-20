# REASON ephemeral — GPU Colab (PoC)

**Date** : 2026-09-20  
**Statut** : PoC — **hors prod H24**, hors audit Atlas 110/111  
**Code** : `orchestrator/team/reason_llm.py` → `reason_ephemeral_route()`  
**Notebook canonique** : `tools/colab/lbg_reason_ephemeral.ipynb`  
**Alt. cloudflared** : `tools/colab/lbg_reason_ephemeral_ollama.ipynb`  
**Archive mai** (Open WebUI, obsolète) : `tools/colab/archive_mai_drive_1kyH4rxH.ipynb` · [Drive](https://colab.research.google.com/drive/1kyH4rxHMPpGId2nshi0f4Ei-pd5CAOlf)

## Intent

Permettre à un **laptop sans GPU** (ou VRAM &lt; 6 Go) d’utiliser un Ollama distant via **Google Colab (T4 gratuit)** + tunnel, branché sur la chaîne REASON existante.

Ce n’est **pas** un substitut de `.110` / `.111`. Pour du H24 sans GPU LAN, préférer **Groq** (`LBG_REASON_CLOUD_*`) — voir [`reason_cloud_free_fallback.md`](reason_cloud_free_fallback.md).

Comparatif Kaggle / Colab / Lightning / APIs : [`llm_cloud_free_vs_local.md`](llm_cloud_free_vs_local.md).

| Runtime GPU free | Verdict LBG |
|------------------|-------------|
| **Colab T4** | Notebooks prêts (`tools/colab/`) — fix check GPU : accepter `Tesla T4` (sans mot « NVIDIA ») |
| **Kaggle** (~30 h/sem., P100 ou 2×T4) | **Recommandé si Colab flaky** — uploader le notebook + Accelerator GPU ; préférer cloudflared |
| **Lightning AI** (~22 h/mois) | Studio GPU + terminal/VS Code ; mêmes commandes Ollama + tunnel |

## Alternatives : Kaggle / Lightning

### Kaggle (recommandé si Colab bloque)

1. [kaggle.com](https://www.kaggle.com) → **Code → New Notebook**
2. **Settings** (droite) → Accelerator = **GPU T4×2** ou **GPU P100** · Internet = **On**
3. **File → Import notebook** → `lbg_reason_ephemeral_ollama.ipynb` (**cloudflared**, Pinggy souvent plus capricieux sur Kaggle)
4. Run All → copier le bloc `export LBG_REASON_EPHEMERAL_*=…`
5. Même branchement Cortex qu’avec Colab

Quota typique : ~30 h GPU / semaine ; sessions souvent plus stables à l’idle que Colab.

### Lightning AI

1. [lightning.ai](https://lightning.ai) → nouveau **Studio** avec GPU free
2. Terminal du Studio :
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama serve &
   ollama pull huihui_ai/qwen3.5-abliterated:9b
   ```
3. Reprendre les cellules **proxy Bearer + tunnel** du notebook (Pinggy ou cloudflared)
4. Coller les `export LBG_REASON_EPHEMERAL_*` en local

Lightning = VS Code web + persistance fichiers ; pas H24, quota ~22 h GPU / mois.

## Bug corrigé (check GPU)

`nvidia-smi -L` renvoie souvent :

```text
GPU 0: Tesla T4 (UUID: …)
```

sans le mot `NVIDIA`. L’ancien test `"NVIDIA" not in out` faisait un faux négatif. Le check accepte désormais `Tesla` / `T4` / `P100` / etc.

## Chaîne de routage

```
local 111/110 → failover heavy → ephemeral? → cloud?
                 (ordre ephemeral/cloud via LBG_REASON_EPHEMERAL_BEFORE_CLOUD)
```

Le tier `ephemeral` n’est ajouté que si **les trois** sont posés :

1. `LBG_REASON_EPHEMERAL_ENABLED=1`
2. `LBG_REASON_EPHEMERAL_BASE_URL` (URL du tunnel)
3. `LBG_REASON_EPHEMERAL_API_KEY` (Bearer du proxy du notebook)

## Schéma d’env

| Variable | Défaut | Rôle |
|----------|--------|------|
| `LBG_REASON_EPHEMERAL_ENABLED` | `0` | Active le tier |
| `LBG_REASON_EPHEMERAL_BASE_URL` | — | Ex. `https://xxxx.trycloudflare.com` (Ollama OpenAI-compat `/v1/...`) |
| `LBG_REASON_EPHEMERAL_API_KEY` | — | Token Bearer (obligatoire) |
| `LBG_REASON_EPHEMERAL_MODEL` | `huihui_ai/qwen3.5-abliterated:9b` | Abliterated T4 (~6.5 Go) ; aligné LAN ≤12B ; `.110` = CPU only |
| `LBG_REASON_EPHEMERAL_TIMEOUT_S` | `45` | Timeout court (session flaky) |
| `LBG_REASON_EPHEMERAL_BEFORE_CLOUD` | `1` | `1` = avant Groq ; `0` = après |

### Catalogue modèles (T4 16 Go)

| Tag Ollama | Taille approx. | Usage PoC |
|------------|----------------|-----------|
| **`huihui_ai/qwen3.5-abliterated:9b`** | ~6.5 Go | **Défaut** — aligné inventaire LAN / Colab T4, think off via `LBG_REASON_OLLAMA_THINK` |
| `huihui_ai/gemma-4-abliterated:12b` | ~7.5 Go | Qualité ↑, parité heavy `.110` |
| `huihui_ai/qwen3.5-abliterated:2B` | ~1.9 Go | Smoke / Compagnon LAB `.111` |
| `huihui_ai/qwen3.5-abliterated:0.8B` | ~1 Go | Ultra-fast |
| `huihui_ai/qwen3-abliterated:8b-v2` | ~5 Go | Legacy (optionnel) |
| `huihui_ai/Qwen3.8-abliterated:27b` | ≫ T4 free | **Non** — legacy disque `.110` |

Garde-fous présentation (maturité A/B/C) restent côté prompts Cortex, pas via un 2ᵉ modèle.

Référence commentée : `infra/secrets/lbg.env.example`.

## Validation locale (sans GPU cloud)

```bash
cd packages/cortex
LBG_SMOKE_BASE_URL=http://192.168.0.110:11434 \
  LBG_SMOKE_MODEL=huihui_ai/qwen3.5-abliterated:9b \
  python tools/colab/validate_ephemeral_notebook.py --smoke-local
```

Vérifie les notebooks + un chat natif `/api/chat` sur LAN (modèle light ; même tag que Colab / LAN 9b).

## Procédure PoC (propre)

1. **Importer** `tools/colab/lbg_reason_ephemeral.ipynb` dans Colab (Fichier → Importer) — **pas** le Drive mai (lecture seule + Open WebUI cassé).
2. Runtime → **GPU T4** → Exécution → **Tout exécuter**.
3. Copier le bloc `export LBG_REASON_EPHEMERAL_*=…` affiché en fin de notebook.
4. Sur le poste / WSL (session locale uniquement) :

```bash
export LBG_REASON_EPHEMERAL_ENABLED=1
export LBG_REASON_EPHEMERAL_BASE_URL="https://….trycloudflare.com"
export LBG_REASON_EPHEMERAL_API_KEY="<token du notebook>"
export LBG_REASON_EPHEMERAL_MODEL="huihui_ai/qwen3.5-abliterated:9b"
# optionnel : couper le local pour forcer le tier
# export LBG_REASON_LLM_DISABLED=0
```

5. Sonde manuelle :

```bash
curl -sS -H "Authorization: Bearer $LBG_REASON_EPHEMERAL_API_KEY" \
  "$LBG_REASON_EPHEMERAL_BASE_URL/v1/models" | head
```

6. Arrêter le notebook / runtime Colab dès la fin du PoC (URL + token deviennent invalides).

## Limites assumées

| Risque | Mitigation PoC |
|--------|----------------|
| Session Colab idle / 12 h | Timeout 45 s + failover cloud |
| URL tunnel change à chaque run | Recopier l’env ; pas de push secrets 140 |
| Exposition Internet | Proxy Bearer obligatoire |
| ToS Google / usage service | Usage perso / démo uniquement |
| VRAM T4 | Défaut **qwen3.5-abliterated:9b** ; option **gemma-4-abliterated:12b** ; pas le 27B |
| Qwen « thinking » via `/v1` | Cortex appelle **`/api/chat`** natif (`think=false`) — le proxy notebook doit forwarder tout path |
| `pip install open-webui` (notebook mai) | **Cassé** sur Colab récent (pas de wheel Python compatible) — bypass : tunnel Pinggy → Ollama `:11434` + proxy Bearer (cellule LBG) |

## Hors scope

- Push de `LBG_REASON_EPHEMERAL_*` vers `/etc/lbg-ia-mmo.env` sur `.140`
- Intégration Atlas / audit LAN
- text-generation-webui (UI inutile pour REASON)
