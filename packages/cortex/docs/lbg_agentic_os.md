# LBG Agentic OS — carte CrewAI / Manus / Dify → Studio LAN

**Date** : 2026-07-31  
**Public** : Team + ops  
**Complète** : `plan_campus_conductor.md`, `plan_team_petri_peau.md`, `architecture_tri_backend_hybride.md`

## 1. Idée

Un **OS agentique** (Manus, CrewAI, Dify…) = couche qui *planifie*, *appelle des outils*, *observe*, *corrige*, sans humain en boucle.

LBG n’importe pas ces frameworks tels quels : on a déjà un **studio multi-agents ancré LAN** (Cortex 140 + Peau Pilot + workers 110/111/245/246).  
Ce doc mappe les concepts « agentic OS » sur **nos** rôles et briques.

## 2. Tableau de correspondance

| Concept | Manus / CrewAI / Dify | Chez LBG |
|---------|----------------------|----------|
| Orchestrateur / chef | Manager agent, Crew, workflow Dify | **Lyra** (Campus Conductor) + **Thémis** (PM / autoconsult) + Cortex `orchestrator` |
| Planification | Planner LLM | `POST /v1/team/plan`, briefs PM, missions Pilot |
| Agents spécialisés | Researcher / Coder / Writer | Argus (qa), Héphaïstos (ops), Atlas (admin), Dédale/Vulcan (dev_game), Iris/Hermès (Godot), Pygmalion (assets), Chœur (player_ia) |
| Outils | Browser, shell, files, APIs | Workflows Team, SSH/scripts, smoke LAN, sidecar Core3, **Cursor Cloud Agent** (PR), Ollama 110/111 |
| Mémoire / état | Memory store, vector DB | SQLite Team tasks, presence hub, state.json jobs, RAG / docs optionnels |
| Observation | Sensors, webhooks | Présence campus WS, healthz, timers systemd, failure follow-up |
| Action proactive | Auto-mail, auto-code | Conductor (drain + coffee fill), jobs QA/Atlas/M9, follow-ups échec |
| Garde-fous | Human-in-the-loop | L1 auto / L2 token, allowlists repos & rôles, dry-run |
| UI « bureau » | Chat / canvas | Pilot `#/team/office` (Peau) |

## 3. Architecture LBG (vue OS)

```mermaid
flowchart TB
  subgraph peau [Peau — observation]
    UI[Pilot bureau + file tâches]
    WS[presence WS]
  end
  subgraph cortex [Cortex — 140]
    LYRA[Lyra Conductor]
    THEM[Thémis PM]
    STORE[(team_tasks SQLite)]
    RUN[run_task / workflows]
  end
  subgraph tools [Outils]
    SMOKE[smokes / SSH]
    LLM[Ollama 110/111]
    CUR[Cursor Cloud Agent]
    GODOT[Prime / Core3 246]
  end
  UI --> WS
  WS --> STORE
  LYRA -->|drain queued + coffee fill| STORE
  THEM -->|plan / autoconsult| STORE
  STORE --> RUN
  RUN --> SMOKE
  RUN --> LLM
  RUN --> CUR
  RUN --> GODOT
  RUN --> WS
```

**Principe** : Cortex décide et exécute ; Peau montre ; pas de second cerveau opaque type SaaS Manus sur le chemin critique LAN.

## 4. Boucle autonome cible (alignée Manus)

```text
Mission NL
  → plan (Thémis / /v1/team/plan)
  → file de tâches spécialisées
  → Lyra : cap busy + démarrage L1 + coffee fill
  → exécution outils
  → échec → failure_followup (triage PM ± retry)
  → smoke / présence → boucle
```

| Niveau | Comportement | État LBG |
|--------|--------------|----------|
| L0 | Lecture / dry-run | OK |
| L1 | Run sans humain (smoke, brief, drain) | OK + Conductor V0/V1 |
| L2 | Approbation (build Core3, Cursor PR, think player) | OK (token) |
| L3 | Mission multi-jours auto-corrigée | Partiel — objectif produit |

## 5. Multi-agents : qui fait quoi (CrewAI-style)

| Persona | Rôle Crew | Sorties typiques |
|---------|-----------|------------------|
| Lyra | Orchestrator / dispatcher | Prefill, coffee fill, rapport idle |
| Thémis | Manager / synthesizer | Plan, autoconsult, brief réunif |
| Argus | QA / critic | Smoke LAN, healthz |
| Héphaïstos | Ops / infra probe | Sondes, selfcheck |
| Atlas | Admin LLM / dual host | Audit Ollama, storage hints |
| Dédale | Gameplay coder | Correctifs, forge propositions |
| Vulcan | Systems / Core3 | Build plan, ZB |
| Iris | Client UI | M9, minimap, HUD |
| Hermès | Network / SOE | Gateway, launchpad |
| Pygmalion | Artist | LoRA, sprites, GLB |
| Chœur | NPC / player sims | Probe / think L2 |

## 6. Ce qu’on ne copie pas (volontairement)

- Remplacer Cortex par CrewAI/Dify en prod LAN (dette + latence + moins de contrôle L2).
- Un seul mega-agent Manus qui SSH partout sans allowlist.
- Chat LLM comme seul bus de coordination (la file SQLite + presence restent la source de vérité).

Réutiliser plutôt les **patterns** : rôles clairs, outils bornés, boucle observe→act→correct, HITL sur L2.

## 7. Roadmap produit (courte)

1. **Fait** — Conductor V0–V2 (drain, coffee fill, act selon état, mission NL, UI Pilot) ; Cursor PR ; présence Petri.
2. **Ensuite** — Clôture mission quand smoke vert ; mémoire autoconsult dans le plan.
3. **Plus tard** — Adapter CrewAI en lab, pas en chemin critique.

## 8. Commandes utiles

```bash
curl -s http://192.168.0.140:8010/v1/team/campus/status
curl -s -X POST http://192.168.0.140:8010/v1/team/campus/conduct \
  -H 'Content-Type: application/json' -d '{"dry_run":true}'
# Bureau
# http://192.168.0.140:8080/#/team/office
```
