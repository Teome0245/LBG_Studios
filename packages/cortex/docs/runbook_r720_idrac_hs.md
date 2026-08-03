# Runbook — matériel R720 depuis l’OS (iDRAC HS)

**Hôte** : Proxmox `lbgr720` — `192.168.0.201` (Dell PowerEdge R720, iDRAC 7)  
**Sonde** : `bash infra/scripts/diagnose_r720_hw_lan.sh`  
**Contexte** : l’iDRAC est soudée à la carte mère. Hors bande (KVM IP, réseau dédié, régulation ventilos) peut être morte tout en laissant l’OS et le PERC opérationnels.

## Symptômes typiques

| Signe | Interprétation |
|-------|----------------|
| Ventilos à 100 % en continu | Failsafe BMC (classique R720 iDRAC HS) |
| `ipmitool` → pas de `/dev/ipmi0` | Interface KCS morte ou BMC grillée |
| `dmesg` : `ipmi_si … Interface detection failed` | BMC ne répond plus sur le bus local |
| UI Proxmox / SSH OK | OS vivant — gestion in-band encore possible |
| CPU ~40–50 °C sous charge | Souvent cohérent avec ventilos max (pas de panique thermique) |

## Ce qui reste gérable depuis Proxmox (OS)

| Domaine | Outil | Indépendant iDRAC ? |
|---------|-------|---------------------|
| RAID / disques PERC H710 | `perccli` / `smartctl -d megaraid,N` | Oui |
| Températures CPU | `coretemp` / `sensors` | Oui (package) |
| Stockage LVM / VMs | `qm` / `lvs` / runbook storage | Oui |
| Capteurs chassis / PSU / fans | IPMI / OMSA / racadm | **Non** si BMC morte |
| Régulation ventilos | iDRAC uniquement | **Non** |
| Flash BIOS / Lifecycle / DUP majeurs | iDRAC / LC | Risqué / bloqué |

## Checklist diagnostic (ordre)

Prérequis : SSH root vers `192.168.0.201` (souvent via clé depuis `lbg@140`).

```bash
# Depuis packages/cortex (ou avec LBG_PROXMOX_SSH_HOST)
bash infra/scripts/diagnose_r720_hw_lan.sh
bash infra/scripts/diagnose_r720_hw_lan.sh --json
```

### 1. Identité machine

```bash
ssh root@192.168.0.201 'dmidecode -s system-product-name; dmidecode -s system-serial-number; pveversion; uptime'
```

Attendu LBG : `PowerEdge R720`, série `JDLFS12`.

### 2. BMC / IPMI local (KCS)

```bash
ssh root@192.168.0.201 'ls -la /dev/ipmi* 2>/dev/null; lsmod | grep ipmi; ipmitool -I open mc info; dmesg | grep -i ipmi | tail -20'
```

| Résultat | Verdict |
|----------|---------|
| `/dev/ipmi0` + `mc info` OK | BMC vivante côté bus local (iDRAC réseau peut quand même être HS) |
| `Interface detection failed` + pas de `/dev/ipmi*` | **BMC HS** (cas actuel 201) |
| Timeout `ipmitool` | Idem ou bus instable |

Reset soft (maintenance, **coupure VMs** à planifier) :

1. Arrêter proprement les VM critiques (`qm shutdown` / `pct shutdown`).
2. Couper les **deux** cordons PSU du R720.
3. Maintenir le bouton power façade **30 s**.
4. Rebrancher, boot, rejouer la sonde.

Si KCS reste en échec → panne matérielle (carte mère / puce iDRAC), pas un simple plantage firmware.

### 3. Stockage PERC H710

Le H710 est indépendant de l’iDRAC. Sur 201 : `lspci` → `MegaRAID SAS 2208`, VD exposé en `/dev/sda` (modèle `PERC H710`).

**Sans perccli** (déjà utilisable) :

```bash
ssh root@192.168.0.201 'bash -s' <<'EOF'
for i in 0 1 2 3 4 5 6 7; do
  smartctl -i -H -A -d megaraid,$i /dev/sda 2>/dev/null \
    | grep -E 'megaraid|Device Model|Serial|SMART overall|Reallocated_Sector|Airflow_Temperature|Temperature' \
    && echo "---"
done
EOF
```

**Avec perccli** (recommandé pour rebuild / VD) :

```bash
# Installer PercCLI Broadcom/LSI (paquet Dell/Broadcom) puis :
perccli /c0 show
perccli /c0/eall/sall show
perccli /c0/eall/sall show status
```

### 4. Thermique CPU (seul levier fiable sans BMC)

```bash
ssh root@192.168.0.201 'for h in /sys/class/hwmon/hwmon*/; do
  echo "== $(cat "$h/name") =="
  for t in "$h"/temp*_input; do
    [ -f "$t" ] || continue
    lab=$(cat "${t%_input}_label" 2>/dev/null || basename "$t")
    echo "$lab: $(($(cat "$t")/1000)) C"
  done
done'
```

Seuils ops (indicatif) : Package **&lt; 70 °C** OK sous charge ; **&gt; 85 °C** → réduire charge (Ollama / VMs) et vérifier flux d’air physique.

### 5. OMSA / racadm (optionnel)

OMSA (`omreport`) et `racadm` s’appuient souvent sur l’iDRAC. Si BMC morte : installer n’apporte rien pour fans/PSU ; le PERC reste le canal utile.

## Contraintes majeures (ne pas oublier)

1. **Ventilos 100 %** : normal et **non corrigeable depuis l’OS** tant que l’iDRAC est HS.
2. **Pas de KVM IP** : console = Proxmox UI / SSH / écran local.
3. **Firmware** : éviter les DUP BIOS/LC tant que BMC morte ; risque de brick soft.
4. **Remplacement** : iDRAC 7 non remplaçable seule → carte mère (ou serveur de secours).

## Incident 201 — snapshot 2026-08-03

| Check | Résultat |
|-------|----------|
| SSH / UI | OK — `pve-manager/9.2.2`, uptime ~55 min au moment du diagnostic |
| DMI | PowerEdge R720, SN `JDLFS12`, BIOS `2.2.3` |
| IPMI KCS | **HS** — `ipmi_si … Interface detection failed`, pas de `/dev/ipmi*` |
| PERC H710 | OK — driver `megaraid_sas`, VD `/dev/sda` ~930 Go (`vg_data`) |
| Disques physiques (smartctl megaraid) | 6× Samsung 870 EVO 250 Go, health **PASSED**, ~30 °C |
| Attention SMART | `megaraid,3` : **95** secteurs réalloués ; `megaraid,4` : **82** — surveiller, planifier rempla |
| OS boot | SSD Crucial `sdb` CT500BX100 — SMART PASSED |
| Backup | iSCSI Synology `sdc` — health OK |
| CPU package | ~43–45 °C sous load ~16 (Ollama 110 + VMs 140/245/246) |
| perccli / OMSA / racadm | **Absents** sur l’hôte |

**Verdict** : hyperviseur **exploitable** ; supervision chassis/fans/PSU **perdue** ; priorité ops = installer **perccli**, surveiller SMART (surtout PD 3 et 4), planifier **carte mère / R720 de secours** si ventilos max / bruit / conso deviennent un problème.

## Liens

- [`runbook_proxmox_storage_prime.md`](runbook_proxmox_storage_prime.md) — pool thin / io-error VM 246
- [`runbook_ops_bots_watchdog.md`](runbook_ops_bots_watchdog.md) — watchdogs infra
- [`architecture_equipe_virtuelle_studio.md`](architecture_equipe_virtuelle_studio.md) — topologie 201
