"""Cycle de vie ComfyUI — probe / ensure / restart depuis Agent_IA Windows."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse


def _truthy(raw: str) -> bool:
    return (raw or "").strip().lower() in {"1", "true", "yes", "on"}


def comfyui_port(get_cfg: Callable[[str], str]) -> int:
    raw = (get_cfg("LBG_COMFYUI_PORT") or "").strip()
    if raw.isdigit():
        return int(raw)
    url = (get_cfg("LBG_COMFYUI_BASE_URL") or "").strip() or "http://127.0.0.1:8188"
    parsed = urlparse(url)
    return int(parsed.port or 8188)


def comfyui_root(get_cfg: Callable[[str], str]) -> Path:
    raw = (get_cfg("LBG_COMFYUI_ROOT") or "").strip()
    if raw:
        return Path(raw)
    return Path(r"C:\Users\sdesh\ComfyUI")


def comfyui_python(get_cfg: Callable[[str], str], root: Path) -> Path:
    raw = (get_cfg("LBG_COMFYUI_PYTHON") or "").strip()
    if raw:
        return Path(raw)
    return root / "venv" / "Scripts" / "python.exe"


def comfyui_args(get_cfg: Callable[[str], str]) -> list[str]:
    raw = (get_cfg("LBG_COMFYUI_ARGS") or "").strip()
    if raw:
        return raw.split()
    return ["--listen", "0.0.0.0", "--port", "8188", "--lowvram"]


def probe_comfyui(base_url: str, *, timeout_s: float = 2.0) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/system_stats"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read()
            data: Any = None
            if body:
                try:
                    data = json.loads(body.decode("utf-8"))
                except json.JSONDecodeError:
                    data = None
            return {
                "ok": 200 <= getattr(resp, "status", 200) < 300,
                "url": url,
                "status_code": getattr(resp, "status", 200),
                "stats": data if isinstance(data, dict) else None,
            }
    except Exception as exc:
        return {"ok": False, "url": url, "error": f"{type(exc).__name__}: {exc}"}


def pids_listening(port: int) -> list[int]:
    if os.name != "nt":
        return _pids_listening_posix(port)
    try:
        proc = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                (
                    f"(Get-NetTCPConnection -LocalPort {int(port)} -State Listen "
                    "-ErrorAction SilentlyContinue).OwningProcess | Sort-Object -Unique"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    pids: list[int] = []
    for line in (proc.stdout or "").splitlines():
        s = line.strip()
        if s.isdigit():
            pid = int(s)
            if pid > 0:
                pids.append(pid)
    return sorted(set(pids))


def _pids_listening_posix(port: int) -> list[int]:
    pids: list[int] = []
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=0.3):
            pass
    except OSError:
        return []
    return pids


def stop_comfyui(port: int) -> dict[str, Any]:
    pids = pids_listening(port)
    killed: list[int] = []
    errors: list[str] = []
    for pid in pids:
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid), "/T"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
            else:
                os.kill(pid, 15)
            killed.append(pid)
        except Exception as exc:
            errors.append(f"pid {pid}: {type(exc).__name__}: {exc}")
    time.sleep(1.2)
    still = pids_listening(port)
    return {
        "killed": killed,
        "still_listening": still,
        "ok": not still,
        "errors": errors,
    }


def start_comfyui(get_cfg: Callable[[str], str]) -> dict[str, Any]:
    root = comfyui_root(get_cfg)
    py = comfyui_python(get_cfg, root)
    args = comfyui_args(get_cfg)
    if not root.is_dir():
        return {"ok": False, "error": f"LBG_COMFYUI_ROOT introuvable: {root}"}
    if not py.is_file():
        return {"ok": False, "error": f"Python ComfyUI introuvable: {py}"}
    log_dir = Path(r"C:\Agent_IA\logs")
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        log_dir = root
    log_path = log_dir / "comfyui_agent.log"
    cmd = [str(py), "main.py", *args]

    if os.name == "nt":
        ps1 = Path(r"C:\Agent_IA\start_comfyui.ps1")
        if ps1.is_file():
            return _start_comfyui_hidden_ps1(ps1, log_path, cmd=cmd, cwd=str(root))
        py_q = f'"{py}"' if " " in str(py) else str(py)
        args_s = " ".join(args)
        cmd_line = f"{py_q} main.py {args_s} >> \"{log_path}\" 2>&1"
        popen_kw: dict[str, Any] = {
            "cwd": str(root),
            "creationflags": subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
        }
        try:
            proc = subprocess.Popen(["cmd.exe", "/c", cmd_line], **popen_kw)
        except OSError as exc:
            return {"ok": False, "error": f"Popen failed: {exc}", "cmd": cmd, "cwd": str(root)}
        return {
            "ok": True,
            "pid": proc.pid,
            "cmd": cmd,
            "cwd": str(root),
            "log": str(log_path),
            "mode": "hidden",
        }

    log_fh = open(log_path, "a", encoding="utf-8", errors="replace")
    popen_kw = {
        "cwd": str(root),
        "stdout": log_fh,
        "stderr": subprocess.STDOUT,
    }
    try:
        proc = subprocess.Popen(cmd, **popen_kw)
    except OSError as exc:
        log_fh.close()
        return {"ok": False, "error": f"Popen failed: {exc}", "cmd": cmd, "cwd": str(root)}
    return {
        "ok": True,
        "pid": proc.pid,
        "cmd": cmd,
        "cwd": str(root),
        "log": str(log_path),
    }


def _start_comfyui_hidden_ps1(
    ps1: Path,
    log_path: Path,
    *,
    cmd: list[str],
    cwd: str,
) -> dict[str, Any]:
    """Lance start_comfyui.ps1 sans fenetre (meme pattern que start_agent.ps1)."""
    try:
        with open(log_path, "a", encoding="utf-8", errors="replace") as log_fh:
            log_fh.write(f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] invoke {ps1}\n")
            proc = subprocess.Popen(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-WindowStyle",
                    "Hidden",
                    "-File",
                    str(ps1),
                ],
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
            )
    except OSError as exc:
        return {"ok": False, "error": f"start_comfyui.ps1 failed: {exc}", "cmd": cmd, "cwd": cwd}
    return {
        "ok": True,
        "pid": proc.pid,
        "cmd": cmd,
        "cwd": cwd,
        "log": str(log_path),
        "mode": "hidden_ps1",
    }


def wait_until_up(base_url: str, *, timeout_s: float = 90.0) -> dict[str, Any]:
    deadline = time.time() + max(5.0, timeout_s)
    last: dict[str, Any] = {"ok": False}
    while time.time() < deadline:
        last = probe_comfyui(base_url, timeout_s=1.5)
        if last.get("ok"):
            return last
        time.sleep(1.5)
    return last


def run_comfyui_lifecycle(
    *,
    kind: str,
    get_cfg: Callable[[str], str],
    base_url: str,
    dry_run: bool,
) -> dict[str, Any]:
    port = comfyui_port(get_cfg)
    root = comfyui_root(get_cfg)
    probe = probe_comfyui(base_url)
    out: dict[str, Any] = {
        "kind": kind,
        "port": port,
        "root": str(root),
        "python": str(comfyui_python(get_cfg, root)),
        "args": comfyui_args(get_cfg),
        "probe": probe,
    }
    if kind == "comfyui_status":
        out["ok"] = True
        out["outcome"] = "ok" if probe.get("ok") else "down"
        out["running"] = bool(probe.get("ok"))
        return out

    if dry_run:
        out["ok"] = True
        out["outcome"] = "dry_run"
        out["would"] = "restart" if kind == "comfyui_restart" else ("noop" if probe.get("ok") else "start")
        return out

    start_timeout = 90.0
    raw_to = (get_cfg("LBG_COMFYUI_START_TIMEOUT_S") or "").strip()
    if raw_to:
        try:
            start_timeout = max(10.0, min(180.0, float(raw_to)))
        except ValueError:
            pass

    if kind == "comfyui_ensure" and probe.get("ok"):
        out["ok"] = True
        out["outcome"] = "already_running"
        out["running"] = True
        return out

    if kind == "comfyui_restart" or (kind == "comfyui_ensure" and not probe.get("ok")):
        if kind == "comfyui_restart" and (probe.get("ok") or pids_listening(port)):
            stopped = stop_comfyui(port)
            out["stop"] = stopped
            if not stopped.get("ok"):
                out["ok"] = False
                out["outcome"] = "error"
                out["error"] = (
                    "Impossible d'arrêter ComfyUI sur :"
                    + str(port)
                    + " (accès refusé ? lancer ComfyUI avec le même utilisateur que Agent_IA)."
                )
                return out
        started = start_comfyui(get_cfg)
        out["start"] = {k: v for k, v in started.items() if k != "cmd"} | {"cmd": started.get("cmd")}
        if not started.get("ok"):
            out["ok"] = False
            out["outcome"] = "error"
            out["error"] = started.get("error")
            return out
        ready = wait_until_up(base_url, timeout_s=start_timeout)
        out["probe"] = ready
        out["running"] = bool(ready.get("ok"))
        out["ok"] = bool(ready.get("ok"))
        out["outcome"] = "ok" if ready.get("ok") else "starting"
        if not ready.get("ok"):
            out["error"] = f"ComfyUI lancé mais /system_stats pas prêt après {int(start_timeout)}s"
        return out

    out["ok"] = False
    out["outcome"] = "bad_request"
    out["error"] = f"kind inconnu: {kind}"
    return out
