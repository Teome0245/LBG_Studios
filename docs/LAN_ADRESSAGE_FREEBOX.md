# Freebox — aligner les baux DHCP sur le lab LBG

**Date** : 2026-10-05 · **Contrôle API** : plan lab sans `.142` (CT hands détruit) — smoke **13/13 OK** · `settings: true`  
**UI** : `https://192.168.0.254/` → *Paramètres* → *Réseau local / DHCP* → onglet **Baux statiques**  
**Source de vérité** : [`REGISTRE.md`](REGISTRE.md) (table *Plan d’adressage Freebox*).

Les CT Proxmox (`.100` / `.110` / `.111` / `.141`) ont déjà une IP **statique dans `pct config`**.  
Les baux Freebox restent utiles pour : nom visible, anti-collision, et VMs en DHCP / NM.

## État (API Freebox OS — 2026-10-05)

| IP | Freebox bail statique | Notes |
|----|----------------------|--------|
| `.10` `.51` `.100` `.110` `.111` `.140` `.141` `.143` `.200` `.201` `.245` `.246` `.251` | **OK** | plan lab |
| **`.142`** | **absent** (OK) | CT détruit — bail DHCP + entrée LAN nettoyés (2026-10-05) |

Extras Freebox hors plan lab : Player / cam / VMware `.217`…

## Vérif LBG

```bash
bash packages/cortex/infra/scripts/smoke_freebox_lan.sh
# (re-pair si besoin) bash packages/cortex/infra/scripts/authorize_freebox_app.sh
```

Inventaire réseau (`network_inventory`) enrichit sa réponse avec l’audit Freebox si `LBG_FREEBOX_APP_TOKEN` est défini.

## Périmètre app `LBG Cortex` (lbg-omarchy) — 2026-10-05

App Freebox OS `fr.lbg.cortex.freebox` (device `lbg-omarchy`). Droits session (contrôle 2026-10-05) :

| Permission API | UI Freebox | Usage LBG | État |
|----------------|------------|-----------|------|
| *(DHCP / LAN)* | — | Audit baux + inventaire (`smoke_freebox_lan.sh`) | **on** |
| `settings` | Modification des réglages de la Freebox | DELETE bail / oublier appareil LAN | **on** |
| `downloader` | Gestionnaire de téléchargements | Piloter / suivre les téléchargements Freebox | on |
| `explorer` | Fichiers Freebox | État / espace disques & explorateur | on |
| `contacts` | Contacts | Consulter et alimenter le carnet | on |
| `calls` | Journal d’appels | Ops / historique (optionnel) | on |
| `tv` / `pvr` | Guide TV / enregistrements | Hors priorité Studio | on |
| `vm` | Contrôle VM Freebox | Hors priorité lab Proxmox | on |
| `wdo` / `player` | Provisionnement / Player | Optionnel | on |
| `parental` / `profile` / `home` / `camera` | — | Non requis lab | off |

### Activer / rouvrir `settings`

Sur Freebox **v7**, l’écran LCD d’appairage **ne propose souvent pas** la checklist de droits : l’auth est accordée sans `settings`. Il faut éditer après coup dans Freebox OS (compte admin, pas Mode invité) :

1. `https://192.168.0.254/` → **Paramètres de la Freebox** → **Gestion des accès** → onglet **Applications**
2. Ligne **LBG Cortex** (`lbg-omarchy`) → crayon **Éditer** → cocher **Modification des réglages de la Freebox** → **OK**

Re-pair si le token est révoqué :

```bash
bash packages/cortex/infra/scripts/authorize_freebox_app.sh
# Puis re-cocher settings dans Gestion des accès (voir ci-dessus)
```

Vérif :

```bash
cd packages/cortex && set -a && source infra/secrets/freebox.env.local && set +a
python3 - <<'PY'
import importlib.util
from pathlib import Path
p = Path("agents/src/lbg_agents/freebox_client.py").resolve()
spec = importlib.util.spec_from_file_location("fb", p)
fb = importlib.util.module_from_spec(spec); spec.loader.exec_module(fb)
meta = fb.discover_api(); s = fb.open_session(api_meta=meta)
print("settings:", (s.get("permissions") or {}).get("settings"))
fb.close_session(s["session_token"], api_meta=meta)
PY
```

**En place** : lecture DHCP + LAN browser + droit `settings` (écritures DHCP/LAN possibles).  
**Rails suivants** (quand on branchera des actions Compagnon / Team) : downloader, explorer (disques), contacts — même token `LBG_FREEBOX_APP_TOKEN`.
