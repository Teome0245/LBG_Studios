from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from mail_imap_preview import run_mail_imap_preview
from pydantic import BaseModel, Field

import core
import session_emitter
from face_parts_import_action import run_import_face_parts
import agent_desktop


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    session_emitter.start_socket_server()
    yield


app = FastAPI(title="lbg-linux-agent-ia", version="0.1.0", lifespan=_lifespan)


class InvokeRequest(BaseModel):
    actor_id: str
    text: str = Field(default="")
    context: dict[str, Any] = Field(default_factory=dict)


class SessionDecisionBody(BaseModel):
    v: int = 1
    approval_id: str
    decision: str
    scope: str = "once"
    ts: str | None = None


@app.get("/healthz")
def healthz() -> dict[str, object]:
    allow_urls = core.url_allowlist()
    allow_hosts = core.url_host_allowlist()
    allow_dirs = core.file_allowlist_dirs()
    return {
        "status": "ok",
        "service": "agent_ia_linux",
        "version": "0.1.0",
        "linux": {
            "env_file": str(core.env_path()),
            "dry_run_env": core.get_cfg("LBG_LINUX_DRY_RUN").strip() or None,
            "url_allowlist_count": len(allow_urls),
            "url_allowlist_preview": allow_urls[:5],
            "url_host_allowlist_count": len(allow_hosts),
            "url_host_allowlist_preview": allow_hosts[:5],
            "file_allowlist_dirs_count": len(allow_dirs),
            "file_allowlist_dirs_preview": [str(p) for p in allow_dirs[:5]],
            "approval_gate_active": bool(core.get_cfg("LBG_LINUX_APPROVAL_TOKEN").strip()),
            "audit_log_path_set": bool(core.get_cfg("LBG_LINUX_AUDIT_LOG_PATH").strip()),
            "learn_enabled": core.learn_enabled(),
            "web_search_enabled": core.web_search_enabled(),
            "search_engine": core.linux_search_engine(),
            "mail_imap_enabled": core.mail_imap_enabled(),
            "face_parts_enabled": core.get_cfg("LBG_LINUX_FACE_PARTS_ENABLED").strip().lower() in {"1", "true", "yes", "on"},
        },
        "session": core.session_info(),
        "presence_agents": session_emitter.status(),
        "agent_desktop": agent_desktop.get_status(),
    }


@app.get("/session/stream")
async def session_stream() -> StreamingResponse:
    """SSE Présence Agents — events session.* (opt-in LBG_SESSION_ISLAND_ENABLED)."""
    return StreamingResponse(
        session_emitter.stream_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/session/recent")
def session_recent(limit: int = 50) -> dict[str, object]:
    return {"ok": True, "events": session_emitter.recent(max(1, min(limit, 200)))}


@app.post("/session/decision")
def session_decision(body: SessionDecisionBody) -> dict[str, object]:
    return session_emitter.apply_decision(body.model_dump())


@app.get("/session/status")
def session_status() -> dict[str, object]:
    return {"ok": True, **session_emitter.status()}


@app.post("/invoke")
def invoke(payload: InvokeRequest) -> dict[str, object]:
    ctx = payload.context if isinstance(payload.context, dict) else {}
    action = ctx.get("desktop_action")
    trace_id = ctx.get("_trace_id") if isinstance(ctx.get("_trace_id"), str) else None
    dry_run = core.linux_dry_run(ctx)

    base: dict[str, object] = {
        "agent": "agent_ia_linux",
        "handler": "desktop",
        "actor_id": payload.actor_id,
        "request_text": payload.text,
        "meta": {"dry_run": dry_run, "execution_gated": core.linux_requires_approval()},
    }

    if not isinstance(action, dict):
        out = {**base, "ok": False, "outcome": "bad_request", "error": "Aucune desktop_action dans context."}
        core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
        return out

    kind = str(action.get("kind") or "").strip()

    if kind == "agent_session_status":
        sess = core.session_info()
        out = {
            **base,
            "ok": True,
            "outcome": "dry_run" if dry_run else "ok",
            "session": sess,
            "reply": (
                f"Omarchy gui_ready={sess.get('gui_ready')} wayland={sess.get('wayland_display')} "
                f"svc={sess.get('user_service_active')}"
            ),
        }
        core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
        return out

    if kind in ("fix_session0", "heal_desktop_agent"):
        # Même kind que Windows Session 0 — ici = heal service + check Wayland.
        if not dry_run and core.linux_requires_approval() and not core.linux_approval_ok(ctx):
            out = {**base, "ok": False, "outcome": "approval_denied", "error": "Approval token requis"}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        result = core.heal_desktop_agent(dry_run=dry_run)
        out = {**base, **result}
        core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
        return out

    if kind in ("update_vscode", "vscode_update"):
        # MAJ paquet AUR visual-studio-code-bin — ne pas lancer si une session Cline/IDE est critique.
        if not dry_run and core.linux_requires_approval() and not core.linux_approval_ok(ctx):
            out = {**base, "ok": False, "outcome": "approval_denied", "error": "Approval token requis"}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        result = core.update_vscode(dry_run=dry_run)
        out = {**base, **result, "kind": "update_vscode"}
        core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
        return out

    if kind == "open_url":
        url = action.get("url")
        if not isinstance(url, str) or not url.strip():
            out = {**base, "ok": False, "outcome": "bad_request", "error": "Champ `url` requis"}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        url = url.strip()
        if not core.url_is_allowed(url):
            out = {
                **base,
                "ok": False,
                "outcome": "allowlist_denied",
                "error": "URL non autorisée",
                "url": url,
                "url_host_allowlist_preview": core.url_host_allowlist()[:5],
            }
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        if not dry_run and core.linux_requires_approval() and not core.linux_approval_ok(ctx):
            out = {**base, "ok": False, "outcome": "approval_denied", "error": "Approval token requis", "url": url}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        if dry_run:
            out = {**base, "ok": True, "outcome": "dry_run", "url": url}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        try:
            # best-effort: xdg-open
            core.popen_quiet(["xdg-open", url])
            out = {**base, "ok": True, "outcome": "ok", "url": url}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        except Exception as e:
            out = {**base, "ok": False, "outcome": "error", "error": str(e), "url": url}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out

    if kind == "search_web_open":
        if not core.web_search_enabled():
            out = {
                **base,
                "ok": False,
                "outcome": "feature_disabled",
                "error": "Recherche web désactivée (LBG_LINUX_WEB_SEARCH=1 pour activer)",
            }
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        query = action.get("query")
        if not isinstance(query, str) or not query.strip():
            out = {**base, "ok": False, "outcome": "bad_request", "error": "Champ `query` requis"}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        url3, qerr = core.build_web_search_url(query)
        if not url3 or qerr:
            out = {**base, "ok": False, "outcome": "bad_request", "error": qerr or "requête invalide"}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        if not core.web_search_url_trusted(url3):
            out = {**base, "ok": False, "outcome": "error", "error": "URL de recherche interne invalide", "url": url3}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        if not dry_run and core.linux_requires_approval() and not core.linux_approval_ok(ctx):
            out = {**base, "ok": False, "outcome": "approval_denied", "error": "Approval token requis", "url": url3}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        if dry_run:
            out = {**base, "ok": True, "outcome": "dry_run", "url": url3, "engine": core.linux_search_engine()}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        try:
            core.popen_quiet(["xdg-open", url3])
            out = {**base, "ok": True, "outcome": "ok", "url": url3, "engine": core.linux_search_engine()}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        except Exception as e:
            out = {**base, "ok": False, "outcome": "error", "error": str(e), "url": url3}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out

    if kind == "mail_imap_preview":
        if not core.mail_imap_enabled():
            out = {
                **base,
                "ok": False,
                "outcome": "feature_disabled",
                "error": "Messagerie IMAP désactivée (LBG_LINUX_MAIL_ENABLED=1 pour activer)",
            }
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        fc_ok, sc_ok, max_m, max_b, max_sc, perr = core.mail_imap_parse_action(action)
        if perr:
            out = {**base, "ok": False, "outcome": "bad_request", "error": perr}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        host, port, user, password, use_ssl, insecure_ssl = core.mail_imap_credentials()
        if not dry_run and core.linux_requires_approval() and not core.linux_approval_ok(ctx):
            out = {
                **base,
                "ok": False,
                "outcome": "approval_denied",
                "error": "Approval token requis",
                "from_contains": fc_ok,
                "subject_contains": sc_ok,
            }
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        if dry_run:
            hint_q = fc_ok or sc_ok
            configured = bool(host and user and password)
            body = (
                "[dry-run] IMAP configuré — aucune connexion en simulation ; Réel lira l'INBOX."
                if configured
                else "[dry-run] Aucune connexion IMAP ; définir LBG_LINUX_MAIL_IMAP_* pour une exécution réelle."
            )
            messages = [
                {
                    "uid": "(dry-run)",
                    "from": "expéditeur@exemple.invalid",
                    "subject": f"… filtre « {hint_q} » (simulation)",
                    "date": "",
                    "body_preview": body,
                }
            ]
            out = {
                **base,
                "ok": True,
                "outcome": "dry_run",
                "messages": messages,
                "matched_count": len(messages),
                "from_contains": fc_ok,
                "subject_contains": sc_ok,
                "imap_configured": configured,
            }
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        if not host or not user or not password:
            out = {
                **base,
                "ok": False,
                "outcome": "configuration_error",
                "error": "IMAP incomplet : LBG_LINUX_MAIL_IMAP_HOST, USER et PASSWORD requis",
            }
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        msgs, ierr = run_mail_imap_preview(
            host=host,
            port=port,
            user=user,
            password=password,
            use_ssl=use_ssl,
            from_contains=fc_ok,
            subject_contains=sc_ok,
            max_messages=max_m,
            max_body_chars=max_b,
            max_scan=max_sc,
            insecure_ssl=insecure_ssl,
        )
        if ierr:
            out = {
                **base,
                "ok": False,
                "outcome": "error",
                "error": ierr,
                "from_contains": fc_ok,
                "subject_contains": sc_ok,
            }
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        out = {
            **base,
            "ok": True,
            "outcome": "ok",
            "messages": msgs,
            "matched_count": len(msgs),
            "from_contains": fc_ok,
            "subject_contains": sc_ok,
        }
        core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
        return out

    if kind == "file_read":
        path = action.get("path")
        if not isinstance(path, str) or not path.strip():
            out = {**base, "ok": False, "outcome": "bad_request", "error": "Champ `path` requis"}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        path = path.strip()
        if not core.path_is_allowed(path):
            out = {
                **base,
                "ok": False,
                "outcome": "allowlist_denied",
                "error": "Chemin non autorisé",
                "path": path,
                "file_allowlist_dirs_preview": [str(p) for p in core.file_allowlist_dirs()[:5]],
            }
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        # Lecture allowlist : soft-confirm suffit (plan_evolutions sync orch→.143)
        if not dry_run and core.linux_requires_approval() and not core.linux_approval_ok(ctx):
            out = {**base, "ok": False, "outcome": "approval_denied", "error": "Approval token requis", "path": path}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        try:
            max_chars = int(action.get("max_chars") or 512_000)
        except (TypeError, ValueError):
            max_chars = 512_000
        max_chars = max(1024, min(max_chars, 2_000_000))
        if dry_run:
            out = {**base, "ok": True, "outcome": "dry_run", "path": path, "max_chars": max_chars}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        try:
            p = Path(path).expanduser()
            raw = p.read_text(encoding="utf-8")
            truncated = len(raw) > max_chars
            text = raw[:max_chars]
            out = {
                **base,
                "ok": True,
                "outcome": "ok",
                "path": str(p),
                "text": text,
                "bytes": len(text.encode("utf-8")),
                "truncated": truncated,
            }
            core.audit_write(
                {
                    "event": "agents.linux.audit",
                    "trace_id": trace_id,
                    "ok": True,
                    "outcome": "ok",
                    "kind": "file_read",
                    "path": str(p),
                    "bytes": out["bytes"],
                }
            )
            return out
        except Exception as e:
            out = {**base, "ok": False, "outcome": "error", "error": str(e), "path": path}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out

    if kind == "file_append":
        path = action.get("path")
        content = action.get("text")
        if not isinstance(path, str) or not path.strip():
            out = {**base, "ok": False, "outcome": "bad_request", "error": "Champ `path` requis"}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        if not isinstance(content, str):
            out = {**base, "ok": False, "outcome": "bad_request", "error": "Champ `text` requis"}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        path = path.strip()
        if not core.path_is_allowed(path):
            out = {
                **base,
                "ok": False,
                "outcome": "allowlist_denied",
                "error": "Chemin non autorisé",
                "path": path,
                "file_allowlist_dirs_preview": [str(p) for p in core.file_allowlist_dirs()[:5]],
            }
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        if not dry_run and core.linux_requires_approval() and not core.linux_approval_ok(ctx):
            out = {**base, "ok": False, "outcome": "approval_denied", "error": "Approval token requis", "path": path}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        if dry_run:
            out = {**base, "ok": True, "outcome": "dry_run", "path": path, "bytes": len(content.encode("utf-8"))}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        try:
            p = Path(path).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.open("a", encoding="utf-8").write(content)
            out = {**base, "ok": True, "outcome": "ok", "path": str(p), "bytes": len(content.encode("utf-8"))}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        except Exception as e:
            out = {**base, "ok": False, "outcome": "error", "error": str(e), "path": path}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out

    if kind == "open_app":
        app_id = action.get("app")
        args = action.get("args")
        want_learn = action.get("learn") is True
        if not isinstance(app_id, str) or not app_id.strip():
            out = {**base, "ok": False, "outcome": "bad_request", "error": "Champ `app` requis"}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        app_id = app_id.strip()
        allow = core.split_csv((core.get_cfg("LBG_LINUX_APP_ALLOWLIST") or "").strip())
        if app_id not in allow:
            out = {
                **base,
                "ok": False,
                "outcome": "allowlist_denied",
                "error": "Application non autorisée",
                "app": app_id,
                "app_allowlist_preview": allow[:10],
            }
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        if args is None:
            args_list: list[str] = []
        elif isinstance(args, list) and all(isinstance(x, str) for x in args):
            args_list = [x for x in args if x.strip()]
        else:
            out = {**base, "ok": False, "outcome": "bad_request", "error": "Champ `args` doit être list[string]"}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out

        if not dry_run and core.linux_requires_approval() and not core.linux_approval_ok(ctx):
            out = {**base, "ok": False, "outcome": "approval_denied", "error": "Approval token requis", "app": app_id}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        if dry_run:
            out = {**base, "ok": True, "outcome": "dry_run", "app": app_id, "args": args_list}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out

        map_raw = (core.get_cfg("LBG_LINUX_APP_MAP_JSON") or "").strip()
        try:
            mapping = json.loads(map_raw) if map_raw else {}
            if not isinstance(mapping, dict):
                mapping = {}
        except Exception:
            mapping = {}
        cmd = mapping.get(app_id) if isinstance(mapping, dict) else None

        cmd_list: list[str]
        if isinstance(cmd, str) and cmd.strip():
            cmd_list = [cmd.strip()]
        elif isinstance(cmd, list) and all(isinstance(x, str) for x in cmd) and cmd:
            cmd_list = [x.strip() for x in cmd if x.strip()]
        else:
            cmd_list = [app_id]

        try:
            core.popen_quiet([*cmd_list, *args_list])
            out = {**base, "ok": True, "outcome": "ok", "app": app_id, "args": args_list}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        except Exception as e:
            if (
                want_learn
                and not dry_run
                and core.learn_enabled()
                and (not core.learn_allowlist() or app_id in core.learn_allowlist())
                and (not core.linux_requires_approval() or core.linux_approval_ok(ctx))
            ):
                resolved = core.which(app_id)
                if resolved:
                    okp, errp = core.persist_learned_app(app_id, resolved)
                    if okp:
                        try:
                            core.popen_quiet([resolved, *args_list])
                            out = {
                                **base,
                                "ok": True,
                                "outcome": "ok",
                                "app": app_id,
                                "args": args_list,
                                "learned": True,
                                "learned_path": resolved,
                            }
                            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
                            return out
                        except Exception as e2:
                            out = {
                                **base,
                                "ok": False,
                                "outcome": "error",
                                "error": str(e2),
                                "app": app_id,
                                "args": args_list,
                                "learned": True,
                                "learned_path": resolved,
                            }
                            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
                            return out
                    out = {
                        **base,
                        "ok": False,
                        "outcome": "error",
                        "error": f"{e} | learn_persist_failed: {errp}",
                        "app": app_id,
                        "args": args_list,
                        "learned": False,
                    }
                    core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
                    return out

            out = {**base, "ok": False, "outcome": "error", "error": str(e), "app": app_id, "args": args_list}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out

    if kind == "import_face_parts":
        if not dry_run and core.linux_requires_approval() and not core.linux_approval_ok(ctx):
            out = {**base, "ok": False, "outcome": "approval_denied", "error": "Approval token requis", "kind": kind}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        result = run_import_face_parts(action=action, get_cfg=core.get_cfg, dry_run=dry_run)
        out = {**base, **result, "kind": kind}
        core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
        return out

    if kind in ("run_cli_agent", "ide_cli", "cli_agent"):
        # ADR 0025 — mains code headless (Claude Code / Cline / OpenCode)
        if not dry_run and core.linux_requires_approval() and not core.linux_approval_ok(ctx):
            out = {**base, "ok": False, "outcome": "approval_denied", "error": "Approval token requis", "kind": "run_cli_agent"}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        app = str(action.get("app") or ctx.get("ide_cli_app") or "opencode").strip()
        prompt = str(action.get("prompt") or ctx.get("ide_cli_prompt") or text or "").strip()
        cwd = action.get("cwd") or ctx.get("ide_cli_cwd")
        cwd_s = str(cwd).strip() if isinstance(cwd, str) else None
        to = action.get("timeout_s")
        try:
            to_i = int(to) if to is not None else None
        except (TypeError, ValueError):
            to_i = None
        result = core.run_cli_agent(
            app=app,
            prompt=prompt,
            cwd=cwd_s,
            dry_run=dry_run,
            timeout_s=to_i,
        )
        out = {**base, **result, "kind": "run_cli_agent"}
        core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
        return out

    # --- Intégration agent-desktop (Vercel Labs : computer use via accessibilité AT-SPI / D-Bus) ---
    if kind in {"ui_snapshot", "desktop_snapshot", "observe_ui"}:
        app_name = action.get("app")
        interactive_only = action.get("interactive", action.get("interactive_only", True))
        compact = action.get("compact", True)
        skeleton = action.get("skeleton", False)
        root_ref = action.get("root_ref") or action.get("root")
        timeout_s = float(action.get("timeout_s", 12.0))
        res = agent_desktop.run_snapshot(
            app=str(app_name) if app_name else None,
            interactive_only=bool(interactive_only),
            compact=bool(compact),
            skeleton=bool(skeleton),
            root_ref=str(root_ref) if root_ref else None,
            timeout_s=timeout_s,
            dry_run=dry_run,
        )
        out = {**base, **res, "kind": kind}
        core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
        return out

    if kind in {"ui_click", "desktop_click"}:
        if not dry_run and core.linux_requires_approval() and not core.linux_approval_ok(ctx):
            out = {**base, "ok": False, "outcome": "approval_denied", "error": "Approval token requis", "kind": kind}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        ref = action.get("ref") or action.get("target") or ""
        button = str(action.get("button") or "left")
        clicks = int(action.get("clicks") or 1)
        headed = bool(action.get("headed", False))
        timeout_s = float(action.get("timeout_s", 8.0))
        res = agent_desktop.run_click(
            ref=str(ref),
            button=button,
            clicks=clicks,
            headed=headed,
            timeout_s=timeout_s,
            dry_run=dry_run,
        )
        out = {**base, **res, "kind": kind}
        core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
        return out

    if kind in {"ui_type", "desktop_type"}:
        if not dry_run and core.linux_requires_approval() and not core.linux_approval_ok(ctx):
            out = {**base, "ok": False, "outcome": "approval_denied", "error": "Approval token requis", "kind": kind}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        ref = action.get("ref") or action.get("target") or ""
        text_val = str(action.get("text") or "")
        headed = bool(action.get("headed", False))
        timeout_s = float(action.get("timeout_s", 10.0))
        res = agent_desktop.run_type(
            ref=str(ref),
            text=text_val,
            headed=headed,
            timeout_s=timeout_s,
            dry_run=dry_run,
        )
        out = {**base, **res, "kind": kind}
        core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
        return out

    if kind in {"ui_press", "desktop_press"}:
        if not dry_run and core.linux_requires_approval() and not core.linux_approval_ok(ctx):
            out = {**base, "ok": False, "outcome": "approval_denied", "error": "Approval token requis", "kind": kind}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        key = str(action.get("key") or "")
        headed = bool(action.get("headed", False))
        timeout_s = float(action.get("timeout_s", 5.0))
        res = agent_desktop.run_press(
            key=key,
            headed=headed,
            timeout_s=timeout_s,
            dry_run=dry_run,
        )
        out = {**base, **res, "kind": kind}
        core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
        return out

    if kind in {"ui_scroll", "desktop_scroll"}:
        if not dry_run and core.linux_requires_approval() and not core.linux_approval_ok(ctx):
            out = {**base, "ok": False, "outcome": "approval_denied", "error": "Approval token requis", "kind": kind}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        ref = action.get("ref") or action.get("target")
        direction = str(action.get("direction") or "down")
        amount = int(action.get("amount") or 3)
        headed = bool(action.get("headed", False))
        timeout_s = float(action.get("timeout_s", 5.0))
        res = agent_desktop.run_scroll(
            ref=str(ref) if ref else None,
            direction=direction,
            amount=amount,
            headed=headed,
            timeout_s=timeout_s,
            dry_run=dry_run,
        )
        out = {**base, **res, "kind": kind}
        core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
        return out

    if kind in {"ui_focus", "desktop_focus"}:
        if not dry_run and core.linux_requires_approval() and not core.linux_approval_ok(ctx):
            out = {**base, "ok": False, "outcome": "approval_denied", "error": "Approval token requis", "kind": kind}
            core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
            return out
        ref = action.get("ref") or action.get("target") or ""
        headed = bool(action.get("headed", False))
        timeout_s = float(action.get("timeout_s", 5.0))
        res = agent_desktop.run_focus(
            ref=str(ref),
            headed=headed,
            timeout_s=timeout_s,
            dry_run=dry_run,
        )
        out = {**base, **res, "kind": kind}
        core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
        return out

    out = {**base, "ok": False, "outcome": "unknown_kind", "error": "Action inconnue", "kind": kind}
    core.audit_write({"event": "agents.linux.audit", "trace_id": trace_id, **out})
    return out

