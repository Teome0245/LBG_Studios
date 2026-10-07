# Joueurs IA — compte · perso IG · pont hors-jeu

**Date** : 2026-10-07 · **Runtime** : [`RUNTIME_GODOT.md`](../RUNTIME_GODOT.md)  
**Admin** : [`ADR 0006`](../../packages/cortex/docs/adr/0006-lbg-admin-levels-refonte.md)  
**Modes** : [`ADR 0004`](../../packages/cortex/docs/adr/0004-assistant-local-vs-persona-mmo.md)

## Principe

| Couche | Qui | Mission |
|--------|-----|---------|
| **PNJ** | Triplons / solos | Monde **fonctionnel** |
| **Perso IG** | Nix, Lia, Mira, Kael… | Jouer le hub |
| **Compte** | login = **persona out-game** | Identité COMPTES + plafond `admin_level` 0–4 |
| **Pont hors-jeu** | `player_bridge_*` | Bridger In ↔ Out + suggestions monde/**dev** |

Le pont **n’est pas** un membre Studio. Certaines suggestions → file Studio ; **pas** de mutation auto.

## Règle login

**`account_login` = `out_game.persona`** (ex. `nix_bridge`), **pas** le nom du personnage IG (`Nix`).

```
COMPTES login: nix_bridge     ← persona out-game
Perso IG:      Nix            ← incarnation hub
Agent pont:    player_bridge_nix
admin_level:   0–4 (ADR 0006) — privilèges en jeu (GM/mod/…)
```

Migration **faite** 2026-10-07 : `Bot_IA*` → `*_bridge` (persos IG conservés). `account_login_legacy` = audit.

## Exemple cible

| Perso IG | Login compte (cible) | Legacy | admin | Pont |
|----------|----------------------|--------|-------|------|
| Nix | `nix_bridge` | Bot_IA_2 | 0 | `player_bridge_nix` |
| Lia | `lia_bridge` | Bot_IA | **1 gm** | `player_bridge_lia` |
| Mira | `mira_bridge` | Bot_IA_3 | 0 | `player_bridge_mira` |
| Kael | `kael_bridge` | Bot_IA_4 | 0 | `player_bridge_kael` |

Humains : même grille admin ; pont hors-jeu optionnel.

## Ops COMPTES

Comptes Prime `.246` (login = persona out-game) :

| Login | ID | admin | Perso IG hub | enabled hub |
|-------|----|-------|--------------|-------------|
| `lia_bridge` | 4 | 1 gm | Lia | oui |
| `nix_bridge` | 9 | 0 | Nix | oui |
| `mira_bridge` | 11 | 0 | Mira | oui |
| `kael_bridge` | 13 | 0 | Kael | oui |
| `renn_bridge` | 14 | 0 | Renn | **oui** |
| `sola_bridge` | 15 | 0 | Sola | **oui** |
| `vex_bridge` | 16 | 0 | Vex | **oui** |
| `ori_bridge` | 17 | 0 | Ori | **oui** |
| `tess_bridge` | 18 | 0 | Tess | **oui** |
| `bram_bridge` | 19 | 0 | Bram | **oui** |

Nouveau joueur : login = persona · perso IG ≠ login · sync `ai_players.json` · `enabled: true` · redeploy.

## Anneau désert (C13)

Périmètre explore hors murs : [`explore_ring_lh.json`](../../packages/prime-hub/data/life/explore_ring_lh.json) (`max_radius_m`, défaut **3000**).

- Autonomy charge waypoints + sample aléatoire dans l’anneau (`hub_bot_autonomy.gd`).
- `POST /v1/bots/move_to` est **clampé** au rayon (hub_sim).
- Skill runtime : `data/agent/skill.md` · manuel canon : [`AGENT_SKILL_MMO.md`](../../packages/cortex/docs/AGENT_SKILL_MMO.md).
- Hors scope : Scrapaltai entière, Zalem jouable (V10b).

Ajuster le rayon : éditer `max_radius_m` → `bash packages/cortex/infra/scripts/deploy_prime_hub_246.sh`.

## Suggestions

`POST /v1/dev/world_suggestions` porte `from` (IG), `agent_id`, `account_login` (persona), `admin_level`, `kind` (`…` \| `dev`).

Data : [`ai_players.json`](../../packages/prime-hub/data/life/ai_players.json) · bootstrap : `GET /v1/agent/bootstrap` → `roster`.
