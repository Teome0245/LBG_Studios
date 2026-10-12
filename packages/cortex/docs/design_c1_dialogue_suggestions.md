# Design C1 — Suggestions dialogue hub (Vague A)

**Ticket** : Boîte §14 **C1** · veille **Everwhere** (2–3 coups typés + texte libre)  
**Date** : 2026-10-05 · **Owner** : Iris (+ Chœur pour data/registry)  
**Statut** : design only — **pas d’implémentation** en Vague A  
**Gate** : C2 (mémoire → `world_hint` / `memory_hint`) alimente la pertinence des coups en **live** ; Vague B implémente C1+C2 ensemble ([`FOCUS_CONCURRENTS_TEAM.md`](../../../docs/FOCUS_CONCURRENTS_TEAM.md)).

---

## Objectif

Exposer dans le panneau dialogue Godot **2–3 actions suggérées** (boutons) plus le **champ texte libre** existant, sans casser le flux actuel `DialogueBridge` → `POST /v1/pilot/agent-dialogue/invoke`.

---

## État actuel (repère code)

| Couche | Comportement |
|--------|----------------|
| **Godot** | Clic PNJ → `main.gd::_open_npc_dialogue` → `DialogueBridge.request_npc_reply` (greeting si texte vide) → réponse dans `DialoguePortraitPanel` ; suivi via `LineEdit` + signal `followup_submitted`. |
| **Contexte wire** | `world_npc_id`, `npc_name`, `session_summary`, `world_hint` (config + map), `history`, `lyra_engagement=mmo_persona`. Clé `memory_hint` prévue dans `session_summary` mais **non alimentée** (C2). |
| **Agent 8020** | `dialogue_http_app.invoke` → `reply`, `lines`, `meta.*`, `commit` optionnel ; **pas** de `suggested_moves`. |
| **Quêtes / tip** | Parallèle : `mission_board_panel.gd` (Daan) — `GET /v1/quests/board`, `POST …/tip` (`lh_show_perle`) ; **non branché** au panneau dialogue. |
| **Registry** | `npc_registry.json` — rôles/goals/constraints par PNJ (`pilot_id=npc:core3_*`). |

---

## 1. Fichiers à toucher (Vague B)

### Prime Client (Godot)

| Fichier | Rôle |
|---------|------|
| `packages/prime-client/scripts/dialogue_portrait_panel.gd` | Zone boutons `suggested_moves` (2–3), désactivation si `busy`, clic → émet utterance. |
| `packages/prime-client/scenes/ui/dialogue_portrait_panel.tscn` | Layout (HBox boutons sous le corps, au-dessus du `LineEdit`). |
| `packages/prime-client/scripts/dialogue_bridge.gd` | Parser `suggested_moves` dans la réponse HTTP ; signal `reply_ready` étendu ou signal dédié ; conserver `free_text` inchangé. |
| `packages/prime-client/scripts/main.gd` | Brancher clic suggestion → `request_npc_reply(utterance, …)` ; optionnel : ouvrir board missions si `action=open_mission_board`. |
| `packages/prime-client/config/dialogue_bridge.json` | Seuils UI (`max_suggested_moves: 3`), pas de coups en dur canon. |
| `packages/prime-client/assets/maps/lost_heaven_npc_anchors.json` | Lecture seule pour `role` / `pilot_id` (pas obligatoire en C1 si coups viennent du serveur). |

### Cortex — agent dialogue & proxy

| Fichier | Rôle |
|---------|------|
| `packages/cortex/agents/src/lbg_agents/dialogue_http_app.py` | Ajouter `suggested_moves` dans le JSON de sortie `POST /invoke`. |
| `packages/cortex/agents/src/lbg_agents/dialogue_llm.py` | Injection prompt « proposer 0–3 coups **hors** du corps de la réply » **ou** post-traitement template (MVP recommandé : **templates data-driven**, LLM optionnel). |
| `packages/cortex/agents/src/lbg_agents/npc_registry.json` | Option : `suggestion_templates[]` par rôle/PNJ (ids stables, labels FR). |
| `packages/cortex/backend/api/v1/routes/pilot/proxy_agents.py` | Pass-through (enveloppe `OkEnvelope` extra=allow). |
| `packages/cortex/backend/api/v1/routes/pilot/_models.py` | Doc/types optionnels si validation stricte du champ (sinon dict libre). |

### Tests / smokes (Vague B)

| Fichier | Rôle |
|---------|------|
| `packages/cortex/agents/tests/test_dialogue_llm.py` | Cas registry + 2–3 moves pour 1 `world_npc_id`. |
| `tools/smoke_rang2_persona_dialogue.sh` | Extension : assert `suggested_moves` length 1–3. |
| `packages/cortex/infra/scripts/smoke_dialogue_llm_action_quest_commit_lan.sh` | Non régressions `commit` / quête. |

### Hors chemin C1 (référence seulement)

- `packages/prime-client/scripts/mission_board_panel.gd` — board Daan / tip scène (lien via coup typé `ui:mission_board`, pas duplication logique tip).
- `packages/prime-client/scripts/initiation_quest_panel.gd` — dialogue scripté Ryn (hors hub LLM).

---

## 2. Contrat API proposé

### Requête (inchangée)

`POST /v1/pilot/agent-dialogue/invoke` — corps identique à aujourd’hui (`actor_id`, `text`, `context` avec `world_npc_id`, `world_hint`, `session_summary`, `history`, …).

**Texte libre** : le client envoie le contenu du `LineEdit` dans `text` (comportement actuel). Les suggestions envoient la même clé `text` avec l’`utterance` du coup choisi.

### Réponse (extension additive)

Champs existants conservés (`ok`, `reply`, `lines`, `meta`, `commit`, …).

```json
{
  "reply": "… réponse PNJ courte …",
  "suggested_moves": [
    {
      "id": "move:perle_rumeur",
      "label": "Rumeurs du soir",
      "utterance": "Qu'est-ce qui se trame à La Perle ce soir ?",
      "kind": "social"
    },
    {
      "id": "move:perle_show",
      "label": "Spectacle ce soir",
      "utterance": "Y a-t-il un show à la scène ?",
      "kind": "info"
    }
  ],
  "meta": {
    "suggested_moves_source": "registry_template",
    "free_text_enabled": true
  }
}
```

| Champ | Type | Règles |
|-------|------|--------|
| `suggested_moves` | `array` | **0–3** éléments ; absent = `[]` (client OK). |
| `id` | `string` | Stable (`move:<slug>`), télémétrie / anti-drift. |
| `label` | `string` | **≤ 28 car.** — libellé bouton. |
| `utterance` | `string` | **≤ 160 car.** — envoyé comme `text` joueur au clic ; défaut = `label`. |
| `kind` | `string` | Enum souple : `social`, `info`, `quest`, `trade`, `training`, `ui` (ouvre panneau client). |
| `action` | `object?` | Si `kind=ui` : ex. `{"name":"open_mission_board"}` — **exécution client**, pas LLM. |

**`free_text`** : pas de champ API — le `LineEdit` reste toujours visible quand `chat_enabled` (PNJ). `meta.free_text_enabled: true` par défaut.

**C2 (future)** : enrichir le **choix** des templates via `context.session_summary.memory_hint` + flags quête ; pas de changement de forme `suggested_moves[]`.

**C12 (future)** : dupliquer les moves dans `structuredContent.suggested_moves` ; C1 reste compatible en lisant la racine.

---

## 3. Exemples de coups (hub Lost Heaven)

IDs registry : cantina **Jax Moro** `npc:core3_barman_jax` · board **Daan Oth** `npc:core3_daan_oth` · trainer MVP **Kell Asa** / `npc:core3_artisan_trainer_c` (ancre LH).

### La Perle (cantina — Jax Moro)

| id | label | utterance |
|----|-------|-----------|
| `move:perle_boisson` | Une boisson | Un verre, Jax — qu'est-ce que tu sers ce soir ? |
| `move:perle_show` | Show à la scène | Il y a un spectacle à La Perle ce soir ? |
| `move:perle_daan` | Missions | Daan Oth a-t-il du travail en ville ? |

### Board missions (Daan Oth)

| id | label | utterance / action |
|----|-------|-------------------|
| `move:daan_offres` | Voir les offres | `kind=ui`, `action={"name":"open_mission_board"}` **ou** utterance « Quelles missions as-tu ? » |
| `move:daan_desert` | Survivre au désert | Un conseil pour tenir hors des murs ? |
| `move:daan_perle` | Tip scène | `utterance` : « Je veux soutenir le show à La Perle. » (renvoie vers tip / quête `lh_show_perle` côté quest engine en Vague B+) |

### Trainer (artisan — Kell Asa / `trainer`)

| id | label | utterance |
|----|-------|-----------|
| `move:train_start` | Commencer | Je veux apprendre ton métier — par où on commence ? |
| `move:train_gear` | Outils | Quels outils il me faut pour travailler ici ? |
| `move:train_perle` | Pas la danse | (Renfort contrainte registry) Je cherche la formation danse — tu n'es pas le bon ? |

Règle Bible : formation **entertainer** → Talen Ress ; **spectacle** → artiste scène La Perle — les coups trainer **ne** proposent pas « cours de danse » sur un artisan/combat.

---

## 4. Smoke de validation

### Vague A (doc-only — Argus)

- Fichier présent : `packages/cortex/docs/design_c1_dialogue_suggestions.md`.
- Sections 1–5 présentes ; exemples JSON valides (parse `python3 -m json.tool` sur extraits ci-dessus).
- **Pas** `godot_login`, pas agent live requis.

### Vague B (runtime — cible)

1. **HTTP** : `curl POST …/v1/pilot/agent-dialogue/invoke` avec `world_npc_id=npc:core3_barman_jax`, `lyra_engagement=mmo_persona` → `reply` non vide + `1 ≤ len(suggested_moves) ≤ 3`, chaque move a `id` + `label`.
2. **Godot** : clic PNJ cantina → boutons visibles ; clic coup → second tour avec `text=utterance` ; saisie libre `LineEdit` inchangée.
3. **Daan** : au moins un coup `ui` ou utterance mission sans régression board (`mission_board_panel`).
4. **Régression** : `tools/smoke_rang2_persona_dialogue.sh` reste vert (`mmo_persona`).

---

## 5. Hors scope Vague A

- Implémentation Godot / agent / prompts LLM.
- **C2** : persistance relations, injection `memory_hint` / graphe.
- **C12** : envelope duale `structuredContent` complète.
- Génération **100 % LLM** des coups (risque drift Bible) — privilégier registry + contexte quête.
- Nouveaux PNJ, events C4, compagnon C3, voix/images Everwhere.
- Refonte `mission_board` ou sidecar quêtes au-delà d’un lien `kind=ui`.

---

## Références

- [`docs/FOCUS_CONCURRENTS_TEAM.md`](../../../docs/FOCUS_CONCURRENTS_TEAM.md) · [`docs/world/BOITE_IDEES_GAMEPLAY.md`](../../../docs/world/BOITE_IDEES_GAMEPLAY.md) §14 C1  
- [`docs/world/CONCURRENTS_IA_MMO_2026-10.md`](../../../docs/world/CONCURRENTS_IA_MMO_2026-10.md) §2 Everwhere  
- [`docs/lyra.md`](lyra.md) · ADR 0004 Rang 2 persona · `packages/prime-client/config/dialogue_bridge.json`
