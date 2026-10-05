"""Plans de remédiation guest — disque / load du mur INFRA LAN (suggestions, pas d'auto-exec)."""

from __future__ import annotations

from typing import Any


def build_guest_remediation_plan(guest_payload: dict[str, Any] | None) -> dict[str, Any]:
    """Construit un remediation_plan à partir de la sonde guest mur."""
    if not isinstance(guest_payload, dict):
        return {
            "kind": "remediation_plan",
            "source": "guest_metrics",
            "outcome": "ok",
            "hints": ["Sonde guest absente — rien à remédier."],
            "suggested_actions": [],
        }

    outcome = str(guest_payload.get("outcome") or "ok")
    stressed = guest_payload.get("stressed") if isinstance(guest_payload.get("stressed"), list) else []
    if not stressed:
        stressed = [
            h
            for h in (guest_payload.get("hosts") or [])
            if isinstance(h, dict)
            and (str(h.get("outcome") or "") in {"warn", "critical"} or not h.get("ok"))
        ]

    if outcome == "ok" and not stressed:
        return {
            "kind": "remediation_plan",
            "source": "guest_metrics",
            "outcome": "ok",
            "hints": ["Mur INFRA LAN OK (disk/load sous seuils)."],
            "suggested_actions": [],
        }

    hints: list[str] = []
    actions: list[dict[str, Any]] = []

    for row in stressed:
        if not isinstance(row, dict):
            continue
        hid = str(row.get("id") or "")
        label = str(row.get("label") or hid)
        host = str(row.get("host") or "")
        disk = row.get("disk_percent")
        load1 = row.get("load1")
        nproc = row.get("nproc")
        oc = str(row.get("outcome") or "warn")

        if not row.get("ok"):
            hints.append(f"{label} ({host}) : sonde inaccessible — vérifier SSH lbg@{host}")
            actions.append(
                {
                    "level": "manual",
                    "label": f"{label} : reconnect SSH / clé lbg@140 → lbg@{host}",
                    "command_hint": f"ssh -o BatchMode=yes lbg@{host} 'hostname && df -h / && uptime'",
                }
            )
            continue

        parts = []
        if isinstance(disk, (int, float)):
            parts.append(f"disk {disk:.0f}%")
        if isinstance(load1, (int, float)):
            parts.append(f"load {load1:.2f}/{nproc or '?'}")
        hints.append(f"{label} ({host}) [{oc}] : {', '.join(parts) or 'alerte'}")

        # Disque
        if isinstance(disk, (int, float)) and disk >= 70:
            if hid in {"web", "front", "front_web", "100"}:
                actions.append(
                    {
                        "level": "manual",
                        "label": f"{label} : inventaire disque (Docker / logs / OWUI)",
                        "command_hint": (
                            f"ssh lbg@{host} "
                            "'df -h /; sudo du -xh /var/lib/docker 2>/dev/null | tail -5; "
                            "sudo journalctl --disk-usage; docker system df 2>/dev/null | head -20'"
                        ),
                    }
                )
                actions.append(
                    {
                        "level": "manual",
                        "label": f"{label} : prune images Docker inutilisées (après revue)",
                        "command_hint": f"ssh lbg@{host} 'docker image prune -f && docker system df'",
                    }
                )
            elif hid in {"prime", "mmo", "246"}:
                actions.append(
                    {
                        "level": "safe",
                        "label": "Prime 246 : purge zArchive Core3 (logs rotatés ~dizaines de Go)",
                        "devops_action": {
                            "kind": "ssh_run",
                            "server_id": "prime",
                            "command": (
                                "Z=/opt/lbg-new-mmo-clean/MMOCoreORB/bin/log/zArchive; "
                                "df -h /; du -sh \"$Z\" 2>/dev/null; "
                                # Rotations cassées type .log.1.1.1… — tout *.log.* (pas les *.log courants)
                                "find \"$Z\" -type f -name '*.log.*' -delete 2>/dev/null; "
                                "find \"$Z\" -type f -name '*.gz' -delete 2>/dev/null; "
                                "du -sh \"$Z\" 2>/dev/null; df -h /"
                            ),
                        },
                        "requires_approval": True,
                    }
                )
                actions.append(
                    {
                        "level": "safe",
                        "label": "Prime 246 : hygiène build Antigravity (approbation SSH)",
                        "devops_action": {
                            "kind": "ssh_run",
                            "server_id": "prime",
                            "command": (
                                "rm -rf /opt/lbg-antigravity/lbg-mmo/build "
                                "&& :> /tmp/core3-antigravity-build.log && df -h /"
                            ),
                        },
                        "requires_approval": True,
                    }
                )
                actions.append(
                    {
                        "level": "manual",
                        "label": "Prime : script hygiene documenté (zArchive + build)",
                        "command_hint": "bash infra/scripts/prime_disk_hygiene_vm.sh",
                    }
                )
                actions.append(
                    {
                        "level": "manual",
                        "label": "Prime : vérifier logrotate zArchive (fichiers *.log.1 hors motif *.log)",
                        "command_hint": (
                            f"ssh lbg@{host} "
                            "'cat /etc/logrotate.d/lbg-core3-prime; "
                            "ls /opt/lbg-new-mmo-clean/MMOCoreORB/bin/log/zArchive | head'"
                        ),
                    }
                )
            elif hid in {"core", "140"}:
                actions.append(
                    {
                        "level": "manual",
                        "label": f"{label} : journal + caches Python / venv",
                        "command_hint": (
                            f"ssh lbg@{host} "
                            "'df -h /; sudo journalctl --disk-usage; "
                            "du -xh /opt/LBG_IA_MMO 2>/dev/null | sort -h | tail -15'"
                        ),
                    }
                )
            elif hid in {"precu", "245", "core3"}:
                actions.append(
                    {
                        "level": "manual",
                        "label": f"{label} : inventaire disque Core3 / logs",
                        "command_hint": (
                            f"ssh lbg@{host} "
                            "'df -h /; sudo du -xh /opt /var/log 2>/dev/null | sort -h | tail -20'"
                        ),
                    }
                )
            else:
                actions.append(
                    {
                        "level": "manual",
                        "label": f"{label} : df + gros répertoires",
                        "command_hint": f"ssh lbg@{host} 'df -h /; sudo du -xh / --max-depth=2 2>/dev/null | sort -h | tail -20'",
                    }
                )

        # Load
        if isinstance(load1, (int, float)) and isinstance(nproc, int) and nproc > 0:
            ratio = load1 / float(nproc)
            if ratio >= 1.0:
                actions.append(
                    {
                        "level": "manual",
                        "label": f"{label} : top CPU (load {load1:.2f})",
                        "command_hint": (
                            f"ssh lbg@{host} "
                            "'uptime; ps aux --sort=-%cpu | head -15; "
                            "systemctl list-units --failed --no-pager'"
                        ),
                    }
                )

    hints.append("Doc : docs/runbook_ops_bots_watchdog.md § guest mur INFRA LAN")

    return {
        "kind": "remediation_plan",
        "source": "guest_metrics",
        "outcome": outcome,
        "hints": hints,
        "suggested_actions": actions,
        "next_steps": [
            "Créer / relancer tâche ops Héphaïstos si pas déjà spawnée.",
            "Approuver les actions SSH allowlistées proposées (Prime hygiene).",
            "Surveiller le mur Cockpit P03 (disk orange → vert).",
        ],
    }


def format_guest_plan_reply(plan: dict[str, Any]) -> str:
    lines = [
        "Plan remédiation guest mur INFRA LAN",
        f"État : {plan.get('outcome')}",
    ]
    for h in plan.get("hints") or []:
        lines.append(f"  → {h}")
    for i, a in enumerate(plan.get("suggested_actions") or [], 1):
        if isinstance(a, dict):
            lines.append(f"  {i}. [{a.get('level')}] {a.get('label')}")
    return "\n".join(lines)
