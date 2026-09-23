# Prompt reprise — 7 sujets Cursor (WSL → SSH `.143`)

**Usage** : nouvelle conversation Agent sur Cursor **SSH `192.168.0.143`**, workspace `/home/lbg/projects/LBG_Studios`.  
Coller le bloc ci-dessous tel quel (ou retirer les sujets hors scope).

---

```text
Tu es sur LBG_Studios en Remote-SSH `.143` (`/home/lbg/projects/LBG_Studios`).
Réponds en français. Source de vérité code = ce clone + GitHub `Teome0245/LBG_Studios`.
Lab/prod = git push + scripts `packages/cortex/infra/scripts/deploy_*` (ex. `deploy_compagnon_100.sh`) — PAS de rsync massif projects → `.100`/`.140`.
Miroir WSL ↔ `.143` : `bash packages/cortex/infra/scripts/sync_projects_143.sh status|from-wsl|to-wsl`.
SMB Godot `.10` : `A:\` = `\\192.168.0.143\projects`. Docs : `packages/cortex/docs/omarchy_vm_143.md`, `docs/REGISTRE.md`.

Priorité monorepo : O1 Studio (`packages/cortex`) puis O2 Jeu (`packages/prime-client`). Pas de réintro web_client / mmo_server legacy.

## Contexte infra déjà fait (2026-09-23) — ne pas refaire
- Disque data `.143` 100 Go monté sur `/home/lbg/projects` ; rsync WSL → `.143` (~17 Go).
- Samba `\\192.168.0.143\projects` ; Cursor/VS Code peuvent travailler en SSH `.143`.
- Compagnon LAB : qualité média/outillage → `gemma-4-abliterated:12b` sur `.110` ; chat léger 2B `.111`.
- Cline Plan → `qwen3.5-abliterated:9b` (`.110`) ; Act → `gemma-4:12b`.
- Contre-pouvoir Agir + soft-confirm ; reshape média = filet si dérive seulement.
- Synchro lab documentée (section omarchy_vm_143 + REGISTRE).

## 7 sujets à reprendre (état WSL — conversations non migrées)

Travaille **un sujet à la fois** ; avant de coder : 5–10 lignes d’état (fichiers clés, prochain pas, risque). Cite chemins monorepo.

### 1) Core3 Prime comparison
Fichier touché : `godot_dev_workflow.py` (et comparatif Core3 / Prime).
But : clarifier écarts runtime Prime `.246` vs référence PreCU `.245` / workflows Godot.
Suite : inventaire écarts actionnables pour O2, sans modifier PreCU.

### 2) Defining AI existence
Fichiers : `lia_autonomy.py`, `lbg.env` (et docs autonomy Lia).
But : posture / flags autonomie Lia (existence, boucles, env).
Suite : aligner code + env lab + doc ; smoke flags `LBG_CORE3_LIA_*` si pertinent.

### 3) Character creation gameplay
Fichiers : `README_HUB.md`, map / hub character creation.
But : parcours création de perso (UX + data) côté Prime / hub.
Suite : état du flux actuel + gaps gameplay + prochain patch minimal.

### 4) Prime client portraits project
Fichiers / tests : `test_core3_account_admin` (portraits client).
But : pipeline portraits Prime Client (assets, admin compte, affichage).
Suite : reprendre tests + contrat UI Godot ; pas casser Launchpad paths.

### 5) Humanizing AI players plan
Fichiers / tests : `test_core3_player_autono*` (population / autonomie joueurs IA).
But : plan « humaniser » les AI players (comportement, timing, social).
Suite : plan court priorisé + 1 premier levier implémentable + tests.

### 6) Alternatives to Cursor IDE (session du jour — avancé)
Déjà livré côté studio local : Omarchy `.143`, Cline Plan 9b / Act 12b, Compagnon sans Groq, soft-confirm, reshape LAB, sync `.143`↔lab.
Suite utile : (a) valider Cline Plan 9b sur `.143` ; (b) smoke Compagnon `:5174` rip/Agir en 12b ; (c) commit doc/scripts sync si demandé ; (d) cutover éditeur (SSH `.143` défaut, WSL secours).

### 7) LBG ecosystem improvements
+444/−51 sur 5 fichiers (session parallèle).
But : améliorations écosystème LBG (Pilot / Compagnon / agents / docs).
Suite : `git status` / `git diff` sur `.143` pour voir ce qui est déjà là ; lister livrables restants ; ne pas écraser sans revue.

## Ordre suggéré aujourd’hui
1. Sujet 6 smoke rapide (Cline + Compagnon) si besoin de confiance outil.
2. Sujet 7 — inventaire diff ecosystem.
3. Puis O2 : 1 → 4 → 3 → 5 (jeu) et 2 (Lia) selon priorité produit.

## Première action demandée
Fais un tableau des 7 sujets : Statut estimé (inconnu/en cours/bloqué) · Fichiers à ouvrir · Prochain pas concret · Dépendance lab (.100/.140/.246).
Puis demande-moi lequel attaquer en premier (défaut : sujet 7 inventaire diff, puis 1).
```

---

**Astuce** : sur `.143`, après collage, envoie d’abord *« commence par le tableau »* pour forcer l’inventaire avant le code.
