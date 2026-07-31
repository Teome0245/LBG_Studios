# Migration gateway Godot — hôte Prime 246

**Date** : 2026-07-22  
**Décision** : le gateway M11/M12 (HTTP auth + WS `lbg-ws/2`) vit sur **Prime `192.168.0.246`**, pas sur PreCU **245**.

| Avant (transition) | Après (produit) |
|--------------------|-----------------|
| HTTP `192.168.0.245:8765` | HTTP **`192.168.0.246:8765`** |
| WS `192.168.0.245:50000` | WS **`192.168.0.246:50000`** |
| SQL via réseau 246 | SQL **locale** `127.0.0.1` sur 246 |

## Pourquoi

- Snapshots / zone bridge / Core3 Prime sont déjà sur **246**.
- Évite un hop inutile 245→246 pour l’auth et le live.
- **245** reste PreCU / sandbox legacy.

## Actions équipe

| Rôle | Action |
|------|--------|
| **Hermès** | `LbgAuthClient` / `LbgWsClient` → défauts `246` ; smokes M11/M12 |
| **Thémis** | Contrat M11↔M12 : `ws_url` = `ws://192.168.0.246:50000` |
| **Argus** | Smokes pointent 246 ; activer `LBG_TEAM_GODOT_GATEWAY_SMOKE=1` sur 140 |
| **Dédale** | Zone bridge feed inchangé (fichiers sur 246) |
| **Ops** | `bash infra/scripts/run_lbg_gateway_vm.sh` (défaut 246) |

## Vérif

```bash
curl -s http://192.168.0.246:8765/health
bash infra/scripts/smoke_godot_m11_login_lan.sh
bash infra/scripts/smoke_godot_m12_ws_lan.sh
```
