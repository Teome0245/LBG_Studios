# Mains Team — CT `.142` (`lbg-hands`)

**Statut** : **créé** (LXC Ubuntu 24.04 sur NUC `.200`, `local-lvm`, 4 Go / 20 Go) — `linux_agent` `:6001`  
**Date** : 2026-08-18

## Ce qu’on ne fait pas

| IP | Pourquoi pas |
|----|----------------|
| **`.200`** | Hyperviseur **Proxmox NUC** (peu chargé, OK comme *hôte*). **Pas** d’IP de service : on n’installe pas linux_agent / Chrome sur l’hyperviseur. |
| **`.150`** | Libre en apparence, trop loin du bloc 140–141 ; on réserve 150+ pour autre chose. |
| **NAS `.51`** comme runtime | `N:` = raccourci SMB vers **Synology `192.168.0.51`**, pas OneDrive. Le NAS **tombe ~6 mois** puis revient ~6 mois → jamais source de vérité ni dépendance d’un job Team. |

## Placement

| | Choix |
|--|--------|
| Hyperviseur | **`.200` (NUC)** — décharge le R720 `.201` (déjà 110 / 140 / 141 / 246) |
| IP invité | **`192.168.0.142`** (CTID 142, à côté de 141) |
| GPU | **Non** |
| Forme | **QEMU (VM)** plutôt qu’un LXC clone de 141 si on veut un **vrai Chromium**. LXC 141 est parfait pour `curl`/`ssh` ; Chromium en unprivileged LXC est fragile (namespaces, sandbox). Alternative : LXC 142 *sans* navigateur, seulement `linux_agent` + Python/PIL. |

## Rôles : 141 vs 142 vs poste `.10`

```
Team .140
  ├─ .141  lbg-executor     pull  /v1/team/wsl/*   (smokes, diag, déjà en place)
  ├─ .142  lbg-hands        push  linux_agent:6001 (fichiers, import_face_parts, Chrome)
  └─ .10   poste Teome      GPU + Comfy + Gemini web *humain* (session Google à toi)
```

| Hôte | Fait | Ne fait pas |
|------|------|-------------|
| **`.141`** | Poll smokes / diag LAN (comme l’ancien WSL) | Pas de navigateur, pas de N: |
| **`.142`** | **Mains** 24/7 : `linux_agent`, import chroma, rsync Pilot/Orch, Chromium/Playwright **si** QEMU | Pas de Comfy, pas de LoRA, pas de secrets Google sur disque sans coffre |
| **`.10`** | GPU, Comfy, génération Gemini *connectée à ton compte* | Pas H24 si le PC dort |
| **NAS `.51`** | Archive / inspiration *quand il est up* | Jamais le seul inbox ; cache local sur le disque de 142 |

## Plus qu’un navigateur ?

**Oui, dès le jour 1** — le navigateur est optionnel.

| Brique | Pourquoi |
|--------|----------|
| `linux_agent` `:6001` | Team / Cursor → `import_face_parts`, `open_url`, fichiers allowlistés |
| Python + Pillow | Chroma → sheets (script déjà là) |
| Disque local 16–32 Go | Inbox + cache ; survive à la panne NAS |
| `curl` / `rsync` / SSH | Deploy `:5174` / Pilot sans passer par `.10` |
| Chromium + Playwright | **Seulement** si on veut Gemini/Leonardo *sans* le PC allumé (compte **dédié**, pas ta session perso) |

Sans GPU, 142 **ne remplace pas** Comfy ni le LoRA. Il remplace « moi qui lance le script à la main ».

## NAS `.51`

- Windows `N:` → share Synology (Cloud Drive / Photos / Inspiration).
- Montage optionnel sur 142 : CIFS `//192.168.0.51/...` **si ping OK**, sinon skip.
- Jobs `import_face_parts` : lire **d’abord** `/var/lib/lbg-hands/inbox` (copie locale). Sync NAS → inbox = best-effort, jamais bloquant.
- Ne pas y mettre Git, secrets, ni les sheets prod (déjà sur `.100` / Pilot).

## Spec minimale (création)

```
Hôte Proxmox : 192.168.0.200
CTID / IP    : 142 / 192.168.0.142
Hostname     : lbg-hands
RAM          : 4096 Mo si Chrome, sinon 2048 (agent seul)
Disque       : 20 Go
OS           : Ubuntu 24.04
User         : lbg
```

Créé le 2026-08-18 (CTID 142, hostname `lbg-hands`). Chrome/Playwright **plus tard**.

Câblage Team :

1. `linux_agent` systemd `:6001` (`lbg-linux-agent.service`)
2. Cible `hands` → `http://192.168.0.142:6001` (`LBG_AGENT_HANDS_URL` + entrée dans `LBG_DESKTOP_TARGETS`)
3. Inbox local `/var/lib/lbg-hands/inbox` + `import_face_parts`
4. Playwright **plus tard** (compte Gemini dédié)

Surveillance Team (Atlas `admin_infra` + `network_inventory`) : hôte **142** dans le périmètre obligatoire, sonde SSH `:22` + `GET :6001/healthz`. Alertes Element si KO, comme 141.

## Pour Cursor / moi

Même worker HTTP que la Team. Depuis WSL : `POST http://192.168.0.142:6001/invoke` (dry-run / approval). Pas besoin que le PC `.10` soit réveillé **sauf** GPU/Comfy et ta session Gemini perso.
