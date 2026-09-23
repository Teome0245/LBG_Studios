# Lab Open WebUI — LBG Simple Chat (P4)
#
# Rôle : UI chat seule (comme le panneau chat Cursor), pour piloter idées /
# questions LLM **sans** utiliser le chat Cursor comme cockpit projet.
#
# - Pilot (.140:8080) = hub Studio / ops / équipe
# - Open WebUI (.100:3080) = Simple Chat → Ollama .110/.111
# - Interdit P4 : Team, Desktop, approvals, jobs

## Déploiement (.100)

```bash
# depuis le monorepo
bash packages/cortex/infra/open_webui/deploy_100.sh
```

URL : http://192.168.0.100:3080/

## Providers

Après démarrage, dans Admin → Connections :
- Ollama : `http://192.168.0.110:11434` (déjà via `OLLAMA_BASE_URL`)
- Optionnel light : ajouter `http://192.168.0.111:11434` comme 2ᵉ Ollama

Modèles attendus (matrice locale) :
- `.110` : `huihui_ai/Qwen3.8-abliterated:27b`, `gemma4:e2b`
- `.111` : `qwen2.5:3b`, `llama3.2:3b`

## Arrêt

```bash
ssh lbg@192.168.0.100 'cd /home/lbg/lbg-open-webui && docker compose down'
```
