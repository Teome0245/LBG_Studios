# Runtime joueur Lost Heaven — Godot-first (post-cutover)

**Date** : 2026-10-07  
**ADR** : [`0026-runtime-hors-core3.md`](../packages/cortex/docs/adr/0026-runtime-hors-core3.md)

## Autorité actuelle

| Rôle | Process | Port | Statut |
|------|---------|------|--------|
| **Monde / move / bots / PNJ / chat** | `lbg-prime-hub` (Godot headless) | **WS 8787** | **Prod joueur** |
| **HTTP peel** (auth, inventaire, quêtes, craft, dialogue, catalog) | `lbg-prime-hub` → proxy | **HTTP 8789** | Prod (proxy) |
| Peel backend | `lbg-hub-runtime` (Python) | **8797** lab | **Conservé** jusqu’à peel natif Godot |
| Core3 Prime + bots IA + gateway | systemd divers | 50000 / sidecar | **Hors chemin joueur** — couper via script |

Client : `packages/prime-client/config/hub_runtime.json`  
→ `ws_url` `:8787` · `http_url` `:8789`

## Équivalent Core3 rapatrié (hub)

- Marche humaine + collision AABB  
- Flotte Nix / Lia / Mira / Kael (goals POI + A*)  
- PNJ hub vivants (wander + ambient)  
- Chat + greet flotte  
- Reprise position joueur (serveur `data/player_positions.json` + LastPos client)

## Pas encore sur Godot (bloque l’arrêt du spike Python)

1. Auth / sessions HTTP natives  
2. Inventaire / board / accept-progress-complete quêtes  
3. Craft + catalog C10  
4. Dialogue invoke (LLM)  
5. (option) HTTP+WS unifié sur un seul port  

Tant que cette liste n’est pas verte : **garder** `lbg-hub-runtime` sur `:8797`.

## Ops

```bash
# Déployer hub Godot
bash packages/cortex/infra/scripts/deploy_prime_hub_246.sh

# Cutover ports (déjà fait en G4)
bash packages/cortex/infra/scripts/cutover_prime_hub_g4_246.sh

# Couper bots Core3 + gateway (+ option --also-prime)
bash packages/cortex/infra/scripts/stop_core3_player_path_246.sh
bash packages/cortex/infra/scripts/stop_core3_player_path_246.sh --also-prime

# Patch client Launchpad
bash packages/prime-client/tools/deploy_prime_client_patch_246.sh
```

## Anti double-build

Contrat `lbg-ws/2` + HTTP C10/C11 **gelé**. On change la boîte (Godot), pas le protocole client.
