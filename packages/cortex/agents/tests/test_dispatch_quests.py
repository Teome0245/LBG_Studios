import pytest

from lbg_agents.dispatch import invoke_after_route
import json


def test_quests_returns_structured_quest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LBG_AGENT_QUESTS_URL", raising=False)
    out = invoke_after_route(
        "agent.quests",
        actor_id="p:1",
        text="Je cherche une quête de prospection hors palissade",
        context={},
    )
    assert out["agent"] == "quests_stub"
    assert out["handler"] == "quests"
    assert out.get("meta", {}).get("lbg") is True
    quest = out["quest"]
    assert isinstance(quest, dict)
    assert "title" in quest
    assert "Lost Heaven" in str(quest.get("hub", "Lost Heaven")) or "Lost Heaven" in quest.get("title", "") or quest.get("planet") == "Scrapaltai"
    assert "objectives" in quest and isinstance(quest["objectives"], list) and quest["objectives"]
    assert "rewards" in quest and isinstance(quest["rewards"], dict)
    # Pas de fantasy loups/bandits
    blob = json.dumps(quest, ensure_ascii=False).lower()
    assert "loup" not in blob and "bandit" not in blob
    st = out.get("quest_state")
    assert isinstance(st, dict)
    assert isinstance(st.get("quest_id"), str) and st["quest_id"]
    assert st.get("status") == "open"


def test_quests_fantasy_keyword_remapped_to_desert(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LBG_AGENT_QUESTS_URL", raising=False)
    out = invoke_after_route(
        "agent.quests",
        actor_id="p:1",
        text="Je cherche une quête contre les loups",
        context={},
    )
    quest = out["quest"]
    assert quest.get("id") == "lh_hunt_chacal"
    obj = ""
    objs = quest.get("objectives") or []
    if objs and isinstance(objs[0], dict):
        obj = str(objs[0].get("text") or "")
    assert "loup fantasy" in obj.lower() or "pas de loups" in obj.lower() or "Chacal" in obj
    assert quest.get("template") == "hunt"


def test_quests_progress_updates_when_quest_state_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LBG_AGENT_QUESTS_URL", raising=False)
    out1 = invoke_after_route(
        "agent.quests",
        actor_id="p:1",
        text="Une quête ?",
        context={},
    )
    qid = out1["quest_state"]["quest_id"]

    out2 = invoke_after_route(
        "agent.quests",
        actor_id="p:1",
        text="J'ai avancé.",
        context={"quest_state": {"quest_id": qid, "status": "open", "step": 0}},
    )
    st2 = out2.get("quest_state")
    assert isinstance(st2, dict)
    assert st2.get("quest_id") == qid
    assert st2.get("step") == 1


def test_quests_completed_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LBG_AGENT_QUESTS_URL", raising=False)
    out = invoke_after_route(
        "agent.quests",
        actor_id="p:1",
        text="Avancement",
        context={"quest_state": {"quest_id": "q-1", "status": "completed", "step": 2}},
    )
    st = out.get("quest_state")
    assert isinstance(st, dict)
    assert st.get("status") == "completed"
    assert st.get("step") == 2

