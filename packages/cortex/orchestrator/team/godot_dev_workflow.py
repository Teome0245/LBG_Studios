"""Workflow dev_godot — personas Iris (2D/UI) et Hermès (réseau/SOE)."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable

from services.action_proposal import propose_action_from_text

from team.godot_client_tracks_workflow import execute_godot_client_tracks_workflow
from team.human_summary import format_validation_summary
from team.m9_map_workflow import execute_m9_map_workflow
from team.m9_map_probe import audit_m9_full_readiness, audit_m9a_readiness, audit_m9b_readiness, audit_m9c_readiness
from team.lost_heaven_code_workflow import (
    execute_lost_heaven_code_workflow,
    resolve_lost_heaven_code_workflow,
)
from team.m11_login_workflow import execute_m11_login_workflow, resolve_m11_login_workflow
from team.models import TeamTask
from team.ui_portraits_workflow import execute_ui_portraits_workflow

Dispatcher = Callable[..., dict[str, object]]

_PERSONA_ALIASES = {
    "iris": "iris",
    "iris_2d": "iris",
    "2d": "iris",
    "hermes": "hermes",
    "hermes_net": "hermes",
    "network": "hermes",
    "soe": "hermes",
}

_TRACK_ALIASES = {
    "m9": "m9_full",
    "m9a": "m9a",
    "m9b": "m9b",
    "m9c": "m9c",
    "m9_full": "m9_full",
    "soe_m3": "soe_m3",
    "soe_m5": "soe_m5",
    "zb0": "zb0",
    "zb1": "zb1",
    "client_live": "client_live",
    "hunt_hub": "hunt_hub",
    "hub_hunt": "hunt_hub",
    "palissade": "hunt_hub",
    "iris_full": "iris_full",
    "hermes_full": "hermes_full",
    "m11_login": "m11_login",
    "m11_ui": "m11_ui",
    "themis_contract": "themis_contract",
    "ui_portraits": "ui_portraits",
    "dialogue_portraits": "ui_portraits",
    "portraits": "ui_portraits",
    "full": "full",
}

_HUNT_HUB_RE = re.compile(
    r"(?i)\b(chasse|hunt|palissade|hub|lost\s*heaven|board|porte\s+est|"
    r"mission\s*board|meute|chacal)\b"
)


def _normalize_persona(raw: str) -> str:
    return _PERSONA_ALIASES.get((raw or "").strip().lower(), (raw or "iris").lower())


def _normalize_track(raw: str) -> str:
    return _TRACK_ALIASES.get((raw or "").strip().lower(), (raw or "iris_full").lower())


def _detect_persona(task: TeamTask) -> str:
    ctx = task.context
    raw = ctx.get("godot_dev_persona") or ctx.get("godot_persona")
    if raw:
        return _normalize_persona(str(raw))
    text = (task.objective or "").lower()
    if re.search(r"\b(hermes|soe|gateway|udp|lbg-ws|zb-?\d)\b", text):
        return "hermes"
    if re.search(r"\b(iris|2d|minimap|carte|m9|scrapaltai|waypoint|ui godot)\b", text):
        return "iris"
    return "iris"


def _detect_track(task: TeamTask, persona: str) -> str:
    ctx = task.context
    raw = ctx.get("godot_dev_track") or ctx.get("m9_track") or ctx.get("godot_track")
    if raw:
        return _normalize_track(str(raw))
    text = (task.objective or "").lower()
    if persona == "hermes":
        if re.search(r"\bzb-?1\b", text):
            return "zb1"
        if re.search(r"\bzb-?0\b", text):
            return "zb0"
        if re.search(r"\bm5\b", text):
            return "soe_m5"
        if re.search(r"\bm3\b", text):
            return "soe_m3"
        return "client_live"
    if re.search(r"\bm9c\b", text):
        return "m9c"
    if re.search(r"\bm9b\b", text):
        return "m9b"
    if re.search(r"\bm9a\b", text):
        return "m9a"
    if re.search(r"\bm9\b", text):
        return "m9_full"
    if re.search(r"\b(portrait|portraits|dialogue_portrait|garr\s*vek|npc_merchant)\b", text):
        return "ui_portraits"
    if persona == "iris" and _HUNT_HUB_RE.search(text):
        return "hunt_hub"
    return "iris_full"


def _prime_client_root() -> Path:
    env = os.environ.get("LBG_PRIME_CLIENT_ROOT", "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[3] / "prime-client"


def audit_hunt_hub_readiness() -> dict[str, object]:
    """Probe L1 : hub → palissade / board chasse (pas M9)."""
    root = _prime_client_root()
    gaps: list[str] = []
    checks: dict[str, bool] = {}
    board = root / "scripts" / "mission_board_panel.gd"
    buildings = root / "assets" / "maps" / "lost_heaven_buildings.json"
    checks["mission_board"] = board.is_file()
    if not checks["mission_board"]:
        gaps.append("scripts/mission_board_panel.gd absent")
    else:
        text = board.read_text(encoding="utf-8", errors="replace")
        checks["board_hunt_or_palissade"] = ("lh_hunt_chacal" in text) or ("hors palissade" in text.lower())
        if not checks["board_hunt_or_palissade"]:
            gaps.append("board sans offre chasse / hors palissade")
    checks["buildings"] = buildings.is_file()
    if not checks["buildings"]:
        gaps.append("lost_heaven_buildings.json absent")
    else:
        raw = buildings.read_text(encoding="utf-8", errors="replace")
        checks["gate_poi"] = "poi:lost_heaven_gate" in raw
        checks["hunt_poi"] = "poi:lh_hunt_chacal" in raw
        if not checks["gate_poi"]:
            gaps.append("poi:lost_heaven_gate manquant")
        if not checks["hunt_poi"]:
            gaps.append("poi:lh_hunt_chacal manquant (hors palissade)")
    agents = Path(__file__).resolve().parents[2] / "agents" / "src" / "lbg_agents" / "hunt_yard.py"
    checks["hunt_yard_module"] = agents.is_file()
    if not checks["hunt_yard_module"]:
        gaps.append("agents hunt_yard.py absent")
    ok = len(gaps) == 0
    return {
        "track": "hunt_hub_readiness",
        "ok": ok,
        "checks": checks,
        "gaps": gaps,
        "summary": "hub → palissade / board chasse" if ok else f"{len(gaps)} gap(s) hunt_hub",
    }


def _iris_probes(track: str) -> list[dict[str, object]]:
    if track == "m9a":
        return [audit_m9a_readiness()]
    if track == "m9b":
        return [audit_m9b_readiness()]
    if track == "m9c":
        return [audit_m9c_readiness()]
    if track == "m9_full":
        return [audit_m9_full_readiness()]
    if track == "hunt_hub":
        return [audit_hunt_hub_readiness()]
    # iris_full / client_live / etc. — plus de fallback M9 silencieux
    return []


def execute_godot_dev_workflow(task: TeamTask, dispatch: Dispatcher) -> dict[str, object]:
    persona = _detect_persona(task)
    track = _detect_track(task, persona)
    ctx = dict(task.context)
    ctx.setdefault("godot_dev_persona", persona)
    ctx.setdefault("godot_dev_track", track)
    ctx.setdefault("subproject", "godot_iris" if persona == "iris" else "godot_hermes")
    ctx.setdefault("dev_godot_focus", True)

    if resolve_lost_heaven_code_workflow(task):
        out = execute_lost_heaven_code_workflow(task, dispatch)
        out["kind"] = "godot_dev_workflow"
        return out

    # M11 login / UI — forge fichiers réels (LoginPanel, LbgAuthClient)
    if resolve_m11_login_workflow(task) or track in ("m11_login", "m11_ui"):
        delegated = dict(task.context)
        delegated["godot_dev_persona"] = "hermes" if track != "m11_ui" else "iris"
        delegated["godot_dev_track"] = track if track in ("m11_login", "m11_ui") else "m11_login"
        sub = TeamTask(
            id=task.id,
            role=task.role,
            objective=task.objective,
            actor_id=task.actor_id,
            context=delegated,
        )
        out = execute_m11_login_workflow(sub, dispatch)
        out["persona"] = delegated["godot_dev_persona"]
        out["godot_dev_track"] = delegated["godot_dev_track"]
        out["kind"] = "godot_dev_workflow"
        return out

    # Portraits UI dialogue (Garr Vek / merchant PNG) — avant fallback M9
    if persona == "iris" and (
        track == "ui_portraits"
        or ctx.get("portrait_ui")
        or ctx.get("dialogue_portraits")
        or re.search(r"\b(portrait|portraits|dialogue_portrait|garr\s*vek|npc_merchant)\b", (task.objective or "").lower())
    ):
        out = execute_ui_portraits_workflow(ctx)
        out["persona"] = "iris"
        out["godot_dev_track"] = "ui_portraits"
        out["kind"] = "godot_dev_workflow"
        out.setdefault("track", "ui_portraits")
        return out

    # Délégation M9 / SOE aux workflows existants
    if persona == "iris" and track in ("m9a", "m9b", "m9c", "m9_full"):
        delegated = dict(task.context)
        delegated["m9_track"] = track
        delegated["subproject"] = "prime_client_2d"
        sub = TeamTask(
            id=task.id,
            role=task.role,
            objective=task.objective,
            actor_id=task.actor_id,
            context=delegated,
        )
        out = execute_m9_map_workflow(sub, dispatch)
        out["persona"] = "iris"
        out["godot_dev_track"] = track
        out["kind"] = "godot_dev_workflow"
        return out

    if persona == "hermes" and track in ("soe_m3", "soe_m5", "zb0", "zb1", "client_live"):
        delegated = dict(task.context)
        delegated["godot_track"] = track
        delegated["subproject"] = "client_godot"
        sub = TeamTask(
            id=task.id,
            role=task.role,
            objective=task.objective,
            actor_id=task.actor_id,
            context=delegated,
        )
        out = execute_godot_client_tracks_workflow(sub, dispatch)
        out["persona"] = "hermes"
        out["godot_dev_track"] = track
        out["kind"] = "godot_dev_workflow"
        return out

    probes = _iris_probes(track) if persona == "iris" else []
    failed = [p for p in probes if not p.get("ok") and not p.get("skipped")]
    ok = len(failed) == 0

    persona_label = "Iris" if persona == "iris" else "Hermès"
    brief = dispatch(
        "agent.pm",
        actor_id=task.actor_id,
        text=task.objective,
        context={
            **ctx,
            "project_pm": {"include_plan": True, "scope": "godot_dev", "subproject": ctx["subproject"]},
            "godot_dev_persona": persona,
        },
    )

    forged = task.objective if ok else f"{persona_label} — corriger: {(failed[0].get('gaps') or ['gap'])[0] if failed else 'gap'}"
    proposal_payload = None
    prop = propose_action_from_text(forged, ctx)
    if prop.proposal is not None:
        proposal_payload = prop.proposal.model_dump()
        proposal_payload["source"] = f"team_godot_dev_{persona}_{track}"

    human_summary = format_validation_summary(
        title=f"{persona_label} — dev Godot ({track})",
        probes=probes,
        forge_note=(proposal_payload or {}).get("summary") if proposal_payload else None,
        checklist=[
            "Pilot #/hunt + board J (porte est / meute)" if track == "hunt_hub" else "Preset Iris M9 / Hermès SOE dans Pilot #/team",
            "Doc docs/FOCUS_WAHOU.md" if track == "hunt_hub" else "Doc docs/jalon_equipe_godot_dev_ia.md",
        ],
    )

    return {
        "kind": "godot_dev_workflow",
        "ok": ok,
        "persona": persona,
        "track": track,
        "godot_dev_track": track,
        "probes": probes,
        "brief": brief,
        "action_proposal": proposal_payload,
        "subproject": ctx["subproject"],
        "failed_count": len(failed),
        "human_summary": human_summary,
    }


def resolve_godot_dev_workflow(task: TeamTask) -> bool:
    if task.role == "dev_godot":
        return True
    ctx = task.context
    return bool(ctx.get("godot_dev") or ctx.get("godot_dev_persona") or ctx.get("dev_godot_focus"))
