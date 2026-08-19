"""Helpers import_face_parts — partagés worker Windows / exécuteur Python."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _truthy(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _cfg(get_cfg, key: str) -> str:
    v = str(get_cfg(key) or "").strip()
    if v:
        return v
    alt = key.replace("LBG_DESKTOP_", "LBG_LINUX_", 1)
    if alt != key:
        return str(get_cfg(alt) or "").strip()
    return ""


def face_parts_enabled(get_cfg) -> bool:
    return _truthy(_cfg(get_cfg, "LBG_DESKTOP_FACE_PARTS_ENABLED"))


def _configured_inbox(get_cfg) -> str:
    return _cfg(get_cfg, "LBG_DESKTOP_FACE_PARTS_INBOX")


def resolve_inbox(action: dict[str, Any], get_cfg) -> Path | None:
    raw = action.get("inbox")
    if isinstance(raw, str) and raw.strip():
        return Path(raw.strip())
    cfg = _configured_inbox(get_cfg)
    if cfg:
        return Path(cfg)
    return None


def inbox_is_allowed(inbox: Path, get_cfg) -> bool:
    roots: list[Path] = []
    cfg = _configured_inbox(get_cfg)
    if cfg:
        roots.append(Path(cfg).expanduser().resolve())
    extra = _cfg(get_cfg, "LBG_DESKTOP_FILE_ALLOWLIST_DIRS")
    if extra:
        for part in extra.split(","):
            p = part.strip()
            if p:
                roots.append(Path(p).expanduser().resolve())
    try:
        target = inbox.expanduser().resolve()
    except Exception:
        return False
    if not roots:
        return True
    for root in roots:
        try:
            target.relative_to(root)
            return True
        except ValueError:
            if target == root:
                return True
    return False


def discover_script(get_cfg) -> Path | None:
    raw = _cfg(get_cfg, "LBG_DESKTOP_FACE_PARTS_SCRIPT")
    if raw:
        p = Path(raw).expanduser()
        return p if p.is_file() else None
    here = Path(__file__).resolve()
    projects = None
    for p in here.parents:
        if (p / "Infographiste_IA" / "scripts" / "import_face_parts.py").is_file():
            projects = p
            break
        if p.name == "LBG_Studios" and (p.parent / "Infographiste_IA" / "scripts" / "import_face_parts.py").is_file():
            projects = p.parent
            break
    cands = [
        Path("/home/sdesh/projects/Infographiste_IA/scripts/import_face_parts.py"),
        Path("C:/Users/sdesh/projects/Infographiste_IA/scripts/import_face_parts.py"),
    ]
    if projects is not None:
        cands.insert(0, projects / "Infographiste_IA" / "scripts" / "import_face_parts.py")
    for cand in cands:
        if cand.is_file():
            return cand
    return None


def discover_python(get_cfg, script: Path | None) -> str:
    raw = _cfg(get_cfg, "LBG_DESKTOP_FACE_PARTS_PYTHON")
    if raw:
        return raw
    if script is not None:
        venv_unix = script.parents[1] / ".venv" / "bin" / "python"
        venv_win = script.parents[1] / ".venv" / "Scripts" / "python.exe"
        if venv_unix.is_file():
            return str(venv_unix)
        if venv_win.is_file():
            return str(venv_win)
    return sys.executable


def run_import_face_parts(
    *,
    action: dict[str, Any],
    get_cfg,
    dry_run: bool,
) -> dict[str, Any]:
    if not face_parts_enabled(get_cfg):
        return {
            "ok": False,
            "outcome": "feature_disabled",
            "error": "import_face_parts désactivé (LBG_DESKTOP_FACE_PARTS_ENABLED=0)",
            "hint": "Activer LBG_DESKTOP_FACE_PARTS_ENABLED=1 dans desktop.env / linux.env",
        }
    inbox = resolve_inbox(action, get_cfg)
    if inbox is None:
        return {
            "ok": False,
            "outcome": "bad_request",
            "error": "Champ `inbox` ou LBG_DESKTOP_FACE_PARTS_INBOX requis",
        }
    if not inbox_is_allowed(inbox, get_cfg):
        return {
            "ok": False,
            "outcome": "allowlist_denied",
            "error": "inbox hors allowlist FACE_PARTS_INBOX / FILE_ALLOWLIST_DIRS",
            "inbox": str(inbox),
        }
    character_id = str(action.get("character_id") or "lyra_assistant").strip() or "lyra_assistant"
    deploy = action.get("deploy") is True
    script = discover_script(get_cfg)
    if script is None:
        return {
            "ok": False,
            "outcome": "error",
            "error": "script import_face_parts.py introuvable",
            "inbox": str(inbox),
        }
    py = discover_python(get_cfg, script)
    cmd = [py, str(script), "--inbox", str(inbox), "--character-id", character_id]
    if dry_run:
        cmd.append("--dry-run")
    if deploy and not dry_run:
        cmd.append("--deploy")
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except Exception as exc:
        return {
            "ok": False,
            "outcome": "error",
            "error": f"{type(exc).__name__}: {exc}",
            "inbox": str(inbox),
        }
    payload: dict[str, Any] = {
        "inbox": str(inbox),
        "character_id": character_id,
        "script": str(script),
        "returncode": proc.returncode,
    }
    stdout = (proc.stdout or "").strip()
    try:
        parsed = json.loads(stdout) if stdout.startswith("{") else None
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        payload.update(parsed)
    else:
        payload["stdout_preview"] = stdout[:800]
        payload["stderr_preview"] = (proc.stderr or "")[:400]
    ok = proc.returncode == 0 and bool(payload.get("ok", True))
    payload["ok"] = ok
    payload["outcome"] = "dry_run" if dry_run and ok else ("ok" if ok else "error")
    if not ok and "error" not in payload:
        payload["error"] = (proc.stderr or stdout or "import_face_parts failed")[:400]
    return payload
