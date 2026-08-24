# Audit LLM local — VM 110 (Ollama H24)

**Date** : 2026-08-16  
**Hôte** : `192.168.0.110` — Ollama heavy (CPU only). **Pilot canonique = `.140:8080`**, pas 110.

---

## État matériel (audit live)

| Ressource | Valeur |
|-----------|--------|
| RAM CT | **24 Gi** |
| GPU | **Aucun** (inférence CPU uniquement) |
| Ollama | `0.32.13` (requis pour `qwen3.8:27b`) |
| Swap | 2 Gi |

---

## Modèles installés sur 110

| Modèle | Taille | Usage |
|--------|--------|-------|
| `qwen3.8:27b` | ~18 Go | **Code / PM / dialogue** (bench août 2026 > `gemma4:26b`) |
| `gemma4:e2b` | ~7 Go | **Forge Iris**, jobs planner, failover light→heavy |
| `gemma4:26b` | ~18 Go | Legacy — ne plus router (reste disque, pas résident) |
| `gemma4-claude:latest` | ~18 Go | Variante 26b (alias) |

Light **`.111`** : `qwen2.5:3b` (Clean) + `llama3.2:3b` (Fast) — **pas** `gemma3:4b`.

> **Matrice dual 110/111 (canonique)** : [`docs/local_llm_route_matrix.md`](local_llm_route_matrix.md)

Appels Qwen : **`think: false`** sinon réponses vides / CPU brûlé.

---

## Matrice profils LBG

| Cas d'usage | Variable | Modèle |
|-------------|----------|--------|
| Dialogue PNJ (local) | `LBG_DIALOGUE_LLM_MODEL` | `qwen3.8:27b` |
| Dialogue rapide (cloud) | `LBG_DIALOGUE_FAST_MODEL` (+ `GROQ_MODEL_*`) | Groq ex. `qwen/qwen3.6-27b` — contrôlé par Atlas (`dialogue_fast_groq`) |
| Forge GDScript Iris | `LBG_REASON_MODEL_FORGE` | `gemma4:e2b` |
| Code | `LBG_REASON_MODEL_CODE` | `qwen3.8:27b` |
| Brief PM / synthèse | `LBG_REASON_MODEL_PM` | `qwen3.8:27b` |
| Jobs Cowork planner | `LBG_JOBS_PLANNER_LLM_MODEL` | `gemma4:e2b` |

---

## Tuning CPU (110 sans GPU)

```bash
# /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment=OLLAMA_MAX_LOADED_MODELS=1
Environment=OLLAMA_NUM_PARALLEL=1
```

Ne pas charger **27b + e2b** simultanément — swap / OOM.

Timeouts conseillés :
- `gemma4:e2b` : 45–90 s (forge)
- `qwen3.8:27b` : 180–300 s (dialogue / code CPU ~0.2 tok/s)

---

## Audit automatisé

```bash
bash infra/scripts/audit_ollama_110_lan.sh
```

Module : `orchestrator/team/ollama_audit.py`  
Timer équipe : `lbg-team-ops-ollama-job` (toutes les 6 h) → tâche ops audit complète.

---

## Chaîne failover actuelle (lbg.env)

1. **Dialogue auto** : Groq fast → `qwen3.8:27b` local
2. **REASON forge** : `gemma4:e2b` local → cloud si `LBG_REASON_FAILOVER=1`
3. **110** reste le socle H24 ; le poste **10** n'est pas requis pour l’inférence
