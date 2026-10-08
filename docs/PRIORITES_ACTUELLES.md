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

Jalons **D0–D6** (+ character / voix) : **OK** sur checklist (smoke D6 V6–V8 **PASS** 2026-10-06).  
Gate feeling Compagnon **ouverte** — voir [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) § D6.  
**Suite Studio** : maintenir causerie sticky / Pilot Agir stables ; ops LAN (status Pilot lent si healthz agents KO).

**Règle produit** : les 30 premières secondes doivent sentir un **compagnon**, pas un hub technique.  
Pilot reste le cockpit ops ; on n’absorbe **pas** Team/Jobs dans un clone de `:5174`.  
O2 / hub Godot peut avancer en parallèle tant que D6 reste vert sur `:5174`.

Infra LLM locale (`.110` heavy / `.111` light) : [`packages/cortex/docs/local_llm_route_matrix.md`](../packages/cortex/docs/local_llm_route_matrix.md).

**Règle dev** : nouvelle feature Studio → `packages/cortex`.

---

## O2 — Jeu

`packages/prime-client` + `packages/prime-hub` + `packages/launchpad` → `.246:8787`.  
Plan : [`PLAN_MMO_O2.md`](PLAN_MMO_O2.md) · runtime : [`RUNTIME_GODOT.md`](RUNTIME_GODOT.md).

**P6 Godot-first G5+ = live** (peel natif, Triplons + autonomie bots, Core3/Python hors chemin joueur).

| Rail | État |
|------|------|
| **P6** | **fait** 2026-10-07 — `prime-hub` G5+ ([`HUB_LIFE_TRIPLONS.md`](design/HUB_LIFE_TRIPLONS.md)) |
| **P3** | Persona en jeu — dialogue + Chœur V50–V53 · **C3–C8 live** (wiki `/v1/wiki`) 2026-10-07 |
| **P4** | Pont SOE joueur — **de facto retiré** (hub Godot) ; nettoyer restes docs/UI |
| **P5** | Cour + densité + hotbar + spawn + engage + **telegraph boss client** **vert** 2026-10-08 |

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

**En une phrase** : Compagnon D6 vert sur `:5174` + Pilot/Team Cortex ; O2 hub Godot (P3–P5) sans diluer l’effort dans le legacy ni rouvrir le MMO web.

### Lot Studio ops (2026-10-07)

Pilote gaps agentiques A–F2 + tick L3 ops_health : **livré** (Fleet Pilot, `action_policy`, presence soft-links, Slack HITL, smoke LAN mission).  
Doc : [`packages/cortex/docs/plan_combler_gaps_agentiques.md`](../packages/cortex/docs/plan_combler_gaps_agentiques.md) · runbook ops health.  
**Suite immédiate** : activer `LBG_TEAM_CAMPUS_*` si besoin pour act Chœur · finir L3 `days_ok=3` · D6.5 greeting/short_social (plan présence).
