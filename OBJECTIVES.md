# Objectifs LBG Studios

**Ordre d’exécution** : Compagnon / Studio (**O1**) → MMO banc d’essai (**O2**) → Joueurs IA portables (**O3**).

**Étoile du nord** (trois piliers) :

| Pilier | Objectif | Rôle |
|--------|----------|------|
| **O1 Compagnon** | Incarnation **hors MMO** de nos IA | Interface humains ↔ environnement / infra / écosystème LBG |
| **O2 MMO** | Lost Heaven / `prime-hub` | Lieu d’**entraînement**, simulation et mise en situation pour les Joueurs IA |
| **O3 Joueurs IA** | Agents = **joueurs** | Identité portable ; à terme, jouer **d’autres jeux** via adapters (le MMO est le premier) |

Formule courte : **Compagnon (hors-jeu) ↔ Joueur IA (noyau agent) ↔ MMO (simulateur borné)**.

**Organisme & Entité globale** : [`docs/ORGANISME_LBG.md`](docs/ORGANISME_LBG.md) — L'entité globale **Gladys**, son incarnation relationnelle **Lia**, et la cartographie des organes d'action multimodaux (`.10`, `.143`, `.140`, `.110/.111`, `.246`).  
Checklist restauration (vert/jaune/rouge) : [`docs/RESTAURATION_PRODUIT.md`](docs/RESTAURATION_PRODUIT.md).  
**Priorités actuelles** : [`docs/PRIORITES_ACTUELLES.md`](docs/PRIORITES_ACTUELLES.md).  
**Focus Compagnon** : [`docs/FOCUS_COMPAGNON.md`](docs/FOCUS_COMPAGNON.md) — présence `:5174` & Desktop Electron ; Pilot `#/assistant` = cockpit ops.  
**Zone d’entraînement** : [`docs/PLAN_PRESENCE_ZONE_ENTRAINEMENT.md`](docs/PLAN_PRESENCE_ZONE_ENTRAINEMENT.md).  
**Pont joueurs IA** : [`docs/design/HUB_AI_PLAYER_BRIDGE.md`](docs/design/HUB_AI_PLAYER_BRIDGE.md).  
*(Archivé jeu)* [`docs/FOCUS_WAHOU.md`](docs/FOCUS_WAHOU.md) — 30 s Lost Heaven.

### Règle mutations dures (canon)

**Pas de LLM libre sur mutations dures** : économie (prix, stock, tip), combat (dégâts, loot), craft / inventaire, progression quête, réputation.  
LLM = sélection d’action allowlistée + expression (dialogue, présence).  
Autorité = `prime-hub` + Bible / Chœur. Suggestions hors-jeu = file Studio, **pas** d’apply auto.  
Réf. : C7 trade borné · seuils présence B3 · [`packages/prime-hub/data/agent/skill.md`](packages/prime-hub/data/agent/skill.md) · Bible V40–V42.

---

## O0 — Cadre (ce repo)

- [x] Dépôt `Teome0245/LBG_Studios` = point de départ docs / Cursor / Team
- [x] Registre + objectifs versionnés ici
- [x] Allowlist Cursor Cloud Agent inclut ce repo (`LBG_CURSOR_AGENT_REPOS` sur 140)
- [x] Workspace Cursor : `LBG_Studios.code-workspace` + `~/projects/projects.active.code-workspace`

---

## O1 — Compagnon / Studio (prioritaire)

**Pilier** : incarnation hors MMO ; interface humain ↔ Studio / infra / écosystème.

Cortex opérationnel : **Compagnon** (présence `:5174` & Desktop Electron), Pilot ops (`:8080`), Team, Campus/Lyra, desktop hybride — **sans** client web legacy `/mmo/`.

| Critère done | Mesure | État |
|--------------|--------|------|
| Code Cortex extrait | `packages/cortex/` | OK |
| Pilot LAN | Deploy `tools/deploy_cortex_140.sh` → 140:8080 | OK |
| Team / healthz | `GET /v1/pilot/status` backend+orchestrator ok | OK |
| Sprint évolution 7j | Timer `lbg-team-evolution-sprint-job` sur 140 ; L1 auto / L2 Pilot | OK (2026-08-18) |
| Méta-autonomie L3 (Miroir→apply) | Judge, leçons, mutator, Feature Proposer, post-judge, `#/team/metrics` — [`packages/cortex/docs/plan_meta_autonomie_l3.md`](packages/cortex/docs/plan_meta_autonomie_l3.md) | OK (2026-08-21) |
| Accueil Pilot | Cartes Studio/Campus/Ops/Jeu/Projet + liens LAN (Cockpit, Compagnon :5174, Hub :8787) | OK |
| Compagnon Studio (présence) | Entrée = `.100:5174` (`compagnon_ui`) ; Desktop Electron = `packages/compagnon-desktop` ; [`docs/FOCUS_COMPAGNON.md`](docs/FOCUS_COMPAGNON.md) | OK (D0–D6 validé, feeling C1/C2 OK) |
| Freeze soft | `LEGACY.md` sur LBG_IA_MMORPG / new_mmo | OK |
| Smoke LAN surfaces | [`docs/SMOKE_LAN.md`](docs/SMOKE_LAN.md) + `tools/smoke_lan_surfaces.sh` | OK (2026-10-13, 24/24 surfaces OK) |
| Fil produit d’origine | [`docs/RESTAURATION_PRODUIT.md`](docs/RESTAURATION_PRODUIT.md) | OK (checklist) |
| Boucle Studio ↔ terrain | Brief présence + retour causerie (C1/C2 zone entraînement) | OK (2026-10-08) |

**Cible continue** : présence crédible (30 s) + Agir borné (dry-run → L2) + conscience monde (`world_stream`, relation memory) sans fusionner Mode A forge / Mode B jeu (ADR 0004).

---

## O2 — MMO (banc d’entraînement)

**Pilier** : Lost Heaven sert d’abord de **simulation / mise en situation** pour les Joueurs IA (situations diverses, présence mesurable), tout en restant un MMO jouable humain.

Client **Godot** `prime-client` + Launchpad + autorité **`prime-hub` `.246:8787`** (G5).  
Runtime : [`docs/RUNTIME_GODOT.md`](docs/RUNTIME_GODOT.md) · plan : [`docs/PLAN_MMO_O2.md`](docs/PLAN_MMO_O2.md).

| Critère done | Mesure | État |
|--------------|--------|------|
| Client extrait | `packages/prime-client/` + `packages/launchpad` | OK |
| Hub Godot-first | `packages/prime-hub` G5 — peel natif, HTTP+WS `:8787` | **OK** 2026-10-07 |
| Core3 / spike Python OFF | `stop_core3_and_spike_246.sh` (chemin joueur) | **OK** 2026-10-07 |
| Pas de Core3/DB dans Git | `.gitignore` + extract filtré | OK |
| Smoke documenté | [`packages/prime-client/SMOKE.md`](packages/prime-client/SMOKE.md) + [`docs/SMOKE_LAN.md`](docs/SMOKE_LAN.md) + hub `:8787/healthz` | OK |
| Login M11 + Launchpad → `J:` | Smoke M11 + M12 ; Launchpad ≥2.1.4 Prime-only | OK |
| Pipeline assets | Lien `Infographiste_IA` dans registre | OK |
| Zone d’entraînement (présence) | Dials B1–B4 + seuils B3 smokeables · [`PLAN_PRESENCE_ZONE_ENTRAINEMENT.md`](docs/PLAN_PRESENCE_ZONE_ENTRAINEMENT.md) | OK (2026-10-08) |
| Mutations dures bornées | Trade C7 ±15 % · craft/quest endpoints · pas de LLM libre prix/combat | OK (live hub) |

**Cible continue** : catalogue de situations (social, craft, explore, combat quand P2, events) pour confronter les Joueurs IA — métriques smokeables, Bible / Chœur comme garde-fous.

---

## O3 — Joueurs IA (agents portables)

**Pilier** : un Joueur IA est un **joueur** (compte + perso IG + pont hors-jeu), pas un PNJ. Le noyau agent doit pouvoir, à terme, brancher d’**autres jeux** via le même contrat d’environnement.

Fondations actuelles : [`HUB_AI_PLAYER_BRIDGE.md`](docs/design/HUB_AI_PLAYER_BRIDGE.md) · `ai_players.json` · `skill.md` hub · flotte `:8787`.

| Critère | Mesure | État |
|---------|--------|------|
| Identité out-game ≠ perso IG | login `*_bridge` · perso Nix/Lia/… · pont `player_bridge_*` | OK (2026-10-07) |
| Soft-link Studio ↔ IG | Vulcan/Hermès sans forge via hub (ADR 0004) | OK |
| Manuel agent | `GET /v1/agent/skill` + catalog / tick-matrix | OK (brouillon live) |
| Présence différenciée | dials + seuils → comportements observables (Nix ≠ Mira) | OK (B3/B4) |
| Noyau agent découplé du MMO | perception → décision → action → mémoire **hors** Godot ; MMO = 1er adapter | **cible** |
| Contrat d’environnement | actions typées + observations ; 2ᵉ jeu = nouvel adapter | **cible** |
| Cap flotte + anti-dérive | `max_ai_players` · anneau LH · Bible V40–V42 | OK (data) |

**Hors scope immédiat O3** : ouverture publique du serveur aux LLM internet ; rewrite text-only ; second jeu avant contrat adapter stable sur Lost Heaven.

---

## Hors scope (volontaire)

- Fusion Infographiste dans ce monorepo ; avatar_app reste en _archive
- Migration Core3 serveur dans Git
- Suppression immédiate des repos GitHub legacy
