# Sprint d'évolution 7j — Team / Thémis

**Date** : 2026-08-18  
**Statut** : **actif sur `.140`** (O1 Studio)  
**Complète** : [vision_equipe_fable_autoconsultation.md](vision_equipe_fable_autoconsultation.md) (santé 12 h)

## But

Une fois par **7 jours**, Thémis fait un **audit full** (infra, Team, LLM, jeu, modules) puis :

1. classe les findings en **gaps** (cassé) et **opportunités** (améliorer) ;
2. **applique L1 toute seule** (sondes, remédiations scriptées, re-smokes) ;
3. pose les actions **L2** dans la file Pilot (`status=review`, token requis).

Ce n’est **pas** l’autoconsult : l’autoconsult vérifie que ça tourne ; le sprint cherche à **faire mieux**.

## Méta (2026-08-21)

Si `LBG_TEAM_EVOLUTION_META=1` (défaut), le sprint spawn aussi :

1. **Mutator** (`agent_mutation`) — golden + candidat prompt → revue L2 → apply `prompt_overrides/`
2. **Feature Proposer** — RFC staging + smoke Argus + revue L2

Détail : [`plan_meta_autonomie_l3.md`](plan_meta_autonomie_l3.md).

## Boucle

```
Timer 7j → Audit → Diagnose → Plan → L1 auto / L2 Pilot (+ méta) → Verify → Mémoire
```

| Cadence | Quoi |
|---------|------|
| **12 h** | Autoconsult — santé (healthz, M9, sidecar…) |
| **7 j** | Sprint évolution — audit + plan + apply borné |

## Périmètre audit

| Volet | Sonde |
|--------|--------|
| Santé (réemploi autoconsult) | QA, ops healthz, M9, Hermès, Launchpad, assets, gameplay, Chœur, Prime UI |
| Infra LAN | Atlas `audit_admin_infra_platform` (110/111/140/141/142/245/246) |
| LLM | Matrice `reason_route_matrix()` vs env ; modèle interdit (`gemma3:4b`) → L2 |
| Capacités Team | Roster déclarations + timers manquants (rapport) |
| Modules LBG_SA | `planned` vs `active` (rapport, pas de spawn hebdo) |
| Charge Team | tâches `failed` 7j, file `review` |
| Sous-projets | gelés / étagère (rapport) |

## Autonomie

| Niveau | Comportement |
|--------|----------------|
| **L1** | Spawn + **run auto** (`LBG_TEAM_EVOLUTION_L1_AUTO_RUN=1`) |
| **L2** | Spawn `approval_required=true` → bureau / `#/team` Approuver → Exécuter |

Règle Studio : pas de restart prod / write Core3 / deploy sans token.

La tâche PM parente peut rester `failed` s’il reste des **gaps** (comme l’autoconsult) : le timer systemd, lui, est `Result=success` dès que le playbook a fini.

## Ops 140

**Installé** le 2026-08-18. Timer `enabled` + `active`.

| | |
|--|--|
| Unité | `lbg-team-evolution-sprint-job.timer` |
| Premier run | 2026-08-18 18:03 CEST (rattrapage `OnBootSec` + `Persistent=true`) |
| Prochain | **2026-08-25 18:03 CEST** (`OnUnitActiveSec=7d`) |
| État job | `/var/lib/lbg/team_evolution/state.json` |
| Rapport | `/var/lib/lbg-ia-mmo/evolution_sprint.json` (à côté de la DB Team) |

```bash
# depuis packages/cortex
bash infra/scripts/install_team_evolution_sprint_job_vm.sh
# manuel (bypass cooldown) :
bash infra/scripts/run_team_evolution_sprint.sh

ssh lbg@192.168.0.140 'systemctl list-timers lbg-team-evolution-sprint-job.timer --no-pager'
ssh lbg@192.168.0.140 'journalctl -u lbg-team-evolution-sprint-job.service -n 40 --no-pager'
```

Deploy code (workflow + spawn) **avant** le timer, sinon le premier tir part sans le module :

```bash
bash tools/deploy_cortex_140.sh --full
# sur 140 :
sudo systemctl restart lbg-orchestrator
```

Rapport API : `GET /v1/team/meta` → `features.traces.last_evolution_sprint`.  
Preset Pilot `#/team` : **Sprint évolution** (clic = config, double-clic = lancer).

Variables : `infra/secrets/lbg.env.example` (`LBG_TEAM_EVOLUTION_*`).

| Variable | Défaut | Rôle |
|----------|--------|------|
| `LBG_TEAM_EVOLUTION_ENABLED` | `1` | Workflow Thémis |
| `LBG_TEAM_EVOLUTION_JOB_ENABLED` | `1` | Spawn timer |
| `LBG_TEAM_EVOLUTION_L1_AUTO_RUN` | `1` | Exécuter les followups L1 |
| `LBG_TEAM_EVOLUTION_PLATFORM_AUDIT` | `1` | Sonde Atlas multi-hôtes |
| `LBG_TEAM_EVOLUTION_JOB_COOLDOWN_S` | `518400` (6 j) | Anti double-tir vs timer 7 j |
| `LBG_TEAM_EVOLUTION_ROUND_TIMEOUT_S` | `840` | Timeout HTTP `POST …/run` |

## Tests

```bash
cd packages/cortex
python -m pytest orchestrator/tests/test_team_evolution_sprint.py \
  orchestrator/tests/test_loop_close_abc.py \
  orchestrator/tests/test_agent_mutator.py \
  orchestrator/tests/test_feature_proposer.py \
  orchestrator/tests/test_outcome_judge.py \
  orchestrator/tests/test_verify_chain.py \
  agents/tests/test_spawn_team_evolution_sprint_job.py -q
```

## Fichiers

- `orchestrator/team/evolution_sprint_workflow.py`
- `orchestrator/team/agent_mutator.py`, `feature_proposer.py`, `outcome_judge.py`, `post_judge.py`, `verify_chain.py`
- `agents/src/lbg_agents/spawn_team_evolution_sprint_job.py`
- `infra/systemd/lbg-team-evolution-sprint-job.{service,timer}`
- `infra/scripts/install_team_evolution_sprint_job_vm.sh`
- `infra/scripts/run_team_evolution_sprint.sh`
- Preset Pilot : `pilot_web/index.html` + `pilot_web/pilot_team.js` + `#/team/metrics`
- Plan : [`plan_meta_autonomie_l3.md`](plan_meta_autonomie_l3.md)
