# Écosystème LBG — développement depuis `.143`

**Date** : 2026-09-23  
**But** : que **Compagnon**, la **Team** et le **studio** portent le développement du monorepo — pas seulement Cursor humain.  
**Poste éditeur** : Omarchy **`.143`** (VS Code + Cline + Continue) · secours WSL `.10`.

Voir aussi : [`sans_cursor.md`](sans_cursor.md) · [`omarchy_vm_143.md`](omarchy_vm_143.md) · [`cline/SMOKE.md`](cline/SMOKE.md) · [`FOCUS_COMPAGNON.md`](../../../docs/FOCUS_COMPAGNON.md).

---

## Qui fait quoi

| Acteur | Rôle développement | Surface |
|--------|--------------------|---------|
| **Humain** | Intention, L2, go/no-go | Compagnon `:5174`, Pilot, VS Code/Cline |
| **Compagnon** | Propose / Agir (dry-run → confirm) · ouvre éditeur `.143` · rappelle objectifs Studio | http://192.168.0.100:5174/ |
| **Team** (Lyra, Thémis, Dédale…) | Plans, tâches L1, smokes, leçons, Self | Pilot `#/team` · orch `:8010` |
| **Cline / VS Code sur `.143`** | Implémentation code (Plan 9b / Act 12b Ollama) | Workspace `/home/lbg/projects/LBG_Studios` |
| **Deploy lab** | git push + `deploy_*` (pas rsync massif) | ex. `deploy_compagnon_100.sh` |

Principe : **percevoir → vouloir → proposer → (humain/L2) → coder sur `.143` → commit/push → deploy → leçon**.

---

## Boucle cible (maturation M1+)

```text
Self / proactive (.140)  →  initiative Compagnon (:5174)
        ↓
  Agir L1 (dry-run)  ou  « ouvre VS Code / Cline sur omarchy »
        ↓
  Team run_task / plan  (Dédale, Argus…)
        ↓
  Édition sur .143 (Cline Plan→Act)  →  git commit/push
        ↓
  deploy_* lab  →  smoke  →  leçon / Self update
```

Compagnon **n’exécute pas** de Réel destructeur sans contre-pouvoir.  
Cline **n’est pas** un second OS : même monorepo, même matrice LLM (`.110`/`.111`).

---

## Actions Agir utiles (éditeur)

| Intention | Texte Agir typique |
|-----------|-------------------|
| Ouvrir l’IDE studio | `ouvre code sur omarchy` / `ouvre vscode sur omarchy` |
| Compagnon | `ouvre http://192.168.0.100:5174/ dans le navigateur` |
| Team / Jobs | `ouvre http://192.168.0.140:8080/#/team` · `#/jobs` |
| Smoke Cline | voir `docs/cline/SMOKE.md` (tags + chat 9b/12b) |

Cible desktop : agent Omarchy `:5005` (alias `omarchy` / `.143`). Soft-confirm LAB si `LBG_DESKTOP_APPROVAL_MODE=confirm`.

---

## Checklist « écosystème prêt à porter un sujet »

- [x] Dirty tree sauvé (lots M1) — pas de secrets dans git  
- [x] Compagnon déploie depuis `.143` (`deploy_compagnon_100.sh --smoke`)  
- [x] Orch Self joignable (`GET /v1/self/status`) + proxy Pilot slim (`/v1/pilot/orchestrator/self/status`)  
- [x] Initiative toast (silence → `jobs:idle` **ou** Self drives / `pending_will`)  
- [x] Bandeau **Self** sur `:5174` (curiosité / tension / intent)  
- [x] Team L1 depuis toast Compagnon (`POST /api/pilot/team/tasks` + run)  
- [x] Contre-pouvoir Agir (`companion/review-proposal` dans ActionCard)  
- [ ] VS Code + Cline sur `.143` (Plan 9b / Act 12b) smoke OK (manuel)  
- [ ] Doc sujet + leçon après merge  

Quand cette liste tient, on peut confier un sujet O2 (Core3/Prime…) à la boucle — pas avant.

---

## Hors scope immédiat

- Réintroduire Cursor Cloud comme unique chemin (optionnel via `cursor_agent_workflow`, pas obligatoire).  
- Features O2 jeu tant que M1–M3 maturité studio ne tiennent pas.  
- Rsync massif projects → `.100`/`.140`.
