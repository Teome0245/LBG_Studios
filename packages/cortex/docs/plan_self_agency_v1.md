# Plan — Agency Self v1 (leçons → drives → buts Lia)

**Date** : 2026-08-27  
**Statut** : Phases **A + B + C livrées** (flags Self / Lia goals défaut **off**)  
**Priorité** : O1 Studio (`packages/cortex`) ; IG Lia = phase C (O2 soft)  
**Exécution** : **équipe virtuelle Team** (declarations + `run_task` + timers + Pilot L2) — pas un chantier hors roster  
**Complète** : [plan_meta_autonomie_l3.md](plan_meta_autonomie_l3.md), [lbg_agentic_os.md](lbg_agentic_os.md), [vision_equipe_fable_autoconsultation.md](vision_equipe_fable_autoconsultation.md), ADR 0004 / 0014

## 0. Décision produit

Objectif : faire **émerger** une boucle d’agency (percevoir → vouloir → agir → apprendre), pas un second OS ni un plus gros LLM.

| Rang | Pilier | Effet | Owner Team (lead) |
|------|--------|-------|-------------------|
| **A** | Mémoire leçons (fermeture qualitative) | Apprendre pour de vrai | **Thémis** (PM) + **Argus** (QA) |
| **B** | Self-State + drives unifiés | Un seul « soi » mesurable | **Lyra** (Conductor) + **Atlas** (admin) |
| **C** | Buts internes Lia | Volonté visible in-game | **Chœur** (player_ia) + **Thémis** |

Ordre figé : **A → B → C**. Ne pas démarrer B tant que les critères A ne passent pas. Ne pas démarrer C tant que B drives-only n’est pas sync sur LAN.

**Principe d’implantation** : chaque livrable code est **porté par une tâche Team** (`role` + `objective` + `context` playbook), drainée par Lyra (L1) ou approuvée Pilot (L2). L’humain (Cursor / toi) implémente derrière Dédale/Iris quand il faut du code monorepo ; la Team **orchestre, vérifie, capitalise**.

---

## 0bis. Roster Team — qui fait quoi (Agency v1)

Personas = `packages/cortex/agents/declarations/*.json`. Pas de nouvel agent : on **étend capabilities / context flags** des existants.

| Persona | `role` | Mission Agency | Autonomie typique |
|---------|--------|----------------|-------------------|
| **Thémis** | `pm` | Briefs de phase, plan `/v1/team/plan`, autoconsult « santé leçons / Self », go/no-go, spawn follow-ups | L1 plan/synthèse ; L2 si propose write prod |
| **Lyra** | `pm` (conductor) | Drain file Agency, coffee-fill tâches L1, rapport idle campus, lit Self `pending_will` (B+) | L1 campus only |
| **Argus** | `qa` | Smokes acceptation A/B/C, post-judge, verify chain, refuse close si smoke rouge | L1 smoke ; bloque missions |
| **Héphaïstos** | `ops` | Sondes healthz, path `/var/lib/lbg/self`, flags env 140, dedup fichier leçons | L1 probe ; L2 restart |
| **Atlas** | `admin_infra` | Audit charge LLM (judge/leçons), matrice `.110`/`.111`, pas de double modèle lourd | L1 audit |
| **Dédale** | `dev_game` | Patches Cortex (lessons, self_state, hooks `roles.py`) — via Cursor / PR | L1 staging ; L2/Cursor merge |
| **Vulcan** | `dev_game` | Si touch Core3 build / ZB pour C (rare en A/B) | L2 build |
| **Iris** / **Hermès** | `dev_godot` | Hors chemin critique A/B ; C seulement si UI Pilot Self ou bridge client | L1/L2 selon surface |
| **Pygmalion** | assets | Hors scope Agency v1 | — |
| **Chœur** | `player_ia` | Phase C : probe sidecar, think/tick L2, garde Bible sur goals IG ; leçons `player_ia` | L1 probe ; **L2** think |

### RACI synthétique

| Livrable | Thémis | Lyra | Argus | Héphaïstos | Atlas | Dédale | Chœur | Humain/Pilot |
|----------|--------|------|-------|------------|-------|--------|-------|--------------|
| A leçons hard-fail/dedup | A | C | R (smoke) | C (ops fails) | C | **R** (code) | I | A (merge) |
| A acceptation LAN | A | C | **R** | R (env) | I | C | I | I |
| B Self-State | A | **R** (consomme) | R (smoke status) | R (path/disk) | **R** (flags LLM) | **R** (code) | I | A enable flag |
| C goals Lia | A | C | R (smoke) | C | I | R (hooks) | **R** (runtime IG) | A L2 think |

R = Responsible, A = Accountable, C = Consulted, I = Informed.

### Boucle Team (comment on exécute, pas un doc mort)

```text
Thémis : brief phase (autoconsult ou tâche pm context.agency_phase=A|B|C)
  → crée / planifie tâches spécialisées (qa, ops, dev_game, player_ia)
  → Lyra : drain L1 (campus conduct)
  → Argus : smoke acceptation
  → échec → post_judge / hard-fail → leçon (Phase A)
  → go/no-go Thémis → phase suivante
  → L2 Pilot si enable Self / think Lia / merge PR
```

Hooks **existants** à brancher (pas reinventer) :

| Hook | Usage Agency |
|------|----------------|
| Autoconsult 12–24 h (`autoconsult_workflow`) | Rubrique « leçons / Self » dans le round Thémis |
| Sprint évolution 7 j | Opportunité « agency_phase_* » → spawn mutator/proposer **seulement après A** |
| `run_task` + `lessons_slice` | Tous les rôles Agency |
| `post_judge` | Argus/PM/ops/player_ia |
| `verify_chain` | Après patch Dédale (smoke Argus) |
| Pilot `#/team` + `#/team/metrics` | Observabilité humaine |
| Timer `lbg-team-player-ia-job` | Phase C Chœur |
| Timer campus conductor | Lyra drain tâches Agency |

---

## 1. Diagnostic (état 2026-08-27)

| Brique | État | Gap bloquant Agency |
|--------|------|---------------------|
| `lessons_learned` + inject `run_task` | ✅ P0 | Effet faible / bruit |
| `post_judge` sample 35 % | ✅ | Rate bas ; leçons génériques répétées |
| Append sur `result.ok=False` | ✅ Agency A | — |
| Dédup leçons | ✅ Agency A | — |
| Trace `lessons_used` / `lessons_trace` | ✅ Agency A | — |
| Brain gauges + proactive tension | ✅ sync Self (B) | — |
| Lia lit `/v1/brain/status` | ✅ | + `/v1/self/status` goals (C) |
| Self-State fichier | ✅ Agency B | goals Lia Phase C ✅ |

---

## 2. Phase A — Fermer la mémoire leçons

**But** : toute tâche Team pertinente qui échoue (ou rate le juge) laisse une leçon **utile, dédupliquée**, et le prochain run peut prouver qu’il l’a vue.

**Lead Team** : Thémis (accountable) · **Argus** (acceptation) · **Dédale** (code) · Lyra (drain).

### 2.0 Playbook Team — tâches à spawner (Phase A)

Context flag commun : `"agency_phase": "A"`, `"agency_plan": "plan_self_agency_v1"`.

| Ordre | `role` | Persona | `objective` (exemple) | `context` clé | Auto |
|-------|--------|---------|----------------------|---------------|------|
| A-T0 | `pm` | Thémis | Brief Agency A — fermer boucle leçons | `agency_brief: true` | L1 |
| A-T1 | `dev_game` | Dédale | Implémenter hard-fail + dédup lessons | `agency_code: "A.1-A.2"` | L1 staging / Cursor |
| A-T2 | `dev_game` | Dédale | lessons_trace sur run_task + meta | `agency_code: "A.6"` | idem |
| A-T3 | `ops` | Héphaïstos | Dedup fichier knowledge + check path leçons 140 | `agency_ops: "A.7"` | L1 |
| A-T4 | `qa` | Argus | Smoke acceptation A1–A2 (fail forcé → 1 leçon) | `agency_smoke: "A"` | L1 |
| A-T5 | `qa` | Argus | Relance tâche → slice contient id + lessons_trace | `agency_smoke: "A2"` | L1 |
| A-T6 | `pm` | Thémis | Go/no-go Phase A → autoriser brief B | `agency_gate: "A"` | L1 |
| A-T7 | `pm` | Thémis | (option) Autoconsult + rubrique leçons | `autoconsult_round: true`, `agency_lessons_audit: true` | L1 timer |

Lyra : ces tâches entrent dans la file campus comme les autres ; pas de file parallèle.

### 2.1 Checklist opérationnelle (acceptation) — owners

- [ ] **A0** Inventaire leçons seed vs auto — **Héphaïstos** + Thémis
- [ ] **A1** Tâche QA smoke rouge → **1** leçon — **Argus** (exec) / Dédale si bug
- [ ] **A2** Relance → `lessons_slice` + `lessons_trace` — **Argus**
- [ ] **A3** Pilot metrics / `GET /v1/team/meta` — **Thémis** vérifie, Atlas charge LLM
- [ ] **A4** 7 j LAN : ≥ 5 leçons non-dup **ou** 1 récit anti-récidive — **Thémis** (suivi), Lyra (volume file)
- [ ] **A5** Pytest A verts — **Dédale** + Argus (CI locale / job)

### 2.2 Livrables code (A)

| # | Livrable | Owner code | Fichiers touchés (prévus) | Done quand |
|---|----------|------------|---------------------------|------------|
| **A.1** | Append **hard-fail** si `result.ok is False` (hors kinds meta exclus) | Dédale | `roles.py`, `lessons_learned.py` | Test : fail → +1 lesson |
| **A.2** | Dédup fenêtre 24–72 h (`last_seen`, `hit_count`) | Dédale | `lessons_learned.py` | 2 fails → pas de clone |
| **A.3** | Post-judge : pas de double-écriture si hard-fail déjà capitalisé | Dédale | `post_judge.py` | 1 leçon max |
| **A.4** | Roles post-judge défaut + `ops`, `player_ia` | Dédale / Argus | `post_judge.py` | Aligné roster |
| **A.5** | Hard-fail rate 1.0 ; soft sample 0.35 | Dédale | env + code | Doc |
| **A.6** | `result.lessons_trace` + meta Team | Dédale | `roles.py`, routes team | Visible Pilot |
| **A.7** | Nettoyage clones knowledge | Héphaïstos | `lessons_learned.json` (± script) | Fichier propre |
| **A.8** | Doc + lien meta L3 | Thémis / Dédale | ce plan + `plan_meta_autonomie_l3.md` | |

### 2.3 Hors Phase A

- Self-State fichier  
- Unification drives  
- Goals Lia  
- Changer le golden / mutator (déjà P1)  
- Spawn Feature Proposer « agency » (attendre go A)

### 2.4 Tests Phase A

```bash
cd packages/cortex && source .venv/bin/activate
python -m pytest orchestrator/tests/test_outcome_judge.py \
  orchestrator/tests/test_loop_close_abc.py \
  orchestrator/tests/test_lessons_close_a.py -q
```

Fichier neuf prévu : `orchestrator/tests/test_lessons_close_a.py`  
Cas : hard-fail append ; dédup ; pas de double post_judge ; slice contient id après append.  
**Argus** peut encapsuler la même commande dans un smoke owner Team.

### 2.5 Env (A)

| Variable | Défaut proposé | Rôle | Qui pose sur 140 |
|----------|----------------|------|------------------|
| `LBG_TEAM_LESSONS_ENABLED` | `1` | inchangé | Héphaïstos |
| `LBG_TEAM_LESSONS_HARD_FAIL` | `1` | A.1 on/off | Héphaïstos |
| `LBG_TEAM_LESSONS_DEDUP_HOURS` | `48` | fenêtre dédup | Héphaïstos |
| `LBG_TEAM_POST_JUDGE` | `1` | inchangé | Héphaïstos |
| `LBG_TEAM_POST_JUDGE_SAMPLE` | `0.35` | soft only | Héphaïstos |
| `LBG_TEAM_POST_JUDGE_ROLES` | `qa,pm,ops,dev_godot,dev_game,player_ia` | A.4 | Héphaïstos + Argus |

### 2.6 Estimation A

| | |
|--|--|
| Effort | ~0.5–1 j Dédale/Cursor + 0.5 j Argus/Héphaïstos smoke LAN |
| Risque | Faible (flags, pas de write hors knowledge/) |
| Rollback | `LBG_TEAM_LESSONS_HARD_FAIL=0` (Héphaïstos) + tâche Thémis « freeze Agency A » |

---

## 3. Phase B — Self-State + drives unifiés

**Prérequis** : go/no-go Thémis Phase A (A-T6) + critères A1–A5 verts Argus.

**But** : un fichier `self/state.json` = projection unique des drives / intent / refs mémoire. `goals[]` **vide**.

**Lead Team** : Lyra (consomme Self) · Atlas (flags/LLM) · Dédale (code) · Héphaïstos (path) · Thémis (gate).

### 3.0 Playbook Team — tâches Phase B

| Ordre | `role` | Persona | Objectif | Auto |
|-------|--------|---------|--------|------|
| B-T0 | `pm` | Thémis | Brief Agency B — Self-State drives-only | L1 |
| B-T1 | `dev_game` | Dédale | `self_state.py` + tests | L1/Cursor |
| B-T2 | `ops` | Héphaïstos | Créer `/var/lib/lbg/self`, droits, env `LBG_SELF_STATE_*` | L1 |
| B-T3 | `admin_infra` | Atlas | Vérifier sync tick n’explose pas charge Ollama | L1 |
| B-T4 | `qa` | Argus | Smoke `GET /v1/self/status` vs brain | L1 |
| B-T5 | `pm` | Lyra/Conductor | Rapport : Self lisible depuis campus / meta | L1 |
| B-T6 | `pm` | Thémis | Go/no-go enable `LBG_SELF_STATE_ENABLED=1` sur 140 | **L2 Pilot** (flag prod) |

### 3.1 Contrat Self-State v0.1

Path runtime : `/var/lib/lbg/self/state.json` (`LBG_SELF_STATE_PATH`)  
Spec : schéma ci-dessous (figé pour B ; goals réservés à C).

```json
{
  "schema_version": 1,
  "updated_ts": 0.0,
  "identity": {
    "self_id": "lbg_cortex_self",
    "display_name": "Cortex",
    "mode": "studio",
    "incarnations": { "studio": "lyra", "mmo": "lia" }
  },
  "drives": {
    "curiosity": 0.25,
    "tension": 0.0,
    "stress": 0.2,
    "fatigue": 0.1,
    "confidence": 0.7,
    "social_hunger": 0.0
  },
  "drives_meta": {
    "scale": "0_1",
    "sources": {
      "curiosity": ["brain.gauges.curiosity", "proactive.curiosite"],
      "tension": ["proactive.tension"],
      "stress": ["brain.gauges.stress"],
      "fatigue": ["brain.gauges.fatigue"],
      "confidence": ["brain.gauges.confidence"],
      "social_hunger": ["lia.silence_players_s"]
    },
    "last_decay_ts": 0.0
  },
  "intent": {
    "primary": "monitor",
    "narrative": "",
    "horizon": "reflex"
  },
  "goals": [],
  "beliefs": {
    "lan_health": "unknown",
    "orchestrator_ok": null,
    "bible_drift": "unknown",
    "team_backlog_pressure": 0.0
  },
  "memory_refs": {
    "lessons_path": "packages/cortex/knowledge/lessons_learned.json",
    "lessons_count": 0,
    "lessons_slice_ids": [],
    "last_lesson_id": null,
    "brain_state_path": "/var/lib/lbg/brain/state.json",
    "evolution_sprint_path": null
  },
  "pending_will": [],
  "last_tick": {
    "kind": "none",
    "ts": 0.0,
    "ok": null,
    "summary": ""
  }
}
```

Échelle drives : **toujours 0–1** dans Self (brain 0–100 → `/100` à la sync).

`beliefs.team_backlog_pressure` : Lyra / store Team (nb queued / busy) — lecture Conductor.

### 3.2 Matrice R/W (B) — code + Team

| Acteur | Team | R | W | Champs |
|--------|------|---|---|--------|
| `services/self_state.py` | Dédale | ● | ● | load/save atomique |
| `services/brain.py` | — | ● | ● | gauges → drives ; intent |
| `services/proactive.py` | — | ● | ● | tension/curiosite |
| `lessons_learned` | tous rôles via run_task | ○ | ● | memory_refs |
| `roles.run_task` | roster | ● | ○ | lit Self / lessons |
| Campus Conductor | **Lyra** | ● | ○ | backlog_pressure, pending_will |
| Atlas audit | **Atlas** | ● | ○ | drives + charge |
| Pilot `#/team` | humain | ● | ○ | `GET /v1/self/status` |
| Chœur / Lia | — | ○ | ○ | **pas en B** |

### 3.3 Livrables code (B)

| # | Livrable | Owner | Fichiers | Done quand |
|---|----------|-------|----------|------------|
| **B.1** | Module `self_state.py` + `LBG_SELF_STATE_ENABLED` défaut `0` | Dédale | `orchestrator/services/self_state.py` | unit tests |
| **B.2** | Sync brain tick | Dédale | `brain.py` | state à chaque tick |
| **B.3** | Sync proactive | Dédale | `proactive.py` | drives |
| **B.4** | Hook append_lesson → memory_refs | Dédale | `lessons_learned.py` | count OK |
| **B.5** | `GET /v1/self/status` + proxy Pilot | Dédale / Iris si UI | routes | curl LAN Argus |
| **B.6** | Doc + présence bureau (Lyra zone Self) optionnel | Thémis | docs / presence | |
| **B.7** | Tests | Dédale + Argus | `test_self_state.py` | pytest vert |
| **B.8** | Capability déclaration (meta) `self_status` sur Atlas ou Lyra | Thémis | `agents/declarations/*.json` **manuel L2** | introspection `/team/meta` |

### 3.4 Hors Phase B

- Génération `goals[]`  
- Mute auto declarations (B.8 = PR humaine / L2)  
- Write desktop depuis Self  

### 3.5 Estimation B

| | |
|--|--|
| Effort | ~1–1.5 j Dédale + 0.5 j Héphaïstos/Atlas/Argus |
| Risque | Faible si flag off ; **enable = L2 Pilot (B-T6)** |
| Rollback | Héphaïstos `LBG_SELF_STATE_ENABLED=0` |

---

## 4. Phase C — Buts internes Lia

**Prérequis** : B-T6 fait ; Self enabled ; A stable (Thémis + Argus).

**But** : si drives dépassent seuils, créer un `goal` `surface=mmo` `owner=lia` ; le tick autonomie **consomme** ce but avant la rotation de scènes déterministes.

**Lead Team** : **Chœur** (runtime) · Thémis (policy) · Dédale (hooks) · Argus (smoke) · Pilot L2 (think).

### 4.0 Playbook Team — tâches Phase C

| Ordre | `role` | Persona | Objectif | Auto |
|-------|--------|---------|--------|------|
| C-T0 | `pm` | Thémis | Brief Agency C — buts Lia + seuils | L1 |
| C-T1 | `dev_game` | Dédale | goal_policy + upsert Self + hooks Lia | Cursor |
| C-T2 | `player_ia` | Chœur | Probe sidecar + baseline bots avant goals | L1 |
| C-T3 | `player_ia` | Chœur | Think/tick avec goals (après flag) | **L2** |
| C-T4 | `qa` | Argus | Smoke : 1 goal créé, 1 action, done/decay | L1 |
| C-T5 | `pm` | Thémis | Go/no-go `LBG_LIA_GOALS_ENABLED=1` | **L2 Pilot** |
| C-T6 | `player_ia` | Chœur | Garde Bible : goal ne contredit pas lore | L1 guard |

### 4.1 Contrat goal (rappel)

```json
{
  "id": "goal_…",
  "surface": "mmo",
  "owner": "lia",
  "title": "Saluer un joueur proche",
  "origin": "drive:social_hunger",
  "priority": 0.6,
  "status": "active",
  "autonomy": "L1",
  "created_ts": 0.0,
  "expires_ts": null,
  "success_when": ["interact:greet"],
  "lesson_refs": [],
  "last_action": null
}
```

Règles :

- Max **2** goals actifs `owner=lia`.  
- `autonomy=L2` si action = think tick Chœur / write sensible (tokens existants).  
- Succès → `status=done` + decay drive + leçon `success` optionnelle (**Chœur** / post_judge).  
- Timeout → `status=expired` + leçon soft.  
- ADR 0004 : goals `mmo` **sans** contexte desktop.  
- Chœur refuse goal si écart Bible (C-T6).

### 4.2 Livrables code (C)

| # | Livrable | Owner | Fichiers | Done quand |
|---|----------|-------|----------|------------|
| **C.1** | `goal_policy.py` seuils → candidats | Dédale + Thémis (seuils) | `team/goal_policy.py` | unit tests |
| **C.2** | `upsert_goal` Self | Dédale | `self_state.py` | |
| **C.3** | Lia consomme goal avant scène rotation | Dédale / Chœur | `lia_orchestrator.py` | tick suit goal |
| **C.4** | `social_hunger` sync | Dédale | `core3_player_events.py` | drive bouge |
| **C.5** | `lessons_slice` dans prompt Lia (cap 2) | Dédale | `lia_orchestrator.py` | |
| **C.6** | Flag + smoke + timer player_ia | Héphaïstos / Chœur | env + job | |
| **C.7** | Tests | Dédale + Argus | `test_lia_goals.py` | |

### 4.3 Estimation C

| | |
|--|--|
| Effort | ~1.5–2 j + smoke Prime 246 (Chœur/Argus) |
| Risque | Moyen IG — flags off ; enable **L2** |
| Rollback | `LBG_LIA_GOALS_ENABLED=0` + freeze tâches `player_ia` Agency |

---

## 5. Plan d’exécution (sprints Team)

```text
Sprint A                 Sprint B                  Sprint C
Thémis brief A           Thémis brief B            Thémis brief C
Dédale A.1–A.6           Dédale Self               Dédale goals
Héphaïstos A.7 + env     Héphaïstos path + Atlas   Chœur probe/think L2
Argus smoke A            Argus smoke /v1/self      Argus smoke IG
Lyra drain file          Lyra lit Self             Lyra drain + Chœur job
Thémis gate A ─────────► Thémis+Pilot L2 enable ─► Thémis+Pilot L2 goals
```

| Sprint | Gate Team | Go / no-go |
|--------|-----------|------------|
| Fin A | Tâche `pm` `agency_gate: A` + Argus vert | Hard-fail → 1 leçon dédup ; meta trace ; pytest A |
| Fin B | Tâche L2 enable Self | Status JSON cohérent ; goals[] vide |
| Fin C | Tâche L2 enable Lia goals | 1 goal → 1 action → done/decay ; flag off = baseline |

PRs (Dédale/Cursor) + **tâches Team miroir** :

1. `feat(team): hard-fail lessons + dedup` ↔ A-T1  
2. `feat(team): lessons_trace on run_task` ↔ A-T2  
3. `feat(orch): self_state + /v1/self/status` ↔ B-T1  
4. `feat(lia): goals from self drives` ↔ C-T1  

Sprint évolution 7 j : **après go A**, Thémis peut lister opportunité `agency_self_state` ; pas avant (évite bruit Feature Proposer).

---

## 6. Garde-fous (inchangés + Team)

1. Pas de second orchestrateur / CrewAI sur chemin critique.  
2. Pas de mute auto `agents/declarations/*.json` (B.8 = L2 / PR).  
3. L2 Pilot pour enable Self, enable goals Lia, think Chœur, merge PR.  
4. ADR 0004 : Self unique ; actionneurs studio (Lyra/Team) vs mmo (Chœur/Lia) séparés.  
5. Atlas : Judge / sync Self respectent matrice LLM `.110`/`.111`.  
6. Lyra ne crée pas de buts IG — elle **draine** la file Studio.

---

## 7. Métriques de succès Agency v1 (Pilot + Team meta)

| Métrique | Owner suivi | Cible 30 j après C |
|----------|-------------|-------------------|
| Leçons auto utiles (non-dup / 7 j) | Thémis / Argus | ≥ 5 |
| Preuve « leçon évitée récidive » | Thémis | ≥ 1 (brief ou metrics) |
| Self-State uptime | Lyra / Héphaïstos | tick brain = update Self |
| Goals Lia completed / expired | Chœur | completed ≥ 40 % sample |
| Régression smoke LAN / Team | Argus | 0 bloquant |
| File campus Agency sans congestion | Lyra | idle rapport OK |

---

## 8. Prochaine action concrète (Team-first)

**Agency v1 code complet** (A leçons → B Self → C buts Lia). Flags prod **off** par défaut.

Enable LAN (ordre L2 Pilot) :

1. Héphaïstos : `/var/lib/lbg/self` + env A  
2. `LBG_SELF_STATE_ENABLED=1`  
3. `LBG_LIA_GOALS_ENABLED=1` (après smoke Self)  
4. Argus : smoke tick Lia → `reason` préfixe `lia_goal:`  
5. Chœur : probe sidecar + think L2 si besoin  

```bash
cd packages/cortex && source .venv/bin/activate
python -m pytest orchestrator/tests/test_lessons_close_a.py \
  orchestrator/tests/test_self_state.py \
  orchestrator/tests/test_goal_policy.py \
  agents/tests/test_lia_goals.py -q
```

Env Phase C :

| Variable | Défaut | Rôle |
|----------|--------|------|
| `LBG_LIA_GOALS_ENABLED` | `0` | active buts Lia |
| `LBG_LIA_GOAL_SOCIAL_HUNGER_MIN` | `0.45` | seuil social |
| `LBG_LIA_GOAL_CURIOSITY_MIN` | `0.55` | seuil curiosité |
| `LBG_LIA_GOAL_TENSION_MIN` | `0.60` | seuil tension |
| `LBG_LIA_GOALS_MAX_ACTIVE` | `2` | plafond |
| `LBG_LIA_GOAL_TTL_S` | `1800` | expiration |

---

## 9. Références

| Sujet | Chemin |
|-------|--------|
| Méta L3 (déjà livré P0–P3) | `docs/plan_meta_autonomie_l3.md` |
| Vision équipe / autoconsult | `docs/vision_equipe_fable_autoconsultation.md` |
| OS agentique | `docs/lbg_agentic_os.md` |
| Déclarations agents | `agents/declarations/*.json` |
| Registre Team | `orchestrator/team/agent_registry.py` |
| Lessons | `orchestrator/team/lessons_learned.py`, `knowledge/lessons_learned.json` |
| Post-judge | `orchestrator/team/post_judge.py` |
| Run task / roles | `orchestrator/team/roles.py` |
| Sprint 7 j | `docs/team_evolution_sprint.md` |
| Brain | `orchestrator/services/brain.py` |
| Proactive | `orchestrator/hybrid_proactive_agent/engine.py` |
| Lia / Chœur | `lia_orchestrator.py`, `studio_player_ia_choeur.json` |
| ADR équipe | `docs/adr/0014-equipe-virtuelle-orchestrateur.md` |
| ADR assistant vs MMO | `docs/adr/0004-assistant-local-vs-persona-mmo.md` |
