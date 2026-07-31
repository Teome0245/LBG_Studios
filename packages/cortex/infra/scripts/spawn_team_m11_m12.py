#!/usr/bin/env python3
"""Distribue M11 (login LBG Godot) + M12 (lbg-ws/2) en parallèle à l'équipe virtuelle."""

from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "agents", "src"))

ACTOR = os.environ.get("LBG_TEAM_M11_M12_ACTOR", "system:spawn_m11_m12")

DOCS = {
    "client_only": "new_mmo/prime-client/docs/CLIENT_ONLY_GODOT.md",
    "human_player": "new_mmo/prime-client/docs/HUMAN_PLAYER.md",
    "bridge_spec": "docs/core3_zone_bridge_spec.md",
    "godot_live": "docs/jalon_godot_client_live_team.md",
    "m11_jalon": "docs/jalon_m11_login_lbg.md",
    "m12_schemas": "docs/schemas/lbg-ws/",
    "adr": "new_mmo/lbg-mmo/docs/adr/0016-prime-axe-lbg-talents-artisanat.md",
}

TASKS: list[dict] = [
    {
        "role": "pm",
        "objective": (
            "M11↔M12 — rédiger le contrat d'interface (1 page max) : token session, "
            "URL WebSocket, messages login/select_character/enter_zone, erreurs "
            "(character_in_use, auth_failed), session kick_other. "
            "Référencer core3_zone_bridge_spec.md §2 et client.zone_command_v2.schema.json. "
            "Livrable : section « Contrat M11-M12 » dans docs/jalon_m11_login_lbg.md + "
            "lien depuis jalon_godot_client_live_team.md. ADR 0016."
        ),
        "context": {
            "handoff_m11_m12": True,
            "godot_dev_track": "themis_contract",
            "pm_include_plan": True,
            "docs": DOCS,
        },
    },
    {
        "role": "dev_godot",
        "objective": (
            "Hermès M11 — Login compte LBG dans prime-client (sans lbgemu, sans retail). "
            "Livrables : (1) docs/jalon_m11_login_lbg.md complet (flux, messages, critères done) ; "
            "(2) extension lbg_gateway : auth SQL compte Prime + liste persos + select_character ; "
            "(3) écran Godot LoginPanel.tscn + LbgAuthClient.gd (WS ou HTTP selon spike) ; "
            "(4) remplacement progressif de soe_handshake --play pour Teome. "
            "Schémas : docs/schemas/lbg-ws/client.login.schema.json et client.zone_command_v2 "
            "(type login, select_character). Ne pas bloquer sur ZB-2 ni sur soe_m3 (legacy). "
            "Pivot produit : CLIENT_ONLY_GODOT.md — plus de dépendance retail/SOE login. "
            "Coordination Thémis pour contrat token → WS. Output : deliverables[]. Revue L2."
        ),
        "context": {
            "handoff_m11_m12": True,
            "godot_dev_persona": "hermes",
            "godot_dev_track": "m11_login",
            "subproject": "godot_hermes",
            "prime_client_root": os.environ.get(
                "LBG_PRIME_CLIENT_ROOT", "/home/sdesh/projects/new_mmo/prime-client"
            ),
            "docs": DOCS,
        },
    },
    {
        "role": "dev_godot",
        "objective": (
            "Hermès M12 — Réseau autoritaire lbg-ws/2 Godot ↔ lbg_gateway ↔ LbgZoneBridge. "
            "Livrables : (1) MAJ docs/jalon_godot_client_live_team.md (ZB-0/1/2 statut) ; "
            "(2) client Godot LbgWsClient.gd : zone_state v2 + move(seq) ; "
            "(3) gateway : traduction WS → bridge C++ ; "
            "(4) smoke avec token dev si M11 pas prêt. "
            "Schémas : server.zone_state_v2.schema.json, client.zone_command_v2.schema.json. "
            "Peut démarrer en parallèle de M11 avec token mock. "
            "Ne pas attendre soe_m3_login/soe_m3_zone verts — chemin cible lbg-ws/2 uniquement. "
            "Retirer à terme prime_controller.py + soe_handshake --play. Output : deliverables[]. Revue L2."
        ),
        "context": {
            "handoff_m11_m12": True,
            "godot_dev_persona": "hermes",
            "godot_dev_track": "m12_lbg_ws2",
            "subproject": "godot_hermes",
            "prime_client_root": os.environ.get(
                "LBG_PRIME_CLIENT_ROOT", "/home/sdesh/projects/new_mmo/prime-client"
            ),
            "docs": DOCS,
        },
    },
    {
        "role": "dev_godot",
        "objective": (
            "Hermès — PIVOT post-échec SOE M3 (Element #a0a903bd) : abandonner le blocage "
            "soe_m3_login / soe_m3_zone comme critère jalon client. Documenter dans "
            "jalon_godot_client_live_team.md que M3/M5 SOE = transition deprecated ; "
            "priorité M11 login LBG + M12 lbg-ws/2. Marquer sondes hermes_soe en "
            "non-bloquant pour smoke Godot-only. Livrable : note + MAJ checklist Argus."
        ),
        "context": {
            "handoff_m11_m12": True,
            "godot_dev_persona": "hermes",
            "godot_dev_track": "hermes_pivot_soe",
            "subproject": "godot_hermes",
            "parent_failure": "soe_m3 KO — dev_game failed",
            "docs": DOCS,
        },
    },
    {
        "role": "dev_godot",
        "objective": (
            "Iris M11 UI — Maquette écran connexion + sélection perso prime-client "
            "(theme prime_ui.tres, champs user/password, liste persos, bouton Entrer). "
            "Brancher sur LbgAuthClient.gd dès que Hermès M11 expose l'API. "
            "Pas de logique SOE. Livrable : scenes/ui/login_panel.tscn + login_panel.gd."
        ),
        "context": {
            "handoff_m11_m12": True,
            "godot_dev_persona": "iris",
            "godot_dev_track": "m11_ui",
            "subproject": "godot_iris",
            "docs": DOCS,
        },
    },
    {
        "role": "dev_game",
        "objective": (
            "Dédale M12 serveur — ZB-1 export zone 20 Hz + ZB-2 injection move validé. "
            "Fichiers : LbgZoneBridge.h/cpp, hooks ZoneServer. "
            "Coordonner avec Hermès M12 pour format batch entities. "
            "Policy session kick_other documentée. Smoke Teome sur VM 246."
        ),
        "context": {
            "handoff_m11_m12": True,
            "handoff_doc": DOCS["bridge_spec"],
            "docs": DOCS,
        },
    },
    {
        "role": "qa",
        "objective": (
            "Argus — Plan smoke M11+M12 E2E Godot-only (sans lbgemu) : "
            "(1) login Teome Prime ; (2) select_character ; (3) WS connect ; "
            "(4) zone_state reçu ; (5) move → position serveur ±1 m. "
            "Scripts : smoke_godot_m11_login_lan.sh + smoke_godot_m12_ws_lan.sh (stubs OK). "
            "Coordination Hermès + Dédale."
        ),
        "context": {
            "handoff_m11_m12": True,
            "godot_supervisor": True,
            "docs": DOCS,
        },
    },
]


def main() -> int:
    dry = "--dry-run" in sys.argv
    only = ""
    for arg in sys.argv[1:]:
        if arg.startswith("--only="):
            only = arg.split("=", 1)[1].strip().lower()

    tasks = TASKS
    if only:
        keys = {k.strip() for k in only.split(",") if k.strip()}
        tasks = [
            t
            for t in TASKS
            if t["role"] in keys or (t.get("context") or {}).get("godot_dev_track", "") in keys
        ]

    if dry:
        for t in tasks:
            track = (t.get("context") or {}).get("godot_dev_track", "")
            label = f"{t['role']}" + (f" [{track}]" if track else "")
            print(f"[dry-run] {label}: {t['objective'][:100]}…")
        print(f"OK dry-run — {len(tasks)} tâche(s)")
        return 0

    from lbg_agents.team_job_spawn import create_and_run_team_task, task_run_summary

    orch = os.environ.get("LBG_ORCHESTRATOR_URL", "http://127.0.0.1:8010")
    print(f"Spawn M11+M12 → {orch}")
    results: list[dict] = []
    for t in tasks:
        role = t["role"]
        track = (t.get("context") or {}).get("godot_dev_track", "")
        print(f"=== {role}{' / ' + track if track else ''} ===")
        try:
            payload = create_and_run_team_task(
                role=role,
                objective=t["objective"],
                actor_id=ACTOR,
                context=t.get("context") or {},
            )
            summary = task_run_summary(payload)
            summary["role"] = role
            summary["track"] = track
            results.append(summary)
            print(f"  task_id={summary.get('task_id')} status={summary.get('task_status')} ok={summary.get('task_ok')}")
        except Exception as exc:
            print(f"  FAIL: {exc}", file=sys.stderr)
            results.append({"role": role, "track": track, "error": str(exc), "ok": False})

    out = {
        "ok": all(r.get("task_ok") is not False for r in results if "error" not in r),
        "tasks": results,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
