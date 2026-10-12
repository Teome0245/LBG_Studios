"""Tests — SSE framing /ask/stream (plan 1.2)."""

from __future__ import annotations

import asyncio
import json
import sys
import unittest
from pathlib import Path

_OVERLAY = Path(__file__).resolve().parents[1]
if str(_OVERLAY) not in sys.path:
    sys.path.insert(0, str(_OVERLAY))

import sse_ask  # noqa: E402


def _frames(raw: bytes) -> list[tuple[str, dict]]:
    text = raw.decode("utf-8")
    out: list[tuple[str, dict]] = []
    for block in text.split("\n\n"):
        if not block.strip():
            continue
        event = "message"
        data_lines: list[str] = []
        for line in block.split("\n"):
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].lstrip())
        if data_lines:
            out.append((event, json.loads("\n".join(data_lines))))
    return out


class SseAskTests(unittest.TestCase):
    def test_sse_event_shape(self) -> None:
        raw = sse_ask.sse_event("start", {"ok": True})
        self.assertTrue(raw.endswith(b"\n\n"))
        self.assertIn(b"event: start\n", raw)
        self.assertIn(b'"ok": true', raw)

    def test_stream_ask_start_ping_delta_done(self) -> None:
        async def _run() -> list[tuple[str, dict]]:
            async def dispatch() -> dict:
                await asyncio.sleep(0.05)
                return {"content": "Hello world from stream", "source": "llm", "model": "test"}

            chunks: list[bytes] = []
            async for chunk in sse_ask.stream_ask(
                dispatch,
                ping_interval=0.02,
                chunk_chars=8,
                chunk_delay=0.0,
            ):
                chunks.append(chunk)
            frames: list[tuple[str, dict]] = []
            for c in chunks:
                frames.extend(_frames(c))
            return frames

        frames = asyncio.run(_run())
        names = [e for e, _ in frames]
        self.assertEqual(names[0], "start")
        self.assertIn("ping", names)
        self.assertIn("delta", names)
        self.assertEqual(names[-1], "done")
        text = "".join(d["content"] for e, d in frames if e == "delta")
        self.assertEqual(text, "Hello world from stream")
        done = frames[-1][1]
        self.assertTrue(done.get("ok"))
        self.assertEqual(done["response"]["source"], "llm")

    def test_stream_ask_error(self) -> None:
        async def _run() -> list[tuple[str, dict]]:
            async def dispatch() -> dict:
                raise RuntimeError("boom")

            chunks: list[bytes] = []
            async for chunk in sse_ask.stream_ask(dispatch, ping_interval=0.5):
                chunks.append(chunk)
            frames: list[tuple[str, dict]] = []
            for c in chunks:
                frames.extend(_frames(c))
            return frames

        frames = asyncio.run(_run())
        self.assertEqual(frames[0][0], "start")
        self.assertEqual(frames[-1][0], "error")
        self.assertIn("boom", frames[-1][1].get("error", ""))


if __name__ == "__main__":
    unittest.main()
