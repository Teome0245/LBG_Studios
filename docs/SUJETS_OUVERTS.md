# Sujets ouverts — LBG Studios

**Mis à jour** : 2026-10-12  
**Rôle** : liste des sujets **pas encore traités** (hors tickets déjà `done` du plan évolutions).  
**Pas** un plan d’exécution détaillé — juste le backlog explicite.  
Quand un sujet est clos : le déplacer en § Clos (avec date) ou le supprimer.

Canon session : [`SESSION_EN_COURS.md`](SESSION_EN_COURS.md) · plan : [`PLAN_PROPOSITIONS_EVOLUTIONS.md`](PLAN_PROPOSITIONS_EVOLUTIONS.md) · Cline : [`../packages/cortex/docs/cline/CLI_SECOND_AVIS.md`](../packages/cortex/docs/cline/CLI_SECOND_AVIS.md)

---

## Ouverts

### O1 — Mains code / coûts LLM

| ID | Sujet | Notes |
|----|--------|--------|
| O-IDE-1 | Smoke **live** Team avec `ide_cli_app=cline` (E4b-qat) | Dry-run OK ; manque preuve bout-en-bout Métis/Iris → `.143` → Ollama `.110` |
| O-IDE-2 | Perf Ollama **`.110`** pour Cline | Au smoke : `size_vram: 0` (CPU) → lent ; viser VRAM ou host adapté sans redescendre sous `E4b-qat` |
| O-IDE-3 | Décision ADR : **OpenCode nominal vs Cline défaut** | Aujourd’hui OpenCode = `big-pickle` (coûts peu visibles) ; Cline = local 0 € API. Basculer = amendement ADR 0025 |
| O-IDE-4 | Aligner `PLAN_PROPOSITIONS_EVOLUTIONS.md` | Encore écrit « Cline CLI absent » — faux depuis install `.143` + `CLI_SECOND_AVIS.md` |

### O1 — Autonomie Campus / plans

| ID | Sujet | Notes |
|----|--------|--------|
| O-CAMP-1 | Rejouer tickets plan encore ouverts / faux « done » | Gate `plan_ticket_closure` livrée ; vérifier tickets restants + sync suivi |
| O-CAMP-2 | Deploy lab overlay Compagnon / orch | Si pas sync : `.100` Compagnon + `.140` orch après `1049e0a` |

### O2 — Jeu

| ID | Sujet | Notes |
|----|--------|--------|
| O-JEUX-1 | Ticket **3.1** Live World Stream Hub → Compagnon | Prochaine action Studio listée dans `SESSION_EN_COURS` / plan évolutions |

### Ops

| ID | Sujet | Notes |
|----|--------|--------|
| O-OPS-1 | Smoke LAN surfaces si reprise ops | `bash tools/smoke_lan_surfaces.sh --functional` + `docs/SMOKE_LAN.md` |

---

## Clos

_Aucun sujet de cette liste clôturé ici pour l’instant._

---

## Règle d’usage

1. Ajouter ici dès qu’un sujet est identifié mais **pas** démarré.  
2. Ne pas dupliquer le détail technique déjà dans ADR / `CLI_SECOND_AVIS` / tickets plan — **lien + une ligne**.  
3. Session en cours = focus immédiat ; **ce fichier** = reste à traiter.
