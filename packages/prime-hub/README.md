# prime-hub — autorité Lost Heaven (Godot headless)

**Statut 2026-10-07 G5** : **prod joueur** sur `.246` — **HTTP+WS unifiés `:8787`**, peel natif (plus de Python).

## Phases

| Phase | Notes |
|-------|--------|
| G0–G4a | Scaffold → cutover → A* → resume position |
| **G5** | Auth, inventaire, quêtes, craft, catalog C10, dialogue ; port unique |

## Ports

| Service | Port |
|---------|------|
| **prime-hub** | **8787** (HTTP + `ws://…/ws`) |
| Python hub_runtime | OFF |
| Core3 | hors chemin joueur |

Voir [`docs/RUNTIME_GODOT.md`](../../docs/RUNTIME_GODOT.md).

## Deploy

```bash
bash packages/cortex/infra/scripts/deploy_prime_hub_246.sh
bash packages/prime-client/tools/deploy_prime_client_patch_246.sh
```
