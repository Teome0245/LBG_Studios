"""Compte rendu suivi plan d'évolutions — pour Compagnon / ask.

« où en est le plan », « suivi plan évol », « tickets bloqués » → markdown depuis
docs/suivi/ (rafraîchi si possible via tools/suivi_plan_evolutions.py).
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger("lbg.plan_suivi")

_SUIVI_RE = re.compile(
    r"(?i)("
    r"\bsuivi\s+(?:du\s+|des\s+)?plan\b|"
    r"\bo[uù]\s+en\s+est\s+le\s+plan\b|"
    r"\bplan\s+d['\u2019 ]?évol|"
    r"\btickets?\s+bloqu\w*|"
    r"\bquels?\s+tickets?\b|"
    r"\bsujets?\s+bloqu\w*|"
    r"\b[àa]\s+relancer\b|"
    r"\bcompte[- ]rendu\s+(?:du\s+)?plan\b|"
    r"\bplan\s+(?:enti[eè]rement\s+)?r[ée]alis\w*"
    r")"
)


def plan_suivi_enabled(*, lab: bool = False) -> bool:
    raw = (os.getenv("LBG_COMPAGNON_PLAN_SUIVI") or "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    return bool(lab)


def wants_plan_suivi(prompt: str) -> bool:
    text = (prompt or "").strip()
    if not text or len(text) > 280:
        return False
    return bool(_SUIVI_RE.search(text))


def _repo_root() -> Path:
    env = (os.getenv("LBG_STUDIO_ROOT") or "").strip()
    if env:
        return Path(env)
    # overlay on CT100 often under /opt/orchestrateur — monorepo may be elsewhere
    candidates = [
        Path("/home/lbg/projects/LBG_Studios"),
        Path("/opt/orchestrateur"),  # CT100 deploy
        Path(__file__).resolve().parents[5],  # …/LBG_Studios/packages/cortex/...
        Path(__file__).resolve().parents[4],
    ]
    for c in candidates:
        if (c / "docs" / "suivi" / "plan_evolutions.json").is_file():
            return c
    return Path("/home/lbg/projects/LBG_Studios")


def refresh_and_read(*, refresh: bool = True) -> str:
    root = _repo_root()
    status = root / "docs" / "suivi" / "PLAN_EVOLUTIONS_STATUS.md"
    script = root / "tools" / "suivi_plan_evolutions.py"
    if refresh and script.is_file():
        try:
            subprocess.run(
                ["python3", str(script), "--refresh"],
                cwd=str(root),
                timeout=45,
                check=False,
                capture_output=True,
            )
        except Exception as e:
            logger.warning("plan_suivi refresh failed: %s", e)
    if status.is_file():
        text = status.read_text(encoding="utf-8")
        # Cap réponse chat
        if len(text) > 3500:
            text = text[:3400].rstrip() + "\n\n_(…tronqué — voir docs/suivi/PLAN_EVOLUTIONS_STATUS.md)_"
        return text
    return (
        "Pas encore de suivi généré. Sur le monorepo : "
        "`python3 tools/suivi_plan_evolutions.py --refresh`."
    )


async def attach_plan_suivi_if_needed(
    result: Any,
    *,
    prompt: str,
    lab: bool = False,
) -> Any:
    if not isinstance(result, dict):
        return result
    if not plan_suivi_enabled(lab=lab):
        return result
    if not wants_plan_suivi(prompt):
        return result
    content = refresh_and_read(refresh=True)
    return {
        **result,
        "content": content,
        "response": content,
        "source": "plan_suivi",
        "model": "plan_suivi",
        "model_used": "plan_suivi",
        "plan_suivi": {"ok": True},
    }
