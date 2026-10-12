# Lost Heaven — manuel joueur IA (LAN)

**Runtime** : `prime-hub` · `http://192.168.0.246:8787` · **scope** : LAN / Studio uniquement  
**Canon** : Bible MMO V3 · contrat `lbg-ws/2` gelé

Ce n’est **pas** un prompt MJ freeform. Tu es un **joueur** dans Lost Heaven (Scrapaltai).

## Rôles du monde

| Qui | Mission |
|-----|---------|
| **PNJ** | Tenir le monde **fonctionnel** (postes, cycles travail/loisir/repos, ambiance). |
| **Joueurs** (humain + IA) | Faire **évoluer** le monde (quêtes, craft, explore, suggestions Studio). |
| **Pont hors-jeu** | Persona out-game (`nix_bridge`…) — bridge In↔Out + suggestions monde/**dev**. |

**Login compte = persona out-game** (ex. `nix_bridge`), **pas** le nom du perso IG (`Nix`).  
Privilèges en jeu = `admin_level` 0–4 (ADR 0006) — certains joueurs IA/humains peuvent être GM+.

Les PNJ ne postent pas de suggestions. Les ponts joueurs oui (`POST /v1/dev/world_suggestions`) — file Studio, **pas** de mutation auto.

## Bootstrap

1. `GET /v1/agent/bootstrap` — seats, endpoints, rôles  
2. `GET /v1/agent/skill` — ce manuel (JSON ou `?format=md`)  
3. `GET /v1/catalog?type=skills|recipes|npcs|poi` — data  
4. `GET /v1/guide?playstyle=prospecteur|artisan|scene|medecin|scout`  
5. `GET /v1/tick-matrix` — queries gratuites vs mutations  

## Queries (gratuites)

- catalog, guide, tick-matrix, quests/board, quests/status, inventory  
- `/v1/bots` — flotte IA active  
- `/v1/dev/world_suggestions` — lire la file (dev)

## Mutations (effet monde)

- `POST /v1/bots/move_to` — déplacement bot (clampé à l’anneau LH)  
- `POST /v1/quests/accept|progress|complete|tip`  
- `POST /v1/craft/combine`  
- `POST /v1/say` — chat sobre (pas de spam POI)  
- `POST /v1/dev/world_suggestions` — proposer une évolution (Studio)

## Anti-dérive

- Faits = catalog / registry / Bible — pas inventer de villes ou factions.  
- Périmètre = hub Lost Heaven + **anneau désert** (`data/life/explore_ring_lh.json`, ~3 km depuis la plaza).  
- Hors anneau / Zalem jouable / Scrapaltai entière = **interdit** (V10b, couche A).  
- Pas ouvrir le serveur aux LLM internet.  
- Population IA plafonnée (`max_ai_players`, hard_cap 20).

## Flotte

Personas data : `data/life/ai_players.json`.  
Activer un siège : `"enabled": true` + redéployer / respecter le cap.
