"""Tests peel inventaire / quêtes hub_runtime."""

from __future__ import annotations

import uuid
from pathlib import Path

from tools.hub_runtime.economy import HubEconomy

QUESTS = (
    Path(__file__).resolve().parents[2] / "content" / "world" / "quests_lbg_templates.json"
)


def test_inventory_default() -> None:
    eco = HubEconomy()
    inv = eco.inventory("TestPlayer")
    assert inv["ok"] and len(inv["inventory"]) >= 3
    assert inv["source"] == "hub_runtime"


def test_board_and_accept_complete() -> None:
    eco = HubEconomy()
    if QUESTS.is_file():
        eco.reload_templates()
    # Joueur unique : évite already_completed si state.json persiste entre runs
    player = f"Alice_{uuid.uuid4().hex[:8]}"
    board = eco.board("npc:core3_daan_oth", player)
    assert board["ok"] and len(board["quests"]) >= 1
    qid = str(board["quests"][0]["id"])
    acc = eco.accept(player, qid, "npc:core3_daan_oth")
    assert acc["ok"], acc
    # progress all steps
    for step in board["quests"][0].get("progress") or []:
        eco.progress(player, qid, str(step["id"]))
    done = eco.complete(player, qid)
    assert done["ok"]
    assert qid in eco.status(player)["completed"]
