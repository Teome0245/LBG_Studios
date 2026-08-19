# Clients Godot — 2D top-down vs 3D (parallèle)

**Canon** : [`docs/REGISTRE.md`](../../docs/REGISTRE.md) · client produit = **`packages/prime-client`**.

**Statut** : **priorité = Prime Client 2D** ; 3D gelée (legacy `lbg_client_godot`, ne pas réimporter).

## Décision actuelle

| Priorité | Client | Statut |
|----------|--------|--------|
| **Active** | **Prime Client** (2D top-down) | Produit O2 — bots, carte, POI, Core3 |
| **Gelé** | Prime Client 3D (`lbg_client_godot`) | Legacy `LBG_IA_MMORPG` — reprise plus tard |
| **Piste future** | Hybride type **Warcraft 3** | À définir |

> Pipeline **Infographiste_IA** → sprites / assets 2D vers **Prime Client** ; mesh 3D via [TRELLIS.2](https://microsoft.github.io/TRELLIS.2/) (R&D, [`jalon_trellis2_pygmalion.md`](jalon_trellis2_pygmalion.md)).

## Vue d’ensemble

| Client | Projet Godot | Mode | Rôle |
|--------|--------------|------|------|
| **Prime Client** | `LBG_Studios/packages/prime-client` | **2D top-down** | Client produit → Prime `.246` |
| **Prime Client 3D** | `LBG_IA_MMORPG/.../lbg_client_godot` | **3D** | Gelé — lab assets uniquement |

Runtime VM **140** (sondes / Iris) : encore **`/opt/new_mmo/prime-client`** via `LBG_PRIME_CLIENT_ROOT` — pas le même dossier que le Git Studios.

## Godot 4.6 (poste dev)

```
J:\mmmorpg\Godot_v4.6.1-stable_win64\Godot_v4.6.1-stable_win64.exe
```

| Projet à ouvrir | Chemin |
|-----------------|--------|
| Prime Client (source) | `/home/sdesh/projects/LBG_Studios/packages/prime-client` |
| Prime Client (Windows sync) | `J:\swgemu\clients\prime-client` |
| Prime Client 3D | `/home/sdesh/projects/LBG_IA_MMORPG/LBG_IA_MMO/lbg_client_godot` (gelé) |

> `LBG Client (4.3)` et `mmmorpg` (J:) = **archives** — ne pas utiliser.

## Quand utiliser lequel ?

| Besoin | Client recommandé |
|--------|-------------------|
| Positions bots, POI, hub LH, playtest | **Prime Client** (2D) |
| Tester un GLB / cantina 3D | **3D gelé** — Infographiste d’abord |
| Sprites unités top-down | **Infographiste_IA** → **Prime Client** |
| Dialogue IA / gateway Prime | Prime Client 2D |

## Lancement rapide (2D)

```bash
godot4 --path /home/sdesh/projects/LBG_Studios/packages/prime-client
```

Smoke : [`packages/prime-client/SMOKE.md`](../prime-client/SMOKE.md) · [`docs/SMOKE_LAN.md`](../../docs/SMOKE_LAN.md).

## Liens

| Doc | Sujet |
|-----|--------|
| [`client_dual_launchpad.md`](client_dual_launchpad.md) | Clients natifs PreCu / Prime (hors Godot) |
| [`jalon_infographiste_ia.md`](jalon_infographiste_ia.md) | Pont assets IA → Godot |
| [`local_llm_route_matrix.md`](local_llm_route_matrix.md) | LLM 110/111 |
