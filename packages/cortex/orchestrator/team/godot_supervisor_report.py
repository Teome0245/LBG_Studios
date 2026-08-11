"""Rapport diagnostic superviseur Godot (Argus) — human_summary + actions."""

from __future__ import annotations

import os
from typing import Any

from team.human_summary import format_probe_lines, format_validation_summary


def blocking_tracks() -> frozenset[str]:
    raw = os.environ.get(
        "LBG_TEAM_GODOT_SUPERVISOR_BLOCKING",
        "sidecar_m1,godot_mirror_m1,lbg_ws2_readiness",
    ).strip()
    if not raw or raw.lower() in ("all", "*"):
        return frozenset()
    return frozenset(t.strip() for t in raw.split(",") if t.strip())


def _is_blocking(track_name: str) -> bool:
    configured = blocking_tracks()
    if not configured:
        return True
    return track_name in configured


def _sidecar_line(track: dict[str, Any]) -> str:
    if track.get("skipped"):
        return "⏭ [sidecar_m1] ignoré"
    ok = bool(track.get("ok"))
    icon = "✅" if ok else "❌"
    base = track.get("sidecar") or os.environ.get("LBG_CORE3_SIDECAR_URL", "http://192.168.0.246:8791")
    line = f"{icon} [sidecar_m1] {base}/healthz"
    if ok:
        line += f" — {track.get('online_count', 0)} bot(s) online"
        return line
    checks = track.get("checks") if isinstance(track.get("checks"), list) else []
    for c in checks:
        if not isinstance(c, dict) or c.get("ok"):
            continue
        if c.get("kind") == "sidecar_healthz":
            err = c.get("error") or f"HTTP {c.get('status')}"
            line += f" — healthz KO ({err})"
            break
        if c.get("kind") == "player_snapshot" and c.get("required"):
            player = c.get("player") or "?"
            line += f" — bot {player} offline"
            break
    else:
        line += " — sidecar injoignable ou bots requis offline (lia,nix)"
    return line


def _mirror_line(track: dict[str, Any]) -> str:
    if track.get("skipped"):
        return "⏭ [godot_mirror_m1] ignoré"
    ok = bool(track.get("ok"))
    icon = "✅" if ok else "❌"
    ents = track.get("entities", 0)
    line = f"{icon} [godot_mirror_m1] snapshots online={ents}"
    if ok:
        return line
    if track.get("error"):
        line += f" — {track['error']}"
    elif ents == 0:
        bots = track.get("required_bots") or ["lia", "nix"]
        line += f" — aucun snapshot (bots requis: {', '.join(bots)})"
    errors = track.get("errors") if isinstance(track.get("errors"), list) else []
    if errors:
        line += f" — {errors[0]}"
    return line


def format_track_lines(tracks: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for t in tracks:
        if not isinstance(t, dict):
            continue
        name = str(t.get("track") or "")
        if name == "sidecar_m1":
            lines.append(_sidecar_line(t))
        elif name == "godot_mirror_m1":
            lines.append(_mirror_line(t))
        else:
            lines.extend(format_probe_lines([t]))
    return lines


def remediation_commands(failed_blocking: list[str]) -> list[str]:
    cmds: list[str] = []
    if any(t in failed_blocking for t in ("sidecar_m1", "godot_mirror_m1")):
        cmds.append("bash infra/scripts/smoke_godot_sidecar_mirror_lan.sh")
        cmds.append("bash infra/scripts/ensure_ia_bots_online_vm.sh  # Prime 246")
    if "lbg_ws2_readiness" in failed_blocking:
        cmds.append("bash infra/scripts/run_lbg_gateway_vm.sh  # sync gateway + lbg-ws/2 sur 246")
        cmds.append(
            'cd packages/cortex/orchestrator && PYTHONPATH=. python -c "from team.lbg_ws2_audit import audit_lbg_ws2_readiness; import json; print(json.dumps(audit_lbg_ws2_readiness(), indent=2))"'
        )
    if "zb0_readiness" in failed_blocking:
        cmds.append("Preset #/team → Plan build ZB-0 (Vulcan dry-run)")
    return cmds[:6]


def build_supervisor_report(
    *,
    tracks: list[dict[str, Any]],
    sidecar_ok: bool,
    mode: str = "full",
) -> dict[str, Any]:
    """Construit human_summary, blockers et ok agrégé (blocking vs advisory)."""
    configured_blocking = blocking_tracks()
    required = [t for t in tracks if isinstance(t, dict) and not t.get("skipped")]
    blocking_failed: list[str] = []
    advisory_failed: list[str] = []

    for t in required:
        name = str(t.get("track") or "")
        if t.get("ok"):
            continue
        if _is_blocking(name):
            blocking_failed.append(name)
        else:
            advisory_failed.append(name)

    if configured_blocking:
        ok = len(blocking_failed) == 0
    else:
        ok = all(t.get("ok") for t in required)

    probe_lines = format_track_lines(tracks)
    checklist = [
        "Sidecar 246 : curl http://192.168.0.246:8791/healthz",
        "Bots IA Lia/Nix online (Core3 Prime)",
        "Gateway lbg-ws/2 : bash infra/scripts/run_lbg_gateway_vm.sh",
        "Godot : godot4 --path packages/prime-client (Launchpad J:)",
    ]
    if advisory_failed:
        checklist.append(f"Advisory (non bloquant) : {', '.join(advisory_failed)}")

    title = "Argus — superviseur Godot (sidecar 246 · miroir M1 · lbg-ws/2)"
    if not ok:
        title += " — action requise"

    human_summary = format_validation_summary(title=title, probes=[], checklist=checklist)
    # Remplacer section sondes par lignes enrichies
    parts = [title, "", "Sondes"]
    parts.extend(probe_lines)
    if blocking_failed:
        parts.extend(["", "Bloquant", *[f"  ❌ {t}" for t in blocking_failed]])
    if advisory_failed:
        parts.extend(["", "Advisory (ne déclenche pas followup si seuls KO)", *[f"  ⚠ {t}" for t in advisory_failed]])
    rem = remediation_commands(blocking_failed)
    if rem:
        parts.extend(["", "Commandes"])
        for c in rem:
            parts.append(f"  $ {c}")
    human_summary = "\n".join(parts).strip()

    blockers: list[str] = []
    for t in required:
        if not t.get("ok") and _is_blocking(str(t.get("track") or "")):
            gaps = t.get("gaps") if isinstance(t.get("gaps"), list) else []
            if gaps:
                blockers.append(f"{t.get('track')}: {gaps[0]}")
            elif t.get("error"):
                blockers.append(f"{t.get('track')}: {t['error']}")
            else:
                blockers.append(str(t.get("track")))

    return {
        "ok": ok,
        "sidecar_ok": sidecar_ok,
        "blocking_failed": blocking_failed,
        "advisory_failed": advisory_failed,
        "human_summary": human_summary,
        "blockers": blockers[:8],
        "deliverables": probe_lines[:12],
    }
