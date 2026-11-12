"""Integration agent-desktop (Vercel Labs) pour Agent_IA.

Fournit le Computer Use sans capture d'écran via l'arbre d'accessibilité natif de l'OS
(Windows UI Automation, Linux AT-SPI, macOS AX).
Permet l'inspection, le clic et la saisie en tâche de fond (mode headless) sans bloquer
la souris physique ni monopoliser l'écran.

CLI sous-jacente : `agent-desktop` (installée via npm ou binaire GitHub).
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("agent_desktop")


def find_agent_desktop_bin() -> str | None:
    """Recherche le binaire ou script agent-desktop sur la machine."""
    # 1. Variable d'environnement explicite
    custom_path = (os.environ.get("LBG_AGENT_DESKTOP_PATH") or os.environ.get("AGENT_DESKTOP_BIN") or "").strip()
    if custom_path:
        p = Path(custom_path)
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
        which_custom = shutil.which(custom_path)
        if which_custom:
            return which_custom

    # 2. PATH standard (binaire ou shim .cmd / .ps1 sous Windows)
    names = ["agent-desktop"]
    if sys.platform == "win32":
        names = ["agent-desktop.cmd", "agent-desktop.exe", "agent-desktop.bat", "agent-desktop"]

    for name in names:
        found = shutil.which(name)
        if found:
            return found

    # 3. Chemins connus npm global selon plateforme
    candidate_dirs: list[Path] = []
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidate_dirs.append(Path(appdata) / "npm")
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            candidate_dirs.append(Path(localappdata) / "npm")
        # Scoop ou Chocolatey
        userprofile = os.environ.get("USERPROFILE")
        if userprofile:
            candidate_dirs.append(Path(userprofile) / "scoop" / "shims")
            candidate_dirs.append(Path(userprofile) / ".cargo" / "bin")
    else:
        candidate_dirs.extend([
            Path("/usr/local/bin"),
            Path("/usr/bin"),
            Path.home() / ".npm-global" / "bin",
            Path.home() / ".cargo" / "bin",
            Path.home() / ".local" / "bin",
        ])

    for cdir in candidate_dirs:
        for name in names:
            target = cdir / name
            if target.is_file():
                return str(target)

    return None


def get_status() -> dict[str, Any]:
    """Retourne l'état de détection de agent-desktop."""
    bin_path = find_agent_desktop_bin()
    if not bin_path:
        return {
            "installed": False,
            "path": None,
            "version": None,
            "platform": sys.platform,
            "hint": "Installer avec: npm i -g agent-desktop",
        }

    version = _probe_version(bin_path)
    return {
        "installed": True,
        "path": bin_path,
        "version": version,
        "platform": sys.platform,
    }


def _probe_version(bin_path: str) -> str | None:
    try:
        res = subprocess.run(
            [bin_path, "--version"],
            capture_output=True,
            text=True,
            timeout=3.0,
            check=False,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception as e:
        logger.debug("Échec lecture version agent-desktop: %s", e)
    return None


def run_snapshot(
    *,
    app: str | None = None,
    interactive_only: bool = True,
    compact: bool = True,
    skeleton: bool = False,
    root_ref: str | None = None,
    timeout_s: float = 12.0,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Capture l'arbre d'accessibilité de l'application ou du bureau."""
    bin_path = find_agent_desktop_bin()
    cmd: list[str] = [bin_path or "agent-desktop", "snapshot"]

    if app:
        cmd.extend(["--app", str(app)])
    if interactive_only:
        cmd.append("-i")
    if compact:
        cmd.append("--compact")
    if skeleton:
        cmd.append("--skeleton")
    if root_ref:
        cmd.extend(["--root", str(root_ref)])

    if dry_run:
        return {
            "ok": True,
            "outcome": "dry_run",
            "cmd": cmd,
            "app": app,
            "interactive_only": interactive_only,
            "compact": compact,
            "skeleton": skeleton,
            "root_ref": root_ref,
        }

    if not bin_path:
        return {
            "ok": False,
            "outcome": "cli_not_found",
            "error": "agent-desktop CLI non trouvé. Installer via: npm i -g agent-desktop",
            "cmd": cmd,
        }

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=max(1.0, float(timeout_s)),
            check=False,
        )
        stdout_raw = proc.stdout.strip()
        stderr_raw = proc.stderr.strip()

        if proc.returncode != 0:
            return {
                "ok": False,
                "outcome": "error",
                "returncode": proc.returncode,
                "error": stderr_raw or stdout_raw or f"Code sortie {proc.returncode}",
                "cmd": cmd,
            }

        # Essayer de parser le flux JSON produit par snapshot
        parsed: Any = None
        if stdout_raw:
            try:
                parsed = json.loads(stdout_raw)
            except Exception:
                # Si le JSON est entouré de texte ou non strict
                parsed = {"raw": stdout_raw}

        return {
            "ok": True,
            "outcome": "ok",
            "snapshot": parsed,
            "cmd": cmd,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "outcome": "timeout",
            "error": f"Délai dépassé ({timeout_s}s) lors du snapshot UI",
            "cmd": cmd,
        }
    except Exception as e:
        return {
            "ok": False,
            "outcome": "error",
            "error": str(e),
            "cmd": cmd,
        }


def run_click(
    *,
    ref: str,
    button: str = "left",
    clicks: int = 1,
    headed: bool = False,
    timeout_s: float = 8.0,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Effectue un clic sur un élément identifié par son @ref via action d'accessibilité."""
    if not ref or not str(ref).strip():
        return {"ok": False, "outcome": "bad_request", "error": "Paramètre `ref` requis"}

    clean_ref = str(ref).strip()
    bin_path = find_agent_desktop_bin()
    cmd: list[str] = [bin_path or "agent-desktop", "click"]

    if headed:
        cmd.append("--headed")
    if timeout_s and timeout_s > 0:
        cmd.extend(["--timeout-ms", str(int(timeout_s * 1000))])

    cmd.append(clean_ref)

    if dry_run:
        return {
            "ok": True,
            "outcome": "dry_run",
            "cmd": cmd,
            "ref": clean_ref,
            "button": button,
            "clicks": clicks,
            "headed": headed,
        }

    if not bin_path:
        return {
            "ok": False,
            "outcome": "cli_not_found",
            "error": "agent-desktop CLI non trouvé. Installer via: npm i -g agent-desktop",
            "cmd": cmd,
        }

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=max(1.0, float(timeout_s)),
            check=False,
        )
        if proc.returncode != 0:
            err = proc.stderr.strip() or proc.stdout.strip()
            outcome = "stale_ref" if "STALE_REF" in err or "stale" in err.lower() else "error"
            return {
                "ok": False,
                "outcome": outcome,
                "returncode": proc.returncode,
                "error": err or f"Erreur click (code {proc.returncode})",
                "ref": clean_ref,
                "cmd": cmd,
            }

        return {
            "ok": True,
            "outcome": "ok",
            "ref": clean_ref,
            "stdout": proc.stdout.strip(),
            "cmd": cmd,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "outcome": "timeout",
            "error": f"Délai dépassé ({timeout_s}s) lors du click sur {clean_ref}",
            "ref": clean_ref,
        }
    except Exception as e:
        return {"ok": False, "outcome": "error", "error": str(e), "ref": clean_ref}


def run_type(
    *,
    ref: str,
    text: str,
    headed: bool = False,
    timeout_s: float = 10.0,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Saisit du texte dans un champ d'interface identifié par son @ref."""
    if not ref or not str(ref).strip():
        return {"ok": False, "outcome": "bad_request", "error": "Paramètre `ref` requis"}

    clean_ref = str(ref).strip()
    bin_path = find_agent_desktop_bin()
    # CLI syntax: agent-desktop type [OPTIONS] <REF> [TEXT]
    # avec --stdin : agent-desktop type --stdin [OPTIONS] <REF>
    cmd: list[str] = [bin_path or "agent-desktop", "type"]

    if headed:
        cmd.append("--headed")
    if timeout_s and timeout_s > 0:
        cmd.extend(["--timeout-ms", str(int(timeout_s * 1000))])

    cmd.extend(["--stdin", clean_ref])

    if dry_run:
        return {
            "ok": True,
            "outcome": "dry_run",
            "cmd": cmd,
            "ref": clean_ref,
            "text_length": len(text),
            "headed": headed,
        }

    if not bin_path:
        return {
            "ok": False,
            "outcome": "cli_not_found",
            "error": "agent-desktop CLI non trouvé. Installer via: npm i -g agent-desktop",
            "cmd": cmd,
        }

    try:
        proc = subprocess.run(
            cmd,
            input=text,
            capture_output=True,
            text=True,
            timeout=max(1.0, float(timeout_s)),
            check=False,
        )
        if proc.returncode != 0:
            err = proc.stderr.strip() or proc.stdout.strip()
            outcome = "stale_ref" if "STALE_REF" in err or "stale" in err.lower() else "error"
            return {
                "ok": False,
                "outcome": outcome,
                "returncode": proc.returncode,
                "error": err or f"Erreur type (code {proc.returncode})",
                "ref": clean_ref,
                "cmd": cmd,
            }

        return {
            "ok": True,
            "outcome": "ok",
            "ref": clean_ref,
            "chars_written": len(text),
            "stdout": proc.stdout.strip(),
            "cmd": cmd,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "outcome": "timeout",
            "error": f"Délai dépassé ({timeout_s}s) lors de la frappe sur {clean_ref}",
            "ref": clean_ref,
        }
    except Exception as e:
        return {"ok": False, "outcome": "error", "error": str(e), "ref": clean_ref}


def run_press(
    *,
    key: str,
    headed: bool = False,
    timeout_s: float = 5.0,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Presse une touche ou combinaison clavier (ex: Enter, Escape, Ctrl+S)."""
    if not key or not str(key).strip():
        return {"ok": False, "outcome": "bad_request", "error": "Paramètre `key` requis"}

    clean_key = str(key).strip()
    bin_path = find_agent_desktop_bin()
    cmd: list[str] = [bin_path or "agent-desktop", "press", clean_key]

    if headed:
        cmd.append("--headed")

    if dry_run:
        return {
            "ok": True,
            "outcome": "dry_run",
            "cmd": cmd,
            "key": clean_key,
            "headed": headed,
        }

    if not bin_path:
        return {
            "ok": False,
            "outcome": "cli_not_found",
            "error": "agent-desktop CLI non trouvé. Installer via: npm i -g agent-desktop",
            "cmd": cmd,
        }

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=max(1.0, float(timeout_s)),
            check=False,
        )
        if proc.returncode != 0:
            err = proc.stderr.strip() or proc.stdout.strip()
            return {
                "ok": False,
                "outcome": "error",
                "returncode": proc.returncode,
                "error": err or f"Erreur press (code {proc.returncode})",
                "key": clean_key,
                "cmd": cmd,
            }

        return {
            "ok": True,
            "outcome": "ok",
            "key": clean_key,
            "stdout": proc.stdout.strip(),
            "cmd": cmd,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "outcome": "timeout",
            "error": f"Délai dépassé ({timeout_s}s) lors du press sur {clean_key}",
            "key": clean_key,
        }
    except Exception as e:
        return {"ok": False, "outcome": "error", "error": str(e), "key": clean_key}


def run_scroll(
    *,
    ref: str | None = None,
    direction: str = "down",
    amount: int = 3,
    headed: bool = False,
    timeout_s: float = 5.0,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Défilement de page ou d'élément dans une direction donnée."""
    bin_path = find_agent_desktop_bin()
    cmd: list[str] = [bin_path or "agent-desktop", "scroll"]

    if ref:
        cmd.append(str(ref).strip())
    if direction in {"up", "down", "left", "right"}:
        cmd.extend(["--direction", direction])
    if amount and int(amount) > 0:
        cmd.extend(["--amount", str(amount)])
    if headed:
        cmd.append("--headed")

    if dry_run:
        return {
            "ok": True,
            "outcome": "dry_run",
            "cmd": cmd,
            "ref": ref,
            "direction": direction,
            "amount": amount,
            "headed": headed,
        }

    if not bin_path:
        return {
            "ok": False,
            "outcome": "cli_not_found",
            "error": "agent-desktop CLI non trouvé. Installer via: npm i -g agent-desktop",
            "cmd": cmd,
        }

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=max(1.0, float(timeout_s)),
            check=False,
        )
        if proc.returncode != 0:
            err = proc.stderr.strip() or proc.stdout.strip()
            return {
                "ok": False,
                "outcome": "error",
                "returncode": proc.returncode,
                "error": err or f"Erreur scroll (code {proc.returncode})",
                "cmd": cmd,
            }

        return {
            "ok": True,
            "outcome": "ok",
            "ref": ref,
            "direction": direction,
            "amount": amount,
            "stdout": proc.stdout.strip(),
            "cmd": cmd,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "outcome": "timeout",
            "error": f"Délai dépassé ({timeout_s}s) lors du scroll",
        }
    except Exception as e:
        return {"ok": False, "outcome": "error", "error": str(e)}


def run_focus(
    *,
    ref: str,
    headed: bool = False,
    timeout_s: float = 5.0,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Place le focus sur un élément identifié par son @ref."""
    if not ref or not str(ref).strip():
        return {"ok": False, "outcome": "bad_request", "error": "Paramètre `ref` requis"}

    clean_ref = str(ref).strip()
    bin_path = find_agent_desktop_bin()
    cmd: list[str] = [bin_path or "agent-desktop", "focus"]

    if headed:
        cmd.append("--headed")
    if timeout_s and timeout_s > 0:
        cmd.extend(["--timeout-ms", str(int(timeout_s * 1000))])

    cmd.append(clean_ref)

    if dry_run:
        return {
            "ok": True,
            "outcome": "dry_run",
            "cmd": cmd,
            "ref": clean_ref,
            "headed": headed,
        }

    if not bin_path:
        return {
            "ok": False,
            "outcome": "cli_not_found",
            "error": "agent-desktop CLI non trouvé. Installer via: npm i -g agent-desktop",
            "cmd": cmd,
        }

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=max(1.0, float(timeout_s)),
            check=False,
        )
        if proc.returncode != 0:
            err = proc.stderr.strip() or proc.stdout.strip()
            return {
                "ok": False,
                "outcome": "error",
                "returncode": proc.returncode,
                "error": err or f"Erreur focus (code {proc.returncode})",
                "ref": clean_ref,
                "cmd": cmd,
            }

        return {
            "ok": True,
            "outcome": "ok",
            "ref": clean_ref,
            "stdout": proc.stdout.strip(),
            "cmd": cmd,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "outcome": "timeout",
            "error": f"Délai dépassé ({timeout_s}s) lors du focus sur {clean_ref}",
            "ref": clean_ref,
        }
    except Exception as e:
        return {"ok": False, "outcome": "error", "error": str(e), "ref": clean_ref}

