# Freebox — aligner les baux DHCP sur le lab LBG

**Date** : 2026-10-02 · **Contrôle API** : plan lab sans `.142` (CT hands détruit) — smoke **13/13 OK**  
**UI** : `https://192.168.0.254/` → *Paramètres* → *Réseau local / DHCP* → onglet **Baux statiques**  
**Source de vérité** : [`REGISTRE.md`](REGISTRE.md) (table *Plan d’adressage Freebox*).

Les CT Proxmox (`.100` / `.110` / `.111` / `.141`) ont déjà une IP **statique dans `pct config`**.  
Les baux Freebox restent utiles pour : nom visible, anti-collision, et VMs en DHCP / NM.

## État (API Freebox OS — 2026-10-02)

| IP | Freebox bail statique | Notes |
|----|----------------------|--------|
| `.10` `.51` `.100` `.110` `.111` `.140` `.141` `.143` `.200` `.201` `.245` `.246` `.251` | **OK** | plan lab |
| **`.142`** | **absent** (OK) | CT détruit — pas de bail DHCP ; entrée LAN fantôme `lbg-Hands (142)` encore visible (inactive) |

Extras Freebox hors plan lab : Player / cam / VMware `.217`…

### Entrée LAN fantôme `.142`

L’API app `fr.lbg.cortex.freebox` a `settings=false` → **DELETE** LAN host refusé (`insufficient_rights`).

Pour nettoyer l’entrée `lbg-Hands (142)` / MAC `BC:24:11:16:BE:5E` :

1. **UI Freebox** : *Paramètres* → *Appareils connectés* (ou LAN) → oublier / supprimer `lbg-Hands (142)`  
   **ou**
2. Activer le droit **Paramètres / settings** pour l’app *LBG Cortex* (écran Freebox), puis relancer un DELETE API.

## Vérif LBG

```bash
bash packages/cortex/infra/scripts/smoke_freebox_lan.sh
# (re-pair une fois) bash packages/cortex/infra/scripts/authorize_freebox_app.sh  # LCD Freebox Server
```

Inventaire réseau (`network_inventory`) enrichit sa réponse avec l’audit Freebox si `LBG_FREEBOX_APP_TOKEN` est défini.

## Périmètre app `LBG Cortex` (lbg-omarchy) — accepté 2026-09-27

App Freebox OS appairée (LCD). Droits actuels côté session :

| Permission API | UI Freebox | Usage LBG |
|----------------|------------|-----------|
| *(DHCP / LAN — déjà OK sans `settings`)* | — | Audit baux + inventaire (`smoke_freebox_lan.sh`) |
| `downloader` | Gestionnaire de téléchargements | Piloter / suivre les téléchargements Freebox |
| `explorer` | Fichiers Freebox | État / espace disques & explorateur |
| `contacts` | Contacts | Consulter et alimenter le carnet |
| `calls` | Journal d’appels | Ops / historique (optionnel) |
| `tv` / `pvr` | Guide TV / enregistrements | Hors priorité Studio |
| `vm` | Contrôle VM Freebox | Hors priorité lab Proxmox |
| `settings` | Paramètres Freebox | **off** — requis pour DELETE bail / oublier appareil LAN |

**En place aujourd’hui** : lecture DHCP + LAN browser.  
**Rails suivants** (quand on brancherá des actions Compagnon / Team) : downloader, explorer (disques), contacts — même token `LBG_FREEBOX_APP_TOKEN`.
