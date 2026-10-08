# Plan d’action — Présence studio → zone d’entraînement MMO

**Date** : 2026-10-08  
**Entrée** : smoke humain D6 [`smoke_humain_d6_2026-10-08.md`](smoke_humain_d6_2026-10-08.md)  
**Objectif produit** : le Compagnon tient une causerie collègue crédible **et** le MMORPG (Lost Heaven / `prime-hub`) sert de **zone d’entraînement** pour l’incarnation des joueurs IA (chaleur, humeur, présence observables).

**Hors scope** : rouvrir le MMO web legacy · diluer O1 dans une grosse feature jeu avant D6.5 vert.

---

## Pourquoi maintenant

Le fil humain a validé l’intention (studio → jeu = terrain d’essai) mais a exposé trois freins Compagnon :

1. Ouverture = hub ops (casse les 30 s).  
2. Demande de plan = méta sans artefact.  
3. « Allons-y » = `short_social` → zéro travail.

Sans corriger (1)–(3), toute transposition présence→MMO restera du roman. Ensuite seulement : injecter des **seuils mesurables** dans le hub (rail P3 / C3 déjà live).

---

## Phase A — D6.5 Compagnon (bloquant feeling)

| # | Livrable | Done quand | Owner | Effort |
|---|----------|------------|-------|--------|
| **A1** | Greeting → causerie courte | « bonjour / ça va » → 1–2 phrases présence, **zéro** Agir/`.143`/dry-run (sauf demande action) | Cortex / Compagnon | **OK code** 2026-10-08 — `is_greeting_chat` + `_SHORT_SOCIAL_RE` élargi |
| **A2** | C2 strict sur « collègues » | 1 avis concret (frustration O1 ou piste) sans bascule template | Cortex | S (partiel via nudge D6.2) |
| **A3** | `short_social` contextuel | `allons-y` / `allez` / `on y va` **ignorés** si livrable pending ou sticky causerie | `router_prompts` + `llm_chat_phase` | **OK code** 2026-10-08 |
| **A4** | Intent « livrer plan » | `wants_plan_delivery` / `plan_delivery_nudge` → markdown Objectif/Phases/Prochaine action | `chat_intent` + `llm_chat_phase` | **OK code** 2026-10-08 |
| **A4b** | Persistance Team | « soumettre au studio » → mission Campus (Hermès PM) + `campus_meta` / L2 cards | `plan_submit.py` + hook `llm_chat_phase` | **OK code** 2026-10-08 · flag `LBG_COMPAGNON_PLAN_SUBMIT` (défaut on en LAB) |
| **A5** | Smoke | V9 greeting + V10 plan delivery (voice-smoke) · deploy `:5174` · rejeu humain | Argus-style | **OK live** 2026-10-08 — `bash tools/smoke_d65_greeting_plan_5174.sh` → `SMOKE_D65_V9V10 OK` (+ mission Campus) |

**Root cause non-livraison** (2026-10-08) : (1) greeting hors causerie → `lab_ops` bible Agir ; (2) `short_social` mangeait « allons-y » ; (3) **aucun intent livrable** — le LLM restait en méta sous nudge « 1 avis ». Fix = A1+A3+A4. **A4b** : le markdown chat seul ne suffisait pas — spawn mission Campus pour Hermès/Team.

**Gate** : A1–A5 verts sur `:5174` (deploy overlay) avant Phase B code jeu.

---

## Phase B — Contrat présence joueurs IA (data / hub)

S’appuie sur l’existant : C3 Nix greet+escort · P3 dialogue · `relation_memory` (C2 gameplay) · Triplons.

| # | Livrable | Done quand | Owner | Effort |
|---|----------|------------|-------|--------|
| **B1** | Schéma `presence_dials` joueur IA | Pack JSON (chaleur, humeur, humour, initiative) aligné dials Compagnon lab, bornes 0–1, défauts par persona (Nix/Lia/…) | Chœur + Iris | S |
| **B2** | Injection runtime | `world_hint` / dialogue hub lit les dials → 1 ligne d’ambiance + 1 comportement observable (follow / commentaire / silence) | `prime-hub` | M |
| **B3** | Seuils d’interaction | Table : dial × distance × event → action autorisée (greet, escort, tip, ignore) — pas de LLM libre sur prix / combat | Iris | M |
| **B4** | Métrique « zone d’entraînement » | Smoke hub : spawn → 30 s présence compagnon IA avec dials ≠ neutre ; log session (tourrique légère) | Argus | S |

**Done Phase B** : un bot incarné au spawn LH se comporte **différemment** selon dials, mesurable au smoke.

---

## Phase C — Boucle Studio ↔ Jeu (entraînement)

| # | Livrable | Done quand | Owner | Effort |
|---|----------|------------|-------|--------|
| **C1** | Mandat Compagnon → brief hub | Depuis `:5174`, « teste présence Nix chaleur haute » crée un brief / job borné (dry-run → L2) vers smoke ou session hub | Compagnon + Pilot | M |
| **C2** | Retour terrain → causerie | Résultat smoke / chronique courte réinjecté dans le fil Compagnon (pas dump ops) | Compagnon | M |
| **C3** | Doc canon | Lien depuis [`PLAN_MMO_O2.md`](PLAN_MMO_O2.md) + [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) · boîte idées ticket « zone entraînement » | Thémis | S |

---

## Ordre d’exécution recommandé

```
A1 greeting ─┬─► A2 C2 avis
             ├─► A3 short_social sticky  ─► A4 intent plan ─► A5 smokes
             └─────────────────────────────────────────────► GATE
                                                              │
                                                              ▼
                                                         B1 → B2 → B3 → B4
                                                              │
                                                              ▼
                                                         C1 → C2 → C3
```

**Jour 1** : A1 + A3 (gros ROI feeling, bug « allons-y »).  
**Jour 2** : A2 + A4 + A5.  
**Jour 3+** : B1–B2 prototype LH ; B3–B4 ; C ensuite.

---

## Contre-pouvoir (inchangé)

- Agir = dry-run → confirm humain.  
- Pas d’exécution L2 depuis la seule causerie.  
- Phase C : briefs hub = allowlist / dry-run comme le reste Pilot.

---

## Critères de succès (objectif atteint)

1. Rejeu du fil humain 2026-10-08 : C1+C2 **PASS**, go-ahead produit un **plan markdown** (pas « Je te suis »).  
2. Sur Lost Heaven : 1 joueur IA avec dials non neutres, présence 30 s **smokeable**.  
3. Compagnon peut **discuter** de la zone d’entraînement **et** **soumettre** un plan studio utilisable sans méta vide.
