"""
Conftest racine (monorepo cortex).

Objectif : permettre de lancer les suites backend / orchestrator / agents
sans collisions de modules ni problèmes de PYTHONPATH.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _prepend(path: Path) -> None:
    p = str(path)
    if p not in sys.path:
        sys.path.insert(0, p)


ROOT = Path(__file__).resolve().parent

_prepend(ROOT / "backend")
_prepend(ROOT / "orchestrator")
_prepend(ROOT / "agents")
