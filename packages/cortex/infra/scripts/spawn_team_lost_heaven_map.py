#!/usr/bin/env python3
"""Distribue Lost Heaven — phases dry → contrôle → réel + compte rendu Element."""

from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import team_spawn_phases as tsp  # noqa: E402

ACTOR = os.environ.get("LBG_TEAM_LH_MAP_ACTOR", "system:spawn_lost_heaven_map")

PRIME = os.environ.get(
    "LBG_PRIME_CLIENT_ROOT", "/home/sdesh/projects/new_mmo/prime-client"
)
GATEWAY = os.environ.get(
    "LBG_GATEWAY_ROOT",
    "/home/sdesh/projects/LBG_IA_MMORPG/LBG_IA_MMO/services/lbg_gateway",
)
VM = os.environ.get("LBG_PRIME_VM", "192.168.0.246")
HTTP = os.environ.get("LBG_GATEWAY_HTTP", f"http://{VM}:8765")

DOCS = {
    "retail_layout": f"{PRIME}/docs/RETAIL_CITY_LAYOUT.md",
    "map_textures": f"{PRIME}/docs/MAP_TEXTURES_AND_RETAIL.md",
    "handoff": "LBG_IA_MMORPG/LBG_IA_MMO/docs/HANDOFF_SPAWN_LOST_HEAVEN_MAP.md",
}

TASKS: list[dict] = [
    {
        "role": "ops",
        "objective": (
            f"Héphaïstos — Déployer sur VM {VM} le gateway Prime avec npc_snapshot_export.py "
            "et la route HTTP GET /v1/world/npcs_near (http_auth.py). "
            "Redémarrer le service lbg_gateway. Vérifier : "
            f"curl -sfS '{HTTP}/healthz' et curl -sfS "
            f"'{HTTP}/v1/world/npcs_near?anchor_x=4749&anchor_z=-737&radius_m=800' "
            "(JSON ok même si count=0). Documenter version déployée + rollback."
        ),
        "context": {
            "lost_heaven_map": True,
            "gateway_root": GATEWAY,
            "prime_vm": VM,
            "docs": DOCS,
        },
    },
    {
        "role": "dev_game",
        "objective": (
            f"Dédale — Spawns PNJ Core3 près de Lost Heaven (Tatooine, hub LBG) sur {VM} "
            "pour alimenter le snapshot gateway. Objectif : au moins quelques NPC online "
            "dans rayon 800 m autour de anchor (4749, -737). "
            "Puis régénérer snapshot si pipeline serveur l'exige. "
            "Coordination Hermès (export client) + Héphaïstos (déploiement HTTP)."
        ),
        "context": {
            "lost_heaven_map": True,
            "anchor_x": 4749,
            "anchor_z": -737,
            "radius_m": 800,
            "docs": DOCS,
        },
    },
    {
        "role": "dev_godot",
        "objective": (
            "Hermès — Valider et documenter le flux PNJ serveur côté prime-client : "
            "retail_layout_layer.merge_zone_entities(), triangles cyan, "
            "tatooine_map_config.json world_render.server_npcs, "
            "tools/retail/export_server_npcs_lost_heaven.sh + build_prime_position_map.sh. "
            "Critère done : après spawn Dédale, npcs_server > 0 en jeu + export JSON à jour. "
            "Ne pas réécrire zone_layers / gate_exits (déjà OK). Livrable : deliverables[] + note dans RETAIL_CITY_LAYOUT.md."
        ),
        "context": {
            "lost_heaven_map": True,
            "godot_dev_persona": "hermes",
            "godot_dev_track": "lh_server_npcs",
            "subproject": "godot_hermes",
            "prime_client_root": PRIME,
            "gateway_http": HTTP,
            "docs": DOCS,
        },
    },
    {
        "role": "dev_godot",
        "objective": (
            "Iris — Carte positionnement Lost Heaven : RetailLayoutLayer visible, "
            "lost_heaven_retail_layout.json, hub tuiles masquées, entity_markers triangle. "
            "MAJ MAP_TEXTURES_AND_RETAIL.md si écart gabarit ME ↔ POI. "
            "Option fond : world_render.show_planet_texture vs planet_backdrop procédural — "
            "recommandation produit 1 paragraphe. Pas de blocage sur texture satellite."
        ),
        "context": {
            "lost_heaven_map": True,
            "godot_dev_persona": "iris",
            "godot_dev_track": "lh_retail_map",
            "subproject": "godot_iris",
            "prime_client_root": PRIME,
            "docs": DOCS,
        },
    },
    {
        "role": "dev_godot",
        "objective": (
            "Hermès — Launchpad + sync J: : confirmer launchpad.config.json chemin WSL prioritaire, "
            "tools/sync_prime_client_to_j.sh et verify_launchpad_prime.ps1 documentés. "
            "Smoke : connexion WS 50000 depuis Windows Launchpad (Teome). "
            "Livrable : entrée ops dans HUMAN_PLAYER ou CLIENT_ONLY si manquant."
        ),
        "context": {
            "lost_heaven_map": True,
            "godot_dev_persona": "hermes",
            "godot_dev_track": "launchpad_wsl_sync",
            "subproject": "godot_hermes",
            "prime_client_root": PRIME,
            "docs": DOCS,
        },
    },
    {
        "role": "qa",
        "objective": (
            f"Argus — Smoke Lost Heaven E2E : (1) Launchpad → login Teome → zone LH ; "
            "(2) sortie palissade sud franchissable ; (3) GET {HTTP}/v1/world/npcs_near ; "
            "(4) build_prime_position_map.sh sans erreur fatale ; "
            "(5) M12 move si déjà vert. Rapport court avec URLs et compteurs PNJ."
        ),
        "context": {
            "lost_heaven_map": True,
            "godot_supervisor": True,
            "gateway_http": HTTP,
            "docs": DOCS,
        },
    },
    {
        "role": "dev_godot",
        "objective": (
            "Pygmalion / infographiste — Habillage LH : pipeline habillage_lost_heaven.sh, "
            "sprites overhead units si NAS/B: disponible ; sinon checklist copie manuelle. "
            "Pas de régression ComfyUI. Coordination Iris (markers carte)."
        ),
        "context": {
            "lost_heaven_map": True,
            "godot_dev_track": "lh_habillage",
            "subproject": "godot_iris",
            "prime_client_root": PRIME,
            "docs": DOCS,
        },
    },
]


def _parse_args(argv: list[str]) -> tuple[str, set[str] | None, bool, bool]:
    phase = "dry"
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
    print(f"=== phase {phase.upper()} → {orch} (run_id={run_id}) ===")
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
            print(f"[dry-run] {label}: {t['objective'][:100]}…")
        print(f"OK dry-run — {len(tasks)} tâche(s) (aucun appel orchestrateur)")
        print("Enchaînement : --phase=dry → --phase=control → --phase=real [--notify-element]")
        return 0

    run_id = tsp.new_run_id()
    all_results: dict[str, list[dict]] = {}

    if phase == "all":
        sequence = ("dry", "control", "real")
    elif phase in tsp.PHASE_LABELS:
        sequence = (phase,)
    else:
        print(f"Phase inconnue : {phase}. Utiliser --list-phases", file=sys.stderr)
        return 2

    exit_code = 0
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

    out = {"ok": exit_code == 0, "run_id": run_id, "phases": all_results}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if phase == "real" or phase == "all":
        print(
            "\nPhase RÉEL : ops/dev_game en L2 — valider dans Element (`valider <id>`) "
            "puis matrix_notify enverra ✅ Terminé."
        )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
