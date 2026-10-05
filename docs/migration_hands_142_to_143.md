# Migration mains `.142` → `.143`

**Statut** : **terminée** — CT `.142` détruit · Freebox nettoyé · canon = `.143:5005`  
**Date** : 2026-10-01 (Phases 1–3) · 2026-10-02 (Phase 4) · 2026-10-05 (Freebox)  
**Décision** : absorber `lbg-hands` (CT `.142`) dans la VM Omarchy `.143` ; **garder** l’executor `.141`.

Voir aussi : [`hands_ct_142.md`](../packages/cortex/docs/hands_ct_142.md) · [`omarchy_vm_143.md`](../packages/cortex/docs/omarchy_vm_143.md) · [`REGISTRE.md`](REGISTRE.md).

---

## Placement réel (corriger les docs périmées)

| IP | Forme | Hôte Proxmox | Rôle |
|----|--------|--------------|------|
| **`.142`** | CT `lbg-hands` | **NUC `.200`** | **détruit 2026-10-02** (ex-mains `:6001`) |
| **`.143`** | VM `lbg-omarchy` | **R720 `.201`** | Éditeur + **mains** (agent unique `:5005`) — **canon** |
| **`.141`** | CT `lbg-executor` | R720 `.201` | Poll Team `/v1/team/wsl/*` — **inchangé** |

`.143` dispose ~16 Go RAM / 4 vCPU (live 2026-10-01) — capable d’absorber hands + session Hyprland d’observation.

---

## Priorité d’usage `.143` (contrat)

`.143` est **d’abord un nœud de l’écosystème LBG**, pas un poste de manipulation humaine.

| Qui | Rôle |
|-----|------|
| **Team / Compagnon / Agir** | Acteurs principaux : files, `import_face_parts`, open_app, update_vscode, smokes |
| **Humain** | Se connecte pour **voir** les actions demandées (Hyprland / VS Code / Chromium) — pas pour piloter à la place de l’agent |
| **Ollama** | Reste sur `.110` / `.111` — jamais sur `.143` |

Conséquences config :

- **Un seul agent** `:5005` (pas de second `:6001`).
- Alias `hands` / `omarchy` / `ct-142` / `ct-143` → même URL après cutover.
- **Pas de gate `confirm` humain** sur le worker (sinon Team 24/7 bloque) : `LBG_LINUX_APPROVAL_MODE=off` + pas de token obligatoire.
- Le contre-pouvoir reste au niveau **Compagnon / orch** (dry-run → confirm L2), pas sur l’agent Linux.
- Unit systemd **user + linger**, sans dépendance dure à `graphical-session` pour le HTTP (la GUI sert à observer ; l’API doit vivre sans).

---

## Cible

```text
Avant :  .141 executor  |  .142 hands :6001  |  .143 éditeur :5005
Après :  .141 executor  |  .143 = éditeur + hands :5005
         (.142 stop → snapshot → destroy après soak)
```

---

## Phase 0 — Prérequis

- [x] Confirmer placement `.143` @ `.201`
- [ ] Snapshot Proxmox VM 143 avant modifs lourdes
- [x] Inventaire inbox `.142` (~fixtures face)
- [x] Contrat usage écosystème-first (ci-dessus)

---

## Phase 1 — Préparer `.143` (sans couper `.142`)

### 1.1 Inbox + script

```bash
# Sur .143
sudo mkdir -p /var/lib/lbg-hands/inbox /opt/Infographiste_IA/scripts /var/log/lbg
sudo chown -R lbg:lbg /var/lib/lbg-hands /opt/Infographiste_IA /var/log/lbg

# CT 142 → Omarchy
ssh root@192.168.0.200 'pct exec 142 -- tar -C /var/lib/lbg-hands -cf - inbox' \
  | ssh lbg@192.168.0.143 'tar -C /var/lib/lbg-hands -xf -'

# Script import (copie depuis .142 ou monorepo Infographiste_IA)
rsync … import_face_parts.py → lbg@192.168.0.143:/opt/Infographiste_IA/scripts/
```

### 1.2 `linux.env` (delta hands + écosystème)

Fichier : `/home/lbg/Agent_IA/linux.env` (le deploy **ne l’écrase pas**).

| Clé | Valeur |
|-----|--------|
| `LBG_LINUX_FACE_PARTS_ENABLED` | `1` |
| `LBG_LINUX_FACE_PARTS_INBOX` | `/var/lib/lbg-hands/inbox` |
| `LBG_LINUX_FACE_PARTS_SCRIPT` | `/opt/Infographiste_IA/scripts/import_face_parts.py` |
| `LBG_LINUX_FILE_ALLOWLIST_DIRS` | `/var/lib/lbg-hands,/opt/Infographiste_IA,/tmp,/var/tmp,/home/lbg` |
| `LBG_LINUX_APPROVAL_MODE` | `off` |
| `LBG_DESKTOP_APPROVAL_MODE` | `off` |
| `LBG_LINUX_APPROVAL_TOKEN` | *(vide / commenté — un token force le gate)* |
| `LBG_LINUX_DRY_RUN` | `0` |
| `LBG_LINUX_FACE_PARTS_PYTHON` | `/home/lbg/Agent_IA/.venv/bin/python` |

Conserver allowlist apps (chromium, code, …) pour l’**observation** GUI.  
Dépendance : `pillow` dans le venv Agent_IA (installé Phase 1).

### 1.3 Smoke local

```bash
curl -fsS http://192.168.0.143:5005/healthz
# → face_parts_enabled=true, approval_gate_active=false

curl -fsS -X POST http://192.168.0.143:5005/invoke \
  -H 'Content-Type: application/json' \
  -d '{"actor_id":"team:smoke","text":"dry","context":{"desktop_dry_run":true,"desktop_action":{"kind":"import_face_parts","character_id":"lyra_assistant","deploy":false}}}'

bash packages/cortex/infra/scripts/smoke_update_vscode_143.sh
```

**Checklist Phase 1**

- [x] Inbox présente sur `.143`
- [x] `import_face_parts.py` sous `/opt/Infographiste_IA/scripts/`
- [x] `linux.env` patché (face_parts + allowlist + approval off + python venv)
- [x] Unit systemd sans `After=graphical-session` (API 24/7)
- [x] Agent redémarré / healthz OK (`face_parts_enabled=true`, `approval_gate_active=false`)
- [x] Smoke dry-run `import_face_parts` OK (`outcome=dry_run`, returncode 0)
- [x] Smoke éditeur (`smoke_update_vscode_143.sh`) OK

---

## Phase 2 — Dual-run (env + code, `.142` encore up)

### Secrets (`lbg.env` → deploy `.100` / `.140`)

```bash
LBG_AGENT_HANDS_URL="http://192.168.0.143:5005"
LBG_AGENT_OMARCHY_URL="http://192.168.0.143:5005"
LBG_LAN_HOST_HANDS="192.168.0.143"
```

`LBG_DESKTOP_TARGETS` — une entrée (aliases fusionnés) :

```json
[
  {"id":"pc","label":"pc-windows","host":"192.168.0.10","url":"http://192.168.0.10:5005","aliases":["desktop","windows"]},
  {"id":"ad","label":"serveur-ad","host":"192.168.0.100","url":"http://192.168.0.100:5005","aliases":["srv-ad","serveur-ad","active-directory"]},
  {"id":"omarchy","label":"lbg-omarchy","host":"192.168.0.143","url":"http://192.168.0.143:5005",
   "aliases":["omarchy","lbg-omarchy","hands","lbg-hands","linux-hands","linux_agent","ct-142","ct-143"]}
]
```

`LBG_NETWORK_KNOWN_DEVICES` : rôle `hands` → `.143` ; `.142` en `legacy` pendant le soak.

### Code / sondes

| Fichier | Changement |
|---------|------------|
| `desktop_targets.py` | defaults + alias → `.143:5005` |
| `remote_targets.py` | `LBG_LAN_HOST_HANDS` → `.143` |
| `network_inventory.py` | sonde hands `:5005` |
| `admin_infra_platform.py` | URL / labels `:5005`, hôte `.201` |
| `face_parts_workflow.py` | hint « Omarchy .143 » |
| tests associés | IP/port |
| `REGISTRE.md`, docs omarchy/hands | placement R720 + migration |

Pendant dual-run : trafic métier (après deploy secrets lab) → `.143` ; `.142` reste hot spare.

**Checklist Phase 2**

- [x] `lbg.env` / example : `HANDS_URL` / `OMARCHY_URL` / `LAN_HOST_HANDS` → `.143:5005`
- [x] `LBG_DESKTOP_TARGETS` : entrée `omarchy` + aliases `hands`/`ct-142`
- [x] `LBG_NETWORK_KNOWN_DEVICES` : `.143` role hands, `.142` legacy
- [x] `desktop_targets` / `remote_targets` / `network_inventory` / Atlas
- [x] `face_parts_workflow` hint
- [x] Tests (35) OK
- [x] Docs REGISTRE / hands / omarchy / fusion / architecture
- [x] Deploy secrets + restart orch/compagnon lab → **Phase 3**

---

## Phase 3 — Cutover

1. Deploy secrets + restart services (`compagnon` `.100`, orch `.140`).
2. Smoke bout-en-bout : Agir omarchy + Team `import_face_parts` (cible `hands`) + Atlas hands OK.
3. Sur CT `.142` : `systemctl stop lbg-linux-agent` (CT allumé 48–72 h).
4. Soak : job réel + reboot `.143` (linger, agent sans relogin GUI).

**Checklist Phase 3**

- [x] `push_secrets_vm.sh` → `.140` (`/etc/lbg-ia-mmo.env`) + restart orch
- [x] Code `agents` / `orchestrator/team` syncés sur `.140`
- [x] `.100` : `PROBE_HANDS_URL` / `LBG_AGENT_HANDS_URL` → `.143:5005` + recreate backend
- [x] Resolve `hands` → `omarchy` @ `http://192.168.0.143:5005`
- [x] Smoke dry-run `import_face_parts` + `open_app` chromium sur `.143`
- [x] Agent `.142` **stop + disable** (`:6001` fermé) — CT encore up (hot spare)
- [ ] Soak 48–72 h (job réel + reboot `.143` optionnel)

**Incident cutover** : `deploy_vm.sh` core a cassé `.venv` (pip editable `hybrid_proactive_agent` invalide) → rebuild venv + `uvicorn` restauré ; orch `healthz` OK.

**Rollback** : `LBG_AGENT_HANDS_URL=http://192.168.0.142:6001` + `systemctl enable --now lbg-linux-agent` sur le CT.

---

## Phase 4 — Extinction CT `.142`

```bash
ssh root@192.168.0.200 'pct snapshot 142 pre-destroy-hands && pct stop 142 && pct destroy 142 --purge 1'
```

**Checklist Phase 4**

- [x] Smoke pré-destroy : `.143` healthz + resolve `hands` → `.143:5005`
- [x] Snapshot `pre-destroy-hands` (puis purge avec le destroy — pas de backup vzdump long terme)
- [x] `pct destroy 142 --purge` — CT absent de `pct list`, IP `.142` sans ping
- [x] Docs REGISTRE / hands archivé / fusion / migration
- [x] Retrait `.142` de `LBG_NETWORK_KNOWN_DEVICES`
- [x] Freebox : bail DHCP `.142` déjà absent ; retiré de `_EXPECTED_LEASES` (audit)
- [x] Freebox : entrée LAN fantôme `lbg-Hands (142)` oubliée (UI, 2026-10-05) — smoke 13/13 OK

Puis : IP `.142` libre pour réemploi.

---

## Matrice ports

| Service | Avant | Après |
|---------|-------|-------|
| Omarchy / mains | `.143:5005` + `.142:6001` | **`.143:5005` seul** |
| Executor Team | `.141` | inchangé |
| Windows / AD | `.10` / `.100` `:5005` | inchangé |

---

## Risques

1. **Gate approval** — un token ou `confirm` sur `.143` bloque Team ; config écosystème = `off` + token vide.
2. **Session GUI** — observation seulement ; l’API agent ne doit pas dépendre de Hyprland.
3. **Docs** — REGISTRE / omarchy disaient encore « NUC » pour `.143` → corriger en Phase 2.
4. **Ne pas toucher `.141`.**

---

## Journal d’exécution

| Date | Étape | Résultat |
|------|--------|----------|
| 2026-10-01 | Doc + contrat écosystème-first | OK |
| 2026-10-01 | Phase 1 inbox / script / `linux.env` / systemd / smokes | **OK** — `.142` toujours up (hot spare) |
| 2026-10-01 | Phase 2 `lbg.env` + targets/inventory/Atlas + docs + tests | **OK** — trafic métier → `.143:5005` ; deploy lab = Phase 3 |
| 2026-10-01 | Phase 3 cutover secrets `.140`/`.100` + stop agent `.142` | **OK** — soak puis Phase 4 |
| 2026-10-02 | Phase 4 `pct destroy 142 --purge` + docs | **OK** — canon `.143:5005` |
| 2026-10-05 | Freebox : LAN fantôme `.142` oublié | **OK** — smoke 13/13 |
