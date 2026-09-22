"""Client HTTP System One (API compatible Jev / laya-serve).

Ne charge jamais torch : l'orchestrateur appelle un process séparé
(`laya-serve` ou équivalent) via ``POST /v1/systemone``.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def laya_base_url() -> str:
    return os.environ.get("LBG_ORCHESTRATOR_INTENT_LAYA_BASE_URL", "").strip().rstrip("/")


def laya_model() -> str:
    return (
        os.environ.get("LBG_ORCHESTRATOR_INTENT_LAYA_MODEL", "laya-latest").strip()
        or "laya-latest"
    )


def laya_timeout_s() -> float:
    try:
        return float(os.environ.get("LBG_ORCHESTRATOR_INTENT_LAYA_TIMEOUT_S", "2").strip())
    except ValueError:
        return 2.0


def _resolve_secret_ref(raw: str | None) -> str:
    s = (raw or "").strip()
    if len(s) >= 4 and s.startswith("${") and s.endswith("}"):
        key = s[2:-1].strip()
        if key:
            return os.environ.get(key, "").strip()
    return s


def laya_api_key() -> str:
    return _resolve_secret_ref(os.environ.get("LBG_ORCHESTRATOR_INTENT_LAYA_API_KEY", "")).strip()


def systemone_predict(
    *,
    state: str | dict[str, Any] | list[Any],
    questions: dict[str, Any],
    model: str | None = None,
    base_url: str | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any] | None:
    """
    Appelle ``POST {base}/v1/systemone`` (contrat Jev / laya-serve).

    Retourne le JSON complet, ou ``None`` si indisponible / erreur réseau.
    """
    base = (base_url if base_url is not None else laya_base_url()).rstrip("/")
    if not base:
        return None
    url = f"{base}/v1/systemone"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    key = laya_api_key()
    if key:
        headers["Authorization"] = f"Bearer {key}"
    body: dict[str, Any] = {
        "model": model or laya_model(),
        "state": state,
        "questions": questions,
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    t = timeout_s if timeout_s is not None else laya_timeout_s()
    try:
        with urllib.request.urlopen(req, timeout=t) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError):
        return None
    try:
        out = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return out if isinstance(out, dict) else None


def extract_choice(
    response: dict[str, Any],
    question_id: str,
) -> tuple[str | None, float, dict[str, float]]:
    """Lit une réponse ``choice`` : (label, confidence, probabilities)."""
    answers = response.get("answers")
    if not isinstance(answers, dict):
        return None, 0.0, {}
    block = answers.get(question_id)
    if not isinstance(block, dict):
        return None, 0.0, {}
    choice = block.get("choice")
    label = choice.strip() if isinstance(choice, str) else None
    try:
        conf = float(block.get("confidence", 0.0))
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))
    probs_raw = block.get("probabilities")
    probs: dict[str, float] = {}
    if isinstance(probs_raw, dict):
        for k, v in probs_raw.items():
            if isinstance(k, str):
                try:
                    probs[k] = float(v)
                except (TypeError, ValueError):
                    continue
    return label, conf, probs


def extract_noul(response: dict[str, Any], question_id: str) -> float | None:
    """Lit une réponse ``noul`` (P(oui)), ou ``None`` si absente."""
    answers = response.get("answers")
    if not isinstance(answers, dict):
        return None
    block = answers.get(question_id)
    if not isinstance(block, dict):
        return None
    raw = block.get("noul")
    try:
        return max(0.0, min(1.0, float(raw)))
    except (TypeError, ValueError):
        return None
