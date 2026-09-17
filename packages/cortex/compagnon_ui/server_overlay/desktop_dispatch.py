"""Desktop open_app depuis Orch UI — même intention que Cockpit Supervisé.

Chemins (dans l'ordre) :
1. Cockpit / P03 ``POST …/v1/pilot/tasks/run`` (injecte approval serveur) — Bearer ``LBG_PILOT_API_TOKEN``
2. Worker Windows ``POST /invoke`` — ``LBG_DESKTOP_APPROVAL_TOKEN``
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

import httpx

from src.http_timeouts import httpx_timeout
from src.settings import Settings

logger = logging.getLogger("lbg.router.desktop")

_OPEN_APP_VERB_RE = re.compile(
    r"\b(?:ouvrir|ouvre|ouvrez|lancer|lance|lancez|demarrer|démarrer|demarre|démarre|"
    r"demarrez|démarrez|start|launch|open|exécute|execute|exécuter|executer)\b",
    re.IGNORECASE,
)

_OPEN_APP_STOP_TOKENS = frozenset(
    {
        "le",
        "la",
        "les",
        "un",
        "une",
        "the",
        "a",
        "an",
        "mon",
        "ma",
        "mes",
        "ton",
        "ta",
        "pc",
        "poste",
        "machine",
        "ordinateur",
        "windows",
        "linux",
    }
)

_DESKTOP_LOCUS_RE = re.compile(
    r"(?i)\b(pc|poste|machine|ordinateur|windows|bureau|desktop)\b"
)


def desktop_dispatch_enabled() -> bool:
    return os.getenv("LBG_DESKTOP_DISPATCH_ENABLED", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _sanitize_app_slug(raw_tail: str) -> str | None:
    t = (raw_tail or "").strip().strip("\"'«»")
    if not t or re.search(r"https?://", t):
        return None
    if "\\" in t or "/" in t or ".." in t:
        return None
    first = re.split(r"\s+", t, maxsplit=1)[0].strip("\"'«»")
    if not first:
        return None
    if len(first) > 80:
        first = first[:80]
    if not re.match(r"^[A-Za-z0-9_.\-]+$", first):
        return None
    # « vghd.exe » → id logique « vghd » (APP_MAP / allowlist)
    first = re.sub(r"\.(exe|bat|cmd|com)$", "", first, flags=re.IGNORECASE)
    if not first:
        return None
    if first.lower() in _OPEN_APP_STOP_TOKENS:
        return None
    return first.lower()


def infer_open_app_from_text(text: str) -> dict[str, Any] | None:
    """Infère ``{kind:open_app, app, args, learn}`` — aligné Cortex/P03."""
    raw = (text or "").strip()
    if not raw:
        return None
    if not _OPEN_APP_VERB_RE.search(raw):
        return None
    matches = list(_OPEN_APP_VERB_RE.finditer(raw))
    if not matches:
        return None
    tail = raw[matches[-1].end() :].strip()
    tail = re.sub(
        r"^\s*(?:l['′'])?\s*(?:application|appli|prog|programme)\s+",
        "",
        tail,
        flags=re.IGNORECASE,
    ).strip()
    tail_chunk = re.split(r"\s+(?:sur|on|avec|pour|dans)\s+", tail, maxsplit=1)[0].strip()
    slug = _sanitize_app_slug(tail_chunk)
    if not slug:
        return None
    return {"kind": "open_app", "app": slug, "args": [], "learn": True}


def wants_desktop_open(prompt: str) -> bool:
    """True si le message demande clairement d'ouvrir une app sur le poste."""
    if not desktop_dispatch_enabled():
        return False
    text = (prompt or "").strip()
    if not text:
        return False
    # « fais un diagnostic : ouvre vghd… » (Agent=Diagnostic) → encore desktop
    cleaned = re.sub(
        r"(?i)^\s*fais\s+un\s+diagnostic\s*:\s*",
        "",
        text,
    ).strip()
    action = infer_open_app_from_text(cleaned)
    if not action:
        return False
    low = cleaned.lower()
    # Exiger un locus PC / poste, ou une app connue hors PATH (jeux)
    known = ("vghd", "swgemu", "notepad", "notepadpp", "vlc", "firefox", "word", "excel")
    if action["app"] in known:
        return True
    return bool(_DESKTOP_LOCUS_RE.search(low))


def _pilot_token() -> str:
    return (
        os.getenv("LBG_PILOT_API_TOKEN", "").strip()
        or os.getenv("COCKPIT_PILOT_API_TOKEN", "").strip()
    )


def _desktop_approval() -> str:
    return (
        os.getenv("LBG_DESKTOP_APPROVAL_TOKEN", "").strip()
        or os.getenv("LBG_DEVOPS_APPROVAL_TOKEN", "").strip()
    )


def _tasks_run_url(settings: Settings) -> str:
    override = os.getenv("LBG_COCKPIT_TASKS_URL", "").strip()
    if override:
        return override.rstrip("/")
    # P03 backend (Cockpit API) — pas Cortex Pilot :8080
    base = os.getenv("LBG_P03_PILOT_URL", "").strip()
    if not base:
        base = "http://192.168.0.140:9800"
    return f"{base.rstrip('/')}/v1/pilot/tasks/run"


def _desktop_worker_url(settings: Settings) -> str:
    for cand in (
        str(settings.cortex_agent_desktop_url or "").strip(),
        str(settings.agent_windows_url or "").strip(),
        os.getenv("CORTEX_AGENT_DESKTOP_URL", "").strip(),
    ):
        if cand and not cand.endswith(":1") and "127.0.0.1:1" not in cand:
            return cand.rstrip("/")
    return "http://192.168.0.10:5005"


def _format_tasks_reply(data: dict[str, Any], goal: str) -> str:
    ok = data.get("ok")
    err = data.get("error") or data.get("detail")
    if isinstance(err, dict):
        err = err.get("error") or err.get("hint") or str(err)
    reply = data.get("reply") or data.get("summary") or ""
    if isinstance(reply, dict):
        reply = reply.get("text") or reply.get("content") or str(reply)
    plan = data.get("plan_source") or data.get("planner") or ""
    if ok is True or (ok is None and not err and data.get("status") in ("success", "ok", "done")):
        app = ""
        blob = str(data)
        m = re.search(r'"app"\s*:\s*"([^"]+)"', blob)
        if m:
            app = m.group(1)
        lines = [
            f"**Desktop** — `{app or 'open_app'}` exécuté via Cockpit Supervisé.",
            f"- objectif : {goal[:160]}",
        ]
        if plan:
            lines.append(f"- plan : `{plan}`")
        if reply:
            lines.append(f"- détail : {str(reply)[:300]}")
        return "\n".join(lines)
    err_s = str(err or "réponse inattendue")
    # WinError 2 ≠ jeton manquant
    if re.search(r"WinError\s*2|introuvable|FileNotFound", err_s, re.I):
        return (
            f"Desktop : exe introuvable — {err_s}. "
            "Vérifie l’id d’app (`vghd` pas `vghd.exe`) et `LBG_DESKTOP_APP_MAP_JSON` sur `.10`."
        )
    if re.search(r"approval|jeton|token|401|403", err_s, re.I):
        return (
            f"Desktop via Cockpit : échec auth — {err_s}. "
            "Vérifie `LBG_PILOT_API_TOKEN` / `LBG_DESKTOP_APPROVAL_TOKEN`."
        )
    return (
        f"Desktop via Cockpit : échec — {err_s}. "
        "Worker `.10:5005` et mapping app à vérifier."
    )


def _format_worker_reply(data: dict[str, Any], action: dict[str, Any]) -> str:
    app = action.get("app") or "?"
    if data.get("ok") is True or data.get("outcome") in ("ok", "dry_run"):
        return (
            f"**Desktop** : `{app}` — {data.get('outcome') or 'ok'} sur windows-desktop "
            f"(worker Agent_IA)."
        )
    err = data.get("error") or data.get("detail") or "échec"
    hint = data.get("hint") or ""
    return f"Desktop worker : `{app}` — {err}" + (f"\n_{hint}_" if hint else "")


async def run_desktop_open(
    prompt: str,
    *,
    settings: Settings,
    dry_run: bool | None = None,
) -> dict[str, Any]:
    """Exécute open_app. Retourne payload normalisable (content, ok, source, …)."""
    cleaned = re.sub(r"(?i)^\s*fais\s+un\s+diagnostic\s*:\s*", "", (prompt or "").strip()).strip()
    action = infer_open_app_from_text(cleaned)
    if not action:
        return {
            "ok": False,
            "content": "Impossible d'inférer une app à ouvrir (ex. « lance vghd sur mon pc »).",
            "source": "desktop",
            "via": "none",
        }

    if dry_run is None:
        dry_run = os.getenv("LBG_DESKTOP_DRY_RUN", "").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

    t0 = time.monotonic()
    timeout = httpx_timeout(read=min(float(settings.httpx_agent_execute_read_s), 60.0))

    # 1) Cockpit / P03 tasks/run
    token = _pilot_token()
    if token:
        url = _tasks_run_url(settings)
        headers = {
            "Authorization": f"Bearer {token}",
            "X-LBG-Pilot-Token": token,
            "Content-Type": "application/json",
        }
        body = {
            "goal": cleaned,
            "context": {
                "desktop_dry_run": bool(dry_run),
                "desktop_action": action,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(url, headers=headers, json=body)
            latency = time.monotonic() - t0
            if r.status_code < 400:
                data = r.json() if r.content else {}
                if not isinstance(data, dict):
                    data = {"raw": data}
                content = _format_tasks_reply(data, cleaned)
                ok = data.get("ok") is True or (
                    "approval" not in str(data.get("error") or "").lower()
                    and r.status_code == 200
                    and data.get("ok") is not False
                )
                return {
                    "ok": ok,
                    "content": content,
                    "source": "desktop",
                    "via": "cockpit_tasks_run",
                    "latency": latency,
                    "app": action["app"],
                    "raw": {
                        k: data.get(k)
                        for k in ("ok", "error", "reply", "plan_source", "status")
                        if k in data
                    },
                }
            logger.info("desktop tasks/run HTTP %s: %s", r.status_code, r.text[:200])
        except Exception as e:
            logger.warning("desktop tasks/run failed: %s", e)

    # 2) Worker Windows direct
    approval = _desktop_approval()
    worker = _desktop_worker_url(settings)
    ctx: dict[str, Any] = {
        "desktop_dry_run": bool(dry_run),
        "desktop_action": action,
    }
    if approval and not dry_run:
        ctx["desktop_approval"] = approval
    invoke_body = {
        "actor_id": "orch-ui:desktop",
        "text": cleaned,
        "context": ctx,
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{worker}/invoke", json=invoke_body)
        latency = time.monotonic() - t0
        data = r.json() if r.content else {}
        if not isinstance(data, dict):
            data = {"raw": data, "ok": False}
        if r.status_code >= 400:
            return {
                "ok": False,
                "content": (
                    f"Worker desktop `{worker}` HTTP {r.status_code}. "
                    "Configure `LBG_PILOT_API_TOKEN` (Cockpit) ou `LBG_DESKTOP_APPROVAL_TOKEN`."
                ),
                "source": "desktop",
                "via": "worker_invoke",
                "latency": latency,
                "app": action["app"],
            }
        return {
            "ok": data.get("ok") is True,
            "content": _format_worker_reply(data, action),
            "source": "desktop",
            "via": "worker_invoke",
            "latency": latency,
            "app": action["app"],
            "outcome": data.get("outcome"),
        }
    except Exception as e:
        latency = time.monotonic() - t0
        return {
            "ok": False,
            "content": (
                f"Desktop indisponible ({type(e).__name__}: {e}). "
                "Utilise Cockpit Supervisé http://192.168.0.100:8093/pilot/#/cockpit "
                "ou configure les jetons Orch (`LBG_PILOT_API_TOKEN` / `LBG_DESKTOP_APPROVAL_TOKEN`)."
            ),
            "source": "desktop",
            "via": "error",
            "latency": latency,
            "app": action["app"],
        }
