# Priorités actuelles — LBG Studios

**Date** : 2026-10-07  
**Source de vérité** : ce monorepo (`Teome0245/LBG_Studios`) — toute nouvelle feature.  
**Legacy** (`LBG_IA_MMORPG`, `new_mmo`) : lecture, correctifs urgents et gel documenté — **pas** de réouverture du client web `/mmo/` ni de `mmo_server` / `mmmorpg_server`.

Liens : [`OBJECTIVES.md`](../OBJECTIVES.md) · [`REGISTRE.md`](REGISTRE.md) · [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) · [`FOCUS_CONCURRENTS_TEAM.md`](FOCUS_CONCURRENTS_TEAM.md) · [`PLAN_72H_CONCURRENTS.md`](PLAN_72H_CONCURRENTS.md) · [`PLAN_MMO_O2.md`](PLAN_MMO_O2.md) · [`RUNTIME_GODOT.md`](RUNTIME_GODOT.md) · [`SMOKE_LAN.md`](SMOKE_LAN.md) · [`RESTAURATION_PRODUIT.md`](RESTAURATION_PRODUIT.md)

---

## Ordre stratégique

**O1 Studio d’abord, O2 Jeu ensuite.**

**Étoile du nord produit** : une IA incarnée sur PC/infra, puis persona au cœur du MMO, avec une évolution contrôlée du monde.  
Checklist de restauration : [`RESTAURATION_PRODUIT.md`](RESTAURATION_PRODUIT.md).

---

## O1 — Studio (priorité actuelle)

Cœur opérationnel : `packages/cortex` — Pilot sur le LAN (`.140:8080`), Team, méta-autonomie L3, smoke LAN, sprint d’évolution 7 jours (L1 auto / L2 Pilot).

### Focus explicite (depuis sept. 2026) — [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md)

**Compagnon Studio** (type Jarvis) :

| Rôle | Surface |
|------|---------|
| Présence conversationnelle | `.100:5174` (`compagnon_ui`) |
| Ops / Team / approvals L2 | Pilot `.140:8080/pilot/` |
| Bureau Windows | `packages/compagnon-desktop` (tray, overlay, notifications) |

Jalons **D0–D5** (+ character / voix) : **OK** sur checklist.  
**Focus suivant** : **D6 Causerie crédible** ([`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) § D6) — fluidité collègue / continuité de fil / pas de runbook Agir en discussion. **Gate avant O2.**

**Règle produit** : les 30 premières secondes doivent sentir un **compagnon**, pas un hub technique.  
Pilot reste le cockpit ops ; on n’absorbe **pas** Team/Jobs dans un clone de `:5174`.  
Tant que D6 (feeling Jarvis / MC sur `:5174`) n’est pas crédible, le pari jeu « 30 s Lost Heaven » ([`FOCUS_WAHOU.md`](FOCUS_WAHOU.md), archivé) et O2 ne repassent pas en tête.

Infra LLM locale (`.110` heavy / `.111` light) : [`packages/cortex/docs/local_llm_route_matrix.md`](../packages/cortex/docs/local_llm_route_matrix.md).

**Règle dev** : nouvelle feature Studio → `packages/cortex`.

---

## O2 — Jeu

`packages/prime-client` + `packages/prime-hub` + `packages/launchpad` → `.246:8787`.  
Plan : [`PLAN_MMO_O2.md`](PLAN_MMO_O2.md) · runtime : [`RUNTIME_GODOT.md`](RUNTIME_GODOT.md).

**P6 Godot-first G5 = live** (peel natif, HTTP+WS unifiés, Core3/Python hors chemin joueur, Launchpad Prime-only).

| Rail | État |
|------|------|
| **P6** | **fait** 2026-10-07 — `prime-hub` G5 |
| **P3** | Persona / compagnon **en jeu** — prochain focus O2 |
| **P4** | Pont SOE joueur — **de facto retiré** (hub Godot) ; nettoyer restes docs/UI |
| **P5** | World Director / combat / cour de chasse sur `prime-hub` |

Lore : [`world/BIBLE_MMO.md`](world/BIBLE_MMO.md).

**Règle dev** : feature jeu → `packages/prime-client` / `packages/prime-hub` (pas Core3, pas spike Python).

---

## Hors scope volontaire

- Fusion d’Infographiste dans le monorepo
- Migration Core3 serveur dans Git
- Suppression immédiate des repos legacy
- Réintroduction du stack MMO web legacy

---

## En pratique pour le dev

| Action | Où |
|--------|-----|
| Nouvelle feature Studio | `packages/cortex` |
| Nouvelle feature jeu (O1 vert) | `packages/prime-client` |
| Vérif LAN | `bash tools/smoke_lan_surfaces.sh --functional` — [`SMOKE_LAN.md`](SMOKE_LAN.md) |

**En une phrase** : consolider le Compagnon sur `:5174` + Pilot/Team sur Cortex, puis P3–P4 MMO sur Prime Client, sans diluer l’effort dans le legacy ni rouvrir le MMO web.
