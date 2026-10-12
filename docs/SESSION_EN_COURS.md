# Session en cours — LBG Studios

**Mis à jour** : 2026-10-12  
**Branche** : `cursor/priorit-s-actuelles-lbg-studios-d491`  
**Outil** : partagé Cursor ↔ Antigravity — **lire au démarrage, mettre à jour avant de partir**.  
**Backlog non traité** : [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md)

---

## Objectif actuel

Continuité multi-outils : même canon O1/O2 pour Antigravity et Cursor.  
Travail produit sous-jacent (inchangé) : Compagnon D6 vert + hub Godot P3–P5 sans rouvrir le legacy.

## Snapshot priorités (voir détail dans PRIORITES_ACTUELLES)

| Rail | État |
|------|------|
| **O1 Compagnon** | D0–D6 OK (smoke D6 V6–V8 PASS 2026-10-06) ; gate *feeling* ouverte — `FOCUS_COMPAGNON.md` |
| **O1 ops** | Lot gaps A–F2 + tick L3 livré 2026-10-07 ; L3 **DONE** `days_ok=3/3` (2026-10-11) |
| **O2 hub** | P6 Godot-first G5+ **live** (`.246:8787`) ; P3 wiki live ; P5 telegraph boss **vert** 2026-10-08 ; **2.3 navmesh `NavigationServer3D` LIVE** 2026-10-11 |
| **Interdit** | Core3 / gateway SOE / `hub_runtime` Python sur chemin joueur |

## Prochaines actions (à ajuster en fin de session)

Backlog explicite : [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md) (mis à jour 2026-10-12 post-L3 DONE).

1. **Plan d'évolutions (10/10 tickets)** : **100 % réalisé & clôturé** (tickets 1.1..1.3, 2.1..2.3, 3.1, 3.2, 5.1, 5.2 DONE).
2. **Feeling Compagnon O-FEEL-1/2 (rejeu humain `:5174`)** : **validé & clôturé** (C1/C2/PLAN/GO ALL PASS).
3. **Prochaines pistes** : **O-FEEL-3** (retour terrain présence long) · **O-IDE-1..3** (Cline) · Ops `smoke_lan_surfaces.sh`.
4. Handoffs Antigravity historiques : **clos** (sonde AD + visuel Compagnon).

## Fichiers / surfaces utiles

| Quoi | Où |
|------|-----|
| Canon agents | `AGENTS.md`, `.agents/rules/` |
| Priorités | `docs/PRIORITES_ACTUELLES.md` |
| Registre | `docs/REGISTRE.md` |
| Runtime jeu | `docs/RUNTIME_GODOT.md` |
| Plan évolutions | `docs/PLAN_PROPOSITIONS_EVOLUTIONS.md` |
| Suivi plan évolutions | `docs/suivi/PLAN_EVOLUTIONS_STATUS.md` |
| Sujets pas encore traités | [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md) |
| Handoff visuel Compagnon (clos) | `docs/handoff_antigravity_visuel_compagnon.md` |
| Handoff sonde AD (clos) | `docs/handoff_antigravity_sonde_ad.md` |
| Workspace | `LBG_Studios.code-workspace` |

## Bloquants

_Aucun bloquant documenté pour ce bootstrap._

## Notes de session

- 2026-10-12 : **initialisation outillage MCP REA (Reverse Engineer Anything) — matrice multi-environnements** —
  - Configurations dédiées créées : [`.cursor/mcp.json`](../.cursor/mcp.json) (Cursor), [`.agents/mcp_config.json`](../.agents/mcp_config.json) (Antigravity), [`.mcp.json`](../.mcp.json) (Claude Code, OpenCode), [`.vscode/cline_mcp_settings.json`](../.vscode/cline_mcp_settings.json) (Cline).
  - Wrapper Studio / CLI exécutable créé dans [`tools/rea_runner.sh`](../tools/rea_runner.sh) pour les agents backend/Team (Iris, Métis).
  - Documentation de référence complète dans [`docs/OUTILS_DEV_MCP.md`](OUTILS_DEV_MCP.md) et référencée dans [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md).
  - Outil 100 % local-first réservé à l'audit et à l'ingénierie Dev/Studio (O1), sans impact sur le runtime joueur Godot O2.
- 2026-10-12 : **rejeu feeling humain Compagnon (O-FEEL-1 / O-FEEL-2) — validé & clôturé** —
  - Déploiement CT 100 actualisé avec le build atomique `1.0.0+40e38c0` (`baf1f65b13777595…`, 36 fichiers).
  - Exécution du script [`tools/smoke_rejeu_humain_d6_5174.sh`](../tools/smoke_rejeu_humain_d6_5174.sh) sur `:5174` : 7 tours exécutés sans aucune rupture ni fuite ops.
  - Verdict 100 % vert : `C1=PASS`, `C2=PASS`, `PLAN=PASS`, `GO_AHEAD=PASS` (`SMOKE_REJEU_HUMAIN_D6_OK`, conversation `rejeu-humain-d6-3fa2fffd`).
  - Salutations et suivi sans template rigide, avis franc collègue studio en causerie, plan d'action structuré markdown et absence de piège sur le go-ahead.
- 2026-10-12 : **ticket 5.2 Outillage Ruff & tests headless Godot CI — validé & clôturé** —
  - Configuration [`ruff.toml`](../ruff.toml) et [`pyproject.toml`](../pyproject.toml) racine pour le linting Python ; `ruff check .` passe à 100 % vert.
  - Runner headless Godot [`tools/ci_godot_headless.sh`](../tools/ci_godot_headless.sh) intégré : sim, nav et db/économie (18/18 checks) exécutés en ~3 s (< 10 s DoD) sans dépendance réseau LAN.
  - Le plan d'évolutions `PLAN_PROPOSITIONS_EVOLUTIONS` est officiellement **100 % réalisé** (10/10 tickets DONE).
- 2026-10-12 : **ticket 3.2 Convergence de la mémoire relationnelle jeu ↔ bureau — validé & clôturé** —
  - Module [`relation_memory.py`](../packages/cortex/compagnon_ui/server_overlay/relation_memory.py) connecté à `prime-hub` (`GET /v1/relation-memory` et `POST /v1/relation-memory/append` sur `:8787`).
  - Ancrage prompt système ([`character_layer.py`](../packages/cortex/compagnon_ui/server_overlay/character_layer.py)) injectant les liens de Teome (Jax, Nix, Daan, pourboires, quêtes) dans la conscience du Compagnon.
  - Détection d'intention `wants_relation_memory` branchée dans [`llm_chat_phase.py`](../packages/cortex/compagnon_ui/server_overlay/llm_chat_phase.py) pour restituer l'état relationnel.
  - Endpoints proxy/append dans [`core.py`](../packages/cortex/compagnon_ui/server_overlay/core.py) et méthodes `fetchRelationMemory`/`appendRelationMemory` dans [`useApi.js`](../packages/cortex/compagnon_ui/src/composables/useApi.js).
  - 6/6 tests unitaires passants dans [`test_relation_memory.py`](../packages/cortex/compagnon_ui/server_overlay/tests/test_relation_memory.py) ; packaging atomique CT 100 validé (`overlay.map` + `pyproject.toml`, 36 fichiers).
  - Axe 3 du plan d'évolutions 100 % achevé.
- 2026-10-12 : **ticket 3.1 Live World Stream Hub → Compagnon — validé & clôturé** —
  - Module [`world_stream.py`](../packages/cortex/compagnon_ui/server_overlay/world_stream.py) connecté au flux `prime-hub` (`GET /v1/world/stream` sur `:8787`) avec timeout 1.5 s, cache mémoire et fallback dégradé silencieux.
  - Salutations sociales ([`router_prompts.py`](../packages/cortex/compagnon_ui/server_overlay/router_prompts.py) / `short_social_reply`) enrichies avec le dernier fait marquant de Lost Heaven (ex. boss abattu, chute de ferraille, escorte Nix).
  - Contexte LLM ([`character_layer.py`](../packages/cortex/compagnon_ui/server_overlay/character_layer.py)) injectant les derniers événements du monde dans le prompt système du Compagnon.
  - Route proxy / cache `GET /world/stream` dans [`core.py`](../packages/cortex/compagnon_ui/server_overlay/core.py) et méthode `fetchWorldStream` dans [`useApi.js`](../packages/cortex/compagnon_ui/src/composables/useApi.js).
  - Suite de tests unitaires dédiée [`test_world_stream.py`](../packages/cortex/compagnon_ui/server_overlay/tests/test_world_stream.py) 100 % passante (7 tests) ; packaging atomique CT 100 validé (`overlay.map` + `pyproject.toml`).
  - Débloque le ticket 3.2 (Mémoire relationnelle).
- 2026-10-12 soir : **L3 DONE** confirmé live (`days_ok=3/3`, `status=done`, `last_ok_day=2026-10-11`) · backlog [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md) réécrit (feeling + 3.1 + clos L3/D6.5).
- 2026-10-12 soir : **fil gaps agentiques A–F2 / revue 7j clos** (`O-GAPS-1`) · suites reportées : `O-OPS-1` smoke LAN · `O-OPS-2` agrégat métriques Fleet · `O-OPS-3` F3 O2 hors plan.
- 2026-10-12 : **ticket 2.2 Découpage modulaire des méga-scripts — validé & clôturé** —
  - Volet client `packages/prime-client/scripts/main.gd` (initialement 2 406 L) ramené à **707 L** et scindé en 4 modules spécialisés < 800 L : `client_gameplay_ops.gd` (529 L, salvage, hunt, combat density, trade, wiki), `client_quest_ops.gd` (281 L, craft M10, board, Echo Hammat, initiation), `client_net_world.gd` (675 L, WebSocket, handoff, zone_state, synchronisation entités), `client_ui_dialogue.gd` (506 L, raccourcis, hotbar, chat hub, pont dialogue PNJ). Preuve : selftest headless `packages/prime-client/tools/client_modular_selftest.gd` 100 % vert sous Godot 4.6.3.
  - Volet serveur `packages/prime-hub/scripts/hub_sim.gd` (initialement 1 669 L) ramené à **771 L** et scindé en 5 modules < 800 L (`hub_combat.gd` 447 L, `hub_presence.gd` 185 L, `hub_sim_ambient.gd` 196 L, `hub_sim_views.gd` 142 L, `hub_sim_defs.gd` 103 L). Preuve : selftest headless `packages/prime-hub/tools/sim_selftest.gd` 100 % vert.
  - Résultat : 100 % des scripts GDScript du jeu et du serveur sous le seuil canonique des 800 lignes. Ticket 2.2 marqué `done`.
- 2026-10-12 : **ticket 2.1 Persistance transactionnelle SQLite hub_player_store validé & clôturé** — couche SQLite threadée non-bloquante `packages/prime-hub/scripts/hub_db.gd` (mode WAL, queue asynchrone `BEGIN IMMEDIATE … COMMIT` sans impact sur le tick de frame) ; couche d'abstraction `hub_player_store.gd` pour les positions joueurs avec auto-migration JSON et export miroir périodique ; résilience validée par selftest (`packages/prime-hub/tools/db_selftest.gd`) et smoke crash-safety `kill -9` sans corruption (`tools/smoke_sqlite_prime_hub.sh`) ; ticket 2.2 (découpage modulaire `hub_sim.gd`) débloqué.
- 2026-10-11 : **ticket 1.3 Modularisation Pilot Web vérifié & clôturé** — monolithe `pilot.js` historique (~8 500 L) découpé en 17 modules ES fonctionnels <1 000 L à la racine de `pilot_web/` ; génération chunks `src/chunks/` via `tools/gen_chunks.mjs` synchronisée et vérifiée (`--check` OK) ; build production Vite `dist/` exécuté avec succès en 957ms ; tests static backend `pytest backend/tests/test_pilot_static.py` 100 % passants.
- 2026-10-11 : **ticket 1.2 Streaming SSE vérifié & validé** — route `POST /ask/stream` live sur CT100 (`:5174`, vérifiée par curl `text/event-stream` start+ping+delta+done) ; intégration front `useApi`/`useChat`/`ChatFlow`/`askStream` avec réflexion progressive ≥300 ms et curseur de streaming ; tests unitaires Python (`test_sse_ask.py` 3/3 OK) et Node (`askStream.test.js` 2/2 OK) tout verts ; `PLAN_PROPOSITIONS_EVOLUTIONS.md` mis à jour.
- 2026-10-11 : **ticket sonde AD traité & clos** (arbitrage : absence d'AD actée dans le LAN). Neutralisation des faux-positifs `ad_agent_down` dans `orchestrator/services/proactive.py` (`_infra_signals`, `infra_objective`) et `hybrid_proactive_agent/engine.py` ; recadrage sur `desktop_agent_down` (`.10:5005`) ; mise à niveau des libellés UI `compagnon_ui/src/lib/initiativeQuota.js`, `compagnon-desktop/main.js`, `pilot_web/pilot_orch.js` ; tests unitaires alignés (`initiativeQuota.test.js`) ; handoff `docs/handoff_antigravity_sonde_ad.md` marqué RÉSOLU.
- 2026-10-11 : **ticket 2.3 navmesh livré** — `packages/prime-hub/scripts/hub_nav.gd` (`NavigationServer3D`, bake 193 polys / 16 empreintes ~0.6 s, `map_force_update` synchrone) ; `PATH_BUDGET_PER_TICK=2` supprimé (`budget_per_tick=0`) ; A* grille conservé en fallback hors bornes. Preuves : self-test `packages/prime-hub/tools/nav_selftest.gd` (40/40 entités/tick, ~34 µs/entité) + `tools/smoke_navmesh_prime_hub.sh` ; `/healthz` expose `navmesh`, endpoints `/v1/navmesh` + `/v1/dev/navmesh/probe`. Débloque 2.1.
- 2026-10-09 : bootstrap continuité Antigravity (`.agents/rules/`, `~/.gemini/GEMINI.md`, ce fichier).
- WIP locaux non commités observés au bootstrap : `FOCUS_COMPAGNON.md`, `spawn_team_campus_conductor_job.py`, `compagnon_ui/nginx.conf`, `chat_intent.py` — ne pas écraser sans vérifier le diff.

---

## Prompt de démarrage (coller dans Antigravity)

```
Repo : LBG_Studios. Réponses en français.
Lis dans l’ordre : AGENTS.md → docs/SESSION_EN_COURS.md → docs/PRIORITES_ACTUELLES.md
→ le handoff @docs/handoff_…md si cité.
Confirme en ≤10 lignes : objectif, contraintes, prochain pas — avant toute édition.
En fin de session : mets à jour docs/SESSION_EN_COURS.md.
```
