# Priorités actuelles — LBG Studios

**Date** : 2026-09-27  
**Source de vérité** : ce monorepo (`Teome0245/LBG_Studios`) — toute nouvelle feature.  
**Legacy** (`LBG_IA_MMORPG`, `new_mmo`) : lecture, correctifs urgents et gel documenté — **pas** de réouverture du client web `/mmo/` ni de `mmo_server` / `mmmorpg_server`.

Liens : [`OBJECTIVES.md`](../OBJECTIVES.md) · [`REGISTRE.md`](REGISTRE.md) · [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) · [`PLAN_MMO_O2.md`](PLAN_MMO_O2.md) · [`SMOKE_LAN.md`](SMOKE_LAN.md) · [`RESTAURATION_PRODUIT.md`](RESTAURATION_PRODUIT.md)

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

Jalons **D0–D3** et pilotage (⌘K, Agir dry-run → réel) : **OK**.  
Le doc du 2026-09-18 couvre surtout polish UX, sonde AD et quota d’initiative.

**Règle produit** : les 30 premières secondes doivent sentir un **compagnon**, pas un hub technique.  
Pilot reste le cockpit ops ; on n’absorbe **pas** Team/Jobs dans un clone de `:5174`.  
Tant que le Compagnon n’est pas crédible sur `:5174`, le pari jeu « 30 s Lost Heaven » ([`FOCUS_WAHOU.md`](FOCUS_WAHOU.md), archivé) ne repasse pas en tête.

Infra LLM locale (`.110` heavy / `.111` light) : [`packages/cortex/docs/local_llm_route_matrix.md`](../packages/cortex/docs/local_llm_route_matrix.md).

**Règle dev** : nouvelle feature Studio → `packages/cortex`.

---

## O2 — Jeu (après O1)

`packages/prime-client` (Godot) + `packages/launchpad` → serveur Prime `.246`.  
Plan exécuteur : [`PLAN_MMO_O2.md`](PLAN_MMO_O2.md).

Beaucoup de rails **P0–P2c** (login M11, M12 WS, talents/craft, missions hub, cantina stub) sont faits ou en smoke vert. En cours / ouvert :

| Rail | État |
|------|------|
| **P3** | Persona en jeu — jaune, Rang 2 |
| **P4** | Retrait du pont SOE Python côté joueur |
| **P5** | World Director / bots en parallèle, sans bloquer P1–P4 |

Lore et anti-dérive : [`world/BIBLE_MMO.md`](world/BIBLE_MMO.md), etc.

**Règle dev** : nouvelle feature jeu (quand O1 est « vert » pour toi) → `packages/prime-client`.

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
