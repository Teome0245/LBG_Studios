#!/usr/bin/env python3
"""ADR 0017 Phase 0 — peel talents/inventaire (sidecar :8791) + Godot M10 live.

Focus UNIQUEMENT Phase 0 (Keep + discipline). Pas de rewrite Core3.
Réf. : docs/adr/0017-core3-spatial-peel-services.md
Lien spawns LH déjà en cours : run b1760be2eb38 (d022bfb1 / 4ae3796a).
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

ACTOR = os.environ.get("LBG_TEAM_ADR0017_P0_ACTOR", "system:spawn_adr0017_phase0")
VM = os.environ.get("LBG_PRIME_VM", "192.168.0.246")
SIDECAR = os.environ.get("LBG_CORE3_SIDECAR_URL", f"http://{VM}:8791").rstrip("/")
HTTP = os.environ.get("LBG_GATEWAY_HTTP", f"http://{VM}:8765")
PRIME = os.environ.get(
    "LBG_PRIME_CLIENT_ROOT", "/home/sdesh/projects/new_mmo/prime-client"
)

# Spawns LH Core3 déjà spawnés — à valider (L2), pas à respawn.
RELATED_RUN_ID = os.environ.get("LBG_ADR0017_RELATED_RUN", "b1760be2eb38")
RELATED_TASK_IDS = [
    "d022bfb1-dbbd-49c4-aae5-ac9a2aaa6260",  # ops audit spawns LH
    "4ae3796a-a293-42c3-8d0e-ed525e906619",  # dev_game fix spawns
]

ADR_REF = "LBG_IA_MMORPG/LBG_IA_MMO/docs/adr/0017-core3-spatial-peel-services.md"
ADR_ID = "0017"

ACCEPTANCE_SIDECAR = """
Critères d'acceptation ops/sidecar (tous obligatoires) :
- [ ] GET {sidecar}/healthz → 200.
- [ ] GET {sidecar}/v1/catalog/skills → 200 (plus de 404) ; JSON ok=true, skills[] non vide.
- [ ] GET {sidecar}/v1/catalog/schematics → 200 OU skills response inclut schematics[] (contrat M10).
- [ ] Route stable après restart service sidecar sur 246 (pas seulement process ad hoc).
- [ ] Inventaire : si contrat déjà prévu, exposer GET /v1/inventory (ou chemin doc) ; sinon handoff court « inventaire → Phase 1 peel » dans result.deliverables[].
- [ ] Aucun rewrite Core3 / Agones / migration monde (hors scope Phase 0 — ADR 0017).
""".strip().format(sidecar=SIDECAR)

ACCEPTANCE_GODOT = """
Critères d'acceptation dev_godot M10 (tous obligatoires) :
- [ ] Panneau M10 (talents_craft_panel.gd) affiche des données live sidecar (status « live — N skills… »).
- [ ] Plus de dépendance produit au mock local (_apply_local_mock) comme chemin nominal ; mock = fallback hors-ligne explicite seulement.
- [ ] Smoke : curl skills 200 puis panneau rempli sans redémarrer mock.
- [ ] Godot reste miroir spatial Core3 (ADR 0017) : pas d'apply_visual_override / vérité spatiale client.
- [ ] Aucun rewrite Core3.
""".strip()

PRINCIPLE = (
    "ADR 0017 accepté (A+B+peel). Phase 0 only : Core3 = vérité spatiale/vie ; "
    "sidecar :8791 = vérité talents (+ inventaire si prévu) ; Godot = miroir. "
    "Interdit : rewrite monde, Agones, remplacer Godot."
)

TASKS: list[dict] = [
    {
        "role": "ops",
        "objective": (
            f"Héphaïstos / sidecar — ADR {ADR_ID} Phase 0 : TUER le mock talents. "
            f"Exposer sur {SIDECAR} : GET /v1/catalog/skills (et inventaire si contrat prévu). "
            f"Constat pilote : healthz=200 mais /v1/catalog/skills a pu répondre 404 — "
            "déployer/redémarrer core3_ia_sidecar avec routes M10 catalogue ; vérifier bind LAN "
            f"(pas seulement 127.0.0.1). Sondes : curl -sfS '{SIDECAR}/healthz' ; "
            f"curl -sfS '{SIDECAR}/v1/catalog/skills' | head -c 400. "
            f"Code : tools/core3_ia_sidecar/ ; tests test_m10_catalog.py. "
            f"Lier run spawns LH `{RELATED_RUN_ID}` (valider "
            f"`valider {RELATED_TASK_IDS[0][:8]}` / `valider {RELATED_TASK_IDS[1][:8]}` si L2). "
            f"Réf. {ADR_REF}. {PRINCIPLE} {ACCEPTANCE_SIDECAR}"
        ),
        "context": {
            "adr": ADR_ID,
            "adr_path": ADR_REF,
            "adr0017_phase0": True,
            "mission": "sidecar_catalog_skills_live",
            "prime_vm": VM,
            "sidecar_url": SIDECAR,
            "gateway_http": HTTP,
            "kill_mock_talents": True,
            "no_core3_rewrite": True,
            "related_run_id": RELATED_RUN_ID,
            "related_task_ids": RELATED_TASK_IDS,
            "related_mission": "lh_core3_spawns_fix",
        },
    },
    {
        "role": "dev_godot",
        "objective": (
            f"Iris/Hermès — ADR {ADR_ID} Phase 0 : brancher panneau M10 sur réponses LIVE "
            f"sidecar {SIDECAR} (plus de dépendance mock comme chemin nominal). "
            f"Fichier : {PRIME}/scripts/talents_craft_panel.gd — "
            "GET /v1/catalog/skills → peupler listes ; status « live ». "
            "Mock local uniquement si hors-ligne (erreur réseau/HTTP), jamais comme vérité produit. "
            "Godot = miroir spatial Core3 (ADR 0017) — ne pas figer PNJ / pos client. "
            f"Lier run `{RELATED_RUN_ID}` (spawns LH). Réf. {ADR_REF}. "
            f"{PRINCIPLE} {ACCEPTANCE_GODOT}"
        ),
        "context": {
            "adr": ADR_ID,
            "adr_path": ADR_REF,
            "adr0017_phase0": True,
            "mission": "m10_panel_live_sidecar",
            "godot_dev_persona": "iris",
            "godot_dev_track": "m10_live_catalog",
            "subproject": "godot_iris",
            "prime_client_root": PRIME,
            "sidecar_url": SIDECAR,
            "kill_mock_talents": True,
            "core3_source_of_truth": True,
            "godot_mirror_only": True,
            "forbid_visual_override_fix": True,
            "no_core3_rewrite": True,
            "related_run_id": RELATED_RUN_ID,
            "related_task_ids": RELATED_TASK_IDS,
            "related_mission": "lh_core3_spawns_fix",
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
    print(f"=== ADR 0017 Phase 0 — phase {phase.upper()} → {orch} (run_id={run_id}) ===")
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
            print(f"[dry-run] {label}: {t['objective'][:140]}…")
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

    os.environ.setdefault(
        "LBG_TEAM_SPAWN_STATE",
        f"/tmp/lbg_spawn_adr0017_phase0_{run_id}.json",
    )

    exit_code = 0
    all_results: dict[str, list[dict]] = {}
    for ph in sequence:
        auto_run = ph != "real" or bool(
            os.environ.get("LBG_TEAM_SPAWN_AUTO_RUN_REAL", "").strip()
        )
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
            # Rappeler les L2 spawns LH liés
            related_note = (
                f"\n🔗 Lié run LH Core3 spawns `{RELATED_RUN_ID}` — "
                f"valider `{RELATED_TASK_IDS[0][:8]}` (ops) / "
                f"`valider {RELATED_TASK_IDS[1][:8]}` (dev_game) si encore L2.\n"
                f"ADR 0017 Phase 0 — peel sidecar + M10 live (pas de rewrite Core3)."
            )
            el = tsp.notify_element_phase(phase=ph, run_id=run_id, results=results)
            extra = tsp.push_element_text(related_note)
            print(
                json.dumps(
                    {"element": el, "element_related": extra},
                    ensure_ascii=False,
                    indent=2,
                )
            )

    out = {
        "ok": exit_code == 0,
        "run_id": run_id,
        "mission": "adr0017_phase0",
        "adr": ADR_ID,
        "related_run_id": RELATED_RUN_ID,
        "related_task_ids": RELATED_TASK_IDS,
        "sidecar_url": SIDECAR,
        "cockpit": "http://192.168.0.110:8093#team",
        "phases": all_results,
        "valider_hints": [
            f"valider {RELATED_TASK_IDS[0][:8]}  # ops audit spawns LH (run {RELATED_RUN_ID})",
            f"valider {RELATED_TASK_IDS[1][:8]}  # dev_game fix spawns LH (run {RELATED_RUN_ID})",
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if phase in ("real", "all"):
        print(
            "\nPhase RÉEL : ops sidecar en L2 — `valider <id>` puis run. "
            "Godot M10 : run si queued. "
            f"Spawns LH liés : `valider {RELATED_TASK_IDS[0][:8]}` / "
            f"`valider {RELATED_TASK_IDS[1][:8]}`. "
            "Cockpit : http://192.168.0.110:8093#team"
        )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
