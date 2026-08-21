"""LLM-as-a-Judge + golden dataset (P0 plan_meta_autonomie_l3).

Évalue une sortie d'agent selon une rubrique ; peut rejouer un cas golden.
Le juge s'exécute **après** les smokes déterministes, jamais à leur place.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Callable

CompleteFn = Callable[..., dict[str, Any]]

_LAST_JUDGE: dict[str, Any] = {}


def judge_enabled() -> bool:
    return os.environ.get("LBG_TEAM_OUTCOME_JUDGE", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def golden_dataset_path() -> Path:
    raw = os.environ.get("LBG_TEAM_GOLDEN_PATH", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent / "data" / "golden_dataset.json"


def load_golden_dataset() -> dict[str, Any]:
    path = golden_dataset_path()
    if not path.is_file():
        return {"schema_version": 1, "rubrics": {"default": []}, "cases": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "rubrics": {"default": []}, "cases": []}
    if not isinstance(data, dict):
        return {"schema_version": 1, "rubrics": {"default": []}, "cases": []}
    if not isinstance(data.get("cases"), list):
        data["cases"] = []
    return data


def list_golden_cases(*, domain: str = "", role: str = "") -> list[dict[str, Any]]:
    cases = [c for c in load_golden_dataset().get("cases") or [] if isinstance(c, dict)]
    if domain:
        d = domain.strip().lower()
        cases = [c for c in cases if str(c.get("domain") or "").lower() == d]
    if role:
        r = role.strip().lower()
        cases = [c for c in cases if str(c.get("role") or "").lower() == r]
    return cases


def get_golden_case(case_id: str) -> dict[str, Any] | None:
    cid = (case_id or "").strip()
    if not cid:
        return None
    for case in list_golden_cases():
        if str(case.get("id") or "") == cid:
            return case
    return None


def last_judge_trace() -> dict[str, Any]:
    return dict(_LAST_JUDGE) if _LAST_JUDGE else {}


def _set_last(trace: dict[str, Any]) -> None:
    global _LAST_JUDGE
    _LAST_JUDGE = dict(trace)


def _extract_json_object(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _keyword_heuristic(
    *,
    artifact_text: str,
    expected_keywords: list[str],
    latency_ms: float,
) -> dict[str, Any]:
    blob = (artifact_text or "").lower()
    hits = [k for k in expected_keywords if k.lower() in blob]
    miss = [k for k in expected_keywords if k.lower() not in blob]
    ratio = (len(hits) / len(expected_keywords)) if expected_keywords else 0.5
    # Coût : pénalité douce si très lent (> 8s) sans mots-clés.
    cout = 1.0 if latency_ms < 8000 else 0.7
    exactitude = ratio
    concision = 1.0 if len(blob) < 1200 else 0.6
    respect = 1.0 if not re.search(r"\b(main\s+sans\s+l2|force.?push|rm\s+-rf\s+/)\b", blob) else 0.2
    score = round(0.45 * exactitude + 0.2 * concision + 0.25 * respect + 0.1 * cout, 4)
    return {
        "score": score,
        "pass": score >= 0.55 and (not expected_keywords or len(hits) >= max(1, len(expected_keywords) // 2)),
        "reasons": [
            f"keywords_hit={hits}",
            f"keywords_miss={miss}",
            f"heuristic exactitude={exactitude:.2f}",
        ],
        "suggested_followups": ([] if score >= 0.55 else ["revoir la réponse vs golden keywords"]),
        "dimensions": {
            "exactitude": exactitude,
            "concision": concision,
            "respect_regles": respect,
            "cout": cout,
        },
        "mode": "heuristic",
    }


def _system_prompt() -> str:
    try:
        from team.prompt_overrides import load_override

        ov = load_override("outcome_judge")
        if ov:
            return ov
    except Exception:
        pass
    return (
        "Tu es Argus (QA Studio LBG). Note une sortie d'agent.\n"
        "Critères: exactitude, concision, respect_regles, cout (tokens/latence).\n"
        "Réponds UNIQUEMENT en JSON compact:\n"
        '{"score":0.0-1.0,"pass":bool,"reasons":["..."],'
        '"suggested_followups":["..."],'
        '"dimensions":{"exactitude":0-1,"concision":0-1,"respect_regles":0-1,"cout":0-1}}'
    )


def _user_prompt(
    *,
    task_id: str,
    rubric_id: str,
    artifacts: list[str],
    expected_keywords: list[str],
    latency_ms: float,
) -> str:
    payload = {
        "task_id": task_id,
        "rubric_id": rubric_id,
        "expected_keywords": expected_keywords,
        "latency_ms": latency_ms,
        "artifacts": [a[:2000] for a in artifacts[:6]],
    }
    return "Évalue:\n" + json.dumps(payload, ensure_ascii=False)


def judge_outcome(
    *,
    task_id: str = "",
    artifacts: list[str] | None = None,
    rubric_id: str = "default",
    expected_keywords: list[str] | None = None,
    latency_ms: float = 0.0,
    complete_fn: CompleteFn | None = None,
    profile: str = "json",
) -> dict[str, Any]:
    """Contrat P0 : artifacts + rubric → score / pass / reasons / followups."""
    started = time.time()
    arts = [str(a) for a in (artifacts or []) if str(a).strip()]
    keys = [str(k) for k in (expected_keywords or []) if str(k).strip()]
    rid = (rubric_id or "default").strip() or "default"
    tid = (task_id or "").strip() or "adhoc"

    if not judge_enabled():
        out = {
            "ok": False,
            "skipped": True,
            "task_id": tid,
            "rubric_id": rid,
            "score": 0.0,
            "pass": False,
            "reasons": ["judge disabled"],
            "suggested_followups": [],
        }
        _set_last(out)
        return out

    blob = "\n".join(arts)
    heuristic = _keyword_heuristic(artifact_text=blob, expected_keywords=keys, latency_ms=latency_ms)

    completer = complete_fn
    if completer is None:
        try:
            from team.reason_llm import complete_reason

            completer = complete_reason
        except Exception:
            completer = None

    llm_part: dict[str, Any] | None = None
    if completer is not None:
        try:
            raw = completer(
                system=_system_prompt(),
                user=_user_prompt(
                    task_id=tid,
                    rubric_id=rid,
                    artifacts=arts,
                    expected_keywords=keys,
                    latency_ms=latency_ms,
                ),
                profile=profile,
                temperature=0.1,
            )
            if isinstance(raw, dict) and raw.get("ok") and raw.get("text"):
                parsed = _extract_json_object(str(raw.get("text") or ""))
                if parsed and "score" in parsed:
                    llm_part = parsed
                    llm_part["mode"] = "llm"
                    llm_part["model"] = raw.get("model")
                    llm_part["tier"] = raw.get("tier")
        except Exception as exc:
            heuristic["reasons"].append(f"llm_error:{exc}")

    if llm_part is not None:
        try:
            score = float(llm_part.get("score"))
        except (TypeError, ValueError):
            score = float(heuristic["score"])
        score = max(0.0, min(1.0, score))
        # Blend léger avec heuristique keywords si présents.
        if keys:
            score = round(0.7 * score + 0.3 * float(heuristic["score"]), 4)
        passed = bool(llm_part.get("pass")) if "pass" in llm_part else score >= 0.55
        reasons = [str(r) for r in (llm_part.get("reasons") or []) if str(r).strip()][:8]
        if not reasons:
            reasons = list(heuristic["reasons"])
        followups = [str(f) for f in (llm_part.get("suggested_followups") or []) if str(f).strip()][:6]
        dimensions = llm_part.get("dimensions") if isinstance(llm_part.get("dimensions"), dict) else heuristic["dimensions"]
        mode = "llm+heuristic" if keys else "llm"
    else:
        score = float(heuristic["score"])
        passed = bool(heuristic["pass"])
        reasons = list(heuristic["reasons"])
        followups = list(heuristic["suggested_followups"])
        dimensions = heuristic["dimensions"]
        mode = "heuristic"

    elapsed_ms = int((time.time() - started) * 1000)
    out: dict[str, Any] = {
        "ok": True,
        "task_id": tid,
        "rubric_id": rid,
        "score": score,
        "pass": passed,
        "reasons": reasons,
        "suggested_followups": followups,
        "dimensions": dimensions,
        "mode": mode,
        "latency_ms": latency_ms,
        "judge_ms": elapsed_ms,
        "tokens_used": None,
    }
    _set_last(out)
    return out


def judge_golden_case(
    *,
    case_id: str,
    artifact_text: str,
    complete_fn: CompleteFn | None = None,
    latency_ms: float = 0.0,
) -> dict[str, Any]:
    case = get_golden_case(case_id)
    if case is None:
        out = {"ok": False, "error": f"golden case inconnu: {case_id}", "pass": False, "score": 0.0}
        _set_last(out)
        return out
    keys = [str(k) for k in (case.get("expected_keywords") or []) if str(k).strip()]
    result = judge_outcome(
        task_id=f"golden:{case_id}",
        artifacts=[artifact_text],
        rubric_id=str(case.get("rubric_id") or "default"),
        expected_keywords=keys,
        latency_ms=latency_ms,
        complete_fn=complete_fn,
    )
    result["golden_case_id"] = case_id
    result["domain"] = case.get("domain")
    result["role"] = case.get("role")
    _set_last(result)
    return result


def meta_status() -> dict[str, object]:
    cases = list_golden_cases()
    return {
        "enabled": judge_enabled(),
        "golden_path": str(golden_dataset_path()),
        "golden_cases": len(cases),
        "last_judge": last_judge_trace(),
    }
