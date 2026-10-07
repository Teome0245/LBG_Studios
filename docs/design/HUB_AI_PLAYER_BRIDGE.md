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

Legacy temporaire : `Bot_IA` / `Bot_IA_2`… stockés en `account_login_legacy` jusqu’à rename COMPTES.

## Exemple cible

| Perso IG | Login compte (cible) | Legacy | admin | Pont |
|----------|----------------------|--------|-------|------|
| Nix | `nix_bridge` | Bot_IA_2 | 0 | `player_bridge_nix` |
| Lia | `lia_bridge` | Bot_IA | **1 gm** | `player_bridge_lia` |
| Mira | `mira_bridge` | Bot_IA_3 | 0 | `player_bridge_mira` |
| Kael | `kael_bridge` | Bot_IA_4 | 0 | `player_bridge_kael` |

Humains : même grille admin ; pont hors-jeu optionnel.

## Ops COMPTES

1. Créer (ou renommer) le login = persona out-game (`nix_bridge`, …).  
2. Niveau LBG selon besoin (défaut **0** ; Lia = **1 gm** si animation terrain).  
3. Perso IG créé sous ce compte = nom incarné (Nix…), **pas** le login.  
4. `ai_players.json` : `account_login` = persona ; `enabled: true` ; redeploy.

## Suggestions

`POST /v1/dev/world_suggestions` porte `from` (IG), `agent_id`, `account_login` (persona), `admin_level`, `kind` (`…` \| `dev`).

Data : [`ai_players.json`](../../packages/prime-hub/data/life/ai_players.json) · bootstrap : `GET /v1/agent/bootstrap` → `roster`.
