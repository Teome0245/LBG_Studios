# REASON ephemeral — GPU Colab (PoC)

**Date** : 2026-09-21  
**Statut** : PoC **câblé** sur chaîne REASON (`.140` via drop-in) — **hors H24**, hors audit Atlas 110/111  
**Code** : `orchestrator/team/reason_llm.py` → `reason_ephemeral_route()` / `reason_routes()`  
**Notebook canonique** : `tools/colab/lbg_reason_ephemeral.ipynb`  
**Alt. cloudflared** : `tools/colab/lbg_reason_ephemeral_ollama.ipynb`  
**Drop-in systemd** : `infra/systemd/lbg-orchestrator.ephemeral-colab.conf.example`  
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
2. Runtime → **GPU T4** → Exécution → **Redémarrer la session et tout exécuter**.
3. Copier le bloc `export LBG_REASON_EPHEMERAL_*=…` affiché en bas de la **cellule 5** (sous les `====`). Smoke Colab : `smoke /v1/models: 0`.

### WSL (session opérateur)

```bash
# Fichier local (non versionné) — ne pas committer l’URL/token
cat > packages/cortex/infra/secrets/lbg.ephemeral.env <<'EOF'
LBG_REASON_EPHEMERAL_ENABLED=1
LBG_REASON_EPHEMERAL_BASE_URL="https://….run.pinggy-free.link"
LBG_REASON_EPHEMERAL_API_KEY="<token du notebook>"
LBG_REASON_EPHEMERAL_MODEL="huihui_ai/qwen3-abliterated:8b-v2"
LBG_REASON_EPHEMERAL_TIMEOUT_S=45
LBG_REASON_EPHEMERAL_BEFORE_CLOUD=1
EOF
chmod 600 packages/cortex/infra/secrets/lbg.ephemeral.env
set -a && source packages/cortex/infra/secrets/lbg.ephemeral.env && set +a

curl -sS -H "Authorization: Bearer $LBG_REASON_EPHEMERAL_API_KEY" \
  "$LBG_REASON_EPHEMERAL_BASE_URL/v1/models" | head
```

### Orchestrateur `.140` (chaîne Studio)

Le tier est déjà dans `reason_routes()` : **local → ephemeral → cloud** si `BEFORE_CLOUD=1`.

Ne **pas** coller le token dans `/etc/lbg-ia-mmo.env` (fichier gros / backups). Utiliser un fichier dédié + drop-in :

```bash
# Sur .140 — après smoke WSL OK
sudo tee /etc/lbg-ephemeral.env >/dev/null <<EOF
LBG_REASON_EPHEMERAL_ENABLED=1
LBG_REASON_EPHEMERAL_BASE_URL="https://….run.pinggy-free.link"
LBG_REASON_EPHEMERAL_API_KEY="<token>"
LBG_REASON_EPHEMERAL_MODEL="huihui_ai/qwen3-abliterated:8b-v2"
LBG_REASON_EPHEMERAL_TIMEOUT_S=45
LBG_REASON_EPHEMERAL_BEFORE_CLOUD=1
EOF
sudo chmod 640 /etc/lbg-ephemeral.env
sudo chown root:lbg /etc/lbg-ephemeral.env

sudo cp packages/cortex/infra/systemd/lbg-orchestrator.ephemeral-colab.conf.example \
  /etc/systemd/system/lbg-orchestrator.service.d/ephemeral-colab.conf
sudo systemctl daemon-reload
sudo systemctl restart lbg-orchestrator
```

Vérif process :

```bash
tr '\0' '\n' < /proc/$(pgrep -f 'uvicorn main:app.*8010' | head -1)/environ | grep EPHEMERAL
```

Smoke Python (sur `.140`) : `complete_reason(...)` doit pouvoir failover en `tier: ephemeral` si le local échoue.

**Couper le PoC** : `LBG_REASON_EPHEMERAL_ENABLED=0` dans `/etc/lbg-ephemeral.env` + `systemctl restart lbg-orchestrator`, puis **Disconnect** runtime Colab.

## Notebook — points durs Colab

| Symptôme | Fix |
|----------|-----|
| `which ollama` exit 1 / `FileNotFoundError` | `_resolve_ollama()` : `command -v` via shell + `/usr/local/bin/ollama` (pas `which` argv seul) |
| `:8088 Address already in use` | `fuser -k {PROXY_PORT}/tcp` avant `ThreadingHTTPServer` |
| `PUBLIC_URL = dashboard.pinggy.io` | filtre `_is_tunnel_url` (exclure dashboard) |
| Sortie « rien vu » | le bloc utile est la **sortie** cellule 5, pas le template `export` dans le code source |

## Limites assumées

| Risque | Mitigation PoC |
|--------|----------------|
| Session Colab idle / 12 h | Timeout 45 s + failover cloud ; garder runtime ouvert pendant le test |
| URL tunnel change à chaque run | Recopier `/etc/lbg-ephemeral.env` + restart orch ; pas de commit token |
| Exposition Internet | Proxy Bearer obligatoire |
| ToS Google / usage service | Usage perso / démo uniquement |
| VRAM T4 | Défaut notebook/env.example **qwen3.5-abliterated:9b** ; PoC validé aussi **qwen3-abliterated:8b-v2** ; pas le 27B |
| Qwen « thinking » via `/v1` | Cortex appelle **`/api/chat`** natif (`think=false`) — le proxy notebook doit forwarder tout path |
| Premier `/api/chat` lent | Chargement modèle GPU — timeout orch 90 s ; `/v1/models` reste le smoke rapide |
| `pip install open-webui` (notebook mai) | **Cassé** sur Colab récent — bypass Pinggy + proxy Bearer |

## Hors scope

- H24 / remplacement de `.110` / `.111`
- Intégration Atlas / audit LAN
- text-generation-webui (UI inutile pour REASON)
