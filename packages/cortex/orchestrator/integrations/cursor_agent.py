"""Client Cursor Cloud Agent — exécutant code/PR (pas un LLM chat).

Opt-in : LBG_CURSOR_AGENT_ENABLED=1 + CURSOR_API_KEY.
Runtime cloud explicite (repos allowlist) ; dry-run sans réseau si disabled.
"""

from __future__ import annotations

import os
from typing import Any


def enabled() -> bool:
    return os.environ.get("LBG_CURSOR_AGENT_ENABLED", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def api_key() -> str:
    return os.environ.get("CURSOR_API_KEY", "").strip()


def api_key_configured() -> bool:
    return bool(api_key())


def repos_allowlist() -> list[str]:
    raw = os.environ.get("LBG_CURSOR_AGENT_REPOS", "").strip()
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def default_model() -> str:
    return os.environ.get("LBG_CURSOR_AGENT_MODEL", "composer-2.5").strip() or "composer-2.5"


def health() -> dict[str, Any]:
    sdk_ok = False
    sdk_err = None
    try:
        import cursor_sdk  # noqa: F401

        sdk_ok = True
    except Exception as e:
        sdk_err = str(e)
    return {
        "service": "cursor_cloud_agent",
        "enabled": enabled(),
        "api_key_configured": api_key_configured(),
        "repos_allowlist": repos_allowlist(),
        "sdk_installed": sdk_ok,
        "sdk_error": sdk_err,
        "model": default_model(),
        "ready": enabled() and api_key_configured() and sdk_ok,
        "note": "Exécutant PR/code distant — pas un provider chat LLM",
    }


def launch_agent_dry_run(
    *,
    prompt: str,
    repository: str,
    model: str | None = None,
) -> dict[str, Any]:
    allowed = repos_allowlist()
    repo_ok = (not allowed) or (repository in allowed)
    h = health()
    return {
        "ok": bool(h["ready"] and repo_ok and prompt.strip() and repository.strip()),
        "dry_run": True,
        "enabled": enabled(),
        "repository": repository,
        "repo_allowed": repo_ok,
        "model": model or default_model(),
        "prompt_preview": (prompt or "")[:240],
        "health": h,
    }


def launch_cloud_agent(
    *,
    prompt: str,
    repository: str,
    model: str | None = None,
    auto_create_pr: bool = True,
    wait: bool = True,
) -> dict[str, Any]:
    """Lance un Cloud Agent Cursor sur un repo allowlisté."""
    if not enabled():
        return {"ok": False, "error": "LBG_CURSOR_AGENT_ENABLED=0", "dry_run": False}
    key = api_key()
    if not key:
        return {"ok": False, "error": "CURSOR_API_KEY manquante", "dry_run": False}
    repo = (repository or "").strip()
    if not repo:
        return {"ok": False, "error": "repository requis (owner/name)", "dry_run": False}
    # Normalise owner/name → URL GitHub pour le SDK cloud
    if "://" not in repo and repo.count("/") == 1:
        repo_url = f"https://github.com/{repo}"
    else:
        repo_url = repo
    allowed = repos_allowlist()
    # allowlist accepte owner/name ou URL
    if allowed:
        short = repo if "://" not in repo else "/".join(repo.rstrip("/").split("/")[-2:])
        ok_allow = repo in allowed or repo_url in allowed or short in allowed
        if not ok_allow:
            return {"ok": False, "error": f"repo hors allowlist: {repo}", "dry_run": False, "allowlist": allowed}
    text = (prompt or "").strip()
    if not text:
        return {"ok": False, "error": "prompt vide", "dry_run": False}

    try:
        from cursor_sdk import Agent, CloudAgentOptions, CursorAgentError
    except Exception as e:
        return {
            "ok": False,
            "error": f"cursor-sdk non installé: {e}",
            "hint": "pip install cursor-sdk",
            "dry_run": False,
        }

    model_id = model or default_model()
    skip_reviewer = os.environ.get("LBG_CURSOR_AGENT_SKIP_REVIEWER", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    try:
        with Agent.create(
            model=model_id,
            api_key=key,
            cloud=CloudAgentOptions(
                repos=[{"url": repo_url}],
                auto_create_pr=auto_create_pr,
                skip_reviewer_request=skip_reviewer,
            ),
        ) as agent:
            agent_id = getattr(agent, "agent_id", None) or getattr(agent, "agentId", None)
            run = agent.send(text)
            run_id = getattr(run, "id", None)
            out: dict[str, Any] = {
                "ok": True,
                "agent_id": agent_id,
                "run_id": run_id,
                "repository": repo,
                "repository_url": repo_url,
                "model": model_id,
                "auto_create_pr": auto_create_pr,
            }
            if wait:
                result = run.wait()
                status = getattr(result, "status", None)
                out["status"] = status
                out["result"] = getattr(result, "result", None)
                out["ok"] = status == "finished"
                if status == "error":
                    out["ok"] = False
                    out["error"] = "run finished with status=error"
            return out
    except Exception as e:
        name = type(e).__name__
        retryable = getattr(e, "is_retryable", getattr(e, "isRetryable", None))
        return {
            "ok": False,
            "error": str(e),
            "error_type": name,
            "retryable": retryable,
            "dry_run": False,
        }
