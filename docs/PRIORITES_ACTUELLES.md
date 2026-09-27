# Priorités actuelles — LBG Studios

**Date** : 2026-09-27  
**Source de vérité** : ce monorepo (`Teome0245/LBG_Studios`) — docs, Cursor et packages.  
**Pas** les repos legacy (`LBG_IA_MMORPG`, `new_mmo`) pour les nouvelles features.

Liens : [`OBJECTIVES.md`](../OBJECTIVES.md) · [`REGISTRE.md`](REGISTRE.md) · [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) · [`PLAN_MMO_O2.md`](PLAN_MMO_O2.md) · [`SMOKE_LAN.md`](SMOKE_LAN.md) · [`RESTAURATION_PRODUIT.md`](RESTAURATION_PRODUIT.md)

---

## Ordre global

**O1 Studio d’abord, O2 Jeu ensuite.**

**Étoile du nord produit** : IA incarnée sur PC/infra → persona au cœur du MMO → évolution contrôlée du monde  
(checklist : [`RESTAURATION_PRODUIT.md`](RESTAURATION_PRODUIT.md)).

---

## O1 — Studio (prioritaire)

Cortex recentré : **Compagnon Studio** (type Jarvis), Team, Campus/Lyra, desktop hybride — **sans** réintroduire le client web legacy `/mmo/` ni `mmo_server` / `mmmorpg_server`.

### Focus actuel (2026-09-16/17) — [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md)

Les **30 premières secondes** du chat produit doivent sentir un **compagnon**, pas un hub technique.

| Surface | Rôle |
|---------|------|
| **Présence conversationnelle** | `compagnon_ui` sur `.100:5174` (entrée produit) |
| **Cockpit ops / L2** | Pilot sur `.140:8080` (`#/assistant`, équipe, jobs, approvals) |
| **Desktop** | `packages/compagnon-desktop` sur poste `.10` (overlay / tray) |

**Autonomie bornée** : L1 auto · L2 toi (Pilot) · L3 Miroir → propositions sans merge aveugle (déjà largement en place côté méta-autonomie).

Beaucoup de jalons O1 sont marqués OK dans [`OBJECTIVES.md`](../OBJECTIVES.md) (extrait Cortex, deploy Pilot LAN, sprint évolution 7j, L3, smoke LAN, compagnon D0–D3).  
Le travail restant est surtout **continuité produit** : greffer/extraire le front Compagnon dans le monorepo, persona/voix unifiées, desktop `.10`.

**Règle dev** : toute nouvelle feature Studio → `packages/cortex`.  
Matrice LLM locale 110/111 documentée dans les règles Cursor du repo.

---

## O2 — Jeu (après O1)

Godot `packages/prime-client` + Launchpad + serveur Prime `.246`.  
Plan exécuteur : [`PLAN_MMO_O2.md`](PLAN_MMO_O2.md).

| Rails | État |
|-------|------|
| **P0–P2c, P5a** | Largement faits (smokes M11/M12, talents/craft, missions hub, cantina stub, cour de chasse sandbox) |
| **P3** | Persona en jeu — jaune, Rang 2 — hors scope immédiat du focus Compagnon |
| **P4** | Retrait pont SOE Python — ouvert |
| **P5** | World Director en parallèle |

Le focus « wahou » 30 s Lost Heaven est **archivé** ([`FOCUS_WAHOU.md`](FOCUS_WAHOU.md)) au profit du Compagnon Studio.

**Règle dev** : nouvelles features jeu après O1 vert → `packages/prime-client`.

---

## Hors scope volontaire

- Fusion Infographiste dans le monorepo
- Core3/DB dans Git
- Suppression immédiate des repos legacy
- Second OS type CrewAI
- Réintégration du legacy gelé (`hybrid_proactive_agent`, etc.) dans l’extract Cloud

---

## En pratique sur ce monorepo

**Priorité immédiate** = faire vivre le Compagnon (UI `:5174`, Pilot assistant, desktop) dans `packages/cortex`, avec smoke LAN ([`SMOKE_LAN.md`](SMOKE_LAN.md)) comme garde-fou.

Le jeu avance surtout en maintenance / P3–P4 tant que le Studio tient le focus Compagnon.
