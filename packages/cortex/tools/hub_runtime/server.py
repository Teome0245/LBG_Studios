#!/usr/bin/env python3
"""Hub runtime spike — FastAPI HTTP (C10/C11) + WebSocket lbg-ws/2 (hors Core3).

Usage:
  cd packages/cortex && .venv/bin/python -m tools.hub_runtime.server
  # ou: uvicorn tools.hub_runtime.server:app --host 127.0.0.1 --port 8787
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# packages/cortex on path
_CORTEX = Path(__file__).resolve().parents[2]
_AGENTS = _CORTEX / "agents" / "src"
for p in (_CORTEX, _AGENTS):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from tools.hub_runtime.sim import HUMAN_OID, SIM


def _load_agent_catalog():  # type: ignore[no-untyped-def]
    """Charge agent_catalog sans passer par lbg_agents.__init__ (httpx/dispatch)."""
    import importlib.util

    candidates = [
        _AGENTS / "lbg_agents" / "agent_catalog.py",
        Path("/opt/LBG_IA_MMO/agents/src/lbg_agents/agent_catalog.py"),
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            spec = importlib.util.spec_from_file_location("lbg_agent_catalog_hub", path)
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
        except Exception:
            continue
    try:
        from lbg_agents import agent_catalog as ac  # noqa: WPS433

        return ac
    except ImportError:
        return None


ac = _load_agent_catalog()

HOST = os.environ.get("LBG_HUB_RUNTIME_HOST", "127.0.0.1")
PORT = int(os.environ.get("LBG_HUB_RUNTIME_PORT", "8787"))
TICK_HZ = float(os.environ.get("LBG_HUB_RUNTIME_TICK_HZ", "20"))

app = FastAPI(title="LBG Hub Runtime", version="0.1.0-spike")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_clients: dict[WebSocket, dict[str, Any]] = {}
_broadcast_task: asyncio.Task[None] | None = None


async def _broadcast_raw(raw: str) -> None:
    dead: list[WebSocket] = []
    for ws in list(_clients.keys()):
        try:
            await ws.send_text(raw)
        except Exception:
            dead.append(ws)
    for ws in dead:
        meta = _clients.pop(ws, None)
        if meta and meta.get("oid"):
            SIM.remove_human(int(meta["oid"]))


async def _broadcast_chat_msg(msg: dict[str, Any]) -> None:
    await _broadcast_raw(json.dumps(msg, ensure_ascii=False))


async def _flush_chat_queue() -> None:
    for msg in SIM.drain_chat():
        await _broadcast_chat_msg(msg)


_llm_say_busy = False


async def _process_one_llm_say() -> None:
    global _llm_say_busy
    if _llm_say_busy:
        return
    reqs = SIM.drain_llm_say_requests()
    if not reqs:
        return
    req = reqs[0]
    for leftover in reqs[1:]:
        SIM._llm_say_requests.append(leftover)
    _llm_say_busy = True
    try:

        def _work() -> str | None:
            from tools.hub_runtime import llm_chat

            return llm_chat.bot_line(
                name=str(req.get("name") or "?"),
                goal=str(req.get("goal") or "explorer"),
                near_human=str(req.get("near") or ""),
                place=str(req.get("place") or "hub"),
            )

        try:
            line = await asyncio.wait_for(asyncio.to_thread(_work), timeout=14.0)
        except Exception:
            line = None
        if line:
            msg = SIM.enqueue_say(
                str(req.get("name") or "?"),
                int(req.get("oid") or 0),
                line,
                source="ia",
                queue=False,
            )
            if msg:
                await _broadcast_chat_msg(msg)
    finally:
        _llm_say_busy = False


@app.on_event("startup")
async def _startup() -> None:
    global _broadcast_task
    SIM.reset()
    _broadcast_task = asyncio.create_task(_sim_loop())


@app.on_event("shutdown")
async def _shutdown() -> None:
    global _broadcast_task
    if _broadcast_task:
        _broadcast_task.cancel()
        try:
            await _broadcast_task
        except asyncio.CancelledError:
            pass


async def _sim_loop() -> None:
    interval = 1.0 / max(1.0, TICK_HZ)
    while True:
        SIM.step()
        await _flush_chat_queue()
        if SIM._llm_say_requests and not _llm_say_busy:
            asyncio.create_task(_process_one_llm_say())
        if _clients:
            dead: list[WebSocket] = []
            # Un payload de base + oid par client (évite N× sim.entity_list)
            base = SIM.zone_state_payload(HUMAN_OID)
            raw_base = json.dumps(base, ensure_ascii=False)
            for ws, meta in list(_clients.items()):
                try:
                    oid = int(meta.get("oid") or HUMAN_OID)
                    if oid == HUMAN_OID:
                        raw = raw_base
                    else:
                        base["your_character_id"] = oid
                        raw = json.dumps(base, ensure_ascii=False)
                    await ws.send_text(raw)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                meta = _clients.pop(ws, None)
                if meta and meta.get("oid"):
                    SIM.remove_human(int(meta["oid"]))
        await asyncio.sleep(interval)


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    from tools.hub_runtime.hub_collision import COLLISION

    return {
        "ok": True,
        "service": "hub_runtime",
        "spike": True,
        "core3": False,
        "tick": SIM.tick,
        "entities": len(SIM.entities),
        "humans": SIM.human_count(),
        "bots": SIM.bot_count(),
        "npcs": SIM.npc_count(),
        "ws_clients": len(_clients),
        "collision_blocks": len(COLLISION.blocks),
        "fence_points": len(COLLISION.fence_ring),
        "enforce_fence": COLLISION.enforce_fence,
    }


@app.get("/catalog")
def catalog(type: str = Query(default="skills", alias="type")) -> JSONResponse:
    if ac is None:
        return JSONResponse({"ok": False, "error": "agent_catalog_missing"}, status_code=501)
    payload = ac.catalog(type)
    return JSONResponse(payload, status_code=200 if payload.get("ok") else 400)


@app.get("/guide")
def guide(playstyle: str = Query(default="prospecteur")) -> JSONResponse:
    if ac is None:
        return JSONResponse({"ok": False, "error": "agent_catalog_missing"}, status_code=501)
    payload = ac.get_guide(playstyle)
    return JSONResponse(payload, status_code=200 if payload.get("ok") else 404)


@app.get("/tick-matrix")
def tick_matrix() -> dict[str, Any]:
    if ac is None:
        return {"ok": False, "error": "agent_catalog_missing"}
    return ac.tick_matrix_payload()


@app.get("/v1/catalog")
def catalog_v1(type: str = Query(default="skills", alias="type")) -> JSONResponse:
    return catalog(type)


@app.get("/v1/guide")
def guide_v1(playstyle: str = Query(default="prospecteur")) -> JSONResponse:
    return guide(playstyle)


@app.get("/v1/tick-matrix")
def tick_matrix_v1() -> dict[str, Any]:
    return tick_matrix()


@app.get("/v1/bots")
def bots_list() -> JSONResponse:
    SIM.ensure()
    return JSONResponse({"ok": True, "bots": SIM.bots_payload(), "count": SIM.bot_count()})


@app.post("/v1/dialogue/invoke")
@app.post("/v1/pilot/agent-dialogue/invoke")
async def dialogue_invoke(body: dict[str, Any]) -> JSONResponse:
    """Phase C — dialogue PNJ stub (compat DialogueBridge Godot)."""
    from tools.hub_runtime.dialogue import invoke as dialogue_invoke_fn

    out = dialogue_invoke_fn(body if isinstance(body, dict) else {})
    return JSONResponse(out, status_code=200 if out.get("ok") else 400)


@app.post("/v1/bots/move_to")
async def bot_move_to(body: dict[str, Any]) -> JSONResponse:
    """Mutation C11 — TickGate si agent_catalog dispo. Cible Nix/Lia/Mira."""
    from tools.hub_runtime.sim import MARKET

    player = str(body.get("player") or "Nix")
    action = "move_to"
    if ac is not None and ac.tick_gate_enabled():
        ok, meta = ac.try_acquire_mutation(player, action)
        if not ok:
            return JSONResponse(meta, status_code=429)
        ac.release_mutation(player)
    x = float(body.get("x", MARKET[0]))
    z = float(body.get("z", MARKET[2]))
    y = float(body.get("y", MARKET[1]))
    ent = SIM.set_bot_target(player, x, y, z)
    if ent is None:
        return JSONResponse({"ok": False, "error": "unknown_bot", "player": player}, status_code=404)
    out: dict[str, Any] = {
        "ok": True,
        "player": ent.name,
        "entity_key": ent.eid,
        "target": [ent.target[0], ent.target[1], ent.target[2]] if ent.target else [x, y, z],
    }
    if ac is not None:
        out = ac.attach_tick_context(out, action)
    return JSONResponse(out)


@app.post("/v1/say")
async def say_v1(body: dict[str, Any]) -> JSONResponse:
    """Chat basique humain/IA — say = free tick (pas de TickGate mutation)."""
    player = str(body.get("player") or body.get("from") or "Nix").strip() or "Nix"
    text = str(body.get("text") or body.get("message") or "").strip()
    if not text:
        return JSONResponse({"ok": False, "error": "empty_text"}, status_code=400)
    SIM.ensure()
    source = str(body.get("source") or "").strip().lower()
    if not source:
        source = "ia" if player.lower() in {"nix", "lia", "mira", "kael"} else "human"
    oid = 0
    bot_key = SIM.resolve_bot_key(player)
    if bot_key:
        bot = SIM.entities.get(bot_key)
        if bot:
            oid = int(bot.oid)
            player = bot.name
            source = "ia"
    else:
        for e in SIM.entities.values():
            if e.kind == "player" and not e.is_bot and e.name.lower() == player.lower():
                oid = int(e.oid)
                break
        if oid == 0:
            oid = int(body.get("oid") or 0)
    msg = SIM.enqueue_say(player, oid or 0, text, source=source, queue=False)
    if msg is None:
        return JSONResponse({"ok": False, "error": "empty_text"}, status_code=400)
    await _broadcast_chat_msg(msg)
    out: dict[str, Any] = {"ok": True, "chat": msg}
    if ac is not None:
        out = ac.attach_tick_context(out, "say")
    return JSONResponse(out)


def _tick_guard(path: str, body: dict[str, Any]) -> JSONResponse | None:
    if ac is None:
        return None
    enabled = getattr(ac, "tick_gate_enabled", None)
    if not callable(enabled) or not enabled():
        return None
    guard_fn = getattr(ac, "http_post_tick_guard", None)
    if not callable(guard_fn):
        return None
    blocked = guard_fn(path, body)
    if blocked is None:
        return None
    if isinstance(blocked, tuple) and len(blocked) == 2:
        status, payload = blocked
        return JSONResponse(payload, status_code=int(status))
    if isinstance(blocked, dict):
        return JSONResponse(blocked, status_code=429)
    return None


def _attach_tick(out: dict[str, Any], action: str) -> dict[str, Any]:
    if ac is None:
        return out
    fn = getattr(ac, "attach_tick_context", None)
    if callable(fn):
        return fn(out, action)
    return out


# --- Peel inventaire / quêtes / craft (contrats sidecar :8791) ---

from tools.hub_runtime.economy import ECONOMY  # noqa: E402
from tools.hub_runtime.auth import AUTH  # noqa: E402
from tools.hub_runtime.sim import HUMAN_OID  # noqa: E402


@app.post("/v1/auth/login")
async def auth_login(body: dict[str, Any]) -> JSONResponse:
    # LbgAuthClient envoie type/username/password
    user = str(body.get("username") or body.get("player") or "")
    pwd = str(body.get("password") or "")
    out = AUTH.register_or_login(user, pwd)
    return JSONResponse(out, status_code=200 if out.get("ok") else 401)


@app.post("/v1/auth/guest")
async def auth_guest(body: dict[str, Any] | None = None) -> JSONResponse:
    body = body or {}
    name = str(body.get("player_name") or body.get("username") or "Voyageur")
    out = AUTH.guest(name)
    return JSONResponse(out, status_code=200 if out.get("ok") else 400)


@app.post("/v1/auth/select_character")
async def auth_select(body: dict[str, Any]) -> JSONResponse:
    token = str(body.get("session_token") or "")
    cid = int(body.get("character_id") or 0)
    out = AUTH.select_character(token, cid)
    return JSONResponse(out, status_code=200 if out.get("ok") else 401)


@app.post("/v1/auth/enter_zone")
async def auth_enter(body: dict[str, Any]) -> JSONResponse:
    token = str(body.get("session_token") or "")
    zone = str(body.get("zone") or "scrapaltai")
    out = AUTH.enter_zone(token, zone)
    return JSONResponse(out, status_code=200 if out.get("ok") else 401)


@app.post("/v1/auth/resolve")
async def auth_resolve(body: dict[str, Any]) -> JSONResponse:
    """Résolution token pour swap process (prime-hub Godot → même sessions Python)."""
    token = str(body.get("session_token") or "")
    sess = AUTH.resolve(token)
    if sess is None:
        return JSONResponse(
            {"ok": False, "error": "session_expired", "message": "token inconnu"},
            status_code=401,
        )
    return JSONResponse(
        {
            "ok": True,
            "username": str(sess.get("username") or "Voyageur"),
            "character_id": int(sess.get("character_id") or HUMAN_OID),
            "source": "hub_runtime",
        }
    )


@app.get("/v1/inventory")
def inventory(player: str = Query(default="Voyageur")) -> dict[str, Any]:
    return ECONOMY.inventory(player)


@app.get("/v1/quests/board")
def quests_board(
    giver: str = Query(default="npc:core3_daan_oth"),
    player: str = Query(default="Voyageur"),
) -> dict[str, Any]:
    return ECONOMY.board(giver, player)


@app.get("/v1/quests/status")
def quests_status(player: str = Query(default="Voyageur")) -> dict[str, Any]:
    return ECONOMY.status(player)


@app.post("/v1/quests/accept")
async def quests_accept(body: dict[str, Any]) -> JSONResponse:
    guard = _tick_guard("/v1/quests/accept", body)
    if guard is not None:
        return guard
    out = ECONOMY.accept(
        str(body.get("player") or "Voyageur"),
        str(body.get("quest_id") or ""),
        str(body.get("giver_id") or ""),
    )
    if ac is not None:
        out = _attach_tick(out, "quests/accept")
    return JSONResponse(out, status_code=200 if out.get("ok") else 400)


@app.post("/v1/quests/progress")
async def quests_progress(body: dict[str, Any]) -> JSONResponse:
    guard = _tick_guard("/v1/quests/progress", body)
    if guard is not None:
        return guard
    out = ECONOMY.progress(
        str(body.get("player") or "Voyageur"),
        str(body.get("quest_id") or ""),
        str(body.get("step_id") or ""),
    )
    out = _attach_tick(out, "quests/progress")
    return JSONResponse(out, status_code=200 if out.get("ok") else 400)


@app.post("/v1/quests/complete")
async def quests_complete(body: dict[str, Any]) -> JSONResponse:
    guard = _tick_guard("/v1/quests/complete", body)
    if guard is not None:
        return guard
    out = ECONOMY.complete(
        str(body.get("player") or "Voyageur"),
        str(body.get("quest_id") or ""),
    )
    out = _attach_tick(out, "quests/complete")
    return JSONResponse(out, status_code=200 if out.get("ok") else 400)


@app.post("/v1/quests/tip")
async def quests_tip(body: dict[str, Any]) -> JSONResponse:
    guard = _tick_guard("/v1/quests/tip", body)
    if guard is not None:
        return guard
    out = ECONOMY.tip(
        str(body.get("player") or "Voyageur"),
        str(body.get("quest_id") or ""),
        int(body.get("amount", 2)),
    )
    out = _attach_tick(out, "tip_stage")
    return JSONResponse(out, status_code=200 if out.get("ok") else 400)


@app.get("/v1/catalog/skills")
def catalog_skills_v1() -> JSONResponse:
    return catalog("skills")


@app.post("/v1/craft/combine")
async def craft_combine(body: dict[str, Any]) -> JSONResponse:
    guard = _tick_guard("/v1/craft/combine", body)
    if guard is not None:
        return guard
    out = ECONOMY.craft_combine(
        str(body.get("player") or "Voyageur"),
        str(body.get("recipe_id") or ""),
    )
    out = _attach_tick(out, "craft/start")
    return JSONResponse(out, status_code=200 if out.get("ok") else 400)


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    session_player = "Voyageur"
    session_oid = HUMAN_OID
    _clients[websocket] = {"oid": session_oid, "name": session_player}
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "bad_json"}))
                continue
            if not isinstance(msg, dict):
                continue
            mtype = str(msg.get("type") or "")
            if mtype == "login":
                token = str(msg.get("session_token") or "")
                sess = AUTH.resolve(token)
                ok = sess is not None
                if ok:
                    session_player = str(sess.get("username") or "Voyageur")
                    session_oid = int(sess.get("character_id") or HUMAN_OID)
                    SIM.ensure_human(session_oid, session_player)
                    _clients[websocket] = {"oid": session_oid, "name": session_player}
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "login_result",
                            "proto": "lbg-ws/2",
                            "success": ok,
                            "reason": "hub_runtime" if ok else "bad_token",
                            "character_id": session_oid if ok else 0,
                            "player": session_player if ok else "",
                        }
                    )
                )
            elif mtype in {"enter_world", "select_character"}:
                SIM.ensure_human(session_oid, session_player)
                _clients[websocket] = {"oid": session_oid, "name": session_player}
                await websocket.send_text(
                    json.dumps(SIM.enter_world_payload(session_oid), ensure_ascii=False)
                )
                SIM.nix_greet_human(session_player, session_oid)
                await _flush_chat_queue()
            elif mtype == "move":
                pos = msg.get("pos")
                if isinstance(pos, list) and len(pos) >= 3:
                    SIM.set_human_pos(session_oid, float(pos[0]), float(pos[1]), float(pos[2]))
                elif isinstance(pos, list) and len(pos) >= 2:
                    SIM.set_human_pos(session_oid, float(pos[0]), 0.15, float(pos[1]))
            elif mtype in {"chat", "say"}:
                text = str(msg.get("text") or msg.get("message") or "").strip()
                if text:
                    chat_msg = SIM.enqueue_say(
                        session_player, session_oid, text, source="human", queue=False
                    )
                    if chat_msg:
                        await _broadcast_chat_msg(chat_msg)
            else:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        meta = _clients.pop(websocket, None)
        if meta and meta.get("oid"):
            # Ne despawn que s'il n'y a plus d'autre socket pour ce oid
            oid = int(meta["oid"])
            still = any(int(m.get("oid") or 0) == oid for m in _clients.values())
            if not still:
                SIM.remove_human(oid)


def main() -> None:
    import uvicorn

    print(f"hub_runtime spike — http://{HOST}:{PORT}/healthz  ws://{HOST}:{PORT}/ws  (Core3=off)")
    uvicorn.run(
        "tools.hub_runtime.server:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
