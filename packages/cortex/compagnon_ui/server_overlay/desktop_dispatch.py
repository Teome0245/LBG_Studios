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
    r"(?i)\b(pc|poste|machine|ordinateur|windows|bureau|desktop|"
    r"portable[- ]?sds|portable|laptop|omarchy)\b"
)

# Aligné `lbg_agents.desktop_targets.infer_desktop_target_from_text` (overlay Orch sans import agents).
_TARGET_FROM_TEXT_RE = (
    (re.compile(r"(?i)\b(serveur ad|srv[- ]?ad|sur l['']?ad|active directory|192\.168\.0\.100)\b"), "ad"),
    (re.compile(r"(?i)\b(sur mon pc|mon pc|pc windows|poste windows|192\.168\.0\.10)\b"), "pc"),
    (
        re.compile(
            r"(?i)\b(portable[- ]?sds|sur le portable|pc portable|laptop|"
            r"portable[- ]?wifi|sur le wifi|192\.168\.0\.(?:40|77))\b"
        ),
        "portable",
    ),
    (re.compile(r"(?i)\b(omarchy|lbg[-_]?omarchy|ct[- ]?143|192\.168\.0\.143)\b"), "omarchy"),
    (re.compile(r"(?i)\b(lbg[-_]?hands|linux[-_]?agent|ct[- ]?142|192\.168\.0\.142)\b"), "hands"),
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
    # ``+`` autorisé pour ``notepad++`` (normalisé ensuite en ``notepadpp``).
    if not re.match(r"^[A-Za-z0-9_.+\-]+$", first):
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
    # Garder ``notepad`` (bloc-notes Windows). ``notepad++`` → ``notepadpp``
    # seulement si l'utilisateur le demande explicitement (N++ pas toujours installé).
    if slug in {"notepad++", "notepadplusplus"}:
        slug = "notepadpp"
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


def _parse_desktop_targets_env() -> list[dict[str, str]]:
    raw = os.getenv("LBG_DESKTOP_TARGETS", "").strip()
    if not raw:
        return []
    try:
        import json

        data = json.loads(raw)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    out: list[dict[str, str]] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        tid = str(row.get("id") or "").strip()
        url = str(row.get("url") or "").strip().rstrip("/")
        host = str(row.get("host") or "").strip()
        label = str(row.get("label") or tid or host).strip()
        if not tid or not url:
            continue
        aliases = row.get("aliases") if isinstance(row.get("aliases"), list) else []
        out.append(
            {
                "id": tid,
                "url": url,
                "host": host,
                "label": label or tid,
                "aliases": ",".join(str(a).strip().lower() for a in aliases if str(a).strip()),
            }
        )
    return out


def infer_desktop_target_id(text: str) -> str | None:
    """Id logique (pc / portable / …) depuis le prompt NL."""
    raw = text or ""
    for cre, tid in _TARGET_FROM_TEXT_RE:
        if cre.search(raw):
            return tid
    return None


# Topologie LAB si `LBG_DESKTOP_TARGETS` absent du conteneur Orch (.100).
_LAB_DESKTOP_FALLBACK: list[dict[str, str]] = [
    {
        "id": "pc",
        "url": "http://192.168.0.10:5005",
        "host": "192.168.0.10",
        "label": "pc-windows",
        "aliases": "desktop,windows",
    },
    {
        "id": "portable",
        "url": "http://192.168.0.77:5005",
        "host": "192.168.0.77",
        "label": "portable-sds",
        "aliases": "portable-sds,laptop,pc-portable,wifi,portable-wifi,192.168.0.40",
    },
    {
        "id": "omarchy",
        "url": "http://192.168.0.143:5005",
        "host": "192.168.0.143",
        "label": "lbg-omarchy",
        "aliases": "omarchy,lbg-omarchy,hands",
    },
]


def resolve_desktop_worker(
    prompt: str,
    *,
    settings: Settings,
) -> tuple[str, str, str]:
    """Retourne ``(worker_url, label, target_id)`` pour le poste cible."""
    targets = _parse_desktop_targets_env() or list(_LAB_DESKTOP_FALLBACK)
    want = infer_desktop_target_id(prompt)
    if want and targets:
        want_l = want.lower()
        for t in targets:
            tid = t["id"].lower()
            aliases = {a for a in t["aliases"].split(",") if a} | {tid, t["label"].lower(), t["host"]}
            if want_l in aliases or want_l == tid:
                return t["url"], t["label"], t["id"]
    # défaut : worker legacy / pc
    if targets:
        for prefer in ("pc", "default"):
            for t in targets:
                if t["id"].lower() == prefer:
                    return t["url"], t["label"], t["id"]
        t0 = targets[0]
        return t0["url"], t0["label"], t0["id"]
    url = _desktop_worker_url(settings)
    return url, "windows-desktop", "pc"


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


def _format_worker_reply(
    data: dict[str, Any],
    action: dict[str, Any],
    *,
    label: str = "windows-desktop",
) -> str:
    app = action.get("app") or "?"
    where = (label or "windows-desktop").strip() or "windows-desktop"
    if data.get("ok") is True or data.get("outcome") in ("ok", "dry_run"):
        outcome = data.get("outcome") or "ok"
        extra = ""
        if outcome == "dry_run":
            extra = (
                f"\n_Simulation : `LBG_DESKTOP_DRY_RUN=1` sur le worker ({where}). "
                "Passe à `0` dans `desktop.env` puis redémarre l’agent pour un vrai open._"
            )
        return (
            f"**Desktop** : `{app}` — {outcome} sur {where} "
            f"(worker Agent_IA).{extra}"
        )
    err = data.get("error") or data.get("detail") or "échec"
    hint = data.get("hint") or ""
    return f"Desktop worker ({where}) : `{app}` — {err}" + (f"\n_{hint}_" if hint else "")


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
    worker, target_label, target_id = resolve_desktop_worker(cleaned, settings=settings)
    # Cockpit P03 historiquement ancré sur le PC `.10` — cible explicite (portable, omarchy…)
    # → worker direct pour ne pas ouvrir l'app sur la mauvaise machine.
    prefer_direct = target_id.lower() not in ("pc", "default", "")

    # 1) Cockpit / P03 tasks/run (poste défaut uniquement)
    token = _pilot_token()
    if token and not prefer_direct:
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
                "desktop_target": target_id,
                "desktop_target_host": worker.rsplit("//", 1)[-1].split(":")[0]
                if "://" in worker
                else target_id,
                "desktop_target_url": worker,
                "desktop_target_label": target_label,
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

    # 2) Worker Windows / Linux direct (cible résolue : portable-sds, pc, …)
    approval = _desktop_approval()
    approval_mode = (
        os.getenv("LBG_DESKTOP_APPROVAL_MODE", "").strip().lower()
        or ("confirm" if os.getenv("LBG_COMPAGNON_LAB", "").strip() in ("1", "true", "yes", "on") else "")
    )
    ctx: dict[str, Any] = {
        "desktop_dry_run": bool(dry_run),
        "desktop_action": action,
        "desktop_target": target_id,
        "desktop_target_host": worker.rsplit("//", 1)[-1].split(":")[0]
        if "://" in worker
        else target_id,
    }
    if not dry_run:
        if approval_mode in ("confirm", "soft", "lab"):
            # Sentinelle LAB — alignée ActionCard / soft-confirm agents
            ctx["desktop_approval"] = "confirmed"
            ctx["desktop_confirm"] = True
        elif approval:
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
                    f"Worker desktop `{worker}` ({target_label}) HTTP {r.status_code}. "
                    "Configure `LBG_PILOT_API_TOKEN` (Cockpit) ou `LBG_DESKTOP_APPROVAL_TOKEN`."
                ),
                "source": "desktop",
                "via": "worker_invoke",
                "latency": latency,
                "app": action["app"],
                "desktop": {"target": target_id, "label": target_label, "url": worker},
            }
        return {
            "ok": data.get("ok") is True,
            "content": _format_worker_reply(data, action, label=target_label),
            "source": "desktop",
            "via": "worker_invoke",
            "latency": latency,
            "app": action["app"],
            "outcome": data.get("outcome"),
            "desktop": {"target": target_id, "label": target_label, "url": worker},
        }
    except Exception as e:
        latency = time.monotonic() - t0
        return {
            "ok": False,
            "content": (
                f"Desktop indisponible sur {target_label} (`{worker}`) "
                f"({type(e).__name__}: {e}). "
                "Utilise Cockpit Supervisé http://192.168.0.100:8093/pilot/#/cockpit "
                "ou configure les jetons Orch (`LBG_PILOT_API_TOKEN` / `LBG_DESKTOP_APPROVAL_TOKEN`)."
            ),
            "source": "desktop",
            "via": "error",
            "latency": latency,
            "app": action["app"],
            "desktop": {"target": target_id, "label": target_label, "url": worker},
        }
