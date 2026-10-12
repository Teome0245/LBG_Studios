# Sujets ouverts — LBG Studios

**Mis à jour** : 2026-10-12  
**Rôle** : liste des sujets **pas encore traités** (hors tickets déjà `done`).  
**Pas** un plan d’exécution détaillé — juste le backlog explicite.  
Quand un sujet est clos : le déplacer en § Clos (avec date) ou le supprimer.

Canon session : [`SESSION_EN_COURS.md`](SESSION_EN_COURS.md) · priorités : [`PRIORITES_ACTUELLES.md`](PRIORITES_ACTUELLES.md) · présence : [`PLAN_PRESENCE_ZONE_ENTRAINEMENT.md`](PLAN_PRESENCE_ZONE_ENTRAINEMENT.md) § *Clôture de fil* · plan évolutions : [`PLAN_PROPOSITIONS_EVOLUTIONS.md`](PLAN_PROPOSITIONS_EVOLUTIONS.md) · suivi : [`suivi/PLAN_EVOLUTIONS_STATUS.md`](suivi/PLAN_EVOLUTIONS_STATUS.md) · Cline : [`../packages/cortex/docs/cline/CLI_SECOND_AVIS.md`](../packages/cortex/docs/cline/CLI_SECOND_AVIS.md)

---

## Ouverts

### O1 — Feeling Compagnon / présence

| ID | Sujet | Notes |
|----|--------|--------|
| O-FEEL-1 | **A2 — C2 collègues** (rejeu humain) | Code/polish livré ; critère #1 encore **PARTIEL** sur certains tours — rejeu [`smoke_rejeu_d6_2026-10-08b.md`](smoke_rejeu_d6_2026-10-08b.md) · `chat_intent` / nudge causerie |
| O-FEEL-2 | Feeling C2 rejeu humain périodique | Sur `:5174` : éviter template « qu’est-ce qui t’amène » / hub ops à l’ouverture |
| O-FEEL-3 | Polish boucle C1/C2 présence (retour terrain) | `presence_brief.py` · `presence_report.py` — retour terrain en **causerie**, pas dump ops, sur rejeux longs |

### O1 — Mains code / coûts LLM

| ID | Sujet | Notes |
|----|--------|--------|
| O-IDE-1 | Smoke **live** Team avec `ide_cli_app=cline` (E4b-qat) | Dry-run OK ; manque preuve bout-en-bout Métis/Iris → `.143` → Ollama `.110` |
| O-IDE-2 | Perf Ollama **`.110`** pour Cline | Au smoke : `size_vram: 0` (CPU) → lent ; viser VRAM ou host adapté sans redescendre sous `E4b-qat` |
| O-IDE-3 | Décision ADR : **OpenCode nominal vs Cline défaut** | OpenCode = `big-pickle` ; Cline = local 0 € API. Basculer = amendement ADR 0025 |

### O1 — Autonomie Campus / CI / desktop

| ID | Sujet | Notes |
|----|--------|--------|
| O-CAMP-1 | Rejouer tickets plan encore ouverts / faux « done » | Gate `plan_ticket_closure` ; sync [`suivi/PLAN_EVOLUTIONS_STATUS.md`](suivi/PLAN_EVOLUTIONS_STATUS.md) |
| O-CAMP-2 | Deploy lab overlay Compagnon / orch si drift | `.100` Compagnon + `.140` orch après overlays récents |
| O-CI-1 | Ticket **5.2** Ruff + tests headless Godot CI | Suivi : *reopen* (faux done ops_probe) — relance `ide_cli` LIVE |
| O-D7-1 | Sync worker **`.143`** Présence Agents D7 | Code monorepo livré — [`LECON_PRESENCE_AGENTS_D7_2026-10-09.md`](LECON_PRESENCE_AGENTS_D7_2026-10-09.md) |

### O2 — Jeu / pont Studio↔Monde

| ID | Sujet | Notes |
|----|--------|--------|
| O-JEUX-2 | Ticket **3.2** Mémoire relationnelle jeu ↔ bureau | **Débloqué** (3.1 done) · prêt pour implémentation |
| O-JEUX-3 | Nettoyage restes P4 / docs SOE | Pont SOE retiré de facto — docs/UI à purger au fil de l’eau |

### Ops

| ID | Sujet | Notes |
|----|--------|--------|
| O-OPS-1 | Smoke LAN surfaces si reprise ops | `bash tools/smoke_lan_surfaces.sh --functional` + [`SMOKE_LAN.md`](SMOKE_LAN.md) |
| O-OPS-2 | Agrégat métriques 7j Fleet (optionnel) | Suite revue ops health — hors feeling Compagnon |

---

## Clos (récents)

| ID | Sujet | Clos |
|----|--------|------|
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
4. Après clôture L3 / présence / 3.1 : reprendre en priorité **O-FEEL-1/2** (feeling) ou **O-JEUX-2** (mémoire relationnelle).
