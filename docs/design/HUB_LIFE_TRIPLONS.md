# Vie hub — Triplons, autonomie IA, suggestions monde

**Date** : 2026-10-07 · **Runtime** : [`RUNTIME_GODOT.md`](../RUNTIME_GODOT.md) (`prime-hub` G5+)

## Objectif

Donner l’impression d’une population vivante **sans** spammer le chat ni faire tourner tout le monde en rond.

**Règle produit** : les **PNJ** maintiennent un monde fonctionnel ; les **joueurs** (humain + IA) le font évoluer. Scope = **LAN / Studio** (pas d’ouverture publique LLM).

| Acteur | Comportement |
|--------|----------------|
| **Joueurs IA** | Flotte `ai_players.json` (4 actifs, 6 prêts → vague 10) · quête / explore / hub · suggestions → Studio |
| **PNJ Triplon** (3–4) | Cycle **travail → loisir → repos** ; 1 off ≈ ⅓ de la pop visible |
| **Objectifs** | court / moyen / long par persona — anti « couloir plaza→market » |

Surface agent : `GET /v1/agent/bootstrap` · `GET /v1/agent/skill` · manuel [`packages/prime-hub/data/agent/skill.md`](../../packages/prime-hub/data/agent/skill.md)

## Triplon (esquadre)

Groupe de **3** (parfois 4) partageant un **poste de travail** (ex. instructeur medic).

À tout moment (idéalement) :

| Phase | Où | Visible |
|-------|-----|---------|
| `work` | Poste (clinique, board, atelier…) | oui |
| `leisure` | POI aspiration (cantina, scène, dunes…) | oui |
| `rest` | « Chez soi » (auberge / logement) | **non** (désactivé / hors zone_state) |

→ **≈ 2/3 actifs**, **1/3 off**, poste toujours tenu par quelqu’un.

Durées cibles (simulées, pas horloge réelle) : work 8–14 min · leisure 5–10 min · rest 6–12 min (accélérable en lab).

## Objectifs persona

```
short  — action immédiate (aller au board, finir un step)
medium — arc session (terminer 1 quête, explorer porte est)
long   — aspiration (devenir référence marché, surveiller Zalem…)
```

Les goals de déplacement découlent de `short` ; `medium`/`long` biaisent le tirage.

## Suggestions monde (off → Studio)

Les joueurs IA (et plus tard PNJ) écrivent dans `data/world_suggestions.jsonl` :

```json
{"ts":…,"from":"Mira","kind":"poi|quest|npc|economy","text":"…","context":{}}
```

HTTP **dev** : `GET /v1/dev/world_suggestions` · `POST /v1/dev/world_suggestions` (pas exposé joueur).  
Pilot/Team lit la file ; pas de mutation monde automatique (anti double-build).

## Hors scope MVP

- Navmesh Godot (A* grille suffit)
- Combat / cour de chasse (P5a ensuite)
- Persona compagnon joueur (P3 parallèle)
- LLM pour chaque choix de bot (règles data-driven d’abord)

## Fichiers

- `packages/prime-hub/data/life/triplons.json`
- `packages/prime-hub/scripts/hub_life.gd`
- `packages/prime-hub/scripts/hub_bot_autonomy.gd`
- `packages/prime-hub/scripts/hub_world_suggest.gd`
