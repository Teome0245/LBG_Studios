"""Workflow M11 — login LBG Godot + contrat Thémis (forge fichiers réels)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from services.action_proposal import propose_action_from_text

from team.human_summary import format_validation_summary
from team.iris_gdscript_forge import forge_from_m9_probes, iris_forge_enabled
from team.iris_llm_forge import forge_with_llm_and_smoke, iris_llm_forge_enabled
from team.m11_login_probe import audit_m11_contract_readiness, audit_m11_login_readiness
from team.m9_map_probe import _repo_root
from team.models import TeamTask

Dispatcher = Callable[..., dict[str, object]]

_CONTRACT_MARKER_START = "## Contrat M11 ↔ M12"
_CONTRACT_STUB_HINT = "À compléter par Thémis"


def _load_contract_fragment() -> str:
    frag = (
        Path(__file__).resolve().parent
        / "forge_templates"
        / "hermes_net"
        / "docs"
        / "contrat_m11_m12_fragment.md"
    )
    if frag.is_file():
        return frag.read_text(encoding="utf-8").strip() + "\n"
    return (
        "## Contrat M11 ↔ M12\n\n"
        "| Champ | Description |\n|-------|-------------|\n"
        "| `session_token` | opaque gateway |\n"
        "| `ws_url` | URL WebSocket lbg-ws/2 |\n"
        "| `your_character_id` | obj_id Core3 |\n"
        "| Erreurs | `auth_failed`, `character_in_use` |\n"
        "| Policy | `kick_other` |\n"
    )


def ensure_m11_contract_in_jalon(*, auto_write: bool = True) -> dict[str, object]:
    """Remplace le stub Thémis par le fragment contrat si demandé."""
    jalon = _repo_root() / "docs/jalon_m11_login_lbg.md"
    out: dict[str, object] = {"path": str(jalon), "written": False, "ok": False}
    if not jalon.is_file():
        out["error"] = "jalon absent"
        return out
    text = jalon.read_text(encoding="utf-8")
    probe = audit_m11_contract_readiness()
    if probe.get("ok"):
        out["ok"] = True
        out["already_complete"] = True
        return out
    if not auto_write:
        out["gaps"] = probe.get("gaps")
        return out

    fragment = _load_contract_fragment()
    # Remplace la section contrat (du titre jusqu'à ## Livrables ou ## Critères)
    pattern = re.compile(
        r"## Contrat M11\s*↔\s*M12.*?(?=\n## |\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    if pattern.search(text):
        new_text = pattern.sub(fragment.rstrip() + "\n\n", text, count=1)
    else:
        # Insère avant Livrables
        insert_at = text.find("## Livrables")
        if insert_at == -1:
            new_text = text.rstrip() + "\n\n" + fragment
        else:
            new_text = text[:insert_at] + fragment + "\n" + text[insert_at:]

    # Statut jalon plus stub Hermès
    new_text = new_text.replace(
        "**Statut** : **à rédiger par Hermès** (spawn M11)",
        "**Statut** : **en cours** (contrat M11↔M12 rédigé · code LoginPanel / LbgAuthClient)",
    )
    jalon.write_text(new_text, encoding="utf-8")
    out["written"] = True
    out["ok"] = bool(audit_m11_contract_readiness().get("ok"))
    return out


def execute_m11_login_workflow(task: TeamTask, dispatch: Dispatcher) -> dict[str, object]:
    ctx = dict(task.context)
    track = str(ctx.get("godot_dev_track") or "m11_login")
    auto_apply = bool(ctx.get("iris_forge_auto_apply") or ctx.get("forge_auto_apply") or ctx.get("write_files"))
    want_forge = bool(
        ctx.get("forge_gdscript")
        or ctx.get("iris_forge")
        or ctx.get("iris_forge_llm")
        or ctx.get("write_files")
        or iris_forge_enabled()
    )

    probes: list[dict[str, object]] = [audit_m11_login_readiness()]
    forge_result = None
    iris_llm_forge_result = None

    if want_forge and not probes[0].get("ok"):
        if iris_llm_forge_enabled() and ctx.get("iris_forge_llm"):
            iris_llm_forge_result = forge_with_llm_and_smoke(
                list(probes[0].get("gaps") or []),
                task_id=task.id,
                track="m11_login",
                persona="hermes",
                auto_apply=auto_apply,
            )
            forge_result = iris_llm_forge_result.get("template_forge")
        else:
            fr = forge_from_m9_probes(
                probes,
                task_id=task.id,
                track="m11_login",
                persona="hermes",
                auto_apply=auto_apply,
            )
            forge_result = fr.to_dict() if fr else None
        # Re-probe après apply
        if auto_apply:
            probes = [audit_m11_login_readiness()]

    # Compléter statut jalon si fichiers présents mais stub
    if probes[0].get("ok") or (forge_result and (forge_result.get("applied_count") or 0) > 0):
        ensure_m11_contract_in_jalon(auto_write=False)

    brief = dispatch(
        "agent.pm",
        actor_id=task.actor_id,
        text=task.objective,
        context={**ctx, "project_pm": {"include_plan": True, "scope": "m11_login"}},
    )
    prop = propose_action_from_text(task.objective, ctx)
    proposal_payload = None
    if prop.proposal is not None:
        proposal_payload = prop.proposal.model_dump()
        proposal_payload["source"] = f"team_godot_dev_hermes_{track}"

    ok = bool(probes[0].get("ok"))
    deliverables = list(probes[0].get("deliverables") or [])
    if forge_result and forge_result.get("patches"):
        for p in forge_result["patches"]:
            if p.get("applied") and p.get("target_rel"):
                path = f"prime-client/{p['target_rel']}"
                if path not in deliverables:
                    deliverables.append(path)

    forge_note = None
    if forge_result:
        forge_note = f"Forge M11 — {forge_result.get('applied_count', 0)} apply · staging={forge_result.get('staging_dir', 'n/a')}"
    elif proposal_payload:
        forge_note = proposal_payload.get("summary")

    human_summary = format_validation_summary(
        title=f"Hermès — M11 login ({track})",
        probes=probes,
        forge_note=forge_note,
        checklist=[
            "LoginPanel.tscn + LbgAuthClient.gd dans prime-client",
            "docs/jalon_m11_login_lbg.md (contrat + critères)",
            "Smoke Argus smoke_godot_m11_login_lan.sh (suite)",
        ],
    )

    return {
        "kind": "godot_dev_workflow",
        "ok": ok,
        "persona": "hermes",
        "track": track,
        "godot_dev_track": track,
        "probes": probes,
        "brief": brief,
        "action_proposal": proposal_payload,
        "iris_forge": forge_result,
        "iris_llm_forge": iris_llm_forge_result,
        "deliverables": deliverables,
        "subproject": "godot_hermes",
        "failed_count": 0 if ok else len(probes[0].get("gaps") or []),
        "human_summary": human_summary,
        "write_files": auto_apply,
    }


def execute_m11_contract_workflow(task: TeamTask, dispatch: Dispatcher) -> dict[str, object]:
    ctx = dict(task.context)
    auto_write = bool(ctx.get("write_files") or ctx.get("pm_write_docs") or True)
    write_out = ensure_m11_contract_in_jalon(auto_write=auto_write)
    probe = audit_m11_contract_readiness()

    brief = dispatch(
        "agent.pm",
        actor_id=task.actor_id,
        text=task.objective,
        context={**ctx, "project_pm": {"include_plan": True, "scope": "m11_contract"}},
    )

    ok = bool(probe.get("ok"))
    human_summary = format_validation_summary(
        title="Thémis — contrat M11↔M12",
        probes=[probe],
        forge_note=("Contrat écrit dans jalon" if write_out.get("written") else "Contrat déjà présent / stub"),
        checklist=[
            "Section Contrat M11-M12 dans docs/jalon_m11_login_lbg.md",
            "Champs session_token, ws_url, select_character, enter_zone, kick_other",
        ],
    )

    return {
        "kind": "pm_m11_contract",
        "ok": ok,
        "track": "themis_contract",
        "probes": [probe],
        "brief": brief,
        "contract_write": write_out,
        "deliverables": probe.get("deliverables") or ["docs/jalon_m11_login_lbg.md"],
        "human_summary": human_summary,
    }


def resolve_m11_login_workflow(task: TeamTask) -> bool:
    ctx = task.context or {}
    track = str(ctx.get("godot_dev_track") or "").lower()
    return track in ("m11_login", "m11_ui") or bool(ctx.get("m11_login_forge"))


def resolve_m11_contract_workflow(task: TeamTask) -> bool:
    ctx = task.context or {}
    track = str(ctx.get("godot_dev_track") or "").lower()
    return track == "themis_contract" or bool(ctx.get("m11_contract_write"))
