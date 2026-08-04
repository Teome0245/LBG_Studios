"""
Logique locale « quêtes » LBG — templates Lost Heaven / Scrapaltai.

Remplace les thèmes fantasy (loups, bandits, herbes) par des missions hub
(docs/world/BOITE_IDEES_GAMEPLAY.md §4). Ne lit pas LBG_AGENT_QUESTS_URL.
"""

from __future__ import annotations

import json
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Any


def _templates_path() -> Path:
    return Path(__file__).resolve().parents[3] / "content" / "world" / "quests_lbg_templates.json"


@lru_cache(maxsize=1)
def _load_templates() -> list[dict[str, Any]]:
    path = _templates_path()
    if not path.is_file():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("templates") if isinstance(raw, dict) else None
    if not isinstance(rows, list):
        return []
    return [r for r in rows if isinstance(r, dict) and r.get("id")]


def _match_template(text: str, context: dict[str, Any] | None) -> dict[str, Any] | None:
    templates = _load_templates()
    if not templates:
        return None
    low = (text or "").lower()
    npc_id = ""
    if isinstance(context, dict):
        raw = context.get("world_npc_id")
        if isinstance(raw, str):
            npc_id = raw.strip()

    # Prefer giver match when talking to a known NPC
    if npc_id:
        for row in templates:
            givers = row.get("giver_ids") or []
            if isinstance(givers, list) and npc_id in givers and not row.get("fallback"):
                return row

    best: dict[str, Any] | None = None
    best_score = 0
    fallback: dict[str, Any] | None = None
    for row in templates:
        if row.get("fallback"):
            fallback = row
        score = 0
        for kw in row.get("keywords") or []:
            if isinstance(kw, str) and kw.lower() in low:
                score += 1
        if score > best_score:
            best_score = score
            best = row
    if best_score > 0 and best is not None:
        return best
    return fallback


def _quest_from_template(
    tmpl: dict[str, Any],
    *,
    giver: str,
) -> dict[str, Any]:
    rewards = tmpl.get("rewards") if isinstance(tmpl.get("rewards"), dict) else {}
    next_steps = tmpl.get("next_steps") if isinstance(tmpl.get("next_steps"), list) else [
        "Accepter la quête.",
        "Accomplir l’objectif.",
        "Revenir voir le donneur de quête.",
    ]
    return {
        "id": str(tmpl.get("id") or ""),
        "title": str(tmpl.get("title") or "Mission Lost Heaven"),
        "template": str(tmpl.get("template") or "aide"),
        "giver": giver,
        "hub": "Lost Heaven",
        "planet": "Scrapaltai",
        "objectives": [
            {
                "kind": "task",
                "text": str(tmpl.get("objective") or "Aider Lost Heaven."),
                "status": "open",
            }
        ],
        "rewards": rewards,
        "next_steps": [str(x) for x in next_steps if isinstance(x, str)],
    }


def run_quests_stub(*, actor_id: str, text: str, context: dict[str, Any]) -> dict[str, Any]:
    t = (text or "").strip()
    ctx = context if isinstance(context, dict) else {}
    npc = ctx.get("npc_name")
    giver = npc.strip() if isinstance(npc, str) and npc.strip() else ""
    npc_id = ctx.get("world_npc_id")
    npc_id = npc_id.strip() if isinstance(npc_id, str) and npc_id.strip() else None

    quest_state = ctx.get("quest_state")
    quest_id = None
    status = "open"
    step = 0
    if isinstance(quest_state, dict):
        qid = quest_state.get("quest_id")
        if isinstance(qid, str) and qid.strip():
            quest_id = qid.strip()
        st = quest_state.get("status")
        if isinstance(st, str) and st.strip():
            status = st.strip()
        raw_step = quest_state.get("step")
        if isinstance(raw_step, int) and raw_step >= 0:
            step = raw_step

    if quest_id:
        if status == "completed":
            updated_state = {"quest_id": quest_id, "status": "completed", "step": step}
            return {
                "agent": "quests_stub",
                "handler": "quests",
                "actor_id": actor_id,
                "request_text": t,
                "quest_state": updated_state,
                "meta": {"stub": True, "lbg": True},
            }

        low = t.lower()
        if status == "open" and step == 0 and re.search(r"\b(accepte|j'accepte|j accepte|accept)\b", low):
            updated_state = {"quest_id": quest_id, "status": "accepted", "step": step}
            out: dict[str, Any] = {
                "agent": "quests_stub",
                "handler": "quests",
                "actor_id": actor_id,
                "request_text": t,
                "quest_state": updated_state,
                "meta": {"stub": True, "lbg": True},
            }
            if npc_id:
                out["commit"] = {
                    "npc_id": npc_id,
                    "flags": {"quest_accepted": True, "quest_id": quest_id},
                }
            return out

        new_step = step + 1
        new_status = "completed" if new_step >= 2 else status
        updated_state = {"quest_id": quest_id, "status": new_status, "step": new_step}
        return {
            "agent": "quests_stub",
            "handler": "quests",
            "actor_id": actor_id,
            "request_text": t,
            "quest_state": updated_state,
            "meta": {"stub": True, "lbg": True},
        }

    tmpl = _match_template(t, ctx)
    if tmpl is None:
        # Dernier recours sans fichier JSON
        tmpl = {
            "id": "lh_aide_generale",
            "title": "Coup de main à Lost Heaven",
            "template": "aide",
            "objective": "Aider un civil de Lost Heaven.",
            "rewards": {"credits": 10, "xp": {"xp_quartier": 10}, "items": []},
            "default_giver": "Daan Oth",
        }
    if not giver:
        giver = str(tmpl.get("default_giver") or "Daan Oth")

    quest = _quest_from_template(tmpl, giver=giver)
    quest_id = f"q-{quest['id']}-{int(time.time())}-{abs(hash(actor_id)) % 10_000}"
    qstate = {
        "quest_id": quest_id,
        "template_id": quest["id"],
        "status": "open",
        "step": 0,
    }
    return {
        "agent": "quests_stub",
        "handler": "quests",
        "actor_id": actor_id,
        "request_text": t,
        "quest": quest,
        "quest_state": qstate,
        "meta": {
            "stub": True,
            "lbg": True,
            "hub": "Lost Heaven",
            "planet": "Scrapaltai",
        },
    }
