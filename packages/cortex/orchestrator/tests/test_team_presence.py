"""Tests presence Team (mapping + sanitize, sans WS)."""

from __future__ import annotations

from team.models import TeamTask
from team import presence as team_presence


def test_map_task_status():
    assert team_presence.map_task_status("running") == "busy"
    assert team_presence.map_task_status("review") == "review"
    assert team_presence.map_task_status("failed") == "failed"
    assert team_presence.map_task_status("done") == "idle"
    assert team_presence.map_task_status("queued") == "idle"
    assert team_presence.map_task_status("queued", approval_required=True) == "review"
    assert team_presence.map_task_status("queued", approval_required=True, approved=True) == "review"
    assert team_presence.map_task_status("waiting_approval", approval_required=True) == "review"



def test_presence_l2_queued_shows_review():
    task = TeamTask(
        id="l2-queued-test",
        role="dev_game",
        objective="Ouvre une PR Core3",
        status="queued",
        approval_required=True,
        trace_id="tr-l2",
        context={"cursor_cloud_agent": True},
    )
    team_presence.emit_from_task(task, event="status_changed")
    snap = team_presence.snapshot(mode="live")
    agents = {a["agent_id"]: a for a in snap["agents"]}
    # résolu vers un agent du rôle (Vulcan/Dédale selon registre)
    matches = [a for a in agents.values() if a.get("task_id") == "l2-queued-test"]
    assert matches, "agent lié à la tâche L2 attendu"
    assert matches[0]["status"] == "review"
    assert matches[0].get("approval_required") is True
    assert matches[0].get("awaiting_human_approval") is True
    assert matches[0].get("awaiting_run") is False


def test_presence_reconcile_clears_done_ghost(monkeypatch):
    """Pastille PRÊT fantôme si la tâche est déjà done en store."""
    ghost = TeamTask(
        id="ghost-done-l2",
        role="pm",
        objective="Revue L2 — Feature proposal fantôme",
        status="queued",
        approval_required=True,
        stored_approval_token="tok",
        context={"approved": True, "feature_proposal_review": True},
    )
    team_presence.emit_from_task(ghost, event="status_changed")
    matches0 = [
        a
        for a in team_presence.snapshot(mode="live")["agents"]
        if a.get("task_id") == "ghost-done-l2"
    ]
    assert matches0 and matches0[0].get("awaiting_run") is True

    done = TeamTask(
        id="ghost-done-l2",
        role="pm",
        objective="Revue L2 — Feature proposal fantôme",
        status="done",
        approval_required=True,
        context={"approved": True},
        result={"ok": True, "kind": "feature_proposal_review"},
    )

    import team.store as ts

    monkeypatch.setattr(ts, "get_task", lambda tid: done if tid == "ghost-done-l2" else None)

    n = team_presence.reconcile_with_store()
    assert n >= 1
    matches = [
        a
        for a in team_presence.snapshot(mode="live")["agents"]
        if a.get("task_id") == "ghost-done-l2"
    ]
    assert not matches
    themis = [
        a
        for a in team_presence.snapshot(mode="live")["agents"]
        if a.get("agent_id") == "studio_pm_themis" or a.get("display_name") == "Thémis"
    ]
    assert themis
    assert themis[0]["status"] == "idle"
    assert themis[0].get("awaiting_run") in (False, None)
    assert themis[0].get("task_id") in (None, "")
    assert themis[0].get("approval_required") in (False, None)


def test_presence_done_clears_task_id():
    """emit done ne doit plus laisser task_id / flags L2 (fantôme bureau)."""
    done = TeamTask(
        id="done-clear-l2",
        role="pm",
        objective="Revue L2 déjà faite",
        status="done",
        approval_required=True,
        context={"approved": True},
        result={"ok": True},
    )
    team_presence.emit_from_task(done, event="status_changed")
    matches = [
        a
        for a in team_presence.snapshot(mode="live")["agents"]
        if a.get("agent_id") == "studio_pm_themis" or a.get("display_name") == "Thémis"
    ]
    assert matches
    assert matches[0].get("task_id") in (None, "")
    assert matches[0].get("awaiting_run") in (False, None)
    assert matches[0].get("approval_required") in (False, None)
    assert matches[0]["status"] == "idle"


def test_guest_metrics_ops_maps_to_hephaistos_not_vulcan():
    """Mur guest avec hosts Core3 SWG/.245 ne doit pas attribuer Vulcan."""
    task = TeamTask(
        id="guest-crit-1",
        role="ops",
        objective="Sonde guest mur INFRA LAN — alerte critical (Front web, Prime monde)",
        status="running",
        context={
            "ops_kind": "guest_metrics",
            "guest_metrics": {
                "hosts": [
                    {"label": "Front web", "host": "192.168.0.100"},
                    {"label": "Core3 SWG", "host": "192.168.0.245"},
                    {"label": "Prime monde", "host": "192.168.0.246"},
                ]
            },
        },
    )
    aid = team_presence.resolve_presence_agent_id(task)
    assert "vulcan" not in aid.lower()
    assert "hephaistos" in aid.lower() or aid == "ops"
    assert team_presence.infer_zone(task, agent_id=aid) == "zone_core"


def test_sanitize_action_truncates_and_redacts():
    long = "x" * 200
    assert len(team_presence.sanitize_action(long)) <= 120
    red = team_presence.sanitize_action("deploy with api_key=supersecret123 now")
    assert "supersecret123" not in red
    assert "***" in red


def test_emit_from_task_updates_snapshot():
    task = TeamTask(
        id="abcd1234-test",
        role="admin_infra",
        objective="Audit Ollama 111",
        status="running",
        trace_id="tr1",
        context={"host": "192.168.0.111"},
    )
    team_presence.emit_from_task(task, event="status_changed")
    snap = team_presence.snapshot(mode="live")
    assert snap["schema"] == "team.presence.snapshot.v1"
    assert snap["mode"] == "live"
    matches = [a for a in snap["agents"] if a.get("task_id") == "abcd1234-test"]
    assert matches, "agent lié à la tâche attendu"
    assert matches[0]["status"] == "busy"
    assert matches[0]["location"] == "zone_llm"
    assert len(matches[0]["current_action"]) <= 120


def test_zone_mmo_lab_annotated_when_offline(monkeypatch):
    monkeypatch.setenv("LBG_ZONE_MMO_LAB_HOST_STATE", "off")
    team_presence._zone_host_cache.clear()
    zones = {z["id"]: z for z in team_presence.zones_for_snapshot(force_refresh=True)}
    lab = zones["zone_mmo_lab"]
    assert lab["host_status"] == "offline"
    assert lab["host_badge"] == "Éteinte"
    assert "Éteinte" in lab["label"]
    assert lab["host"] == "192.168.0.245"


def test_zone_mmo_lab_online_force(monkeypatch):
    monkeypatch.setenv("LBG_ZONE_MMO_LAB_HOST_STATE", "on")
    team_presence._zone_host_cache.clear()
    zones = {z["id"]: z for z in team_presence.zones_for_snapshot(force_refresh=True)}
    lab = zones["zone_mmo_lab"]
    assert lab["host_status"] == "online"
    assert lab.get("host_badge") in (None, "")
    assert "Éteinte" not in lab["label"]
    snap = team_presence.snapshot(mode="live")
    snap_lab = next(z for z in snap["zones"] if z["id"] == "zone_mmo_lab")
    assert snap_lab["host_status"] == "online"


def test_zone_games_player_bridges_expose_login():
    assert team_presence.default_zone_for_agent("player_bridge_nix", "player_bridge") == "zone_games"
    snap = team_presence.snapshot(mode="live")
    assert any(z["id"] == "zone_games" for z in snap["zones"])
    games = [a for a in snap["agents"] if a.get("location") == "zone_games"]
    assert len(games) >= 4
    nix = next((a for a in games if a.get("agent_id") == "player_bridge_nix"), None)
    assert nix is not None
    assert nix.get("account_login") == "nix_bridge"
    assert nix.get("mmo_player") == "Nix"
    assert "login=nix_bridge" in (nix.get("current_action") or "")


def test_soft_link_vulcan_vex_and_hermes_tess():
    snap = team_presence.snapshot(mode="live")
    by_id = {a["agent_id"]: a for a in snap["agents"]}
    vex = by_id.get("player_bridge_vex")
    tess = by_id.get("player_bridge_tess")
    vulcan = by_id.get("studio_dev_vulcan")
    hermes = by_id.get("godot_dev_hermes")
    assert vex and vex.get("linked_studio_agent_id") == "studio_dev_vulcan"
    assert vex.get("linked_studio_display") == "Vulcan"
    assert "↔ Vulcan" in (vex.get("current_action") or "")
    assert tess and tess.get("linked_studio_agent_id") == "godot_dev_hermes"
    assert tess.get("linked_studio_display") == "Hermès"
    assert vulcan and vulcan.get("mmo_player") == "Vex"
    assert vulcan.get("mmo_account_login") == "vulcan_bridge"
    assert hermes and hermes.get("mmo_player") == "Tess"
    assert hermes.get("mmo_account_login") == "hermes_bridge"
    assert hermes.get("bridge_agent_id") == "player_bridge_tess"
    assert vex.get("account_login") == "vulcan_bridge"
    assert tess.get("account_login") == "hermes_bridge"