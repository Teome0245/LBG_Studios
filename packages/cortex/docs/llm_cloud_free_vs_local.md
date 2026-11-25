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

## Note — MoE + Offload hybride RAM/VRAM pour le PowerEdge R720 (en réserve)

**Source veille (2026-11-25)** : Kiara • IA locale — [*Ta carte de 8 Go peut faire tourner une grosse IA : la technique secrète du MoE*](https://www.youtube.com/watch?v=eYNdQTp2dPs).

Principe : contrairement à un modèle dense (ex. 14B où 100 % des poids sont calculés à chaque token), un modèle **MoE (*Mixture of Experts*)** comme `Qwen3-30B-A3B` ou `Qwen3-Coder-30B-A3B` stocke ~18–20 Go en Q4_K_M mais **n’active qu’environ 3B paramètres par token**. Avec `llama.cpp` (`--override-tensor` / `-ot ".ffn_.*_exps.=CPU"`), on place le routeur, les couches d’attention et le KV Cache en VRAM (≤8 Go) et les experts MoE en RAM système.

| Scénario sur R720 (`.201` / CT `.110`) | Intérêt concret | Prérequis / Vigilance R720 |
|----------------------------------------|-----------------|----------------------------|
| **A. Sans aucun GPU (Xeon + RAM pure)** | **Validé par benchmark live (2026-11-25)** sur `.110` (32 Go LXC, `2× Xeon E5-2650 v2`) : `huihui_ai/qwen3-coder-abliterated:30b` (MoE 30B-A3B, 19 Go RAM) bat `huihui_ai/qwen2.5-coder-abliterate:14b` dense sur toute la ligne : **Prefill ×2,40** (`19,75` vs `8,22 tok/s`) et **Génération ×1,48** (`1,57` vs `1,06 tok/s`, `119 s` vs `182 s` sur 180 tok). | Sur R720 64 Go actuels : monte l'hôte `.201` à `57/62 Go` (`5,7 Go` dispos, `~800 Mo` swap) et disque `.110` à `79 %` (`16 Go` libres). Pour basculer H24 en confort total : purger un modèle legacy non routé sur `.110` + réduire l'enveloppe vide de `VM 140` ou ajouter de la DDR3 ECC dans les 16 slots libres du R720. |
| **B. Petit GPU PCIe ≤8 Go + RAM R720** | Le GPU absorbe le *prompt processing* (gros contexte Cline / RAG) et le KV Cache ; les Xeon + RAM servent les experts MoE (`-ot`). | Privilégier une carte **≤75 W sur slot PCIe sans câble d’alim Dell propriétaire** : ex. **NVIDIA Tesla P4 (8 Go, ~60–80 €)** ou **Quadro T1000 / RTX A2000**. *(Bonus `.201` : les ventilos châssis à 100 % refroidissent parfaitement une Tesla P4 passive — cf. [`runbook_r720_idrac_hs.md`](runbook_r720_idrac_hs.md)).* |

**Décision actuelle (MAJ 2026-11-25 — Jalon 3–4 décembre 2026)** :
- Upgrade prévu les **3–4 décembre 2026** : PC `.10` passe sur **MSI RTX 3060 VENTUS 2X 12G OC** (12 Go VRAM) et la **GTX 1050 Ti (4 Go, Pascal `sm_61`)** remplace la vieille `Tesla M2090` (`42:00.0`, Fermi obsolète) déjà montée sur le riser GPU de `.201` (`intel_iommu=on iommu=pt` déjà actif).
- Priorité d'affectation de la GTX 1050 Ti sur `.201` : **passthrough PCIe vers VM `143` (`lbg-omarchy`)** pour l'accélération matérielle H24 WebGL Three-VRM / Blender / NVENC + CUDA MusicGen (alternative : driver hôte Proxmox partagé aux LXC). Aucun changement sur `reason_route_matrix()` d'ici le montage physique.

---

## Hors scope

- Push `LBG_REASON_EPHEMERAL_*` vers `.140`  
- Remplacer Atlas / audit Ollama par un notebook  
- Héberger un tunnel public H24 vers un Colab  
- AirLLM / layer-streaming sur le chemin Studio H24
