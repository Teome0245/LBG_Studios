# GPU / API cloud gratuits vs stack locale Cortex

**Date** : 2026-09-20  
**Statut** : décisionnel — hors prod H24 sauf voie API déjà câblée  
**Canon local** : [`local_llm_route_matrix.md`](local_llm_route_matrix.md)  
**Secours API** : [`reason_cloud_free_fallback.md`](reason_cloud_free_fallback.md)  
**GPU éphémère** : [`reason_ephemeral_colab.md`](reason_ephemeral_colab.md)

---

## Verdict

| Besoin | Choix LBG |
|--------|-----------|
| H24 Studio / Team / Pilot | **Ollama `.110` / `.111`** (abliterated ≤12B) |
| Secours rapide si LAN down | **Groq** via `LBG_REASON_CLOUD_*` / `LBG_DIALOGUE_FAST_*` |
| Laptop sans GPU (PoC) | **Colab T4** + tunnel → `LBG_REASON_EPHEMERAL_*` |
| Chat one-shot / script hors Cortex | Groq / OpenRouter free / HF Inference |
| Remplacer `.110` | **Non** — quotas, idle kill, ToS, pas d’audit Atlas |

---

## Comparatif

| Plateforme | Quota free (ordre de grandeur) | GPU | Persistance | Fit Cortex | Notes |
|------------|--------------------------------|-----|-------------|------------|-------|
| **LAN `.110` / `.111`** | illimité LAN | local | H24 | **Canon** | Matrice `reason_route_matrix()` ; Atlas audit |
| **GroqCloud** | RPM/TPM free tier | N/A (API) | N/A | **Secours #1** | Déjà câblé ; modèles *ouverts* filtrés (pas abliterated) |
| **OpenRouter** | modèles `:free` | N/A | N/A | Secours optionnel | Via `LBG_DIALOGUE_GLM_*` ou `LBG_REASON_CLOUD_*` OpenAI-compat |
| **HF Inference** | crédits / rate-limit | N/A | N/A | Expérimental | Clé HF ; modèles communauté (dont uncensored) |
| **Kaggle** | ~30 h GPU / sem. (P100 / 2×T4) | oui | notebooks + dataset | **PoC GPU (alt. Colab)** | Sessions plus stables idle ; vérif téléphone ; notebook `lbg_reason_ephemeral_ollama.ipynb` |
| **Google Colab** | T4 free (quota non garanti) | oui | Drive | **PoC documenté** | Notebooks `tools/colab/` ; check GPU accepte `Tesla T4` |
| **Lightning AI** | ~22 h GPU / mois | oui | VS Code web | PoC alt. | Studio + mêmes étapes Ollama/tunnel |

---

## Abliterated / « sans filtre »

| Contexte | Réalité |
|----------|---------|
| Local `.110` / `.111` | Tags `huihui_ai/*-abliterated` — garde-fous = maturité A/B/C (prompts) |
| Colab / Kaggle (Ollama) | Même famille possible (T4 → **8b**, pas le 9b/.110 ni 27B) |
| Groq / OpenRouter free | Modèles **ouverts standard** (Llama, Mixtral, Qwen catalog) — **pas** équivalent abliterated |
| Contournement API | Ne pas compter sur un provider free pour le profil `uncensored` / Prométhée |

Chaîne REASON :

```
local 111/110 → failover heavy → ephemeral? → cloud?
```

- `ephemeral` = Ollama sur GPU cloud + tunnel (abliterated possible).  
- `cloud` = Groq (ou autre OpenAI-compat) — latence/dispo, pas le même contrat « uncensored ».

---

## Quand utiliser quoi

1. **Développement Team / Pilot sur LAN** → matrice locale uniquement.  
2. **`.110` down, besoin de continuer** → activer `LBG_REASON_CLOUD_*` (Groq) — voir secours API.  
3. **Démo laptop / voyage sans GPU** → notebook Colab (ou Kaggle) + `LBG_REASON_EPHEMERAL_*` ; couper dès la fin.  
4. **Script ad hoc hors orchestrateur** → Groq / OpenRouter free avec clé perso (hors `/etc/lbg-ia-mmo.env` prod).

---

## Note — AirLLM (méthode, pas un provider)

**AirLLM** ([lyogavin/airllm](https://github.com/lyogavin/airllm)) : inférence **couche par couche** (une couche GPU à la fois) pour faire tenir un gros modèle sur peu de VRAM (ex. 70B ≈ 4 Go). Contrepartie : **très lent**. Pas intégré à Ollama.

| Chez LBG | Décision |
|----------|----------|
| Remplacer Ollama `.110` / `.111` | **Non** |
| Compagnon / Team / Cline H24 | **Non** (latence) |
| PoC « gros modèle » si host **avec GPU** lab | **OK périphérie** — même case que Colab éphémère |
| `.110` CPU only (état actuel) | Gain VRAM **quasi nul** → pas prioritaire |

Pas d’install tant qu’il n’y a pas de GPU lab. Si un jour : wrapper OpenAI-compat optionnel, hors matrice, hors Atlas H24.

---

## Hors scope

- Push `LBG_REASON_EPHEMERAL_*` vers `.140`  
- Remplacer Atlas / audit Ollama par un notebook  
- Héberger un tunnel public H24 vers un Colab  
- AirLLM / layer-streaming sur le chemin Studio H24
