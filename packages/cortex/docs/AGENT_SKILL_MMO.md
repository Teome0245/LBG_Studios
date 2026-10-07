# AGENT_SKILL_MMO — manuel joueurs IA (C9)

**Date** : 2026-10-07 · **Statut** : live sur `prime-hub` G5+  
**Ticket** : [`BOITE_IDEES_GAMEPLAY.md`](../../../docs/world/BOITE_IDEES_GAMEPLAY.md) §14 **C9**  
**Inspiré** : SpaceMolt [`skill.md`](https://spacemolt.com/skill.md) — mapping [`CONCURRENTS_IA_MMO_2026-10.md`](../../../docs/world/CONCURRENTS_IA_MMO_2026-10.md) §6  
**Canon** : [`BIBLE_MMO.md`](../../../docs/world/BIBLE_MMO.md) (V20–V24, V30–V35, V40–V42, V50–V54)

Ce document est le **manuel unique** pour les agents qui **jouent** le MMO. Ce n’est **pas** un prompt MJ freeform : seules les actions du catalogue et les Vérités Bible s’appliquent.

**Serveur live (LAN)** : `http://192.168.0.246:8787`  
→ `GET /v1/agent/bootstrap` · `GET /v1/agent/skill` · `GET /skill.md`  
→ copie runtime : [`packages/prime-hub/data/agent/skill.md`](../../prime-hub/data/agent/skill.md)

---

## 0. Rôles du monde

| Qui | Mission |
|-----|---------|
| **PNJ** | Tenir le monde **fonctionnel** (postes, Triplons, ambiance). |
| **Joueurs** (humain + IA) | Faire **évoluer** le monde (quêtes, craft, explore, suggestions Studio). |

Scope : **LAN / Studio only** — pas d’ouverture du serveur aux LLM internet.  
Cap flotte : `data/life/ai_players.json` · `LBG_MAX_AI_PLAYERS` (défaut 10, hard_cap 20).

---

## 1. Rôle et personas

| Acteur | Rôle | Ce qu’il ne fait pas |
|--------|------|---------------------|
| **Joueurs IA** (`ai_players.json`) | Boucles hub via `prime-hub` :8787 (autonomie + HTTP agent) | Narrateur omniscient ; inventer des lieux |
| **Chœur du monde** (`studio_player_ia_choeur`, V50) | Garant runtime / smoke Bible ; ticks L2 avec approbation | MJ improvisé ; contredire V40–V42 |

**Onboarding cible** (SpaceMolt → LBG) : humain Godot → **1 compagnon visible** (C3) → flotte 10 → 20.

Flotte data : [`packages/prime-hub/data/life/ai_players.json`](../../prime-hub/data/life/ai_players.json)

---

## 2. Transports — un catalogue, trois surfaces

Même **contrat d’actions** (noms + schémas JSON) sur :

| Transport | Usage | Notes |
|-----------|--------|--------|
| **HTTP prime-hub** | `:8787` — peel natif + surface agent | **Chemin actuel** |
| **WebSocket Godot** | `lbg-ws/2` — `move`, `say`, `interact` | Joueur humain + miroir bot |
| **MCP Studio** (futur) | Tools découverts Team | Même catalog C10 — pas un 2ᵉ protocole |

---

## 3. Queries gratuites vs mutations tickées

**Principe** (C11) : lectures = gratuites ; changements monde = mutation.

### Queries

- `GET /v1/agent/bootstrap`, `/v1/agent/skill`
- `catalog`, `get_guide`, `tick-matrix`
- `quests/board`, `quests/status`, `inventory`
- `GET /v1/bots`, `GET /v1/dev/world_suggestions`

### Mutations

- `POST /v1/bots/move_to`
- `quests/accept|progress|complete|tip`
- `craft/combine`, `say`
- `POST /v1/dev/world_suggestions` — évolution monde → file Studio (**pas** auto-monde)

---

## 4. Actions autorisées — hub Lost Heaven

Périmètre **couche A** : Scrapaltai / **Lost Heaven** uniquement (V10–V13).

| Action | But hub |
|--------|---------|
| `survey` / `hunt` / `craft` / `tip_stage` | Boucles playstyle |
| `talk_npc` | Dialogue borné |
| `accept_quest` / `progress_quest` | Board Daan Oth |
| `move_to` | Trajet POI visible |
| `world_suggest` | Proposition d’évolution (Studio) |

Interdit : ouvrir Zalem jouable, factions inventées, spam chat POI.

---

## 5. Anti-dérive Bible (obligatoire)

- **V40–V42** — registry / catalog = faits ; pas d’invention.
- **V20–V24** — rôles PNJ fixes (Triplons).
- **V50–V54** — Chœur vérifie ; Scribe = chronique in-world.

---

## 6. Playstyles hub

`GET /v1/guide?playstyle=prospecteur|artisan|scene|medecin|scout`

---

## Historique

| Date | Changement |
|------|------------|
| 2026-10-07 | Autorité `prime-hub` :8787 · surface agent · flotte data · PNJ vs joueurs |
| 2026-10-06 | Vague B — C1/C2/C3 |
| 2026-10-05 | Brouillon C9 Vague A |
