"""Prométhée — avis complémentaires / alternatives hors cadre (L0, LLM uncensored).

Ne modifie rien : consultatif uniquement. Garde-fous durs (CSAM / harm IRL) restent.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from team.models import TeamTask
from team.reason_llm import complete_reason, reason_llm_enabled, reason_local_model

_LAST: dict[str, Any] = {}

_SYSTEM = """Tu es Prométhée, agent Studio LBG — conseil hors cadre.
Tu complètes Thémis / Iris / Atlas : avis francs, alternatives non orthodoxes,
idées « personne n'ose les dire » — sans langue de bois corporate.

Règles :
- Français. Sortie = **un seul objet JSON** (pas de markdown hors JSON).
- Fiction adulte / thèmes sombres OK si pertinent au brief.
- Interdit absolu : exploitation sexuelle de mineurs, doxxing, harm IRL concret (armes, fraude, etc.).
- Tu ne décides pas, tu proposes. Pas d'ordre d'exécution ni de claim « à appliquer tout de suite ».
- Reste ancré Lost Heaven / Scrapaltai / Studio Cortex si le brief est LBG ; sinon reste général.

Schéma JSON strict :
{
  "summary": "1-2 phrases",
  "opinions": ["avis complémentaire…"],
  "alternatives": [{"title": "…", "why": "…", "tradeoffs": "…"}],
  "risks": ["…"],
  "out_of_scope_notes": ["ce qui sort du process habituel…"],
  "stay_legal": true
}
Max 5 opinions, 4 alternatives, 4 risks.
"""


def last_contrarian() -> dict[str, Any]:
    return dict(_LAST)


def _extract_json(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if not raw:
        return None
    m = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    if m:
        raw = m.group(1).strip()
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    start, end = raw.find("{"), raw.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(raw[start : end + 1])
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def _normalize_payload(data: dict[str, Any] | None, *, fallback_text: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {
            "summary": (fallback_text or "")[:400] or "Réponse non structurée",
            "opinions": [],
            "alternatives": [],
            "risks": ["parse_failed"],
            "out_of_scope_notes": [],
            "stay_legal": True,
            "raw_preview": (fallback_text or "")[:600],
        }
    opinions = [str(x).strip() for x in (data.get("opinions") or []) if str(x).strip()][:5]
    alts_in = data.get("alternatives") or []
    alternatives: list[dict[str, str]] = []
    if isinstance(alts_in, list):
        for a in alts_in[:4]:
            if isinstance(a, dict):
                alternatives.append(
                    {
                        "title": str(a.get("title") or "")[:120],
                        "why": str(a.get("why") or "")[:400],
                        "tradeoffs": str(a.get("tradeoffs") or "")[:400],
                    }
                )
            elif isinstance(a, str) and a.strip():
                alternatives.append({"title": a.strip()[:120], "why": "", "tradeoffs": ""})
    risks = [str(x).strip() for x in (data.get("risks") or []) if str(x).strip()][:4]
    notes = [str(x).strip() for x in (data.get("out_of_scope_notes") or []) if str(x).strip()][:4]
    return {
        "summary": str(data.get("summary") or "")[:500],
        "opinions": opinions,
        "alternatives": alternatives,
        "risks": risks,
        "out_of_scope_notes": notes,
        "stay_legal": bool(data.get("stay_legal", True)),
    }


def _brief_from_task(task: TeamTask) -> str:
    ctx = task.context if isinstance(task.context, dict) else {}
    parts: list[str] = [f"Objectif: {task.objective}"]
    for key in ("brief", "parent_summary", "proposal", "question", "topic"):
        v = ctx.get(key)
        if isinstance(v, str) and v.strip():
            parts.append(f"{key}: {v.strip()[:2000]}")
    orthodox = ctx.get("orthodox_view") or ctx.get("canonical_view")
    if isinstance(orthodox, str) and orthodox.strip():
        parts.append(f"Vue orthodoxe (à challenger): {orthodox.strip()[:2000]}")
    return "\n".join(parts)


def execute_contrarian_workflow(task: TeamTask, _dispatch: Any = None) -> dict[str, object]:
    """Exécute Prométhée — second avis + alternatives (profil REASON uncensored)."""
    started = time.time()
    global _LAST
    ctx = task.context if isinstance(task.context, dict) else {}

    if not reason_llm_enabled():
        out: dict[str, object] = {
            "ok": False,
            "skipped": True,
            "error": "REASON LLM désactivé ou aucune route",
            "agent_id": "studio_contrarian_promethee",
            "persona": "promethee",
            "autonomy": "L0",
        }
        _LAST = dict(out)
        return out

    model = reason_local_model(profile="uncensored")
    user = _brief_from_task(task)
    temp = float(os.environ.get("LBG_CONTRARIAN_TEMPERATURE", "0.55"))
    llm = complete_reason(
        system=_SYSTEM,
        user=user,
        temperature=temp,
        profile="uncensored",
    )
    text = str(llm.get("text") or "") if isinstance(llm, dict) else ""
    parsed = _normalize_payload(_extract_json(text), fallback_text=text)
    ok = bool(isinstance(llm, dict) and llm.get("ok"))
    out = {
        "ok": ok,
        "agent_id": "studio_contrarian_promethee",
        "persona": "promethee",
        "role": "contrarian",
        "autonomy": "L0",
        "capability": "second_opinion",
        "llm_profile": "uncensored",
        "model": llm.get("model") if isinstance(llm, dict) else model,
        "tier": llm.get("tier") if isinstance(llm, dict) else None,
        "latency_ms": int((time.time() - started) * 1000),
        "counsel": parsed,
        "context_echo": {
            "force": bool(ctx.get("contrarian") or ctx.get("promethee")),
        },
        "error": None if ok else (llm.get("error") if isinstance(llm, dict) else "llm_failed"),
    }
    _LAST = {k: v for k, v in out.items() if k != "counsel"} | {"counsel_summary": parsed.get("summary")}
    return out
