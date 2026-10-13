# Sujets ouverts — LBG Studios

**Mis à jour** : 2026-10-12  
**Rôle** : liste des sujets **pas encore traités** (hors tickets déjà `done`).  
**Pas** un plan d’exécution détaillé — juste le backlog explicite.  
Quand un sujet est clos : le déplacer en § Clos (avec date) ou le supprimer.

Canon session : [`SESSION_EN_COURS.md`](SESSION_EN_COURS.md) · priorités : [`PRIORITES_ACTUELLES.md`](PRIORITES_ACTUELLES.md) · présence : [`PLAN_PRESENCE_ZONE_ENTRAINEMENT.md`](PLAN_PRESENCE_ZONE_ENTRAINEMENT.md) § *Clôture de fil* · plan évolutions : [`PLAN_PROPOSITIONS_EVOLUTIONS.md`](PLAN_PROPOSITIONS_EVOLUTIONS.md) · suivi : [`suivi/PLAN_EVOLUTIONS_STATUS.md`](suivi/PLAN_EVOLUTIONS_STATUS.md) · Cline : [`../packages/cortex/docs/cline/CLI_SECOND_AVIS.md`](../packages/cortex/docs/cline/CLI_SECOND_AVIS.md)

---

## Ouverts

### O1 — Feeling Compagnon / présence

_Aucun sujet ouvert en attente — O-FEEL-1, O-FEEL-2 et O-FEEL-3 clos._


### O1 — Mains code / coûts LLM

_Aucun sujet ouvert en attente — O-IDE-1, O-IDE-2 et O-IDE-3 clos (2026-10-13)._


### O1 — Autonomie Campus / CI / desktop

_Aucun sujet ouvert en attente — O-CAMP-1, O-CAMP-2 et O-D7-1 clos (2026-10-13)._


### O2 — Jeu / pont Studio↔Monde

_Aucun sujet ouvert en attente — O-JEUX-1..3 clos (2026-10-13, retrait pont SOE P4 et autorité Godot G5+ actés)._


### Ops (suites du fil gaps A–F2 / L3 — fil **clos** 2026-10-12)

_O-OPS-1 clos (2026-10-13) — `smoke_lan_surfaces.sh --functional` vert (24 OK, 0 KO)._

| ID | Sujet | Notes |
|----|--------|--------|
| O-OPS-2 | Agrégat métriques 7j Fleet (optionnel) | DoD plan gaps encore `[~]` — [`revue_ops_health_7j.md`](../packages/cortex/docs/revue_ops_health_7j.md) · hors feeling Compagnon |
| O-OPS-3 | **F3** O2 jeu (hors plan gaps) | Explicitement hors [`plan_combler_gaps_agentiques.md`](../packages/cortex/docs/plan_combler_gaps_agentiques.md) — voir P3–P5 [`PRIORITES_ACTUELLES.md`](PRIORITES_ACTUELLES.md) |

### O1 — Suite veille évolution (batch TikTok — fil **clos** 2026-10-12)

_O-VEIL-1, O-VEIL-2 et O-VEIL-3 clos (2026-10-13) — ADR 0028 + doc mapping [`agentic_rag_mapping.md`](../packages/cortex/docs/agentic_rag_mapping.md)._

| ID | Sujet | Notes |
|----|--------|--------|
| O-VEIL-4 | Fiabiliser chemin LLM veille (optionnel) | Batch 8 a timeouté Ollama → fallback heuristique OK ; profil `json` / timeout / pas de bascule lourde 111→110 |

### Docs — suites fil priorités (PR #4 mergée — fil **clos** 2026-10-12)

_O-DOC-1 clos (2026-10-13) — canon `OBJECTIVES.md` harmonisé (présence `:5174` vs Pilot ops `:8080`)._

| ID | Sujet | Notes |
|----|--------|--------|
| O-DOC-2 | Review Bugbot formelle du snapshot priorités (optionnel) | Review manuelle OK au fil ; Bugbot / Composer 2.5 hors quota à l’époque — relancer si besoin d’une review outillée |

---

## Clos (récents)

| ID | Sujet | Clos |
|----|--------|------|
| O-VEIL-3 | Doc mapping **Agentic RAG** → bus Team / mémoire Compagnon | **2026-10-13** · doc [`agentic_rag_mapping.md`](../packages/cortex/docs/agentic_rag_mapping.md) · mapping conceptuel sur bus SQLite Team + mémoires Compagnon · zéro framework tiers |
| O-DOC-1 | Harmoniser `OBJECTIVES.md` entrée Compagnon | **2026-10-13** · entrée canonique fixée à `:5174` (présence) et Desktop Electron · Pilot `:8080` clarifié cockpit ops |
| O-JEUX-3 | Nettoyage restes P4 / docs SOE | **2026-10-13** · jalon P4 clos dans `PLAN_MMO_O2.md` et `PRIORITES_ACTUELLES.md` · autorité exclusive Godot headless G5+ (`:8787`) |
| O-VEIL-1 | Spike **DeepSeek Harness** `.10` → go/no-go `dsh_headless` | **2026-10-13** · ADR 0028 · NO-GO formel pour `dsh_headless` Team (OpenCode nominal, saturation CPU .110) · .10 exploratoire libre |
| O-VEIL-2 | Spike **VoiceStudio** (ou équiv.) TTS/ASR LAN Compagnon | **2026-10-13** · ADR 0028 · maintien de la stack nominale Edge TTS + Piper LAN (.111:8098) · pas de surcharge GPU lourde |
| O-OPS-1 | Smoke LAN surfaces si reprise ops | **2026-10-13** · `tools/smoke_lan_surfaces.sh --functional` 100% vert (24 OK, 1 WARN, 0 KO) · Godot G5+ `:8787` intégré, Core3 legacy offline toléré |
| O-CAMP-1 | Rejouer tickets plan encore ouverts / faux « done » | **2026-10-13** · audit suivi_plan_evolutions.py 10/10 tickets DONE, plan_complete: true, zéro faux done |
| O-CAMP-2 | Deploy lab overlay Compagnon / orch si drift | **2026-10-13** · CT 100 overlay f346979 à jour, deploy 140 Pilot OK (HTTP 200 /) et orch :8010/healthz OK |
| O-D7-1 | Sync worker **`.143`** Présence Agents D7 | **2026-10-13** · `LBG_SESSION_ISLAND_ENABLED=1`, EnvironmentFile systemd, socket Unix actif `/run/user/1000/lbg-presence-agents.sock`, live :5005/session/status OK |
| O-IDE-1 | Smoke **live** Team avec `ide_cli_app=cline` (E4b-qat) | **2026-10-13** · pipeline Orch:8010 → worker:5005 → cline → Ollama:11434 prouvé bout-en-bout |
| O-IDE-2 | Perf Ollama **`.110`** pour Cline (diagnostic CPU) | **2026-10-13** · mesuré `size_vram: 0` (CPU pur, >350s timeout) · consigné dans `CLI_SECOND_AVIS.md` |
| O-IDE-3 | Décision ADR : **OpenCode nominal vs Cline défaut** | **2026-10-13** · OpenCode confirmé nominal Team (vélocité/stabilité) · Cline second avis 0 € local · ADR 0025 amendé |
| O-FEEL-3 | Polish boucle C1/C2 présence (retour terrain) | **2026-10-12** · `presence_report.py` + `presence_brief.py` · regex fil long naturelle · persona ciblé dynamique (ex: Lia) · anti-ops offline causerie · smoke live 5174 PASS |
| O-REA-1 | Intégration MCP **REA** (Reverse Engineer Anything) | **2026-10-12** · `.cursor/mcp.json` + `.agents/mcp_config.json` configurés · doc [`OUTILS_DEV_MCP.md`](OUTILS_DEV_MCP.md) |
| O-FEEL-1 | **A2 — C2 collègues** (rejeu humain) | **2026-10-12** · rejeu 7 tours `smoke_rejeu_humain_d6_5174.sh` C1/C2/PLAN/GO **PASS** (`rejeu-humain-d6-3fa2fffd`) |
| O-FEEL-2 | Feeling C2 rejeu humain périodique | **2026-10-12** · pas de template ops à l'ouverture, greeting + follow naturels |
| O-CI-1 | Ticket **5.2** Ruff + tests headless Godot CI | **2026-10-12** · `ruff.toml` 100% vert · `tools/ci_godot_headless.sh` sim/nav/db 18/18 en 3s · Plan d'évolutions 10/10 DONE |
| O-JEUX-2 | Ticket **3.2** Mémoire relationnelle jeu ↔ bureau | **2026-10-12** · `relation_memory.py` `:8787` · bloc prompt in-game Teome · tests 6/6 · package CT100 |
| O-PRIO-0 | Fil priorités actuelles + PR #4 (`PRIORITES_ACTUELLES.md`) | **2026-10-12** · mergée · suites optionnelles = `O-DOC-1..2` |
| O-VEIL-0 | Fil veille batch 8 pistes + workflow Team `evolution_veille` + Lyra ON | **2026-10-12** · mission `4c28ada8-…` done · API `POST /v1/team/evolution/lead` · suites = `O-VEIL-1..4` |
| O-GAPS-1 | Fil gaps agentiques A–F2 + revue 7j + soft-links Fleet | **2026-10-12** · pilote live · revue **GO** · Vulcan↔Vex / Hermès↔Tess · doc alignée |
| O-JEUX-1 | Ticket **3.1** Live World Stream Hub → Compagnon | **2026-10-12** · `world_stream.py` `:8787` · tests 7/7 · greeting enrichi · package CT100 |
| O-L3-1 | Mission L3 smoke LAN `days_ok` → 3 | **2026-10-11** · `status=done` · `tools/status_l3_smoke_lan_mission.sh` |
| O-DESK-1 | Desktop portable notepad (O6 plan présence) | **2026-10-12** · worker `.77` · allowlist |
| O-HUB-1 | P5b telegraph boss + B3/B4 presence dials | **2026-10-08** · smokes hub |
| O-D65-1 | D6.5 greeting / sticky go-ahead / plan→Campus | **2026-10-08** · V9/V10 live `:5174` |
| O-IDE-4 | Aligner doc « Cline CLI absent » dans plan évolutions | **2026-10-12** · pointeur `CLI_SECOND_AVIS.md` |

---

## Règle d’usage

1. Ajouter ici dès qu’un sujet est identifié mais **pas** démarré (ou pas `done`).  
2. Ne pas dupliquer le détail technique déjà dans ADR / leçons / tickets plan — **lien + une ligne**.  
3. Session en cours = focus immédiat ; **ce fichier** = reste à traiter.  
4. Fil gaps/L3 **clos** : suites ops = `O-OPS-1..3` seulement. Fil veille batch **clos** : suites = `O-VEIL-1..4`. Fil priorités PR #4 **clos** : suites optionnelles = `O-DOC-1..2`. Plan d'évolutions 10/10 **DONE**. Feeling O-FEEL-1/2 **DONE**. Suite recommandée : **O-FEEL-3** ou **O-IDE-1..3** (Cline).
