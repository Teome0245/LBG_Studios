# Session en cours — LBG Studios

**Mis à jour** : 2026-10-13  
**Branche** : `main`  
**Outil** : partagé Cursor ↔ Antigravity — **lire au démarrage, mettre à jour avant de partir**.  
**Backlog non traité** : [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md)

---

## Objectif actuel

Continuité multi-outils : même canon O1/O2 pour Antigravity et Cursor.  
Travail produit sous-jacent (inchangé) : Compagnon D6 vert + hub Godot P3–P5 sans rouvrir le legacy.  
**2026-10-14** : `O-JEUX-ESCORT` **clos & live** sur `.246:8787` · suite polish O2 = `O-JEUX-SHOW` / `O-JEUX-HOTBAR`.

## Snapshot priorités (voir détail dans PRIORITES_ACTUELLES)

| Rail | État |
|------|------|
| **O1 Compagnon** | D0–D6 OK (smoke D6 V6–V8 PASS 2026-10-06) ; gate *feeling* ouverte — `FOCUS_COMPAGNON.md` |
| **O1 ops** | Lot gaps A–F2 + tick L3 livré 2026-10-07 ; L3 **DONE** `days_ok=3/3` (2026-10-11) ; métriques 7j Fleet **OK** |
| **O2 hub** | P6 Godot-first G5+ **live** (`.246:8787`) ; P3 wiki live ; P5 telegraph boss **vert** 2026-10-08 ; **2.3 navmesh `NavigationServer3D` LIVE** 2026-10-11 |
| **Interdit** | Core3 / gateway SOE / `hub_runtime` Python sur chemin joueur |

## Prochaines actions (à ajuster en fin de session)

Backlog explicite : [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md) (mis à jour 2026-10-13 post O-VEIL-4 / O-OPS-2 DONE).

1. **Plan d'évolutions (10/10 tickets)** : **100 % réalisé & clôturé** (tickets 1.1..1.3, 2.1..2.3, 3.1, 3.2, 5.1, 5.2 DONE).
2. **Feeling Compagnon O-FEEL-1..3 (rejeux humains `:5174`)** : **100 % validé & clôturé** (C1/C2/PLAN/GO ALL PASS + retour terrain présence naturel).
3. **Mains code & coûts LLM O-IDE-1..3** : **100 % validé & clôturé** (smoke live cline prouvé, diagnostic CPU Ollama .110 chiffré, OpenCode confirmé nominal ADR 0025).
4. **Thème 1 — Autonomie Campus / CI / desktop (O-CAMP-1, O-CAMP-2, O-D7-1)** : **100 % validé & clôturé** (tickets plan réconciliés 10/10 DONE, overlay & 140 synchro, Présence Agents D7 actif sur `.143:5005` avec socket `/run/user/1000/lbg-presence-agents.sock`).
5. **Thème 2 — Ops LAN (O-OPS-1)** : **100 % validé & clôturé** (`smoke_lan_surfaces.sh --functional` 100% vert, 24 OK, 1 WARN, 0 KO ; autorité Godot G5+ `:8787` intégrée, Core3 legacy offline toléré).
6. **Thème 3 — Veille Évolution (O-VEIL-1..4)** : **100 % validé & clôturé** (ADR 0028 formalisé pour DSH & VoiceStudio ; doc de cadrage L1 [`agentic_rag_mapping.md`](../packages/cortex/docs/agentic_rag_mapping.md) ; fiabilisation route LLM veille O-VEIL-4 avec format json Ollama et dimensionnement dynamique timeout/tokens).
7. **Harmonisation Doc & Retrait SOE (O-DOC-1, O-JEUX-3)** : **100 % validé & clôturé** (`OBJECTIVES.md` aligné sur Compagnon présence `:5174` vs Pilot cockpit ops `:8080`, jalon P4 clos dans `PLAN_MMO_O2.md` et `PRIORITES_ACTUELLES.md`).
8. **Ops — Agrégat 7j Fleet (O-OPS-2)** : **100 % validé & clôturé** (`metrics_7d` et `rolling_7d` intégrés dans `team/fleet.py`, DoD plan combler gaps agentiques 100% OK).
9. **Reste ouvert** : polish O2 `O-JEUX-SHOW` / `O-JEUX-HOTBAR` · optionnel `O-DOC-2` Bugbot — [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md).
10. **Docs périmées (O-DOC-ALIGN)** : **fait** 2026-10-13 — registre / restauration / suite RUNTIME / smoke en-tête / README alignés sur `:8787` + packages `prime-hub` / `compagnon-desktop`.
11. **O-JEUX-ESCORT** : **clos & live** 2026-10-14 — civil suivable porte→clinique sur `:8787`.

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

- 2026-10-13 : **Locomotion Bots IA & Répartition Factions sur 2 Nouveaux POI (O2 Jeu) — validé & déployé live `.246:8787`** —
  - **Déblocage bots IA (`hub_sim.gd`)** : Correction du bug d'anti-stuck où `stuck_ticks >= 6` réinitialisait systématiquement `stuck_ticks = 0`, empêchant d'atteindre le seuil de dégagement `stuck_ticks >= 12` et bloquant les bots dans une boucle infinie contre les obstacles. Préservation de `linger_until` pour des pauses de rôle naturelles de 3 à 7 s à destination.
  - **2 Nouveaux POI calés sur la carte planétaire** :
    - *Avant-poste Zalem* (`city:avant_poste_zalem`, `u: 0.565, v: 0.405`, Core3 `(2400.0, 0.15, -600.0)`) : relais fortifié sur la route rouge de la capitale. Accueille la **Milice locale** (Capitaine Vael) et les **Artisans** (Soren Kray).
    - *Ksar Nomade* (`city:ksar_nomade`, `u: 0.730, v: 0.220`, Core3 `(6850.0, 0.15, -1450.0)`) : campement et oasis de ferraille dans les dunes est au pied des montagnes. Accueille les **Civils du désert** (Ancien Nadir) et la **Confrérie des soins** (Miran Sael).
  - **Intégration moteur & données** : Inscrits dans `scrapaltai_planet_map.json` (Ctrl+M), `scrapaltai_pois.json`, `catalog_poi.json`, `hub_sim_defs.gd` (`POIS` + `HUB_NPCS`), `triplons.json` (solos), `npc_registry.json`, `explore_ring_lh.json` et préférences de voyage des bots dans `ai_players.json`.
  - **Rendu Client (`entity.gd` & `hub_focus.gd`)** : Ajout du micro-bobbing de marche pour les bots en mouvement, orientation `flip_h` automatique selon la vélocité horizontale, et autorisation des rayons outposts dans `hub_focus.gd` pour afficher les PNJ distants sans fuite de clutter legacy.
  - **Preuve & Déploiement Live** : Tests headless CI Godot (`ci_godot_headless.sh`) 100% verts en 3s. Déploiement live sur `.246:8787` via `deploy_prime_hub_246.sh`. Sonde live `/v1/bots` mesurée : **10/10 bots en déplacement actif et exploration fluide** (ex: Mira en route vers Ksar Nomade à 33 m en 3s, Lia libérée vers le sud à 34.5 m).
- 2026-10-14 : **O-JEUX-ESCORT clos & live** — `GET /v1/quests/escort` → 200 sur `.246:8787` · déjà dans `9baecef` (deploy hub) · ticket déplacé en § Clos.
- 2026-10-13 : **Alignement docs périmées (audit)** —
  - [`REGISTRE.md`](REGISTRE.md) : packages `prime-hub` / `compagnon-desktop` ; autorité joueur **`:8787`** ; `:8792` = lab Core3 OFF ; matrice mermaid + jalons oct. ;
  - [`RESTAURATION_PRODUIT.md`](RESTAURATION_PRODUIT.md) : Rang 2 P3/dialogue/hub **vert** ; Core3 sidecar **rouge** ; prochaine traction = backlog léger (O-OPS-3, polish, unification client) ;
  - [`RUNTIME_GODOT.md`](RUNTIME_GODOT.md) : section « suite » scindée **fait** vs **ouvert** (plus de P3/P5 listés comme TODO) ;
  - [`SMOKE_LAN.md`](SMOKE_LAN.md) en-tête + libellé Compagnon `:5174` ; [`README.md`](../README.md) remotes liés.
- 2026-10-13 : **Fiabilisation LLM veille (O-VEIL-4) & Agrégat métriques 7j Fleet (O-OPS-2) — validés & clôturés** —
  - **O-VEIL-4 (Route LLM veille)** : Injection du paramètre natif `"format": "json"` pour Ollama et `"response_format": {"type": "json_object"}` dans `reason_llm.py` pour le profil `json` ; calcul dynamique du timeout (`min(150, max(45, n_input * 15))`) et `max_tokens` dans `evolution_veille_workflow.py` proportionnels au nombre de pistes (pour éviter les timeouts constatés sur les batchs de 8 pistes) tout en conservant le fallback heuristique ultra-rapide. Tests 5/5 validés.
  - **O-OPS-2 (Agrégat métriques 7j Fleet)** : Calcul d'une fenêtre glissante de 7 jours sur les jobs Cowork (`jobs_7d`), tâches virtuelles Team (`tasks_7d`, L2 pending), stabilité de la mission L3 LAN et décision du pilote Ops Health. Exposé sous `metrics_7d` et `metrics.rolling_7d` dans `team/fleet.py`. Critère DoD §6 dans [`plan_combler_gaps_agentiques.md`](../packages/cortex/docs/plan_combler_gaps_agentiques.md) et [`revue_ops_health_7j.md`](../packages/cortex/docs/revue_ops_health_7j.md) passés à 100% OK. Tests 6/6 validés.
- 2026-10-13 : **Mapping Agentic RAG (O-VEIL-3) — validé & clôturé** —
  - Rédaction du document de cadrage architectural L1 [`agentic_rag_mapping.md`](../packages/cortex/docs/agentic_rag_mapping.md) démontrant la correspondance directe des concepts Agentic RAG sur nos briques natives : routeur d'intentions (`router_prompts.py`), bus SQLite Team (`team_tasks`/`team_messages`), mémoire Compagnon et World Stream (`:8787`). Respect strict de la règle : zéro framework tiers lourd sur le chemin critique.
- 2026-10-13 : **Harmonisation Doc & Retrait SOE (O-DOC-1, O-JEUX-3) — validé & clôturé** —
  - **O-DOC-1 ([`OBJECTIVES.md`](../OBJECTIVES.md))** : Canon harmonisé — clarification formelle : le Compagnon Studio (présence) s'incarne sur `:5174` (`compagnon_ui`) et l'application Desktop Electron (`packages/compagnon-desktop`), tandis que Pilot (`:8080`) est le cockpit ops / méta-autonomie. Smoke LAN 24/24 surfaces OK mis à jour.
  - **O-JEUX-3 ([`PLAN_MMO_O2.md`](PLAN_MMO_O2.md) & [`PRIORITES_ACTUELLES.md`](PRIORITES_ACTUELLES.md))** : Jalon P4 formellement clos. Retrait définitif du pont SOE/Core3 et confirmation de l'autorité exclusive du runtime Godot headless G5+ (`:8787` unifié HTTP+WS).
- 2026-10-13 : **Veille Évolution (O-VEIL-1, O-VEIL-2) — validé & clôturé** —
  - **O-VEIL-1 (DeepSeek Harness / dsh_headless)** : Suite aux résultats de la veille et au constat de charge CPU sur `.110` (O-IDE-2), formalisation de l'ADR 0028 actant un **NO-GO** pour toute greffe `dsh_headless` dans Cortex/Team (OpenCode étant le nominal éprouvé et aucun Node.js n'étant toléré sur 140). DSH reste strictement réservé au poste exploratoire dev `.10`. ADR 0020 clos.
  - **O-VEIL-2 (VoiceStudio / TTS LAN Compagnon)** : Évaluation de VoiceStudio / modèles de clonage vocal lourds (F5-TTS/Chatterbox) : rejet de tout déploiement lourd sans GPU audio dédié. Maintien et validation de la stack nominale de production existante documentée dans [`voice_local.md`](../voice_local.md) : **Edge TTS** (primaire `fr-FR-DeniseNeural` 0 €) + **Piper** LAN `.111:8098` (fallback local ultra-léger).
- 2026-10-13 : **Ops LAN (O-OPS-1) — validé & clôturé** —
  - `tools/smoke_lan_surfaces.sh` modernisé : intégration de l'autorité jeu G5+ Godot-first sur `.246:8787` (`/healthz` et `/v1/events/active`) en vérification nominale ; tolérance gracieuse des sondes Core3/PreCU `:8792` dépréciées (OFF par ADR 0026).
  - Validation complète bout-en-bout avec `bash tools/smoke_lan_surfaces.sh --functional` : **24 OK, 1 WARN (clé cloud), 0 KO**. Pilot Studio, Cockpit P03, Orch UI 5174, Orch API :3000, WebUI 3080, Godot Hub :8787, Patches, MCP, Team WSL, Desktop dry-run route, Cockpit Desktop réel, et Team bus (6/6) tous au vert.
- 2026-10-13 : **Autonomie Campus / CI / desktop (O-CAMP-1, O-CAMP-2, O-D7-1) — validé & clôturé** —
  - **O-CAMP-1 (Audit tickets plan)** : `tools/suivi_plan_evolutions.py --audit` exécuté avec succès : 10/10 tickets DONE, `plan_complete: true`, `orphan_failed: []`, aucun faux done.
  - **O-CAMP-2 (Deploy overlay CT100 & Pilot 140)** : Vérification de cohérence OK, CT 100 à jour, Pilot Web sur `.140` répond 200 OK sur `:8080/` et Orchestrateur `:8010/healthz` OK.
  - **O-D7-1 (Présence Agents D7 sur worker .143)** : Injection de `LBG_SESSION_ISLAND_ENABLED=1`, `LBG_SESSION_ISLAND_FAIL_OPEN=1`, `LBG_SESSION_ISLAND_APPROVAL_TIMEOUT_S=60` pérennisés dans `deploy_linux_agent_143.sh`, `session_emitter.py` complété pour résolution dynamique via `_get_cfg`, `EnvironmentFile` ajouté dans le service systemd `lbg-omarchy-agent.service`. Tests 4/4 verts. Endpoint `http://192.168.0.143:5005/session/status` vérifié live : `enabled: true`, `socket_alive: true` (`/run/user/1000/lbg-presence-agents.sock`).
- 2026-10-13 : **mains code Cline / perf Ollama .110 / décision ADR (O-IDE-1..3) — validé & clôturé** —
  - **O-IDE-1 (Smoke live bout-en-bout)** : Preuve d'exécution complète validée depuis l'Orchestrateur Team (`:8010`) vers l'agent Linux `.143:5005` (`run_cli_agent app=cline`) déclenchant `/home/lbg/.local/bin/cline` avec le modèle `huihui_ai/gemma-4-abliterated:E4b-qat` vers Ollama `.110:11434`.
  - **O-IDE-2 (Mesure de perf & diagnostic VRAM)** : Constat chiffré sur `.110` via `ollama ps` : `size_vram: 0` (exécuté 100 % en RAM CPU) avec 32k context. La latence CPU dépasse 350 s par tour, provoquant le timeout du client Cline (`Error: The operation timed out` à 357 s). Respect strict de la matrice locale : interdiction de descendre sous `E4b-qat` (plancher qualité de codage).
  - **O-IDE-3 (Décision formelle ADR 0025)** : OpenCode headless (`opencode run -m opencode/big-pickle`) est formellement maintenu comme **nominal de production** pour les mains de code Team (Métis / Iris / Dédale). Cline CLI reste un outil de **second avis / option locale 0 € API** prêt pour le jour où `.110` disposera d'accélération VRAM GPU.
  - Documents mis à jour : [`packages/cortex/docs/cline/CLI_SECOND_AVIS.md`](../packages/cortex/docs/cline/CLI_SECOND_AVIS.md), [`packages/cortex/docs/adr/0025-mains-code-143-run-cli-agent.md`](../packages/cortex/docs/adr/0025-mains-code-143-run-cli-agent.md), [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md).
- 2026-10-12 : **polish retour terrain longue durée Compagnon (O-FEEL-3) — validé & clôturé** —
  - `presence_report.py` enrichi : regex de détection étendue aux tournures naturelles de fil long (« comment réagissent les personas sur le terrain », « des nouvelles de Lia »).
  - Personnalisation dynamique du retour terrain selon le persona ciblé (`_persona_from_prompt`), avec conservation du comparatif équilibré Nix vs Mira par défaut.
  - Garantie anti-ops stricte : en cas de hub de jeu inaccessible, réponse collègue fluide sans fuite d'exception brute, de numéro de port (`:8787`) ni de commande bash.
  - `presence_brief.py` nettoyé de toute mention de tâche shell en fallback.
  - Suite de tests unitaire étendue (9/9 tests verts), build atomique `1.0.0+f346979` déployé sur CT 100 (`192.168.0.100:5174`), smokes de rejeu terrain et rejeu humain 7 tours (`smoke_rejeu_humain_d6_5174.sh`) validés 100 % PASS.
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
