# Priorités actuelles — LBG Studios

**Date** : 2026-10-14  
**Source de vérité** : ce monorepo (`Teome0245/LBG_Studios`) — toute nouvelle feature.  
**Legacy** (`LBG_IA_MMORPG`, `new_mmo`) : lecture, correctifs urgents et gel documenté — **pas** de réouverture du client web `/mmo/` ni de `mmo_server` / `mmmorpg_server`.

Liens : [`OBJECTIVES.md`](../OBJECTIVES.md) · [`REGISTRE.md`](REGISTRE.md) · [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md) · [`SESSION_EN_COURS.md`](SESSION_EN_COURS.md) · [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) · [`PLAN_PRESENCE_ZONE_ENTRAINEMENT.md`](PLAN_PRESENCE_ZONE_ENTRAINEMENT.md) · [`design/HUB_AI_PLAYER_BRIDGE.md`](design/HUB_AI_PLAYER_BRIDGE.md) · [`FOCUS_CONCURRENTS_TEAM.md`](FOCUS_CONCURRENTS_TEAM.md) · [`PLAN_72H_CONCURRENTS.md`](PLAN_72H_CONCURRENTS.md) · [`PLAN_MMO_O2.md`](PLAN_MMO_O2.md) · [`RUNTIME_GODOT.md`](RUNTIME_GODOT.md) · [`SMOKE_LAN.md`](SMOKE_LAN.md) · [`RESTAURATION_PRODUIT.md`](RESTAURATION_PRODUIT.md)

---

## Ordre stratégique

**O1 Compagnon → O2 MMO (banc d’essai) → O3 Joueurs IA (portables).**  
Canon : [`OBJECTIVES.md`](../OBJECTIVES.md).

| Pilier | Priorité | Rôle |
|--------|----------|------|
| **O1 Compagnon** | actuelle | Incarnation hors MMO ; interface humains ↔ Studio / infra / écosystème |
| **O2 MMO** | parallèle si O1 vert | Terrain d’entraînement / simulation pour les Joueurs IA (+ MMO jouable) |
| **O3 Joueurs IA** | fondations OK, noyau = suite | Agents = joueurs ; à terme adapters hors Lost Heaven |

**Mutations dures** : pas de LLM libre sur économie / combat / craft / quête / réputation — [`OBJECTIVES.md`](../OBJECTIVES.md) § règle.  
Checklist de restauration : [`RESTAURATION_PRODUIT.md`](RESTAURATION_PRODUIT.md).

---

## O1 — Compagnon / Studio (priorité actuelle)

**Pilier** : incarnation hors MMO.  
Cœur ops : `packages/cortex` — Pilot (`.140:8080`), Team, méta-autonomie L3, smoke LAN, sprint évolution 7j (L1 auto / L2 Pilot).

### Focus explicite — [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md)

| Rôle | Surface |
|------|---------|
| Présence conversationnelle | `.100:5174` (`compagnon_ui`) |
| Ops / Team / approvals L2 | Pilot `.140:8080/pilot/` |
| Bureau Windows | `packages/compagnon-desktop` (tray, overlay, notifications) |

Jalons **D0–D6** (+ character / voix) : **OK** (smoke D6 V6–V8 **PASS** 2026-10-06).  
Fil **Jarvis / D5** : **clôturé** — [`lecon_d5_jarvis_proactif_2026-09-27.md`](lecon_d5_jarvis_proactif_2026-09-27.md).  
Gate feeling Compagnon **ouverte** — [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) § D6.  
**Suite Studio** : fil D6.5 / présence **clos** 2026-10-11 (A1–A4c.1 + Phases B/C) · L3 smoke LAN **DONE** 2026-10-11 · **ouverts** : A2/C2 feeling / polish retour terrain — [`PLAN_PRESENCE_ZONE_ENTRAINEMENT.md`](PLAN_PRESENCE_ZONE_ENTRAINEMENT.md) § *Clôture de fil*.  
**Fil hygiène contexte / monde** : **clos** 2026-10-14 — [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) § *Fil hygiène*.  
**Fil Mods→Compagnon** : **clos & live** 2026-10-14 — [`FOCUS_COMPAGNON.md`](FOCUS_COMPAGNON.md) § *Fil Mods Claude*.  
**D7 Présence Agents** : code livré — [`LECON_PRESENCE_AGENTS_D7_2026-10-09.md`](LECON_PRESENCE_AGENTS_D7_2026-10-09.md) · sync worker `.143` encore ouvert.

**Règle produit** : les 30 premières secondes = **compagnon**, pas hub technique.  
Pilot = cockpit ops ; pas d’absorption Team/Jobs dans un clone de `:5174`.  
O2 / O3 peuvent avancer en parallèle tant que D6 reste vert sur `:5174`.

Infra LLM locale (`.110` heavy / `.111` light) : [`packages/cortex/docs/local_llm_route_matrix.md`](../packages/cortex/docs/local_llm_route_matrix.md).

**Règle dev** : feature Compagnon / Studio → `packages/cortex`.

---

## O2 — MMO (banc d’entraînement)

**Pilier** : Lost Heaven = simulation / mises en situation pour Joueurs IA (+ jeu humain).  
`packages/prime-client` + `packages/prime-hub` + `packages/launchpad` → `.246:8787`.  
Plan : [`PLAN_MMO_O2.md`](PLAN_MMO_O2.md) · runtime : [`RUNTIME_GODOT.md`](RUNTIME_GODOT.md) · zone entraînement : [`PLAN_PRESENCE_ZONE_ENTRAINEMENT.md`](PLAN_PRESENCE_ZONE_ENTRAINEMENT.md).

**P6 Godot-first G5+ = live** (peel natif, Triplons + autonomie bots, Core3/Python hors chemin joueur).

| Rail | État |
|------|------|
| **P6** | **fait** 2026-10-07 — `prime-hub` G5+ ([`HUB_LIFE_TRIPLONS.md`](design/HUB_LIFE_TRIPLONS.md)) |
| **P3** | Persona en jeu — dialogue + Chœur V50–V53 · **C3–C8 live** (wiki `/v1/wiki`) 2026-10-07 |
| **P4** | Pont SOE joueur — **retiré (clos)** · autorité exclusive Godot headless G5+ (`:8787`) |
| **P5** | Cour + densité + hotbar + spawn + engage + **telegraph boss client** **vert** 2026-10-08 |
| **Zone entraînement** | Dials / seuils B1–B4 + boucle Compagnon C1/C2 **OK** 2026-10-08 |

Lore : [`world/BIBLE_MMO.md`](world/BIBLE_MMO.md).

**Règle dev** : feature jeu / hub → `packages/prime-client` / `packages/prime-hub` (pas Core3, pas spike Python).

---

## O3 — Joueurs IA (portables)

**Pilier** : agents = joueurs (compte + perso IG + pont) ; MMO = 1er adapter ; autres jeux = suite.  
Canon pont : [`design/HUB_AI_PLAYER_BRIDGE.md`](design/HUB_AI_PLAYER_BRIDGE.md) · data `ai_players.json` · `skill.md` hub.

| Fondations | État |
|------------|------|
| Identité `*_bridge` ≠ perso IG | OK |
| Soft-link Studio ↔ IG (ADR 0004) | OK |
| Présence différenciée (B3/B4) | OK |
| Noyau agent découplé + contrat d’environnement | **cible** (voir [`OBJECTIVES.md`](../OBJECTIVES.md) O3) |

**Hors scope immédiat** : 2ᵉ jeu avant contrat adapter stable sur Lost Heaven ; ouverture publique aux LLM internet.

**Règle dev** : contrats / flotte / skill agent → `prime-hub` data + docs design ; pas de logique joueur IA dans le legacy web.

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
| Feature Compagnon / Studio (O1) | `packages/cortex` |
| Feature banc d’essai / hub (O2) | `packages/prime-client` / `packages/prime-hub` |
| Contrats Joueurs IA (O3) | `prime-hub` data + [`HUB_AI_PLAYER_BRIDGE.md`](design/HUB_AI_PLAYER_BRIDGE.md) |
| Vérif LAN | `bash tools/smoke_lan_surfaces.sh --functional` — [`SMOKE_LAN.md`](SMOKE_LAN.md) |

**En une phrase** : Compagnon (O1) interface écosystème ; MMO (O2) entraîne les Joueurs IA (O3) sous mutations bornées — sans diluer dans le legacy.

### Lot Studio ops (2026-10-07)

Pilote gaps agentiques A–F2 + tick L3 ops_health : **livré** (Fleet Pilot, `action_policy`, presence soft-links, Slack HITL, smoke LAN mission).  
Doc : [`packages/cortex/docs/plan_combler_gaps_agentiques.md`](../packages/cortex/docs/plan_combler_gaps_agentiques.md) · runbook ops health.  
**Suite immédiate** : voir [`SUJETS_OUVERTS.md`](SUJETS_OUVERTS.md) — World Stream **clos** · feeling C2 rejeu · L3 ops **DONE**.
