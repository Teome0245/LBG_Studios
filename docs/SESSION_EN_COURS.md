# Session en cours — LBG Studios

**Mis à jour** : 2026-10-09  
**Branche** : `cursor/priorit-s-actuelles-lbg-studios-d491` (HEAD `eb67117` au bootstrap)  
**Outil** : partagé Cursor ↔ Antigravity — **lire au démarrage, mettre à jour avant de partir**.

---

## Objectif actuel

Continuité multi-outils : même canon O1/O2 pour Antigravity et Cursor.  
Travail produit sous-jacent (inchangé) : Compagnon D6 vert + hub Godot P3–P5 sans rouvrir le legacy.

## Snapshot priorités (voir détail dans PRIORITES_ACTUELLES)

| Rail | État |
|------|------|
| **O1 Compagnon** | D0–D6 OK (smoke D6 V6–V8 PASS 2026-10-06) ; gate *feeling* ouverte — `FOCUS_COMPAGNON.md` |
| **O1 ops** | Lot gaps A–F2 + tick L3 livré 2026-10-07 ; L3 `days_ok` → viser 3/3 |
| **O2 hub** | P6 Godot-first G5+ **live** (`.246:8787`) ; P3 wiki live ; P5 telegraph boss **vert** 2026-10-08 |
| **Interdit** | Core3 / gateway SOE / `hub_runtime` Python sur chemin joueur |

## Prochaines actions (à ajuster en fin de session)

1. Confirmer dans Antigravity : Customizations → Rules voit `.agents/rules/` + `AGENTS.md`.
2. Si reprise Compagnon UI : coller `docs/handoff_antigravity_visuel_compagnon.md` (ticket séparé de la sonde AD).
3. Si reprise ops LAN : `bash tools/smoke_lan_surfaces.sh --functional` + `docs/SMOKE_LAN.md`.

## Fichiers / surfaces utiles

| Quoi | Où |
|------|-----|
| Canon agents | `AGENTS.md`, `.agents/rules/` |
| Priorités | `docs/PRIORITES_ACTUELLES.md` |
| Registre | `docs/REGISTRE.md` |
| Runtime jeu | `docs/RUNTIME_GODOT.md` |
| Handoff visuel Compagnon | `docs/handoff_antigravity_visuel_compagnon.md` |
| Handoff sonde AD | `docs/handoff_antigravity_sonde_ad.md` |
| Workspace | `LBG_Studios.code-workspace` |

## Bloquants

_Aucun bloquant documenté pour ce bootstrap._

## Notes de session

- 2026-10-09 : bootstrap continuité Antigravity (`.agents/rules/`, `~/.gemini/GEMINI.md`, ce fichier).
- WIP locaux non commités observés au bootstrap : `FOCUS_COMPAGNON.md`, `spawn_team_campus_conductor_job.py`, `compagnon_ui/nginx.conf`, `chat_intent.py` — ne pas écraser sans vérifier le diff.

---

## Prompt de démarrage (coller dans Antigravity)

```
Repo : LBG_Studios. Réponses en français.
Lis dans l’ordre : AGENTS.md → docs/SESSION_EN_COURS.md → docs/PRIORITES_ACTUELLES.md
→ le handoff @docs/handoff_…md si cité.
Confirme en ≤10 lignes : objectif, contraintes, prochain pas — avant toute édition.
En fin de session : mets à jour docs/SESSION_EN_COURS.md.
```
