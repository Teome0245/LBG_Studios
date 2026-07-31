# Handoff équipe — Prime LBG · Godot · TreFiles minimal

**Date** : 2026-07-14  
**Émetteur** : Pilote (via Cockpit P03)  
**Statut** : **à exécuter** — tâches équipe distribuées  
**ADR** : [`new_mmo/lbg-mmo/docs/adr/0016-prime-axe-lbg-talents-artisanat.md`](../../../../new_mmo/lbg-mmo/docs/adr/0016-prime-axe-lbg-talents-artisanat.md)

---

## Décision produit (à partager)

| Axe | Décision |
|-----|----------|
| **Gameplay Prime** | Talents Pre-CU + **artisanat** uniquement |
| **Univers** | **LBG** — sortie progressive Star Wars (`core3_cleanup_plan`) |
| **Client cible** | **Godot `prime-client`** — SWGEmu en **transition** puis retrait |
| **Serveur 246** | TreFiles **minimal** actif (`LBG_TRE_MINIMAL_SERVER=1`) — boot OK, sidecar `:8791` OK |
| **Docs** | Inventaire TRE, ADR 0016, vision `prime_axis_talents_artisanat.md` |

---

## Missions par rôle

### @themis (pm) — Thémis

**Objectif** : tenir le fil réunification et jalons M10–M12.

| # | Action | Livrable |
|---|--------|----------|
| 1 | Intégrer ADR 0016 au brief réunification | Ligne dans `subprojects.py` + prochain timer pm |
| 2 | Planifier jalons client Godot M10→M12 | Tableau dates dans `plan_de_route.md` |
| 3 | Marquer `client_swgemu` **transition** → retrait post-M12 | Registre Cockpit |
| 4 | Valider critères « done » Piste 1 (craft smoke) | Checklist ADR 0016 |

**Preset Cockpit** : `@themis brief réunification Prime LBG Godot jalons M10`

---

### @dedale (dev_game) — Dédale

**Objectif** : serveur Core3 axe artisan + neutralisation IP SW.

| # | Action | Livrable |
|---|--------|----------|
| 1 | **Smoke craft** bout-en-bout sur 246 (novice → schematic → experiment) | Rapport + log core3 |
| 2 | Backlog `core3_cleanup_plan` phase 1 — screenplays/Jedi/GCW | PR ou doc jalons |
| 3 | Hub artisan LBG — valider distributeur Mod+ sur 246 | `core3_artisan_hub.md` à jour |
| 4 | Inventorier IFF minimal extrait vers `bin/datatables/` (phase B) | Liste chemins |

**Preset** : `@dedale smoke craft artisan prime 246 après TreFiles minimal`

---

### @iris (dev_godot) — Iris

**Objectif** : UI Godot talents + craft (M10).

| # | Action | Livrable |
|---|--------|----------|
| 1 | Spec écrans **skills tree** + **schematics** 2D (prime-client) | `docs/jalon_m10_craft_ui.md` |
| 2 | Brancher sidecar `:8791` pour état joueur / skills (lecture) | Proto Godot |
| 3 | Aligner sprites stations/outils (Infographiste) | `sprite_manifest.json` |

**Preset** : `@iris spec UI talents craft prime-client M10 sidecar 8791`

---

### @hermes (dev_godot) — Hermès

**Objectif** : réseau Godot ↔ Core3 (M11–M12), remplacement login SOE.

| # | Action | Livrable |
|---|--------|----------|
| 1 | Spec pont **lbg-ws/2** ou protocole documenté | `jalon_godot_client_live_team.md` MAJ |
| 2 | POC login LBG sans client SWG (sidecar ou UDP léger) | Spike + ADR amendement |
| 3 | Coordonner avec `@dedale` pour commandes craft serveur | Contrat API |

**Preset** : `@hermes spec réseau Godot Core3 remplacement client SWG M12`

---

### @pygmalion (dev_game) — Pygmalion / Infographiste

**Objectif** : assets 2D LBG pour Godot (pas TRE retail).

| # | Action | Livrable |
|---|--------|----------|
| 1 | Sprites overhead **Lia / Nix / Mira** (BACKLOG prime) | PNG dans `prime-client/assets/` |
| 2 | Icônes stations craft + ressources (2D) | Manifest + deploy script |
| 3 | Pas de dépendance client SWG — pipeline LOCAL ComfyUI | `Infographiste_IA` |

**Preset** : `@pygmalion sprites craft stations prime-client overhead joueurs`

---

### @choeur (player_ia) — Chœur du monde

**Objectif** : valider le monde Prime après changement TreFiles.

| # | Action | Livrable |
|---|--------|----------|
| 1 | Sonde 246 — joueurs en ligne, sidecar, bots Lia/Nix/Mira | Snapshot équipe |
| 2 | Test in-game craft (compte bot ou Mod+) post-minimal TRE | Note dans events sidecar |
| 3 | Signaler régressions mesh/log si bloquant gameplay | Issue ops/qa |

**Preset** : `@choeur valider monde prime 246 après TreFiles minimal craft bots`

---

### @hephaistos (ops) — Héphaïstos

**Objectif** : infra 246 stable, doc ops TreFiles.

| # | Action | Livrable |
|---|--------|----------|
| 1 | Documenter config `config-local.lua` TreFiles minimal + rollback | Lien inventaire TRE |
| 2 | Surveiller disque 246 (watchdog P03 actif) | Pas de régression < 85 % |
| 3 | Backup `tre.bak` optionnel avant purge fichiers inutilisés sur disque | Runbook |

**Preset** : `@hephaistos documenter TreFiles minimal 246 rollback smoke`

---

### @argus (qa) — Argus

**Objectif** : smokes post-changement.

| # | Action | Livrable |
|---|--------|----------|
| 1 | Smoke **boot** 246 + UDP 44553 + sidecar 8791 | Vert LAN |
| 2 | Smoke **Godot** sidecar mirror + M5 play | `smoke_godot_sidecar_mirror_lan.sh` |
| 3 | Smoke **craft** (coordination Dédale) | Entrée historique plan_de_route |
| 4 | `smoke_tre_minimal_prime_246.sh --dry-run` dans CI ops | Script versionné |

**Preset** : `@argus smoke prime 246 TreFiles minimal godot sidecar lan`

---

## Références techniques

| Doc | Chemin |
|-----|--------|
| ADR 0016 | `new_mmo/lbg-mmo/docs/adr/0016-prime-axe-lbg-talents-artisanat.md` |
| Inventaire TRE | `new_mmo/lbg-mmo/docs/inventaire_tre_prime_246.md` |
| Vision | `new_mmo/lbg-mmo/docs/prime_axis_talents_artisanat.md` |
| Smoke script | `new_mmo/lbg-mmo/infra/scripts/smoke_tre_minimal_prime_246.sh` |
| Registre projets | `docs/REGISTRE_PROJETS_LBG.md` |

---

## Déclenchement automatique

```bash
# Sur VM core 140 (orchestrateur legacy :8010)
cd /opt/LBG_IA_MMO
bash infra/scripts/spawn_team_prime_lbg_handoff.sh

# Dry-run
bash infra/scripts/spawn_team_prime_lbg_handoff.sh --dry-run
```

Depuis poste dev :

```bash
LBG_ORCHESTRATOR_URL=http://192.168.0.140:8010 \
  bash LBG_IA_MMORPG/LBG_IA_MMO/infra/scripts/spawn_team_prime_lbg_handoff.sh
```

**Cockpit P03** (:8093) — preset **« Handoff Prime LBG »**

---

## Historique

| Date | Événement |
|------|-----------|
| 2026-07-14 | Handoff Pilote → équipe virtuelle |
