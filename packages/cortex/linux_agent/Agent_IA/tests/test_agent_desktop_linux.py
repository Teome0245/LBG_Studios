import os
import sys
import unittest
from pathlib import Path
import importlib.util

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from fastapi.testclient import TestClient  # type: ignore
except Exception:  # pragma: no cover
    TestClient = None  # type: ignore[misc,assignment]


class TestAgentDesktopLinuxIntegration(unittest.TestCase):
    def setUp(self) -> None:
        if TestClient is None:
            self.skipTest("fastapi non installé dans cet environnement")

        main_path = _ROOT / "main.py"
        spec = importlib.util.spec_from_file_location("main", main_path)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        sys.modules["main"] = mod
        spec.loader.exec_module(mod)
        mod.InvokeRequest.model_rebuild()

        self.client = TestClient(mod.app)

    def _invoke(self, action: dict, context_extra: dict | None = None) -> dict:
        ctx = {"desktop_action": action}
        if context_extra:
            ctx.update(context_extra)
        r = self.client.post("/invoke", json={"actor_id": "test_linux", "text": "t", "context": ctx})
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

    def test_ui_snapshot_dry_run_success(self) -> None:
        os.environ["LBG_LINUX_DRY_RUN"] = "1"
        j = self._invoke({"kind": "ui_snapshot", "app": "firefox", "interactive": True})
        self.assertTrue(j.get("ok"))
        self.assertEqual(j.get("outcome"), "dry_run")
        self.assertEqual(j.get("app"), "firefox")
        self.assertIn("snapshot", j.get("cmd", []))

    def test_ui_click_approval_denied_when_token_required(self) -> None:
        os.environ["LBG_LINUX_APPROVAL_TOKEN"] = "SECRET_LINUX"
        os.environ["LBG_LINUX_DRY_RUN"] = "0"
        j = self._invoke({"kind": "ui_click", "ref": "@s8f3k2p9:e3"})
        self.assertFalse(j.get("ok"))
        self.assertEqual(j.get("outcome"), "approval_denied")

    def test_ui_click_dry_run_success(self) -> None:
        os.environ["LBG_LINUX_DRY_RUN"] = "1"
        os.environ.pop("LBG_LINUX_APPROVAL_TOKEN", None)
        j = self._invoke({"kind": "ui_click", "ref": "@s8f3k2p9:e3", "button": "left"})
        self.assertTrue(j.get("ok"))
        self.assertEqual(j.get("outcome"), "dry_run")
        self.assertEqual(j.get("ref"), "@s8f3k2p9:e3")
        self.assertIn("click", j.get("cmd", []))

    def test_ui_type_dry_run_success(self) -> None:
        os.environ["LBG_LINUX_DRY_RUN"] = "1"
        os.environ.pop("LBG_LINUX_APPROVAL_TOKEN", None)
        j = self._invoke({"kind": "ui_type", "ref": "@s8f3k2p9:e2", "text": "systemctl status"})
        self.assertTrue(j.get("ok"))
        self.assertEqual(j.get("outcome"), "dry_run")
        self.assertEqual(j.get("ref"), "@s8f3k2p9:e2")
        self.assertEqual(j.get("text_length"), 16)
        self.assertIn("type", j.get("cmd", []))
