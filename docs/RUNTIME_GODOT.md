# Runtime joueur Lost Heaven — Godot-first (G5)

**Date** : 2026-10-07  
**ADR** : [`0026-runtime-hors-core3.md`](../packages/cortex/docs/adr/0026-runtime-hors-core3.md)

## Autorité actuelle

| Rôle | Process | Port | Statut |
|------|---------|------|--------|
| **Monde + peel HTTP + WS** | `lbg-prime-hub` (Godot headless) | **8787** (HTTP+WS unifiés) | **Prod joueur** |
| hub_runtime Python | — | — | **Arrêté** (peel porté) |
| Core3 Prime / bots / gateway | — | — | **Hors chemin joueur** |

Client : `packages/prime-client/config/hub_runtime.json`  
→ `http_url` **et** `ws_url` sur `:8787`

## Peel natif (G5)

- Auth : `/v1/auth/login|guest|select_character|enter_zone|resolve`
- Inventaire / board / quêtes / tip / craft
- Catalog C10 + guide + tick-matrix (snapshots `data/catalog_*.json`)
- Dialogue invoke (+ LLM Ollama optionnel `.110`)
- Persistance : `data/accounts.json`, `players_state.json`, `player_positions.json`

## Ops

```bash
bash packages/cortex/infra/scripts/deploy_prime_hub_246.sh
bash packages/cortex/infra/scripts/stop_core3_player_path_246.sh --also-prime
bash packages/prime-client/tools/deploy_prime_client_patch_246.sh
```

## Anti double-build

Contrat `lbg-ws/2` + HTTP C10/C11 **gelé**. Process = Godot only.
