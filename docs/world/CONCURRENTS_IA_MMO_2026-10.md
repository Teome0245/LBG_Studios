# Veille concurrents IA / MMO — 2026-10

**Date** : 2026-10-05  
**Statut** : extrait vivant — **n’écrit pas de Vérité** sans décision datée dans [`BIBLE_MMO.md`](BIBLE_MMO.md)  
**ADR** : [`../adr/0002-veille-concurrents-ia-mmo.md`](../adr/0002-veille-concurrents-ia-mmo.md)  
**Tickets gameplay** : [`BOITE_IDEES_GAMEPLAY.md`](BOITE_IDEES_GAMEPLAY.md) §14  
**Canon produit** : [`PLAN_MMO_O2.md`](../PLAN_MMO_O2.md) · Bible · Chœur

---

## 0. Règle de lecture

| On prend | On ne prend pas |
|----------|-----------------|
| UX, boucles, contrats agent, densité contenu hub | Pivot « text adventure only », rewrite UE5, freeform sans Bible |
| Patterns qui renforcent P3 persona + wahou Lost Heaven | Magie / fantasy générique, tokens pay-to-win, megaserver marketing |
| Idées mappables vers registry / EventEngine / M10 / bots | Contredire V40–V42 (invention libre) ou V60–V65 (maturité) |

**Position LBG** : MMO spatial Godot + Core3 Prime, IA **bornée** (Bible + Chœur), boucle craft Pre-CU. Différenciateur = monde cohérent + persona, pas LLM libre.

---

## 1. Cartographie

| Produit | Genre | Lien | Proche LBG ? |
|---------|-------|------|--------------|
| [Everwhere](https://everwhere.app/) | MJ texte multi-genres (AI Dungeon++) | persona persistante, journeys | UX narration / mémoire — pas spatial |
| [Jenova Roleplay GM](https://www.jenova.ai/a/roleplay-game-master) | Chat MJ + mémoire | cohérence personnage | Dialogue PNJ (P3) |
| [Epitome](https://epitomegame.com/) | MMO UE5 + pitch AI NPCs | compagnons, quêtes IA, events | Pitch produit ; prod opaque |
| [World of ClaudeCraft](https://worldofclaudecraft.com/) | Micro-MMO browser classique | sim unique, wiki data, densités | Boucle MMO + archi Team |
| [SpaceMolt](https://spacemolt.com/) | MMO texte **joué par agents IA** | MCP, tick, skill.md, catalog | Contrats bots / Chœur / flotte |

---

## 2. Everwhere — idées retenues / rejetées

**Retenir**

| Idée | Mapping LBG |
|------|-------------|
| Suggestions d’actions + texte libre | Dialogue hub P3 : 2–3 coups proposés + champ libre |
| Persona / mémoire transversale (dettes, rencontres) | Graphe relations + réputation locale → `world_hint` |
| « Journey book » en fin de run | Scribe (N6) : chronique session 5–10 lignes |
| Voix / images optionnelles | Hors P0 ; Compagnon Studio déjà voix |

**Rejeter** : mondes libres sans canon ; permadeath persona comme défaut hub ; pivot text-only.

---

## 3. Jenova RP GM — idées retenues / rejetées

**Retenir**

| Idée | Mapping LBG |
|------|-------------|
| Onboarding « configurer un scénario » | Création personnage / premier contact Lost Heaven |
| Promesse produit « mémoire + cohérence » | Déjà V40–V42 — à **exposer** joueur (pas promettre « illimité ») |

**Rejeter** : mémoire illimitée comme claim marketing ; scénarios hors Scrapaltai sans registry.

---

## 4. Epitome — idées retenues / rejetées

**Retenir**

| Idée | Mapping LBG |
|------|-------------|
| Compagnons IA qui grandissent | Lia/Nix/Mira **joueur-facing** dans le hub (pas seulement Pilot `#/hunt`) |
| Quêtes IA adaptées au playstyle | QuestEngine templates + skills M10 du joueur |
| Négociation marchand | Vendors hub : deltas prix + réputation, bornés |
| Événements dynamiques (monoliths) | Events Scrapaltai : chute scrap, meute portes, panne starport |

**Rejeter** : claims megaserver 33k / UE5 ; contests P2W ; lore Archons générique.

---

## 5. World of ClaudeCraft — idées retenues / rejetées

Sources : [site](https://worldofclaudecraft.com/) · [repo](https://github.com/levy-street/world-of-claudecraft) · [DEV article](https://dev.to/max_polaczuk/stop-benchmarking-ai-coding-agents-on-todo-apps-make-them-build-an-mmo-4ecl)

**Retenir**

| Idée | Mapping LBG |
|------|-------------|
| Une sim, trois hôtes (offline / online / headless) | Smokes Team + bac chasse sans Core3 live |
| Déterminisme / replay | Smokes reproductibles ; météo render-only |
| Wiki généré depuis data live | Guide joueur depuis inventaire PNJ + catalogue M10 + Bible |
| Book of Deeds / chronicles PNJ | Scribe + titres cosmétiques |
| Delve 1–2 j + compagnon IA | Boucle hors palissade (chasse chacals) |
| Procédural = stratégie de scope | Densifier LH sans pipeline art lourd |

**Rejeter** : rewrite Three.js/TS à la place de Godot/Core3 ; token Solana ; scope classic WoW complet.

---

## 6. SpaceMolt — idées retenues / rejetées

Sources : [spacemolt.com](https://spacemolt.com/) · [about](https://spacemolt.com/about) · [skill.md](https://spacemolt.com/skill.md) · [connections](https://spacemolt.com/docs/connections) · [skills](https://spacemolt.com/docs/skills)

**Ce que c’est** : MMO persistant **conçu pour être joué par des agents LLM** (capitaines de vaisseau). Galaxy ~500 systèmes ; mine / trade / explore / pirate / faction. Serveur fermé ; site + clients ref open. Transports : **MCP (préféré)** · WebSocket · HTTP ; catalogue unique.

**Retenir (fort fit LBG bots / Chœur / Team)**

| Idée SpaceMolt | Mapping LBG |
|----------------|-------------|
| **`skill.md` agent manual** | Manuel unique pour bots joueurs IA (Lia/Nix/…) + Chœur — **brouillon** [`AGENT_SKILL_MMO.md`](../../packages/cortex/docs/AGENT_SKILL_MMO.md) (C9) |
| **MCP / outils découverts + schémas JSON** | Surface « agent joue le MMO » : tools bornés (`survey`, `craft`, `talk_npc`, `hunt`, `tip_stage`) plutôt que prose libre |
| **Un catalogue, 3 transports** | Même contrat actions pour Pilot HTTP, WS Godot, éventuel MCP Studio |
| **Tick mutations vs queries gratuites** | Mutations monde (craft, quête, tip) = coût / file ; lectures snapshot = free — protège Core3 + LLM |
| **Réponse duale** `result` texte + `structuredContent` JSON | Dialogue joueur + commit machine (flags, deltas) — pattern déjà proche pont Lyra |
| **`get_guide(playstyle)`** | Guides playstyle hub : Prospecteur / Artisan / Scène / Médecine / Scout — data réelle M10, pas hallucination |
| **`catalog` read-only** | `catalog(type=skills\|recipes\|npcs\|poi)` → M10 + inventaire + POI LH |
| **Progression par usage** (pas de file skill) | Aligné V2 / Pre-CU — renforcer feedback « skill_up » visible |
| **Captaine’s log / notes** | Chronique Scribe + notes perso session |
| **Notifications typées** (combat, craft, faction, system) | Bus événements hub → HUD / Chœur / Pilot |
| **Docs MCP pour codeurs** (`mcp/docs`) | Équivalent : agent Team lit contrats live (OpenAPI sidecar `:8791`) au lieu de conjecturer |
| **3 stages onboarding** : humain → agent → flotte | Humain Godot → 1 bot compagnon → flotte Chœur (Lia/Nix/Mira) |
| **Salvage / wrecks** | Loot scrap hors palissade → craft M10 (fit Scrapaltai) |
| **Faction missions postées** | Board Daan Oth + missions joueur/faction plus tard |

**Rejeter / différer**

| Idée | Pourquoi |
|------|----------|
| MMO 100 % texte / JSON-only | Client produit = Godot spatial (V3) |
| Galaxy 500 systèmes comme scope v1 | Hub Lost Heaven d’abord (couche A) |
| Combat tick-based spatial flotte | Hors vitrine courte (V34) |
| Empires PvP / piracy comme boucle centrale | Tone hub civil Scrapaltai |
| Registration codes / dashboard agent public | LAN Studio d’abord ; pas ouvrir le serveur aux LLM internet |

**Leçon méta** : SpaceMolt prouve qu’un **contrat d’actions machine-readable** + manuel agent + tick est plus important qu’un « bon prompt MJ » pour faire jouer des IA dans un monde persistant. LBG a déjà les bots et le pont ; il manque surtout le **manuel + catalogue d’outils** unifiés.

---

## 7. Synthèse priorités (3 moves + 2 arches)

### Moves produit (court terme — wahou / P3)

1. **Dialogue suggestions + mémoire dette** (Everwhere / Jenova)  
2. **Compagnon IA visible au spawn LH** (Epitome + bots existants)  
3. **1 event dynamique board** (Epitome → Scrapaltai)

### Arches technique (moyen terme)

4. **Wiki / guide auto** depuis data (ClaudeCraft)  
5. **Agent skill + catalog tools + tick mutations** pour joueurs IA (SpaceMolt → Chœur / sidecar)

Détail tickets : [`BOITE_IDEES_GAMEPLAY.md`](BOITE_IDEES_GAMEPLAY.md) §14.

---

## Historique

| Date | Changement |
|------|------------|
| 2026-10-05 | Première veille : Everwhere, Jenova, Epitome, ClaudeCraft, SpaceMolt |
