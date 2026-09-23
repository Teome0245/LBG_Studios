"""Audit readiness lbg-ws/2 (schémas, gateway, spec) — sans réseau obligatoire."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ensure_repo_lbg_gateway_package() -> None:
    """Expose services/lbg_gateway du dépôt même si orchestrator/services occupe ``services``."""
    import sys

    root = _repo_root()
    gateway_dir = root / "services" / "lbg_gateway"
    if not gateway_dir.is_dir():
        raise ImportError(f"missing gateway package dir: {gateway_dir}")

    pkg_name = "services.lbg_gateway"
    existing = sys.modules.get(pkg_name)
    if existing is not None:
        paths = [str(p) for p in getattr(existing, "__path__", [])]
        if str(gateway_dir) in paths:
            return

    pkg = type(sys)(pkg_name)
    pkg.__path__ = [str(gateway_dir)]  # type: ignore[attr-defined]
    pkg.__package__ = pkg_name
    sys.modules[pkg_name] = pkg

    svc = sys.modules.get("services")
    if svc is not None:
        setattr(svc, "lbg_gateway", pkg)
        return

    svc_root = root / "services"
    svc_pkg = type(sys)("services")
    svc_pkg.__path__ = [str(svc_root)]  # type: ignore[attr-defined]
    svc_pkg.__package__ = "services"
    setattr(svc_pkg, "lbg_gateway", pkg)
    sys.modules["services"] = svc_pkg


def _new_mmo_root() -> Path:
    raw = os.environ.get("LBG_NEW_MMO_ROOT", "").strip()
    if raw:
        return Path(raw)
    for candidate in (Path("/opt/new_mmo"), Path("/home/sdesh/projects/new_mmo")):
        if candidate.is_dir():
            return candidate
    return Path("/home/sdesh/projects/new_mmo")


def _zb0_header_paths() -> list[Path]:
    root = _new_mmo_root()
    return [
        root / "lbg-mmo/server-core3/server/lbg/LbgZoneBridge.h",
        root / "lbg-mmo/server-core3/server/lbg/LbgZoneBridge.cpp",
        root / "lbg-mmo/server-core3/server/lbg/LbgZoneBridgeReadOnly.cpp",
        root / "lbg-mmo/server-core3/server/lbg/LbgZoneBridgeTickTask.h",
        root / "lbg-mmo/server-core3/server/lbg/LbgZoneBridgeInit.cpp",
    ]


def audit_zb0_readiness() -> dict[str, Any]:
    """Audit ZB-0 — header LbgZoneBridge + spec (sans build C++ obligatoire)."""
    root = _repo_root()
    gaps: list[str] = []
    checks: dict[str, Any] = {}

    spec = root / "docs/core3_zone_bridge_spec.md"
    checks["spec_zone_bridge"] = spec.is_file()

    header_paths = _zb0_header_paths()
    for i, hp in enumerate(header_paths):
        checks[f"zb0_file_{i}"] = hp.is_file()
    checks["zb0_header"] = header_paths[0].is_file() if header_paths else False
    checks["zb0_impl"] = header_paths[1].is_file() if len(header_paths) > 1 else False
    checks["zb0_readonly_impl"] = header_paths[2].is_file() if len(header_paths) > 2 else False
    checks["zb0_tick_task"] = header_paths[3].is_file() if len(header_paths) > 3 else False
    checks["zb0_init"] = header_paths[4].is_file() if len(header_paths) > 4 else False

    cmake = _new_mmo_root() / "lbg-mmo/server-core3/CMakeLists.txt"
    checks["cmake_lbg_sources"] = False
    if cmake.is_file():
        cmake_text = cmake.read_text(encoding="utf-8", errors="ignore")
        checks["cmake_lbg_sources"] = "server/lbg/*.cpp" in cmake_text

    if not checks["spec_zone_bridge"]:
        gaps.append("spec core3_zone_bridge_spec.md manquante")
    if not checks.get("zb0_header"):
        gaps.append("LbgZoneBridge.h absent (ZB-0)")
    if checks.get("zb0_header") and not checks.get("zb0_impl"):
        gaps.append("LbgZoneBridge.cpp absent (ZB-0 squelette)")
    if checks.get("zb0_header") and not checks.get("zb0_readonly_impl"):
        gaps.append("LbgZoneBridgeReadOnly.cpp absent (ZB-0 lecture seule)")
    if checks.get("zb0_header") and not checks.get("zb0_tick_task"):
        gaps.append("LbgZoneBridgeTickTask absent (ZB-0 tick 20 Hz)")
    if checks.get("zb0_header") and not checks.get("cmake_lbg_sources"):
        gaps.append("CMakeLists.txt sans server/lbg/*.cpp")

    zone_server = _new_mmo_root() / "lbg-mmo/server-core3/server/zone/ZoneServerImplementation.cpp"
    checks["zone_server_impl_path"] = zone_server.is_file()
    if zone_server.is_file():
        text = zone_server.read_text(encoding="utf-8", errors="ignore")
        checks["zone_server_zb_hook"] = "startZoneBridgeTick" in text
        if not checks["zone_server_zb_hook"]:
            gaps.append("hook ZoneServer startManagers sans startZoneBridgeTick (ZB-0)")

    hook_ok = bool(checks.get("zone_server_zb_hook"))
    files_ok = bool(checks.get("zb0_header")) and bool(checks.get("zb0_readonly_impl")) and bool(
        checks.get("zb0_tick_task")
    )
    ok = bool(checks.get("spec_zone_bridge")) and files_ok and hook_ok and bool(checks.get("cmake_lbg_sources"))

    next_actions: list[str] = []
    if not checks.get("zb0_header"):
        next_actions.append("Créer server/lbg/LbgZoneBridge.h (interface lecture seule)")
    elif not hook_ok:
        next_actions.append("Hook startZoneBridgeTick dans ZoneServerImplementation::startManagers")
    elif not checks.get("cmake_lbg_sources"):
        next_actions.append("Ajouter server/lbg/*.cpp au CMakeLists server-core3")
    elif ok:
        next_actions.append("Compiler Core3 (Vulcan) puis ZB-1 : export JSON/SHM 20 Hz vers lbg_gateway")
    else:
        next_actions.append("Compléter LbgZoneBridgeReadOnly + LbgZoneBridgeTickTask (ZB-0)")

    return {
        "track": "zb0_readiness",
        "ok": ok,
        "checks": checks,
        "gaps": gaps,
        "next_actions": next_actions[:4],
        "new_mmo_root": str(_new_mmo_root()),
    }


def _probe_zone_bridge_feed_ssh(host: str) -> dict[str, Any]:
    """Sonde feed ZB-1 sur Prime via SSH (orchestrateur 140 → VM 246)."""
    import json
    import subprocess

    user = os.environ.get("LBG_ZONE_BRIDGE_PROBE_USER", "lbg").strip()
    json_path = os.environ.get(
        "LBG_ZONE_BRIDGE_JSON_PATH",
        "/opt/lbg-new-mmo-clean/MMOCoreORB/bin/ia_bridge/zone_bridge_live.json",
    )
    checks: dict[str, Any] = {"json_path": json_path, "remote": True, "live_enabled": True}
    try:
        stat_proc = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", f"{user}@{host}", "stat", "-c", "%Y", json_path],
            capture_output=True,
            text=True,
            timeout=12.0,
        )
        if stat_proc.returncode == 0 and stat_proc.stdout.strip().isdigit():
            checks["mtime_age_s"] = round(time.time() - float(stat_proc.stdout.strip()), 3)
            checks["file_exists"] = True
        else:
            checks["file_exists"] = False
    except (OSError, subprocess.TimeoutExpired, ValueError):
        checks["file_exists"] = False

    # Lecture stable côté remote : fichier réécrit ~20 Hz (tmp+rename).
    # Un `cat` SSH unique tombe souvent sur une frame déchirée (UTF-8/JSON KO).
    remote_src = (
        "import json, pathlib, time\n"
        f"p = pathlib.Path({json_path!r})\n"
        "data = None\n"
        "for _ in range(40):\n"
        "    raw = p.read_bytes()\n"
        "    if not raw:\n"
        "        time.sleep(0.02)\n"
        "        continue\n"
        "    parsed = None\n"
        "    for enc in ('utf-8', 'latin-1'):\n"
        "        try:\n"
        "            parsed = json.loads(raw.decode(enc))\n"
        "            break\n"
        "        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):\n"
        "            parsed = None\n"
        "    if isinstance(parsed, dict) and parsed.get('type') == 'zone_state':\n"
        "        data = parsed\n"
        "        break\n"
        "    time.sleep(0.02)\n"
        "print(json.dumps(data if isinstance(data, dict) else {}))\n"
    )
    data: dict[str, Any] | None = None
    try:
        proc = subprocess.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=8",
                f"{user}@{host}",
                "python3",
                "-",
            ],
            input=remote_src,
            capture_output=True,
            text=True,
            timeout=20.0,
        )
        if proc.returncode == 0 and (proc.stdout or "").strip():
            parsed = json.loads(proc.stdout.strip().splitlines()[-1])
            if isinstance(parsed, dict) and parsed:
                data = parsed
                checks["read_mode"] = "stable_remote"
        elif proc.returncode != 0:
            checks["read_stderr_tail"] = (proc.stderr or "")[-180:]
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError) as exc:
        checks["read_error"] = str(exc)[:160]

    ok = isinstance(data, dict) and data.get("type") == "zone_state"
    if isinstance(data, dict):
        checks["tick"] = data.get("tick")
        checks["zone"] = data.get("zone")
        checks["entity_count"] = len(data.get("entities") or [])
    if ok:
        return {"track": "zb1_live_feed", "ok": True, "checks": checks}
    return {
        "track": "zb1_live_feed",
        "ok": False,
        "checks": checks,
        "gaps": ["feed live JSON absent ou illisible sur Prime (SSH)"],
    }


def _zb1_export_paths() -> list[Path]:
    root = _new_mmo_root()
    return [
        root / "lbg-mmo/server-core3/server/lbg/LbgZoneBridgeJsonExport.h",
        root / "lbg-mmo/server-core3/server/lbg/LbgZoneBridgeJsonExport.cpp",
    ]


def audit_zb1_readiness(*, probe_live_feed: bool = True) -> dict[str, Any]:
    """Audit ZB-1 — export JSON C++ + module gateway live."""
    gaps: list[str] = []
    checks: dict[str, Any] = {}
    zb0 = audit_zb0_readiness()
    checks["zb0_ok"] = bool(zb0.get("ok"))

    export_paths = _zb1_export_paths()
    checks["zb1_json_export_h"] = export_paths[0].is_file()
    checks["zb1_json_export_cpp"] = export_paths[1].is_file() if len(export_paths) > 1 else False

    tick_task = _new_mmo_root() / "lbg-mmo/server-core3/server/lbg/LbgZoneBridgeTickTask.h"
    if tick_task.is_file():
        tt = tick_task.read_text(encoding="utf-8", errors="ignore")
        checks["zb1_tick_publishes_json"] = "publishZoneBridgeJson" in tt
    else:
        checks["zb1_tick_publishes_json"] = False

    gw_feed = _repo_root() / "services/lbg_gateway/zone_bridge_feed.py"
    checks["gateway_zone_bridge_feed"] = gw_feed.is_file()

    if not checks.get("zb1_json_export_cpp"):
        gaps.append("LbgZoneBridgeJsonExport.cpp absent (ZB-1)")
    if not checks.get("zb1_tick_publishes_json"):
        gaps.append("LbgZoneBridgeTickTask n'appelle pas publishZoneBridgeJson")
    if not checks.get("gateway_zone_bridge_feed"):
        gaps.append("services/lbg_gateway/zone_bridge_feed.py absent")

    live_probe: dict[str, Any] | None = None
    if probe_live_feed:
        remote_host = os.environ.get("LBG_ZONE_BRIDGE_PROBE_HOST", "").strip()
        if not remote_host:
            # Sur orchestrateur .140 le JSON vit sur Prime — sonder via SSH par défaut
            remote_host = (
                os.environ.get("LBG_LAN_HOST_CORE3_PRIME", "").strip()
                or os.environ.get("LBG_LAN_HOST_MMO", "").strip()
                or "192.168.0.246"
            )
        if remote_host in ("0", "local", "none", "off"):
            remote_host = ""
        if remote_host:
            live_probe = _probe_zone_bridge_feed_ssh(remote_host)
            checks["live_feed_ok"] = bool(live_probe.get("ok"))
            checks["live_probe_host"] = remote_host
            if not live_probe.get("ok"):
                gaps.extend(live_probe.get("gaps") or ["feed live JSON absent sur Prime (SSH)"])
        elif checks.get("gateway_zone_bridge_feed"):
            try:
                _ensure_repo_lbg_gateway_package()
                from services.lbg_gateway.zone_bridge_feed import probe_zone_bridge_feed

                live_probe = probe_zone_bridge_feed()
                checks["live_feed_ok"] = bool(live_probe.get("ok"))
                if not live_probe.get("ok"):
                    gaps.append("feed live JSON absent ou périmé (compile + Prime requis)")
            except ImportError as e:
                checks["live_feed_ok"] = False
                gaps.append(f"import zone_bridge_feed: {e}")

    code_ok = bool(checks.get("zb1_json_export_cpp")) and bool(checks.get("zb1_tick_publishes_json"))
    code_ok = code_ok and bool(checks.get("gateway_zone_bridge_feed"))
    ok = bool(checks.get("zb0_ok")) and code_ok
    if probe_live_feed:
        if live_probe is not None:
            ok = ok and bool(live_probe.get("ok"))
            checks["runtime_feed"] = live_probe.get("checks")
        elif checks.get("live_feed_ok") is False:
            ok = False

    next_actions: list[str] = []
    if not checks.get("zb0_ok"):
        next_actions.append("Finaliser ZB-0 avant ZB-1")
    elif not code_ok:
        next_actions.append("Implémenter LbgZoneBridgeJsonExport + zone_bridge_feed gateway")
    elif live_probe and not live_probe.get("ok"):
        next_actions.append("Compiler Core3 (Vulcan) et redémarrer Prime — feed JSON 20 Hz")
    else:
        next_actions.append("ZB-2 : injection move validé depuis gateway")

    return {
        "track": "zb1_readiness",
        "ok": ok,
        "code_ok": code_ok,
        "checks": checks,
        "gaps": gaps,
        "live_probe": live_probe,
        "next_actions": next_actions[:4],
        "zb0": zb0,
    }


def _zb2_inject_paths() -> list[Path]:
    root = _new_mmo_root()
    return [
        root / "lbg-mmo/server-core3/server/lbg/LbgZoneBridgeInject.h",
        root / "lbg-mmo/server-core3/server/lbg/LbgZoneBridgeInject.cpp",
    ]


def _probe_zb2_runtime_ssh(host: str) -> dict[str, Any]:
    """Sonde runtime ZB-2 sur Prime : pending.jsonl + symbole inject + gateway inject on."""
    import subprocess

    user = os.environ.get("LBG_ZONE_BRIDGE_PROBE_USER", "lbg").strip()
    pending = os.environ.get(
        "LBG_GATEWAY_PENDING_FILE",
        "/opt/lbg-new-mmo-clean/MMOCoreORB/bin/ia_bridge/pending.jsonl",
    )
    checks: dict[str, Any] = {"remote": True, "host": host, "pending_path": pending}
    remote = f"{user}@{host}"
    ssh_base = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", remote]

    def _ssh(args: list[str], *, timeout: float = 25.0) -> tuple[int, str]:
        try:
            proc = subprocess.run(
                [*ssh_base, *args],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
        except (OSError, subprocess.TimeoutExpired) as exc:
            return 1, str(exc)

    rc, _ = _ssh(["test", "-f", pending])
    checks["pending_exists"] = rc == 0

    # Une seule commande remote (évite sh -c mangled via SSH argv)
    rc, out = _ssh(
        [
            f"grep -a -q pollPendingInjectMoves /opt/lbg-new-mmo-clean/MMOCoreORB/bin/core3-clean "
            f"|| grep -a -q pollPendingInjectMoves /opt/lbg-new-mmo-clean/MMOCoreORB/bin/core3"
        ],
        timeout=30.0,
    )
    checks["inject_symbol"] = rc == 0

    rc, out = _ssh(["test", "-f", "/home/lbg/lbg-gateway/pending_bridge.py"])
    checks["gateway_pending_bridge"] = rc == 0

    rc, out = _ssh(["systemctl", "is-active", "lbg-gateway"])
    checks["gateway_active"] = "active" in out

    rc, out = _ssh(
        ["grep", "-E", "^LBG_GATEWAY_INJECT_MOVE=", "/home/lbg/lbg-gateway/gateway.env"]
    )
    inject_line = ""
    for line in out.splitlines():
        if "LBG_GATEWAY_INJECT_MOVE=" in line:
            inject_line = line.split("=", 1)[-1].strip().strip('"').strip("'")
    checks["inject_move_env"] = inject_line
    checks["inject_enabled"] = inject_line.lower() in ("1", "true", "yes", "on")

    gaps: list[str] = []
    if not checks.get("pending_exists"):
        gaps.append("pending.jsonl absent sur Prime")
    if not checks.get("inject_symbol"):
        gaps.append("symbole pollPendingInjectMoves absent du binaire Core3")
    if not checks.get("inject_enabled"):
        gaps.append("LBG_GATEWAY_INJECT_MOVE off sur gateway Prime")
    if not checks.get("gateway_pending_bridge"):
        gaps.append("pending_bridge.py absent sur gateway Prime")
    ok = len(gaps) == 0
    return {"track": "zb2_runtime", "ok": ok, "checks": checks, "gaps": gaps}


def audit_zb2_readiness(*, probe_runtime: bool = True) -> dict[str, Any]:
    """Audit ZB-2 — Inject C++ + pending_bridge gateway + runtime Prime optionnel."""
    gaps: list[str] = []
    checks: dict[str, Any] = {}
    zb1 = audit_zb1_readiness(probe_live_feed=False)
    checks["zb1_code_ok"] = bool(zb1.get("code_ok"))

    inject_paths = _zb2_inject_paths()
    checks["zb2_inject_h"] = inject_paths[0].is_file()
    checks["zb2_inject_cpp"] = inject_paths[1].is_file() if len(inject_paths) > 1 else False

    tick_task = _new_mmo_root() / "lbg-mmo/server-core3/server/lbg/LbgZoneBridgeTickTask.h"
    if tick_task.is_file():
        tt = tick_task.read_text(encoding="utf-8", errors="ignore")
        checks["zb2_tick_polls_inject"] = "pollPendingInjectMoves" in tt
    else:
        checks["zb2_tick_polls_inject"] = False

    pending_mod = _repo_root() / "services/lbg_gateway/pending_bridge.py"
    checks["gateway_pending_bridge"] = pending_mod.is_file()
    if pending_mod.is_file():
        text = pending_mod.read_text(encoding="utf-8", errors="ignore")
        checks["pending_inject_move_to"] = "def inject_move_to" in text
        checks["pending_inject_enabled"] = "def inject_enabled" in text
    else:
        checks["pending_inject_move_to"] = False
        checks["pending_inject_enabled"] = False

    if not checks.get("zb2_inject_cpp"):
        gaps.append("LbgZoneBridgeInject.cpp absent (ZB-2)")
    if not checks.get("zb2_tick_polls_inject"):
        gaps.append("LbgZoneBridgeTickTask n'appelle pas pollPendingInjectMoves")
    if not checks.get("gateway_pending_bridge"):
        gaps.append("services/lbg_gateway/pending_bridge.py manquant")

    runtime: dict[str, Any] | None = None
    if probe_runtime:
        remote_host = (
            os.environ.get("LBG_ZONE_BRIDGE_PROBE_HOST", "").strip()
            or os.environ.get("LBG_LAN_HOST_CORE3_PRIME", "").strip()
            or os.environ.get("LBG_LAN_HOST_MMO", "").strip()
            or "192.168.0.246"
        )
        if remote_host not in ("0", "local", "none", "off"):
            runtime = _probe_zb2_runtime_ssh(remote_host)
            checks["runtime_ok"] = bool(runtime.get("ok"))
            if not runtime.get("ok"):
                gaps.extend(runtime.get("gaps") or ["runtime ZB-2 KO sur Prime"])
        else:
            checks["runtime_ok"] = None

    code_ok = (
        bool(checks.get("zb2_inject_cpp"))
        and bool(checks.get("zb2_tick_polls_inject"))
        and bool(checks.get("gateway_pending_bridge"))
        and bool(checks.get("pending_inject_move_to"))
    )
    ok = bool(checks.get("zb1_code_ok")) and code_ok
    if probe_runtime and runtime is not None:
        ok = ok and bool(runtime.get("ok"))
        checks["runtime"] = runtime.get("checks")

    next_actions: list[str] = []
    if not checks.get("zb1_code_ok"):
        next_actions.append("Finaliser ZB-1 avant ZB-2")
    elif not code_ok:
        next_actions.append("Porter pending_bridge + LbgZoneBridgeInject (pollPendingInjectMoves)")
    elif runtime and not runtime.get("ok"):
        next_actions.append("Activer LBG_GATEWAY_INJECT_MOVE=1 et rebuild Core3 avec Inject")
    else:
        next_actions.append("ZB-3 : session policy / move indoor (cell) si besoin")

    return {
        "track": "zb2_readiness",
        "ok": ok,
        "code_ok": code_ok,
        "checks": checks,
        "gaps": gaps,
        "runtime_probe": runtime,
        "next_actions": next_actions[:4],
        "zb1": {"code_ok": zb1.get("code_ok"), "ok": zb1.get("ok")},
    }


def audit_lbg_ws2_readiness() -> dict[str, Any]:
    root = _repo_root()
    gaps: list[str] = []
    checks: dict[str, Any] = {}

    schema_zone = root / "docs/schemas/lbg-ws/server.zone_state_v2.schema.json"
    schema_cmd = root / "docs/schemas/lbg-ws/client.zone_command_v2.schema.json"
    spec = root / "docs/core3_zone_bridge_spec.md"
    gateway_main = root / "services/lbg_gateway/main.py"
    ws2_mod = root / "services/lbg_gateway/lbg_ws2.py"

    checks["schema_zone_state_v2"] = schema_zone.is_file()
    checks["schema_zone_command_v2"] = schema_cmd.is_file()
    checks["spec_zone_bridge"] = spec.is_file()
    checks["gateway_main"] = gateway_main.is_file()
    checks["lbg_ws2_module"] = ws2_mod.is_file()

    if not checks["schema_zone_state_v2"]:
        gaps.append("schéma server.zone_state_v2 manquant")
    if not checks["lbg_ws2_module"]:
        gaps.append("module services/lbg_gateway/lbg_ws2.py manquant")
    else:
        try:
            _ensure_repo_lbg_gateway_package()
            from services.lbg_gateway.lbg_ws2 import build_zone_state_v2, supported_protos

            sample = build_zone_state_v2(
                zone="tatooine",
                tick=1,
                entities=[{"id": "player:Teome", "kind": "player", "name": "Teome", "pos": [0.0, 0.0, 0.0]}],
                your_character_id=1,
            )
            checks["sample_zone_state_v2"] = sample.get("proto") == "lbg-ws/2"
            checks["supported_protos"] = supported_protos()
            if not checks["sample_zone_state_v2"]:
                gaps.append("build_zone_state_v2 ne produit pas proto lbg-ws/2")
        except Exception as e:
            checks["lbg_ws2_import_error"] = str(e)
            gaps.append(f"import lbg_ws2: {e}")

    preview_on = os.environ.get("LBG_GATEWAY_WS2_PREVIEW", "1").strip().lower() in ("1", "true", "yes", "on")
    checks["ws2_preview_env"] = preview_on
    if gateway_main.is_file():
        text = gateway_main.read_text(encoding="utf-8", errors="ignore")
        checks["gateway_ws2_handler"] = "lbg-ws/2" in text or "lbg_ws2" in text
        if not checks["gateway_ws2_handler"]:
            gaps.append("gateway main.py sans branche lbg-ws/2")

    readiness_score = sum(1 for k, v in checks.items() if v is True) / max(len(checks), 1)
    ok = len(gaps) == 0

    return {
        "track": "lbg_ws2_readiness",
        "ok": ok,
        "readiness_score": round(readiness_score, 2),
        "checks": checks,
        "gaps": gaps,
        "next_actions": _suggest_next_actions(gaps),
    }


def _suggest_next_actions(gaps: list[str]) -> list[str]:
    actions: list[str] = []
    if any("gateway" in g for g in gaps):
        actions.append("Étendre lbg_gateway pour négocier proto lbg-ws/2 (preview lecture snapshots)")
    if any("lbg_ws2" in g or "schéma" in g for g in gaps):
        actions.append("Compléter schémas JSON et module lbg_ws2.py")
    if not actions:
        actions.append("Implémenter LbgZoneBridge C++ ZB-0 (hook ZoneServer lecture seule)")
    return actions[:4]
