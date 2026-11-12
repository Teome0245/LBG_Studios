import os
import unittest

try:
    from fastapi.testclient import TestClient  # type: ignore
except Exception:  # pragma: no cover
    TestClient = None  # type: ignore[misc,assignment]


class TestAgentDesktopIntegration(unittest.TestCase):
    def setUp(self) -> None:
        if TestClient is None:
            self.skipTest("fastapi non installé dans cet environnement")
        from main import app  # type: ignore

        self.client = TestClient(app)

    def _invoke(self, action: dict, context_extra: dict | None = None) -> dict:
        ctx = {"desktop_action": action}
        if context_extra:
            ctx.update(context_extra)
        r = self.client.post("/invoke", json={"actor_id": "test", "text": "t", "context": ctx})
        self.assertEqual(r.status_code, 200)
        return r.json()

    def test_healthz_contains_agent_desktop(self) -> None:
        r = self.client.get("/healthz")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("agent_desktop", data)
        ad = data["agent_desktop"]
        self.assertIn("installed", ad)
        self.assertIn("platform", ad)

    def test_ui_snapshot_disabled_by_default(self) -> None:
        os.environ.pop("LBG_DESKTOP_COMPUTER_USE_ENABLED", None)
        j = self._invoke({"kind": "ui_snapshot", "app": "notepad"})
        self.assertFalse(j.get("ok"))
        self.assertEqual(j.get("outcome"), "feature_disabled")

    def test_ui_snapshot_approval_denied_when_configured(self) -> None:
        os.environ["LBG_DESKTOP_COMPUTER_USE_ENABLED"] = "1"
        os.environ["LBG_DESKTOP_OBSERVE_REQUIRES_APPROVAL"] = "1"
        os.environ["LBG_DESKTOP_APPROVAL_TOKEN"] = "SECRET_TOKEN"
        os.environ["LBG_DESKTOP_DRY_RUN"] = "1"
        j = self._invoke({"kind": "ui_snapshot", "app": "notepad"})
        self.assertFalse(j.get("ok"))
        self.assertEqual(j.get("outcome"), "approval_denied")

    def test_ui_snapshot_dry_run_success(self) -> None:
        os.environ["LBG_DESKTOP_COMPUTER_USE_ENABLED"] = "1"
        os.environ["LBG_DESKTOP_OBSERVE_REQUIRES_APPROVAL"] = "0"
        os.environ["LBG_DESKTOP_DRY_RUN"] = "1"
        j = self._invoke({"kind": "ui_snapshot", "app": "notepad", "interactive": True})
        self.assertTrue(j.get("ok"))
        self.assertEqual(j.get("outcome"), "dry_run")
        self.assertEqual(j.get("app"), "notepad")
        self.assertIn("snapshot", j.get("cmd", []))

    def test_ui_click_dry_run_success(self) -> None:
        os.environ["LBG_DESKTOP_COMPUTER_USE_ENABLED"] = "1"
        os.environ["LBG_DESKTOP_DRY_RUN"] = "1"
        os.environ.pop("LBG_DESKTOP_APPROVAL_TOKEN", None)
        j = self._invoke({"kind": "ui_click", "ref": "@s8f3k2p9:e3", "button": "left"})
        self.assertTrue(j.get("ok"))
        self.assertEqual(j.get("outcome"), "dry_run")
        self.assertEqual(j.get("ref"), "@s8f3k2p9:e3")
        self.assertIn("click", j.get("cmd", []))

    def test_ui_type_dry_run_success(self) -> None:
        os.environ["LBG_DESKTOP_COMPUTER_USE_ENABLED"] = "1"
        os.environ["LBG_DESKTOP_DRY_RUN"] = "1"
        os.environ.pop("LBG_DESKTOP_APPROVAL_TOKEN", None)
        j = self._invoke({"kind": "ui_type", "ref": "@s8f3k2p9:e2", "text": "echo hello"})
        self.assertTrue(j.get("ok"))
        self.assertEqual(j.get("outcome"), "dry_run")
        self.assertEqual(j.get("ref"), "@s8f3k2p9:e2")
        self.assertEqual(j.get("text_length"), 10)
        self.assertIn("type", j.get("cmd", []))

    def test_ui_press_and_scroll_dry_run(self) -> None:
        os.environ["LBG_DESKTOP_COMPUTER_USE_ENABLED"] = "1"
        os.environ["LBG_DESKTOP_DRY_RUN"] = "1"
        os.environ.pop("LBG_DESKTOP_APPROVAL_TOKEN", None)
        j_press = self._invoke({"kind": "ui_press", "key": "Enter"})
        self.assertTrue(j_press.get("ok"))
        self.assertEqual(j_press.get("key"), "Enter")

        j_scroll = self._invoke({"kind": "ui_scroll", "direction": "down", "amount": 5})
        self.assertTrue(j_scroll.get("ok"))
        self.assertEqual(j_scroll.get("direction"), "down")

    def test_run_steps_with_agent_desktop_actions(self) -> None:
        os.environ["LBG_DESKTOP_COMPUTER_USE_ENABLED"] = "1"
        os.environ["LBG_DESKTOP_OBSERVE_REQUIRES_APPROVAL"] = "0"
        os.environ["LBG_DESKTOP_DRY_RUN"] = "1"
        steps = [
            {"kind": "ui_snapshot", "app": "notepad"},
            {"kind": "ui_click", "ref": "@s8f3k2p9:e1"},
            {"kind": "ui_type", "ref": "@s8f3k2p9:e2", "text": "Automation test"},
            {"kind": "ui_press", "key": "Ctrl+s"},
        ]
        j = self._invoke({"kind": "run_steps", "steps": steps})
        self.assertTrue(j.get("ok"))
        self.assertEqual(j.get("steps_executed"), 4)
        self.assertEqual(len(j.get("results", [])), 4)

