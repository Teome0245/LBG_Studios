"""Pytest : PYTHONPATH orchestrator + parent cortex."""

from __future__ import annotations

import sys
from pathlib import Path

_ORCH = Path(__file__).resolve().parent
_CORTEX = _ORCH.parent


def _prepend(path: Path) -> None:
    p = str(path)
    if p not in sys.path:
        sys.path.insert(0, p)


_prepend(_ORCH)
_prepend(_CORTEX)
