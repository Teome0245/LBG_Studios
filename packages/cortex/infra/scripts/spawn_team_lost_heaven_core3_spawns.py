#!/usr/bin/env python3
"""Lost Heaven — corriger spawns Core3 (246) sans figer locomotion / sim de vie.

Principe NON NÉGOCIABLE :
  Core3 @ 246 = source de vérité (spawns, move, rotations, multiplons, sim IA).
  Client Godot = vue / miroir — pas d'ancrage apply_visual_override comme fix cible.
"""

from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import team_spawn_phases as tsp  # noqa: E402

ACTOR = os.environ.get("LBG_TEAM_LH_SPAWNS_ACTOR", "system:spawn_lh_core3_spawns")
VM = os.environ.get("LBG_PRIME_VM", "192.168.0.246")
HTTP = os.environ.get("LBG_GATEWAY_HTTP", f"http://{VM}:8765")
HUB_X = 4749
HUB_Z = -737

ACCEPTANCE = """
Critères d'acceptation (tous obligatoires) :
- [ ] Inventaire spawns LH documenté (id, template, x/z, rôle, multiplon oui/non).
- [ ] Spawns « cassés » (mauvais point / mauvais monde) corrigés sur 246.
- [ ] PNJ post-spawn se déplacent toujours (patrol/AI) — smoke observé.
- [ ] Multiplons/triplons service toujours présents si définis.
- [ ] Aucune « solution » client qui fige les PNJ au bâtiment comme modèle cible.
- [ ] Hub Lost Heaven : densité PNJ service cohérente à l'intérieur / aux POI prévus ;
      outdoor (ronto etc.) explicitement accepté hors palissade.
""".strip()

PRINCIPLE = (
    "Principe produit : Core3 vivant (246) = vérité ; Godot = miroir. "
    "Interdit comme solution cible : apply_visual_override / collage PNJ aux bâtiments. "
    "Les PNJ DOIVENT bouger après spawn (patrol, rotations, multi-instances). "
    "Joueurs IA = joueurs (explorer), pas des statues. Corriger contenu/spawns, pas rewrite serveur."
)

TASKS: list[dict] = [
    {
        "role": "ops",
        "objective": (
            f"Héphaïstos / L2 — AUDIT spawns Lost Heaven sur Core3 {VM}. "
            f"Hub ancre (~{HUB_X}, {HUB_Z}). "
            "Lister templates PNJ, coords spawn, multiplons/triplons, distance au hub. "
            "Identifier spawns hors zone intentionnelle (palissade vs outdoor OK — ronto etc.). "
            f"Sondes : curl -sfS '{HTTP}/healthz' ; "
            f"curl -sfS '{HTTP}/v1/world/npcs_near?anchor_x={HUB_X}&anchor_z={HUB_Z}&radius_m=1200'. "
            "Livrable : inventaire (id, template, x/z, rôle, multiplon) + liste suspects "
            "(mauvais point / mauvais monde) vs outdoor légitime. "
            f"{PRINCIPLE} {ACCEPTANCE}"
        ),
        "context": {
            "lost_heaven_map": True,
            "lh_core3_spawns_fix": True,
            "mission": "audit_spawns_lh_246",
            "prime_vm": VM,
            "gateway_http": HTTP,
            "anchor_x": HUB_X,
            "anchor_z": HUB_Z,
            "radius_m": 1200,
            "forbid_visual_override_fix": True,
            "core3_source_of_truth": True,
        },
    },
    {
        "role": "dev_game",
        "objective": (
            f"Dédale / content — CORRIGER spawns Core3 Lost Heaven sur {VM} "
            "(Lua/JSON/content monorepo ou /opt selon process existant). "
            "Spawn initial cohérent hub LH / outdoor prévu ; "
            "CONSERVER multi-instances et scripts de mouvement (patrol/AI). "
            "Ne pas figer la locomotion ni la sim de vie. "
            "Après fix : smoke PNJ qui se déplacent ; multiplons/triplons service présents. "
            f"Outdoor hors palissade (ronto…) OK si intentionnel. {PRINCIPLE} {ACCEPTANCE}"
        ),
        "context": {
            "lost_heaven_map": True,
            "lh_core3_spawns_fix": True,
            "mission": "fix_spawns_core3_246",
            "prime_vm": VM,
            "anchor_x": HUB_X,
            "anchor_z": HUB_Z,
            "preserve_locomotion": True,
            "preserve_multiplons": True,
            "forbid_visual_override_fix": True,
            "core3_source_of_truth": True,
            "content_fix": True,
        },
    },
    {
        "role": "dev_godot",
        "objective": (
            "Hermès (optionnel) — Vérifier que le client Godot affiche la pos feed Core3 "
            "SANS override qui écrase la locomotion (pas d'apply_visual_override collant "
            "les PNJ aux bâtiments comme modèle cible). "
            "Documenter en handoff court : Core3 = vérité spatiale/mouvement ; Godot = miroir. "
            f"Smoke : triangles PNJ suivent le feed move. {PRINCIPLE} {ACCEPTANCE}"
        ),
        "context": {
            "lost_heaven_map": True,
            "lh_core3_spawns_fix": True,
            "mission": "verify_godot_mirror_no_freeze",
            "godot_dev_persona": "hermes",
            "godot_dev_track": "lh_spawn_mirror",
            "subproject": "godot_hermes",
            "forbid_visual_override_fix": True,
            "core3_source_of_truth": True,
            "godot_mirror_only": True,
        },
    },
]


def _parse_args(argv: list[str]) -> tuple[str, set[str] | None, bool, bool]:
    phase = "real"
    only: set[str] | None = None
    notify = False
    list_phases = False
    for arg in argv:
        if arg == "--dry-run":
            continue
        if arg == "--notify-element":
            notify = True
            continue
        if arg == "--list-phases":
            list_phases = True
            continue
        if arg.startswith("--phase="):
            phase = arg.split("=", 1)[1].strip().lower()
            continue
        if arg.startswith("--only="):
            only = {k.strip() for k in arg.split("=", 1)[1].split(",") if k.strip()}
    if list_phases:
        for k, v in tsp.PHASE_LABELS.items():
            print(f"{k}: {v}")
        sys.exit(0)
    return phase, only, notify, "--dry-run" in argv


def _run_phase(
    phase: str,
    *,
    run_id: str,
    only: set[str] | None,
    auto_run: bool,
) -> list[dict]:
    orch = os.environ.get("LBG_ORCHESTRATOR_URL", "http://192.168.0.140:8010")
    os.environ.setdefault("LBG_ORCHESTRATOR_URL", orch)
    print(f"=== LH Core3 spawns — phase {phase.upper()} → {orch} (run_id={run_id}) ===")
    return tsp.spawn_tasks_for_phase(
        tasks=TASKS,
        phase=phase,
        actor_id=ACTOR,
        http_gateway=HTTP,
        vm=VM,
        run_id=run_id,
        only_filter=only,
        root=_ROOT,
        auto_run=auto_run,
    )


def main() -> int:
    phase, only, notify, print_only = _parse_args(sys.argv[1:])

    if print_only:
        tasks = TASKS
        if only:
            tasks = [
                t
                for t in TASKS
                if t["role"] in only
                or (t.get("context") or {}).get("godot_dev_track", "") in only
            ]
        for t in tasks:
            track = (t.get("context") or {}).get("godot_dev_track", "")
            label = f"{t['role']}" + (f" [{track}]" if track else "")
            print(f"[dry-run] {label}: {t['objective'][:120]}…")
        print(f"OK dry-run — {len(tasks)} tâche(s) (aucun appel orchestrateur)")
        return 0

    run_id = tsp.new_run_id()
    if phase == "all":
        sequence = ("dry", "control", "real")
    elif phase in tsp.PHASE_LABELS:
        sequence = (phase,)
    else:
        print(f"Phase inconnue : {phase}. Utiliser --list-phases", file=sys.stderr)
        return 2

    # State dédié pour ne pas écraser le state map LH
    os.environ.setdefault(
        "LBG_TEAM_SPAWN_STATE",
        f"/tmp/lbg_spawn_lh_core3_spawns_{run_id}.json",
    )

    exit_code = 0
    all_results: dict[str, list[dict]] = {}
    for ph in sequence:
        auto_run = ph != "real" or bool(os.environ.get("LBG_TEAM_SPAWN_AUTO_RUN_REAL", "").strip())
        results = _run_phase(ph, run_id=run_id, only=only, auto_run=auto_run)
        for r in results:
            role = r.get("role")
            track = r.get("track") or ""
            tid = r.get("task_id")
            err = r.get("error")
            if err:
                print(f"  FAIL {role}: {err}", file=sys.stderr)
                exit_code = 2
            else:
                print(
                    f"  {role}{' / ' + track if track else ''} "
                    f"task_id={tid} status={r.get('task_status')} ok={r.get('task_ok')} "
                    f"L2={bool(r.get('approval_required'))}"
                )
        tsp.persist_phase(run_id, ph, results)
        all_results[ph] = results
        if notify:
            el = tsp.notify_element_phase(phase=ph, run_id=run_id, results=results)
            print(json.dumps({"element": el}, ensure_ascii=False, indent=2))

    out = {
        "ok": exit_code == 0,
        "run_id": run_id,
        "mission": "lh_core3_spawns_fix",
        "cockpit": "http://192.168.0.110:8093#team",
        "principle": "Core3 vivant / Godot miroir",
        "phases": all_results,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if phase in ("real", "all"):
        print(
            "\nPhase RÉEL : ops/dev_game en L2 — valider dans Element (`valider <id>`) "
            "puis matrix_notify. Cockpit : http://192.168.0.110:8093#team"
        )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
