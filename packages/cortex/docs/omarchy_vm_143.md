# VM Omarchy `.143` — lab Linux desktop sur NUC

**Statut** : **installée et joignable** — NUC `.200`, VMID **143**, IP **`192.168.0.143`**, user `lbg` (SSH clé)  
**Rôle** : bac Omarchy (Arch + Hyprland) 24/7 sur le LAN — **ne remplace pas** `.10`, `.141`, `.142`.  
**Date** : 2026-09-15

> Incident install : le premier cidata pointait `/dev/vda` ; sous VirtIO-SCSI Proxmox le disque est **`/dev/sda`**. Corrigé dans le script + relance `omarchy-iso-install`.

## Placement

| | Choix |
|--|--------|
| Hyperviseur | **`.200` (NUC)** — décharge le R720 `.201` |
| Forme | **QEMU VM** (UEFI/OVMF, Q35, VirtIO) — pas LXC |
| IP / VMID | **`192.168.0.143` / 143** |
| Hostname | `lbg-omarchy` |
| Spec | 4 vCPU · 8 Go RAM · **60 Go** root (`scsi0` / `/dev/sda`) + **100 Go** data (`scsi1` / `/dev/sdb` → `/home/lbg/projects`) · `local-lvm` |
| MAC | `BC:24:11:43:00:01` (réservation DHCP recommandée) |
| ISO | Omarchy **4.0.3** → `local:iso/omarchy-4.0.3.iso` |

## Disque data `projects` (option B)

**Date** : 2026-09-23

| | |
|--|--|
| Proxmox | `qm set 143 --scsi1 local-lvm:100,discard=on,iothread=1` → `vm-143-disk-2` |
| Guest | `/dev/sdb` · ext4 label `LBG_PROJECTS` · UUID `867dd627-1275-42c7-b207-fa44afbe59b1` |
| Mount | `/home/lbg/projects` (`fstab` `noatime,discard`) |
| Taille | **100 Go** (cible 120 Go impossible : `local-lvm` ~108 Go libres sur NUC `.200`) |
| Contenu | Rsync depuis WSL `sdesh@…:/home/sdesh/projects/` (~17 Go utiles ; exclus : `.venv`, `node_modules`, caches) |

Vérif :

```bash
ssh lbg@192.168.0.143 'df -h ~/projects; findmnt /home/lbg/projects; ls ~/projects'
ssh root@192.168.0.200 'qm config 143 | grep scsi'
```

Re-sync incrémental :

```bash
rsync -aH --partial --info=stats2 \
  --exclude '.venv/' --exclude '**/.venv/' \
  --exclude 'node_modules/' --exclude '**/node_modules/' \
  --exclude '__pycache__/' --exclude '**/.pytest_cache/' \
  --chown=lbg:lbg \
  /home/sdesh/projects/ lbg@192.168.0.143:~/projects/
```

Suite : share SMB pour Godot / Explorer depuis `.10` :

| | |
|--|--|
| UNC | `\\192.168.0.143\projects` |
| User | `lbg` (mdp = `LBG_OMARCHY_PASSWORD` dans `infra/secrets/omarchy-143.env.local`) |
| Service | `smb` (UFW 445/139 depuis `192.168.0.0/24`) |
| Note | `/home/lbg` en `711` pour permettre le traverse Samba |

```text
\\192.168.0.143\projects\LBG_Studios
\\192.168.0.143\projects\new_mmo
```

## Synchro `.143` ↔ lab / prod (ne pas oublier)

`.143` = **miroir éditeur** (VS Code / Cursor SSH / Cline). Ce n’est **pas** le runtime lab.

| Couche | Rôle | Comment synchroniser |
|--------|------|----------------------|
| **GitHub** `Teome0245/LBG_Studios` | Source de vérité code | `git pull` / `commit` / `push` depuis `.143` *ou* WSL |
| **`.143`** `/home/lbg/projects` | Poste édition + SMB `A:` | Miroir ; script `infra/scripts/sync_projects_143.sh` |
| **WSL `.10`** `/home/sdesh/projects` | Copie historique / secours | `sync_projects_143.sh from-wsl` ou `to-wsl` |
| **Lab `.100`** `/opt/orchestrateur` | Compagnon / orch UI runtime | **`deploy_compagnon_100.sh`** (pas un rsync projects entier) |
| **Prod Cortex `.140`** `/opt/LBG_IA_MMO` | Pilot / Team runtime | scripts `deploy_*` / REGISTRE — pas le share SMB |
| **Agents** `.10` / `.141` / `.142` / `.143:5005` | Exécution | deploy agent dédié (`deploy_linux_agent_143.sh`, etc.) |

**Flux nominal (édition sur `.143`)**

```text
edit .143 → git commit/push → deploy_compagnon_100.sh (et autres deploy_*) → smoke lab
                 ↘ sync_projects_143.sh to-wsl   # optionnel, garder WSL aligné
```

**À ne pas faire** : prendre `A:\` ou `.143` comme seule vérité sans push Git ; rsync massif `projects/` → `.100`/`.140`.

```bash
bash packages/cortex/infra/scripts/sync_projects_143.sh status
bash packages/cortex/infra/scripts/sync_projects_143.sh from-wsl   # WSL → .143
bash packages/cortex/infra/scripts/deploy_compagnon_100.sh --smoke
```

### GitHub depuis `.143`

Une **deploy key = un repo** (limite GitHub) → une clé + alias SSH par dépôt Teome0245.

| Dépôt local | Remote SSH | Clé |
|-------------|------------|-----|
| `LBG_Studios` | `git@github-studios:Teome0245/LBG_Studios.git` | `id_ed25519_gh_studios` |
| `Infographiste_IA` | `git@github-infographiste:Teome0245/Infographist_IA.git` | `…_infographiste` |
| `LBG_IA_MMORPG` | `git@github-lbg-ia-mmorpg:…` | `…_lbg-ia-mmorpg` |
| `new_mmo` | `git@github-new-mmo:…` | `…_new-mmo` |
| `_archive/*`, `_shelf/LBG_Project_03` | idem aliases | clés dédiées |
| `new_mmo/Core3` | `https://github.com/swgemu/Core3.git` | upstream public (HTTPS) |

Config : `~/.ssh/config` → `Host github-<alias>` · IdentityFile `~/.ssh/id_ed25519_gh_<alias>`.
Test : `git -C ~/projects/<repo> ls-remote --heads origin`.

## Ce que c’est / n’est pas

| Fait | Ne fait pas |
|------|-------------|
| Lab desktop Linux agent-friendly | Remplacer le poste `.10` (GPU / Comfy) |
| Snapshots Proxmox, console noVNC | Remplacer `lbg-executor` `.141` ou `lbg-hands` `.142` |
| SSH + tooling Arch (après install) | Porter le stack Studio / Prime |

## Déploiement

Depuis `packages/cortex` (WSL / poste dev, SSH root NUC) :

```bash
# 1) Télécharger l’ISO (~6 Go) + créer la VM (sans démarrer)
bash infra/scripts/create_omarchy_vm_proxmox.sh --download-iso

# 2a) Install interactive — démarrer puis console Proxmox
bash infra/scripts/create_omarchy_vm_proxmox.sh --start
# → https://192.168.0.200:8006/ → VM 143

# 2b) Install unattended (cidata) + démarrage
# Mot de passe auto → infra/secrets/omarchy-143.env.local (gitignoré)
bash infra/scripts/create_omarchy_vm_proxmox.sh --unattended --start
# ou :
# LBG_OMARCHY_PASSWORD='…' bash infra/scripts/create_omarchy_vm_proxmox.sh --unattended --start
```

Variables utiles : `LBG_PVE_HOST`, `LBG_OMARCHY_VMID`, `LBG_OMARCHY_MEMORY_MB`, `LBG_OMARCHY_DISK_GB`, `LBG_OMARCHY_ISO_VERSION`.

## Après install

1. **Retirer l’ISO** (boot disque) :

```bash
ssh root@192.168.0.200 'qm set 143 --ide2 none,media=cdrom --boot order=scsi0'
# si cidata :
ssh root@192.168.0.200 'qm set 143 --delete ide3'
```

2. **qemu-guest-agent** (si pas déjà via packages cidata) :

```bash
ssh lbg@192.168.0.143 'sudo pacman -S --noconfirm qemu-guest-agent && sudo systemctl enable --now qemu-guest-agent'
```

3. **IP fixe** `192.168.0.143/24` (gw/dns `.254`) via NetworkManager, ou réservation DHCP sur la MAC ci-dessus.

4. Smoke :

```bash
ping -c2 192.168.0.143
ssh lbg@192.168.0.143 'hostname; uname -r'
ssh root@192.168.0.200 'qm agent 143 network-get-interfaces'
```

## Agent desktop Linux (worker)

Même rôle que `C:\Agent_IA` sur `.10`, mais via `packages/cortex/linux_agent` :

| | |
|--|--|
| URL | `http://192.168.0.143:5005` |
| Cible Agir | `desktop_target=omarchy` · « sur omarchy » · IP `.143` |
| Deploy | `bash packages/cortex/infra/scripts/deploy_linux_agent_143.sh` |
| Token | `LBG_OMARCHY_LINUX_APPROVAL_TOKEN` dans `infra/secrets/omarchy-143.env.local` |
| Service | `systemctl --user status lbg-omarchy-agent` (user `lbg`, linger) |

```bash
curl -fsS http://192.168.0.143:5005/healthz
# dry-run
curl -fsS -X POST http://192.168.0.143:5005/invoke \
  -H 'Content-Type: application/json' \
  -d '{"actor_id":"t","text":"x","context":{"desktop_dry_run":true,"desktop_action":{"kind":"open_app","app":"chromium"}}}'
```

Sur le core (Pilot / orch) : `LBG_AGENT_OMARCHY_URL` + entrée `omarchy` dans `LBG_DESKTOP_TARGETS`.

## Éditeur sans Cursor (VS Code // `.10`)

Poste GUI dédié : même stack que Windows (Continue + Cline → Ollama `.110`/`.111`).

```bash
# Depuis WSL / LAN
bash packages/cortex/infra/scripts/install_editor_alt_omarchy_143.sh
# Sur Hyprland (.143) :
code ~/projects/LBG_Studios
```

Déjà en place si le script a tourné : `visual-studio-code-bin`, extensions Continue/Cline, configs `~/.continue` + `~/.cline`.  
Specs VM (4 vCPU / 8 Go) : éditeur local OK — **LLM reste sur 110/111**, pas sur 143.

### Autonomie (sans Cursor)

Même intention que Session 0 sur `.10` : Compagnon AGIR peut **diagnostiquer** et **réparer** le worker.

| Action | Texte Agir | Effet sur `.143` |
|--|--|--|
| `agent_session_status` | « vérifie la session sur omarchy » | Wayland / GUI ready / service user |
| `fix_session0` | « répare session 0 sur omarchy » | `systemctl --user restart lbg-omarchy-agent` + re-check GUI |
| `open_app` | « ouvre chromium sur omarchy » | Lance l’app avec env Wayland injecté |

Le service systemd démarre souvent **sans** `DISPLAY` ; le worker injecte `WAYLAND_DISPLAY` / `XDG_RUNTIME_DIR` à chaque `open_app` / `open_url` (Hyprland).
## Accès distant depuis `.10` (sans noVNC)

### Diagnostic (2026-09-16)

- Bureau local **OK** (grim 1920×1080 propre).
- **wayvnc** : capture Wayland/virtio → **écran gris** (buffers inutilisables) → **désactivé**.
- **Sunshine** : crash répété (ABRT/avahi/tray) → **désactivé**.

### RustDesk (recommandé maintenant)

| | |
|--|--|
| ID | `LBG_OMARCHY_RUSTDESK_ID` dans `infra/secrets/omarchy-143.env.local` |
| MDP | `LBG_OMARCHY_RUSTDESK_PASSWORD` |
| Client `.10` | [RustDesk](https://rustdesk.com/) Windows |
| Connexion | coller l’ID + MDP, ou IP directe `192.168.0.143` si proposé |

Service : `rustdesk.service` (system) + app session Hyprland (autostart).

Partage Wayland : picker auto `~/.local/bin/lbg-auto-share-picker` (sélectionne `Virtual-1` sans dialogue).  
Si un prompt « sélectionner l’écran » réapparaît : reconnecter après restart portals (déjà câblé).

```bash
ssh lbg@192.168.0.143 'systemctl is-active rustdesk; rustdesk --get-id'
```

### Anciens services

- wayvnc / Sunshine : laissés installés mais stoppés (capture/stream inutilisables sur ce virtio).
- noVNC Proxmox : à éviter pour le desktop Hyprland.## Accès console (Proxmox)

Le clavier **noVNC** déforme souvent les MDP (AZERTY) → échec SDDM alors que SSH marche.

**Autologin SDDM** activé pour `lbg` (`/etc/sddm.conf.d/autologin.conf`).  
Après reboot / restart `sddm`, la session Omarchy/Hyprland démarre toute seule.

Si besoin de login manuel : MDP dans `infra/secrets/omarchy-143.env.local` — préférer **SPICE** ou taper comme en **QWERTY**.

### Chromium / Cursor Agent

Sous virtio-gpu, Chromium crashait (`SIGTRAP`) avec ozone Wayland GPU.  
Flags VM dans `~/.config/chromium-flags.conf` : Wayland + SwiftShader, `--no-sandbox`, `--disable-gpu`.

Pour login **Cursor Agent** : sur l’écran « Press any key to log in… », appuyer une touche — Chromium doit s’ouvrir.  
Sinon depuis SSH : `agent login` (ou équivalent) une fois Chromium OK.

Notif Fcitx « Diagnostique Wayland » = cosmétique (keymap), ignorable.

## Accès

| Voie | URL / commande |
|------|----------------|
| Console Proxmox | https://192.168.0.200:8006/ → VM 143 (autologin) |
| SSH | `ssh lbg@192.168.0.143` |
| Secrets | `packages/cortex/infra/secrets/omarchy-143.env.local` |

## Garde-fous

- **Pas d’onboot** par défaut (`LBG_OMARCHY_ONBOOT=0`) — activer seulement si le lab doit survivre au reboot NUC.
- Thin pool NUC `local-lvm` : vérifier avant agrandissement (`pvesm status`).
- Ne pas enchâsser une Windows-VM Omarchy dans cette VM (perf / complexité).
- `.10` reste le poste GPU / humain.

## Voir aussi

- Script : [`../infra/scripts/create_omarchy_vm_proxmox.sh`](../infra/scripts/create_omarchy_vm_proxmox.sh)
- Hands CT : [`hands_ct_142.md`](hands_ct_142.md)
- Registre : [`../../docs/REGISTRE.md`](../../docs/REGISTRE.md)
- Manuel Omarchy unattended : https://omarchy.org/manual/unattended-installs/
