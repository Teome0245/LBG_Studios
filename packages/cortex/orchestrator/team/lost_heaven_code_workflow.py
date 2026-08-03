"""Workflow Lost Heaven CODE — docs prime-client + deliverables (spawn lh_code)."""

from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from services.action_proposal import propose_action_from_text

from team.human_summary import format_validation_summary
from team.m9_map_probe import _repo_root
from team.models import TeamTask
from team.prime_client_paths import resolve_prime_client_root

Dispatcher = Callable[..., dict[str, object]]

_LH_TRACKS = frozenset(
    {
        "lh_server_npcs",
        "lh_retail_map",
        "launchpad_wsl_sync",
        "lh_habillage",
    }
)


def _prime_client_root(ctx: dict) -> Path:
    return resolve_prime_client_root(ctx)


def _append_section_if_missing(path: Path, marker: str, block: str, *, auto_write: bool) -> dict[str, object]:
    out: dict[str, object] = {"path": str(path), "written": False, "ok": path.is_file()}
    if not path.is_file():
        if auto_write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {path.stem.replace('_', ' ').title()}\n\n", encoding="utf-8")
            out["created_file"] = True
        else:
            out["error"] = "fichier absent"
            out["ok"] = False
            return out
    text = path.read_text(encoding="utf-8")
    if marker in text:
        out["already_present"] = True
        out["ok"] = True
        return out
    if not auto_write:
        out["ok"] = False
        out["gap"] = f"section manquante: {marker}"
        return out
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path.write_text(text.rstrip() + f"\n\n{block.format(stamp=stamp)}\n", encoding="utf-8")
    out["written"] = True
    out["ok"] = True
    return out


def _run_export_dry(prime: Path) -> dict[str, object]:
    script = prime / "tools/retail/export_server_npcs_lost_heaven.sh"
    if not script.is_file():
        return {"ok": False, "skipped": True, "error": "script export absent"}
    try:
        proc = subprocess.run(
            ["bash", str(script)],
            cwd=str(prime),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        # Export peut échouer sans PNJ / route — non bloquant pour CODE doc
        return {
            "ok": True,
            "skipped": proc.returncode != 0,
            "returncode": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-400:],
            "stderr_tail": (proc.stderr or "")[-400:],
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc)}


def _track_blocks(track: str, prime: Path, http: str) -> list[tuple[Path, str, str]]:
    docs = prime / "docs"
    if track == "lh_server_npcs":
        return [
            (
                docs / "RETAIL_CITY_LAYOUT.md",
                "## PNJ serveur (snapshot gateway)",
                (
                    "## PNJ serveur (snapshot gateway)\n\n"
                    "Dernière MAJ équipe LH CODE ({stamp}).\n\n"
                    f"- HTTP : `{http}/v1/world/npcs_near?anchor_x=4749&anchor_z=-737&radius_m=800`\n"
                    "- Export client : `tools/retail/export_server_npcs_lost_heaven.sh`\n"
                    "- Carte : `tools/retail/build_prime_position_map.sh`\n"
                    "- Triangles **cyan** = entités fusionnées depuis le serveur (`retail_layout_layer`).\n"
                ),
            ),
        ]
    if track == "lh_retail_map":
        return [
            (
                docs / "MAP_TEXTURES_AND_RETAIL.md",
                "## Lost Heaven — fond carte (recommandation)",
                (
                    "## Lost Heaven — fond carte (recommandation)\n\n"
                    "MAJ équipe ({stamp}).\n\n"
                    "**Recommandation produit** : garder `world_render.show_planet_texture: false` "
                    "et le fond procédural `planet_backdrop` pour LH en jalon actuel ; "
                    "réactiver la texture planète (`tatooine.svg`) pour captures / marketing uniquement.\n"
                ),
            ),
        ]
    if track == "launchpad_wsl_sync":
        return [
            (
                docs / "HUMAN_PLAYER.md",
                "## Launchpad Windows (WSL prime-client)",
                (
                    "## Launchpad Windows (WSL prime-client)\n\n"
                    "Ops ({stamp}).\n\n"
                    "- `launchpad.config.json` : chemin WSL **prioritaire** vers `prime-client`.\n"
                    "- Sync lecteur J: : `tools/sync_prime_client_to_j.sh` (WSL).\n"
                    "- Vérif Windows : `tools/verify_launchpad_prime.ps1`.\n"
                    "- WS gateway : `ws://192.168.0.246:50000` · compte test Teome.\n"
                ),
            ),
        ]
    if track == "lh_habillage":
        return [
            (
                docs / "RETAIL_CITY_LAYOUT.md",
                "## Habillage Lost Heaven (pipeline art)",
                (
                    "## Habillage Lost Heaven (pipeline art)\n\n"
                    "Checklist ({stamp}).\n\n"
                    "- Pipeline : `tools/retail/habillage_lost_heaven.sh`\n"
                    "- Sprites overhead : copie `units_overhead` si NAS/B: indisponible → copie manuelle documentée.\n"
                    "- ComfyUI : pas de régression ; coordonner Iris (markers carte).\n"
                ),
            ),
        ]
    return []


def execute_lost_heaven_code_workflow(task: TeamTask, dispatch: Dispatcher) -> dict[str, object]:
    ctx = dict(task.context)
    track = str(ctx.get("godot_dev_track") or "lh_server_npcs")
    auto_write = bool(ctx.get("write_files") or ctx.get("lh_code_respawn"))
    prime = _prime_client_root(ctx)
    http = str(ctx.get("gateway_http") or "http://192.168.0.246:8765")

    writes: list[dict[str, object]] = []
    deliverables: list[str] = []
    for path, marker, block in _track_blocks(track, prime, http):
        w = _append_section_if_missing(path, marker, block, auto_write=auto_write)
        writes.append(w)
        if w.get("ok"):
            try:
                rel = path.relative_to(prime)
            except ValueError:
                rel = path.name
            deliverables.append(f"new_mmo/prime-client/{rel}")

    export_probe = None
    if track == "lh_server_npcs":
        export_probe = _run_export_dry(prime)

    persona = "hermes" if track in ("lh_server_npcs", "launchpad_wsl_sync") else "iris"
    probes = [{"track": track, "writes": writes, "export": export_probe}]
    ok = all(w.get("ok") for w in writes) if writes else False
    if export_probe and export_probe.get("ok") is False and not export_probe.get("skipped"):
        ok = False

    brief = dispatch(
        "agent.pm",
        actor_id=task.actor_id,
        text=task.objective,
        context={**ctx, "project_pm": {"include_plan": True, "scope": "lost_heaven_code"}},
    )
    prop = propose_action_from_text(task.objective, ctx)
    proposal_payload = prop.proposal.model_dump() if prop.proposal else None

    recommendation = "go" if ok else "go-with-caveats"
    blockers = [str(w.get("error") or w.get("gap")) for w in writes if not w.get("ok")]
    if export_probe and export_probe.get("ok") is False:
        blockers.append("export_server_npcs_lost_heaven.sh non vert")

    human_summary = format_validation_summary(
        title=f"{'Hermès' if persona == 'hermes' else 'Iris'} — LH CODE ({track})",
        probes=probes,
        forge_note=f"Sections doc {'écrites' if auto_write else 'à écrire (write_files=0)'}",
        checklist=[d for d in deliverables[:4]],
    )

    return {
        "kind": "lost_heaven_code_workflow",
        "ok": ok,
        "status": "done" if ok else "failed",
        "persona": persona,
        "track": track,
        "godot_dev_track": track,
        "probes": probes,
        "brief": brief,
        "action_proposal": proposal_payload,
        "deliverables": deliverables,
        "blockers": blockers,
        "recommendation": recommendation,
        "human_summary": human_summary,
        "write_files": auto_write,
    }


def resolve_lost_heaven_code_workflow(task: TeamTask) -> bool:
    ctx = task.context or {}
    track = str(ctx.get("godot_dev_track") or "").lower()
    if bool(ctx.get("lh_code_respawn")):
        return True
    return track in _LH_TRACKS and bool(ctx.get("write_files") or ctx.get("lh_code_forge"))
