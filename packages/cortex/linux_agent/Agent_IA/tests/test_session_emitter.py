"""Tests unitaires — Présence Agents session_emitter."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import session_emitter as se  # noqa: E402


class TestSessionEmitter(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["LBG_SESSION_ISLAND_ENABLED"] = "1"
        os.environ["LBG_SESSION_ISLAND_FAIL_OPEN"] = "1"
        os.environ["LBG_SESSION_ISLAND_APPROVAL_TIMEOUT_S"] = "2"
        with se._LOCK:
            se._EVENTS.clear()
            se._PENDING.clear()

    def test_emit_and_recent(self) -> None:
        sid = se.new_session_id("t")
        se.emit("session.start", session_id=sid, agent="opencode", summary="hello")
        recent = se.recent(5)
        self.assertTrue(recent)
        self.assertEqual(recent[-1]["event"], "session.start")
        self.assertEqual(recent[-1]["session_id"], sid)

    def test_decision_allow(self) -> None:
        sid = se.new_session_id("t")
        aid = se.request_approval(session_id=sid, agent="opencode", summary="need")
        out = se.apply_decision({"approval_id": aid, "decision": "allow", "scope": "once"})
        self.assertTrue(out.get("ok"))
        dec = se.wait_decision(aid, timeout_s=0.5)
        # already resolved → unknown
        self.assertIn(dec.get("decision"), {"allow", "deny"})

    def test_decision_flow_before_wait(self) -> None:
        sid = se.new_session_id("t")
        aid = se.request_approval(session_id=sid, agent="opencode", summary="need")

        def decide() -> None:
            se.apply_decision({"approval_id": aid, "decision": "deny", "scope": "once"})

        import threading

        threading.Timer(0.05, decide).start()
        dec = se.wait_decision(aid, timeout_s=2)
        self.assertEqual(dec.get("decision"), "deny")
        self.assertFalse(dec.get("timed_out"))

    def test_disabled_noop_status(self) -> None:
        os.environ["LBG_SESSION_ISLAND_ENABLED"] = "0"
        st = se.status()
        self.assertFalse(st["enabled"])


if __name__ == "__main__":
    unittest.main()
