"""Pytest : PYTHONPATH backend + parent cortex (imports `api.*` et `backend.main`)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parent
_CORTEX = _BACKEND.parent


def _prepend(path: Path) -> None:
    p = str(path)
    if p not in sys.path:
        sys.path.insert(0, p)


_prepend(_BACKEND)
_prepend(_CORTEX)


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    """Pydantic Settings est mis en cache ; les tests patchent os.environ."""
    from config import get_settings

    get_settings.cache_clear()
    yield  # type: ignore[misc]
    get_settings.cache_clear()
