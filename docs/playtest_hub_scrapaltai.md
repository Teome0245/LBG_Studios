# Playtest hub Scrapaltai / Lost Heaven — checklist O2

**Date** : 2026-08-12  
**Mission Team** : `pilot:o2_backlog` O2-3  
**Sources** : [`BIBLE_MMO.md`](../world/BIBLE_MMO.md) · [`INVENTAIRE_PNJ.md`](../world/INVENTAIRE_PNJ.md) · [`SMOKE_LAN.md`](SMOKE_LAN.md)

## Critère de done (session humaine)

Une session est **verte** si les 3 blocs passent sans workaround manuel hors Launchpad.

### A — Login produit (M11 / M12)

| # | Check | Comment |
|---|--------|---------|
| A1 | Launchpad → client Godot `prime-client` | |
| A2 | Login compte LBG (ex. Teome) → sélection perso | |
| A3 | Entrée zone WS → entités visibles | Smoke M11/M12 OK côté Team |
| A4 | Move personnage OK | |

### B — Hub Scrapaltai / Lost Heaven

| # | Check | Vérité Bible |
|---|--------|--------------|
| B1 | UI / dialogue **ne** disent pas « Tatooine » / « Mos Eisley » | C0 |
| B2 | Map / minimap hub visible (M9) | Couche A hub |
| B3 | Au moins 1 POI cantina / starport identifiable | Inventaire §1 |
| B4 | Ancres PNJ LH chargées (`lost_heaven_npc_anchors.json`) | |

### C — Présence IA (sidecar)

| # | Check | Attendu |
|---|--------|---------|
| C1 | Sidecar `.246:8791/healthz` | 3 bots online (Lia / Nix / Mira) |
| C2 | Miroir Godot snapshots | online ≥ 3 |
| C3 | Bots visibles / sonde Chœur | `player_ia` |

## Gaps lore connus (ne bloquent pas le smoke)

- Wording **debt_me** sur certains pilots (ex. Garr Vek) — à migrer Lost Heaven
- Fantasy stubs gelés (loups / auberge générique) — ne pas propager
- GLB 3D Infographiste : phase suivante (manifests 2D OK, couverture GLB = 0)

## Commandes ops (Team / LAN)

```bash
# Superviseur Godot (Argus)
bash packages/cortex/infra/scripts/diag_godot_supervisor_wsl.sh --summary

# Ou enqueue CT executor .141
curl -s -X POST http://192.168.0.140:8010/v1/team/wsl/tasks \
  -H 'Content-Type: application/json' \
  -d '{"wsl_skill":"diag_godot_supervisor","objective":"Playtest hub recheck","actor_id":"pilot:playtest"}'

# Surfaces LAN
bash tools/smoke_lan_surfaces.sh --functional
```

## Suivi Team

| Étape | Rôle | Statut 2026-08-13 |
|-------|------|-------------------|
| O2-1 lbg-ws/2 schémas | Hermès / audit | **vert** |
| O2-2 Infographiste manifests | Pygmalion | **vert** |
| O2-3 Brief playtest | PM + ce doc | **checklist prête** |
| O2-4 Re-supervise | Argus | **vert** (0 advisory) |
| ZB-1 feed live JSON Prime | Core3 | **vert** (tick frais, 3 entities, SSH `.246`) |
| Smoke M11 + M12 | Argus / owners | **vert** (`BUNDLE=godot_login`) |
| Smoke M9 minimap | Iris | **KO** — chemins legacy `new_mmo` (hors critère hub login) |
| Smoke M10 craft | Iris | **vert** |
| Session humaine hub | Teome | **à faire** (Launchpad) |
