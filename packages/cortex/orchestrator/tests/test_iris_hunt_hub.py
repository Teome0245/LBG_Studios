"""Iris — piste hunt_hub (hub → palissade), sans fallback M9."""

from __future__ import annotations

from team.godot_dev_workflow import (
    _detect_track,
    _iris_probes,
    audit_hunt_hub_readiness,
)
from team.models import TeamTask
from team import roles as team_roles


def test_iris_at_mention_chasse_uses_hunt_hub() -> None:
    props = team_roles._plan_from_at_mentions(
        "@themis brief 72h ; @iris hub Lost Heaven → palissade / board chasse",
        actor_id="u:test",
    )
    assert props is not None
    iris = next(p for p in props if (p.get("context") or {}).get("godot_dev_persona") == "iris")
    assert (iris.get("context") or {}).get("godot_dev_track") == "hunt_hub"


def test_iris_at_mention_m9_stays_m9() -> None:
    props = team_roles._plan_from_at_mentions(
        "@iris audit M9 minimap ; @argus smoke healthz",
        actor_id="u:test",
    )
    assert props is not None
    iris = next(p for p in props if (p.get("context") or {}).get("godot_dev_persona") == "iris")
    assert (iris.get("context") or {}).get("godot_dev_track") == "m9_full"


def test_detect_track_hunt_hub_from_objective() -> None:
    task = TeamTask(
        id="t1",
        role="dev_godot",
        objective="Iris — entrée hub → palissade / board chasse",
        actor_id="u:1",
        context={"godot_dev_persona": "iris"},
    )
    assert _detect_track(task, "iris") == "hunt_hub"


def test_iris_probes_no_m9_fallback_for_iris_full() -> None:
    assert _iris_probes("iris_full") == []
    assert _iris_probes("client_live") == []


def test_audit_hunt_hub_readiness_ok_in_repo() -> None:
    out = audit_hunt_hub_readiness()
    assert out["track"] == "hunt_hub_readiness"
    assert out["ok"] is True, out.get("gaps")
    assert out["checks"].get("hunt_poi") is True
