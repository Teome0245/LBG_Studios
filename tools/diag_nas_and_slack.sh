#!/usr/bin/env bash
# Outil canonique d'auto-diagnostic Infra LBG Studios (NAS, Stockage Proxmox, Canal Ops Slack, Surfaces LAN).
# Utilisable directement par l'humain ou exécuté par l'orchestrateur / Compagnon.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-/tmp/diag_infra_report.txt}"
exec > >(tee "$OUT") 2>&1

echo "========================================================"
echo " AUTO-DIAGNOSTIC INFRASTRUCTURE & ÉCOSYSTÈME LBG STUDIOS"
echo " Date : $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================================"

echo
echo "--- 1. DIAGNOSTIC DU NAS SYNOLOGY (.51 - DS1815+) ---"
NAS_IP="192.168.0.51"
NAS_MAC="00:11:32:40:be:2f"
NAS_REACHABLE=0

if ping -c 2 -W 2 "$NAS_IP" >/dev/null 2>&1; then
    echo "  [OK] Ping $NAS_IP réussi"
    NAS_REACHABLE=1
else
    echo "  [KO] Ping $NAS_IP : 100% perte de paquets"
fi

# Audit ARP local
ARP_ENTRY=$(ip neigh show | grep "$NAS_IP" || true)
if [[ -n "$ARP_ENTRY" ]]; then
    echo "  Cache ARP local : $ARP_ENTRY"
else
    echo "  Cache ARP local : Aucune entrée pour $NAS_IP"
fi

# Sondage des ports NAS
if [[ "$NAS_REACHABLE" -eq 1 ]]; then
    echo "  Vérification des ports services NAS :"
    for port in 80 445 2049 3260 5000 5001; do
        if nc -z -w 2 "$NAS_IP" "$port" 2>/dev/null; then
            echo "    - Port $port OUVERT"
        else
            echo "    - Port $port FERMÉ"
        fi
    done
else
    echo "  Ports services NAS : ignorés (hôte injoignable)"
fi

# Sondage présence L2 via Freebox API
if [[ -f "${ROOT}/packages/cortex/infra/secrets/freebox.env.local" ]] || [[ -f "${ROOT}/packages/cortex/infra/secrets/lbg.env" ]]; then
    echo "  Vérification présence physique sur Freebox OS (L2) :"
    FB_CHECK=$("${ROOT}/packages/cortex/.venv/bin/python" - <<'PY' 2>/dev/null || echo "FAIL_PY"
import os, sys
from pathlib import Path
root = Path("packages/cortex")
for f in ["infra/secrets/lbg.env", "infra/secrets/freebox.env.local"]:
    p = root / f
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")
sys.path.insert(0, "packages/cortex/agents/src")
try:
    import lbg_agents.freebox_client as fb
    res = fb.probe_freebox(include_lan=True)
    hosts = res.get("lan_hosts") or []
    found = False
    for h in hosts:
        l2 = h.get("l2ident", {}).get("id", "").lower()
        if "00:11:32:40:be:2f" in l2:
            found = True
            print(f"ACTIF | Nom: {h.get('primary_name')} | Joignable: {h.get('reachable')}")
            break
    if not found:
        print("ABSENT_L2 | Le NAS n'émet aucune trame Ethernet vers la Freebox.")
except Exception as e:
    print(f"ERR | {e}")
PY
)
    echo "    $FB_CHECK"
fi

echo
echo "--- 2. STOCKS PROXMOX & SESSIONS ISCSI (.200 & .201) ---"
for pve in 192.168.0.200 192.168.0.201; do
    echo "  Nœud Proxmox $pve :"
    if ssh -o BatchMode=yes -o ConnectTimeout=3 "root@$pve" 'true' 2>/dev/null; then
        ssh -o BatchMode=yes "root@$pve" '
            root_usage=$(df -h / | awk "NR==2 {print \$5}")
            echo "    - Espace disque racine (pve-root) : $root_usage utilisé"
            
            # Check LUN mount
            lun_mnt=$(findmnt -T /mnt/pve/nas-lun-backup 2>/dev/null | awk "NR==2 {print \$2}")
            if [[ "$lun_mnt" == *"pve-root"* ]]; then
                echo "    - [ALERTE CRITIQUE] /mnt/pve/nas-lun-backup retombe sur le root local ($lun_mnt) !"
            elif [[ -n "$lun_mnt" ]]; then
                echo "    - Montage nas-lun-backup : $lun_mnt (OK)"
            else
                echo "    - /mnt/pve/nas-lun-backup non monté"
            fi
            
            # Check iSCSI
            if command -v iscsiadm >/dev/null 2>&1; then
                sessions=$(iscsiadm -m session 2>&1 || true)
                if [[ "$sessions" == *"No active sessions"* ]]; then
                    echo "    - [ALERTE] Session iSCSI Synology : DÉCONNECTÉE"
                else
                    echo "    - Session iSCSI active : $(echo "$sessions" | head -n 1)"
                fi
            fi
        '
    else
        echo "    - SSH non disponible sur $pve (clé requise)"
    fi
done

echo
echo "--- 3. CANAL OPS SLACK & NOTIFICATIONS (.140) ---"
if ssh -o BatchMode=yes -o ConnectTimeout=3 lbg@192.168.0.140 'true' 2>/dev/null; then
    ssh -o BatchMode=yes lbg@192.168.0.140 '
        # Check env file
        has_webhook=$(sudo grep -c "LBG_SLACK_WEBHOOK_OPS" /etc/lbg-ia-mmo.env || true)
        has_token=$(sudo grep -c "LBG_SLACK_BOT_TOKEN" /etc/lbg-ia-mmo.env || true)
        
        if [[ "$has_webhook" -gt 0 && "$has_token" -gt 0 ]]; then
            echo "  [OK] Configuration Slack présente dans /etc/lbg-ia-mmo.env"
        else
            echo "  [KO] Variables Slack MANQUANTES dans /etc/lbg-ia-mmo.env !"
        fi
        
        # Check systemd services
        poll_status=$(systemctl is-active lbg-slack-hitl-poll.service 2>/dev/null || echo "inactive")
        notify_timer=$(systemctl is-active lbg-slack-notify.timer 2>/dev/null || echo "inactive")
        echo "  Service lbg-slack-hitl-poll  : $poll_status"
        echo "  Timer lbg-slack-notify        : $notify_timer"
        
        # Check probe via ops_notify
        set -a; source /etc/lbg-ia-mmo.env 2>/dev/null || true; set +a
        probe_slack=$(/opt/LBG_IA_MMO/.venv/bin/python -c "from lbg_agents.ops_notify import slack_configured; print(slack_configured())" 2>/dev/null || echo "False")
        if [[ "$probe_slack" == "True" ]]; then
            echo "  [OK] Module lbg_agents.ops_notify : Slack opérationnel"
        else
            echo "  [KO] Module lbg_agents.ops_notify : Slack désactivé"
        fi
    '
else
    echo "  SSH vers 192.168.0.140 injoignable"
fi

echo
echo "--- 4. SURFACES CANON LAN (SMOKE RAPIDE) ---"
bash "${ROOT}/tools/smoke_lan_surfaces.sh"

echo
echo "========================================================"
echo " SYNTHÈSE & RECOMMANDATIONS"
echo "========================================================"
if [[ "$NAS_REACHABLE" -eq 0 ]]; then
    echo "  ⚠️ NAS HORS LIGNE : Suspension impérative des jobs vzdump sur Proxmox (.200/.201)"
    echo "     pour éviter de saturer /dev/mapper/pve-root."
fi
echo "  Rapport généré dans : $OUT"
echo "========================================================"
