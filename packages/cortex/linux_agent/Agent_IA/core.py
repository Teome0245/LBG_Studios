from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore

# -----------------------------------------------------------------------------
# Config hot-reload (linux.env)
# -----------------------------------------------------------------------------

CFG_CACHE: dict[str, object] = {"mtime": None, "vars": {}}

_LOCAL_TZ = None
if ZoneInfo is not None:
    try:
        _LOCAL_TZ = ZoneInfo(os.environ.get("LBG_LOCAL_TIMEZONE", "Europe/Paris"))
    except Exception:
        pass

if _LOCAL_TZ is None:
    try:
        _LOCAL_TZ = datetime.now().astimezone().tzinfo or timezone.utc
    except Exception:
        _LOCAL_TZ = timezone.utc



def local_now_iso() -> str:
    return datetime.now(_LOCAL_TZ).isoformat(timespec="seconds")


def env_path() -> Path:
    raw = os.environ.get("LBG_LINUX_ENV_PATH", "").strip()
    if raw:
        return Path(raw)
    return Path("linux.env")


def load_env_vars() -> dict[str, str]:
    p = env_path()
    try:
        st = p.stat()
    except Exception:
        CFG_CACHE["mtime"] = None
        CFG_CACHE["vars"] = {}
        return {}

    mtime = getattr(st, "st_mtime", None)
    if mtime is not None and CFG_CACHE.get("mtime") == mtime:
        return CFG_CACHE.get("vars") or {}  # type: ignore[return-value]

    out: dict[str, str] = {}
    try:
        raw = p.read_text(encoding="utf-8")
    except Exception:
        raw = ""
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k:
            out[k] = v
    CFG_CACHE["mtime"] = mtime
    CFG_CACHE["vars"] = out
    return out


def get_cfg(key: str) -> str:
    v = os.environ.get(key)
    if v is not None:
        return v
    return load_env_vars().get(key, "")


def split_csv(raw: str) -> list[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]


def truthy(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def linux_dry_run(context: dict[str, Any] | None = None) -> bool:
    env = get_cfg("LBG_LINUX_DRY_RUN").strip()
    if env and truthy(env):
        return True
    if not isinstance(context, dict):
        return False
    return context.get("desktop_dry_run") is True or context.get("dry_run") is True


def linux_requires_approval() -> bool:
    mode = get_cfg("LBG_LINUX_APPROVAL_MODE").strip().lower() or get_cfg(
        "LBG_DESKTOP_APPROVAL_MODE"
    ).strip().lower()
    if mode in ("confirm", "soft", "lab"):
        return True
    soft = get_cfg("LBG_LINUX_SOFT_CONFIRM").strip().lower() or get_cfg(
        "LBG_DESKTOP_SOFT_CONFIRM"
    ).strip().lower()
    if soft in ("1", "true", "yes", "on"):
        return True
    return bool(get_cfg("LBG_LINUX_APPROVAL_TOKEN").strip())


def linux_soft_confirm_enabled() -> bool:
    mode = get_cfg("LBG_LINUX_APPROVAL_MODE").strip().lower() or get_cfg(
        "LBG_DESKTOP_APPROVAL_MODE"
    ).strip().lower()
    if mode in ("confirm", "soft", "lab"):
        return True
    soft = get_cfg("LBG_LINUX_SOFT_CONFIRM").strip().lower() or get_cfg(
        "LBG_DESKTOP_SOFT_CONFIRM"
    ).strip().lower()
    return soft in ("1", "true", "yes", "on")


def linux_approval_ok(context: dict[str, Any] | None = None) -> bool:
    if not isinstance(context, dict):
        context = {}
    got = context.get("desktop_approval")
    if linux_soft_confirm_enabled():
        if context.get("desktop_confirm") is True:
            return True
        if isinstance(got, str) and got.strip().lower() in (
            "confirmed",
            "confirm",
            "yes",
            "1",
            "ok",
        ):
            return True
    token = get_cfg("LBG_LINUX_APPROVAL_TOKEN").strip()
    if not token:
        return not linux_soft_confirm_enabled() or (
            isinstance(got, str)
            and got.strip().lower() in ("confirmed", "confirm", "yes", "1", "ok")
        )
    return isinstance(got, str) and bool(got) and secrets.compare_digest(got, token)


def audit_write(line: dict[str, Any]) -> None:
    line = dict(line)
    line["ts"] = local_now_iso()
    raw = json.dumps(line, ensure_ascii=False)

    if truthy(get_cfg("LBG_LINUX_AUDIT_STDOUT") or "1"):
        print(raw)

    path = get_cfg("LBG_LINUX_AUDIT_LOG_PATH").strip()
    if not path:
        return
    try:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.open("a", encoding="utf-8").write(raw + "\n")
    except Exception as e:
        print(
            json.dumps({"event": "agents.linux.audit_file_error", "error": f"{type(e).__name__}: {e}"}),
            file=sys.stderr,
        )


def url_allowlist() -> list[str]:
    raw = get_cfg("LBG_LINUX_URL_ALLOWLIST").strip()
    return split_csv(raw) if raw else []


def url_host_allowlist() -> list[str]:
    raw = get_cfg("LBG_LINUX_URL_HOST_ALLOWLIST").strip()
    return split_csv(raw) if raw else []


def host_matches(needle: str, rule: str) -> bool:
    n = (needle or "").strip().lower().rstrip(".")
    r = (rule or "").strip().lower().rstrip(".")
    if not n or not r:
        return False
    if r.startswith("*."):
        suf = r[2:]
        return bool(suf) and n.endswith("." + suf)
    if n == r:
        return True
    return n.endswith("." + r)


def url_allowed_by_host(url: str) -> bool:
    allow = url_host_allowlist()
    if not allow:
        return False
    try:
        p = urlparse(url)
    except Exception:
        return False
    if p.scheme not in {"http", "https"}:
        return False
    host = (p.hostname or "").strip().lower()
    return any(host_matches(host, rule) for rule in allow)


def url_is_allowed(url: str) -> bool:
    if url in url_allowlist():
        return True
    return url_allowed_by_host(url)


def web_search_enabled() -> bool:
    return truthy(get_cfg("LBG_LINUX_WEB_SEARCH"))


def linux_search_engine() -> str:
    v = get_cfg("LBG_LINUX_SEARCH_ENGINE").strip().lower()
    if v in ("google",):
        return "google"
    return "duckduckgo"


def build_web_search_url(query: str) -> tuple[str | None, str | None]:
    from urllib.parse import quote_plus

    q = (query or "").strip()
    if not q:
        return None, "requête vide"
    if len(q) > 220:
        q = q[:220]
    if linux_search_engine() == "google":
        return "https://www.google.com/search?q=" + quote_plus(q), None
    return "https://duckduckgo.com/?q=" + quote_plus(q), None


def web_search_url_trusted(url: str) -> bool:
    try:
        p = urlparse(url)
    except Exception:
        return False
    if p.scheme != "https":
        return False
    host = (p.hostname or "").lower()
    if linux_search_engine() == "google":
        return host in ("www.google.com", "google.com")
    return host in ("duckduckgo.com", "www.duckduckgo.com", "lite.duckduckgo.com")


def file_allowlist_dirs() -> list[Path]:
    raw = get_cfg("LBG_LINUX_FILE_ALLOWLIST_DIRS").strip()
    if not raw:
        return []
    out: list[Path] = []
    for item in split_csv(raw):
        try:
            out.append(Path(item).expanduser().resolve())
        except Exception:
            continue
    return out


def path_is_allowed(path_str: str) -> bool:
    dirs = file_allowlist_dirs()
    if not dirs:
        return False
    try:
        p = Path(path_str).expanduser().resolve()
    except Exception:
        return False
    return any(p == d or d in p.parents for d in dirs)


def env_set_key(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    out = []
    found = False
    for ln in lines:
        if ln.strip().startswith(key + "="):
            out.append(f"{key}={value}")
            found = True
        else:
            out.append(ln)
    if not found:
        if out and out[-1].strip() != "":
            out.append("")
        out.append(f"{key}={value}")
    return "\n".join(out) + ("\n" if not text.endswith("\n") else "")


def learn_enabled() -> bool:
    return truthy((get_cfg("LBG_LINUX_LEARN_ENABLED") or "").strip() or "0")


def learn_allowlist() -> list[str]:
    raw = (get_cfg("LBG_LINUX_LEARN_APP_ALLOWLIST") or "").strip()
    return split_csv(raw) if raw else []


def persist_learned_app(app_id: str, exe_path: str) -> tuple[bool, str | None]:
    p = env_path()
    try:
        current = p.read_text(encoding="utf-8") if p.exists() else ""
    except Exception as e:
        return (False, f"read_env_failed: {e}")

    allow = split_csv((get_cfg("LBG_LINUX_APP_ALLOWLIST") or "").strip())
    if app_id not in allow:
        allow.append(app_id)

    map_raw = (get_cfg("LBG_LINUX_APP_MAP_JSON") or "").strip()
    try:
        mapping = json.loads(map_raw) if map_raw else {}
        if not isinstance(mapping, dict):
            mapping = {}
    except Exception:
        mapping = {}
    mapping[app_id] = [exe_path]

    new_text = current
    new_text = env_set_key(new_text, "LBG_LINUX_APP_ALLOWLIST", ",".join(allow))
    new_text = env_set_key(new_text, "LBG_LINUX_APP_MAP_JSON", json.dumps(mapping, ensure_ascii=False))

    try:
        p.write_text(new_text, encoding="utf-8")
        CFG_CACHE["mtime"] = None
        CFG_CACHE["vars"] = {}
        return (True, None)
    except Exception as e:
        return (False, f"write_env_failed: {e}")


def popen_quiet(argv: list[str]) -> None:
    env = graphical_environ()
    subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)


def graphical_environ() -> dict[str, str]:
    """Env pour lancer une GUI depuis un service systemd --user (souvent sans DISPLAY)."""
    env = dict(os.environ)
    uid = os.getuid()
    runtime = env.get("XDG_RUNTIME_DIR") or f"/run/user/{uid}"
    env["XDG_RUNTIME_DIR"] = runtime
    # Wayland (Hyprland / Omarchy)
    if not env.get("WAYLAND_DISPLAY"):
        for name in ("wayland-1", "wayland-0"):
            sock = Path(runtime) / name
            if sock.exists():
                env["WAYLAND_DISPLAY"] = name
                break
    # X11 fallback (Xwayland)
    if not env.get("DISPLAY"):
        for disp in (":0", ":1"):
            # socket path varies; set if wayland found (Xwayland often :0)
            if env.get("WAYLAND_DISPLAY"):
                env["DISPLAY"] = ":0"
                break
            if Path(f"/tmp/.X11-unix/X{disp.lstrip(':')}").exists():
                env["DISPLAY"] = disp
                break
    # Hyprland signature (certains outils)
    if not env.get("HYPRLAND_INSTANCE_SIGNATURE"):
        hypr = Path(runtime) / "hypr"
        if hypr.is_dir():
            try:
                kids = sorted(hypr.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
                if kids:
                    env["HYPRLAND_INSTANCE_SIGNATURE"] = kids[0].name
            except OSError:
                pass
    return env


def session_info() -> dict[str, object]:
    """État session graphique — équivalent Linux du diagnostic Session 0 Windows."""
    env = graphical_environ()
    runtime = env.get("XDG_RUNTIME_DIR") or ""
    wayland = env.get("WAYLAND_DISPLAY") or ""
    display = env.get("DISPLAY") or ""
    sock_ok = bool(wayland and Path(runtime, wayland).exists())
    svc = "lbg-omarchy-agent.service"
    active = False
    try:
        r = subprocess.run(
            ["systemctl", "--user", "is-active", svc],
            capture_output=True,
            text=True,
            timeout=5,
        )
        active = (r.stdout or "").strip() == "active"
    except Exception:
        pass
    gui_ok = sock_ok or bool(display)
    return {
        "host_role": "omarchy_linux",
        "xdg_runtime_dir": runtime,
        "wayland_display": wayland or None,
        "display": display or None,
        "wayland_socket_ok": sock_ok,
        "gui_ready": gui_ok,
        "gui_risk": not gui_ok,
        "user_service": svc,
        "user_service_active": active,
        "heal_kind": "fix_session0",  # même kind AGIR, mapping Linux = heal service + env
    }


def heal_desktop_agent(*, dry_run: bool) -> dict[str, object]:
    """Redémarre le worker user + vérifie la session graphique (poste .143)."""
    svc = "lbg-omarchy-agent.service"
    before = session_info()
    if dry_run:
        return {
            "ok": True,
            "outcome": "dry_run",
            "task": svc,
            "before": before,
            "hint": "Réel: systemctl --user restart lbg-omarchy-agent + re-check Wayland",
        }
    try:
        r = subprocess.run(
            ["systemctl", "--user", "restart", svc],
            capture_output=True,
            text=True,
            timeout=30,
        )
        detail = ((r.stdout or "") + "\n" + (r.stderr or "")).strip()
        if r.returncode != 0:
            return {
                "ok": False,
                "outcome": "error",
                "task": svc,
                "error": f"restart rc={r.returncode}",
                "detail": detail[:400],
                "before": before,
            }
        # petite pause puis relecture (le process courant va mourir au restart —
        # si on est DANS le service, ce code peut ne pas renvoyer ; l'orch verra coupure puis ok)
        import time

        time.sleep(1)
        after = session_info()
        return {
            "ok": True,
            "outcome": "ok",
            "task": svc,
            "before": before,
            "after": after,
            "detail": detail[:200],
            "reply": (
                "Agent Omarchy redémarré. "
                + ("GUI prête (Wayland)." if after.get("gui_ready") else "Attention: pas de socket Wayland — ouvrir une session Hyprland.")
            ),
        }
    except Exception as e:
        return {"ok": False, "outcome": "error", "task": svc, "error": f"{type(e).__name__}: {e}", "before": before}


# Paquets AUR/pacman que l’agent peut mettre à jour (allowlist stricte).
_VSCODE_PKG = "visual-studio-code-bin"
_PACKAGE_UPDATE_ALLOWLIST = frozenset({_VSCODE_PKG})


def vscode_package_status() -> dict[str, object]:
    """Lit version installée + éventuelle MAJ (pacman -Q / checkupdates), sans écrire."""
    pkg = _VSCODE_PKG
    current: str | None = None
    available: str | None = None
    try:
        r = subprocess.run(
            ["pacman", "-Q", pkg],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode == 0 and (r.stdout or "").strip():
            parts = (r.stdout or "").strip().split()
            if len(parts) >= 2:
                current = parts[1]
    except Exception as e:
        return {
            "package": pkg,
            "ok": False,
            "error": f"pacman -Q: {type(e).__name__}: {e}",
        }
    # Prefer checkupdates: compares against a temp sync DB (no root, no /var/lib/pacman mutate).
    # pacman -Qu alone often returns empty if the local sync DB is stale.
    try:
        cu = which("checkupdates") or "/usr/bin/checkupdates"
        r2 = subprocess.run(
            [cu],
            capture_output=True,
            text=True,
            timeout=120,
        )
        for line in (r2.stdout or "").splitlines():
            s = line.strip()
            if not s.startswith(pkg + " "):
                continue
            if "->" in s:
                available = s.split("->", 1)[1].strip().split()[0]
                break
    except Exception:
        available = None
    if available is None:
        try:
            r3 = subprocess.run(
                ["pacman", "-Qu", pkg],
                capture_output=True,
                text=True,
                timeout=30,
            )
            line = (r3.stdout or "").strip()
            if line and "->" in line:
                available = line.split("->", 1)[1].strip().split()[0]
        except Exception:
            available = None
    update_available = bool(current and available and available != current)
    return {
        "ok": True,
        "package": pkg,
        "current": current,
        "available": available,
        "update_available": update_available,
        "installed": current is not None,
    }


def update_vscode(*, dry_run: bool) -> dict[str, object]:
    """Met à jour VS Code (AUR visual-studio-code-bin) via yay — poste Omarchy .143."""
    pkg = _VSCODE_PKG
    if pkg not in _PACKAGE_UPDATE_ALLOWLIST:
        return {"ok": False, "outcome": "allowlist_denied", "error": f"Paquet hors allowlist: {pkg}"}
    status = vscode_package_status()
    if not status.get("ok"):
        return {
            "ok": False,
            "outcome": "error",
            "package": pkg,
            "error": status.get("error") or "statut paquet illisible",
            "status": status,
        }
    if dry_run:
        return {
            "ok": True,
            "outcome": "dry_run",
            "package": pkg,
            "status": status,
            "hint": (
                f"Réel: yay -S --noconfirm --needed {pkg}"
                + (
                    f" ({status.get('current')} → {status.get('available')})"
                    if status.get("update_available")
                    else " (déjà à jour ou pas de sync)"
                )
            ),
            "reply": (
                f"MAJ VS Code disponible : {status.get('current')} → {status.get('available')}"
                if status.get("update_available")
                else f"VS Code déjà à jour ({status.get('current')}) ou aucune MAJ listée."
            ),
        }
    if not status.get("update_available"):
        return {
            "ok": True,
            "outcome": "ok",
            "package": pkg,
            "status": status,
            "skipped": True,
            "reply": f"VS Code déjà à jour ({status.get('current')}).",
        }
    yay = which("yay") or "/usr/bin/yay"
    try:
        # Sync DB d’abord : sinon « --needed » peut ignorer une MAJ déjà listée par checkupdates.
        subprocess.run(
            [yay, "-Sy", "--noconfirm"],
            capture_output=True,
            text=True,
            timeout=180,
        )
        r = subprocess.run(
            [yay, "-S", "--noconfirm", pkg],
            capture_output=True,
            text=True,
            timeout=600,
        )
        detail = ((r.stdout or "") + "\n" + (r.stderr or "")).strip()
        after = vscode_package_status()
        if r.returncode != 0:
            return {
                "ok": False,
                "outcome": "error",
                "package": pkg,
                "error": f"yay rc={r.returncode}",
                "detail": detail[-800:],
                "before": status,
                "after": after,
            }
        return {
            "ok": True,
            "outcome": "ok",
            "package": pkg,
            "before": status,
            "after": after,
            "detail": detail[-400:],
            "reply": (
                f"VS Code mis à jour : {status.get('current')} → "
                f"{after.get('current') or status.get('available')}."
            ),
            "hint": "Redémarrer VS Code manuellement quand les sessions Cline/Continue sont libres.",
        }
    except Exception as e:
        return {
            "ok": False,
            "outcome": "error",
            "package": pkg,
            "error": f"{type(e).__name__}: {e}",
            "before": status,
        }


def mail_imap_enabled() -> bool:
    return truthy(get_cfg("LBG_LINUX_MAIL_ENABLED"))


def mail_imap_credentials() -> tuple[str, int, str, str, bool, bool]:
    host = get_cfg("LBG_LINUX_MAIL_IMAP_HOST").strip()
    pr = (get_cfg("LBG_LINUX_MAIL_IMAP_PORT").strip() or "993")
    try:
        port = int(pr) if pr else 993
    except ValueError:
        port = 993
    user = get_cfg("LBG_LINUX_MAIL_IMAP_USER").strip()
    password = get_cfg("LBG_LINUX_MAIL_IMAP_PASSWORD").strip()
    use_ssl = not truthy(get_cfg("LBG_LINUX_MAIL_IMAP_NO_SSL").strip())
    insecure_ssl = truthy(get_cfg("LBG_LINUX_MAIL_IMAP_INSECURE_SSL").strip())
    return host, port, user, password, use_ssl, insecure_ssl


def _mail_imap_parse_int_local(action: dict[str, Any], key: str, default: int, lo: int, hi: int) -> int:
    v = action.get(key, default)
    if isinstance(v, bool):
        return default
    if isinstance(v, int):
        n = v
    elif isinstance(v, str) and v.strip().lstrip("-").isdigit():
        try:
            n = int(v.strip())
        except ValueError:
            return default
    else:
        try:
            n = int(v)  # type: ignore[arg-type]
        except Exception:
            return default
    return max(lo, min(hi, n))


def mail_imap_parse_action(action: dict[str, Any]) -> tuple[str, str, int, int, int, str | None]:
    fc = action.get("from_contains")
    sc = action.get("subject_contains")
    fc_s = fc.strip() if isinstance(fc, str) else ""
    sc_s = sc.strip() if isinstance(sc, str) else ""
    if len(fc_s) > 80:
        fc_s = fc_s[:80]
    if len(sc_s) > 120:
        sc_s = sc_s[:120]
    if not fc_s and not sc_s:
        recent = action.get("recent") is True or str(action.get("recent") or "").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        if not recent:
            return "", "", 0, 0, 0, "Champs `from_contains` et/ou `subject_contains` requis (ou recent=true)"
    fold = action.get("folder")
    if isinstance(fold, str) and fold.strip() and fold.strip().upper() != "INBOX":
        return "", "", 0, 0, 0, "Dossier non supporté (MVP : INBOX seulement)"
    max_m = _mail_imap_parse_int_local(action, "max_messages", 3, 1, 10)
    max_b = _mail_imap_parse_int_local(action, "max_body_chars", 800, 0, 4000)
    max_sc = _mail_imap_parse_int_local(action, "max_scan", 200, 10, 500)
    return fc_s, sc_s, max_m, max_b, max_sc, None


def which(exe: str) -> str:
    return shutil.which(exe) or ""


# -----------------------------------------------------------------------------
# CLI agents IDE (Claude Code / Cline / OpenCode) — ADR 0025
# -----------------------------------------------------------------------------

_CLI_AGENT_APPS: frozenset[str] = frozenset({"claude", "cline", "opencode"})
_DEFAULT_CLI_CWD = "/home/lbg/projects/LBG_Studios"


def cli_agent_enabled() -> bool:
    return os.environ.get("LBG_LINUX_CLI_AGENT_ENABLED", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def cli_agent_timeout_s(action: dict[str, object] | None = None) -> int:
    raw = None
    if isinstance(action, dict):
        raw = action.get("timeout_s")
    if raw is None:
        raw = os.environ.get("LBG_LINUX_CLI_AGENT_TIMEOUT_S", "300")
    try:
        n = int(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        n = 300
    return max(30, min(n, 1800))


def cli_agent_cwd_allowlist() -> list[Path]:
    raw = os.environ.get("LBG_LINUX_CLI_AGENT_CWD_ALLOWLIST", "").strip()
    roots: list[str] = []
    if raw:
        roots.extend(x.strip() for x in raw.split(",") if x.strip())
    else:
        roots.append("/home/lbg/projects")
    out: list[Path] = []
    for r in roots:
        try:
            out.append(Path(r).expanduser().resolve())
        except Exception:
            continue
    return out


def cli_agent_cwd_ok(cwd: str) -> bool:
    try:
        p = Path(cwd).expanduser().resolve()
    except Exception:
        return False
    if not p.is_dir():
        return False
    for root in cli_agent_cwd_allowlist():
        try:
            if p == root or root in p.parents:
                return True
        except Exception:
            continue
    return False


def resolve_cli_agent_argv(app: str, prompt: str) -> list[str] | None:
    """Construit argv headless pour l'app (allowlist)."""
    a = (app or "").strip().lower()
    if a not in _CLI_AGENT_APPS:
        return None
    bin_path = which(a)
    if a == "cline" and not bin_path:
        bin_path = which("cline-cli")
    if not bin_path:
        return None
    if a == "claude":
        return [bin_path, "-p", prompt, "--output-format", "text"]
    if a == "cline":
        return [bin_path, "run", "--prompt", prompt]
    if a == "opencode":
        return [bin_path, "run", prompt]
    return None


def run_cli_agent(
    *,
    app: str,
    prompt: str,
    cwd: str | None = None,
    dry_run: bool,
    timeout_s: int | None = None,
) -> dict[str, object]:
    """Exécute un agent coding CLI headless (ADR 0025). Dry-run par défaut côté caller."""
    if not cli_agent_enabled() and not dry_run:
        return {
            "ok": False,
            "outcome": "feature_disabled",
            "error": "LBG_LINUX_CLI_AGENT_ENABLED=0 — activer après smoke .143",
            "app": app,
        }
    app_id = (app or "").strip().lower()
    if app_id not in _CLI_AGENT_APPS:
        return {
            "ok": False,
            "outcome": "allowlist_denied",
            "error": f"app hors allowlist: {app_id}",
            "allowed": sorted(_CLI_AGENT_APPS),
        }
    prompt_s = (prompt or "").strip()
    if not prompt_s:
        return {"ok": False, "outcome": "bad_request", "error": "prompt vide", "app": app_id}
    if len(prompt_s) > 12000:
        return {"ok": False, "outcome": "bad_request", "error": "prompt trop long (>12000)", "app": app_id}

    work = (cwd or "").strip() or os.environ.get("LBG_OMARCHY_STUDIO_WORKSPACE", _DEFAULT_CLI_CWD).strip()
    if not cli_agent_cwd_ok(work):
        return {
            "ok": False,
            "outcome": "allowlist_denied",
            "error": f"cwd hors allowlist: {work}",
            "cwd": work,
            "cwd_allowlist": [str(p) for p in cli_agent_cwd_allowlist()],
        }

    argv = resolve_cli_agent_argv(app_id, prompt_s)
    if not argv:
        if dry_run:
            # Dry-run : preview même si binaire absent (smoke orch sans .143)
            fake = {
                "claude": ["claude", "-p", prompt_s, "--output-format", "text"],
                "cline": ["cline", "run", "--prompt", prompt_s],
                "opencode": ["opencode", "run", prompt_s],
            }.get(app_id, [app_id])
            to = timeout_s if timeout_s is not None else cli_agent_timeout_s()
            return {
                "ok": True,
                "outcome": "dry_run",
                "app": app_id,
                "cwd": work,
                "argv": fake,
                "timeout_s": to,
                "prompt_preview": prompt_s[:240],
                "bin_missing": True,
                "hint": f"Binaire « {app_id} » absent sur ce host — install sur .143 avant live",
                "reply": f"Dry-run run_cli_agent app={app_id} cwd={work} (bin missing)",
            }
        return {
            "ok": False,
            "outcome": "not_installed",
            "error": f"binaire « {app_id} » introuvable sur PATH",
            "app": app_id,
            "cwd": work,
        }

    to = timeout_s if timeout_s is not None else cli_agent_timeout_s()
    if dry_run:
        return {
            "ok": True,
            "outcome": "dry_run",
            "app": app_id,
            "cwd": work,
            "argv": argv,
            "timeout_s": to,
            "prompt_preview": prompt_s[:240],
            "hint": "Réel: LBG_LINUX_CLI_AGENT_ENABLED=1 + approval desktop",
            "reply": f"Dry-run run_cli_agent app={app_id} cwd={work}",
        }

    try:
        proc = subprocess.run(
            argv,
            cwd=work,
            capture_output=True,
            text=True,
            timeout=to,
            check=False,
            env={**os.environ, "TERM": "dumb"},
        )
        stdout = (proc.stdout or "")[-4000:]
        stderr = (proc.stderr or "")[-2000:]
        ok = proc.returncode == 0
        return {
            "ok": ok,
            "outcome": "ok" if ok else "error",
            "app": app_id,
            "cwd": work,
            "argv": argv,
            "timeout_s": to,
            "returncode": proc.returncode,
            "stdout_tail": stdout,
            "stderr_tail": stderr,
            "reply": (stdout or stderr or f"rc={proc.returncode}")[:500],
            "error": None if ok else f"cli rc={proc.returncode}",
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "outcome": "timeout",
            "error": f"timeout après {to}s",
            "app": app_id,
            "cwd": work,
            "argv": argv,
            "timeout_s": to,
        }
    except Exception as exc:
        return {
            "ok": False,
            "outcome": "error",
            "error": f"{type(exc).__name__}: {exc}",
            "app": app_id,
            "cwd": work,
            "argv": argv,
        }
