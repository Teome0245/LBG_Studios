"""Journal de contexte injecté — transparence Compagnon (A1).

Liste les blocs sous les yeux du LLM **sans** secrets (pas de tokens,
mots de passe, contenus bruts longs). Surface UI : « Contexte ce tour ».
"""

from __future__ import annotations

from typing import Any

_SUMMARY_MAX = 160
_SECRET_MARKERS = (
    "password",
    "passwd",
    "secret",
    "api_key",
    "apikey",
    "token",
    "authorization",
    "bearer ",
)


def _sanitize_summary(text: str) -> str:
    s = " ".join(str(text or "").split())
    low = s.lower()
    for marker in _SECRET_MARKERS:
        if marker in low:
            return "(ommis — contenu sensible)"
    if len(s) > _SUMMARY_MAX:
        return s[: _SUMMARY_MAX - 1] + "…"
    return s


def make_block(
    id: str,
    *,
    label: str,
    summary: str = "",
    chars: int = 0,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Construit une entrée journal (sanitisée)."""
    safe = _sanitize_summary(summary)
    out: dict[str, Any] = {
        "id": str(id or "unknown")[:48],
        "label": str(label or id or "bloc")[:80],
        "summary": safe,
        "detail": safe,  # alias UI
        "chars": max(0, int(chars or 0)),
    }
    if meta and isinstance(meta, dict):
        cleaned: dict[str, Any] = {}
        for k, v in list(meta.items())[:12]:
            key = str(k)[:40]
            low = key.lower()
            if any(m in low for m in _SECRET_MARKERS):
                continue
            if isinstance(v, bool):
                cleaned[key] = v
            elif isinstance(v, (int, float)):
                cleaned[key] = v
            elif isinstance(v, str):
                cleaned[key] = _sanitize_summary(v)[:80]
            elif isinstance(v, list) and all(
                isinstance(x, (str, int, float)) for x in v[:8]
            ):
                cleaned[key] = v[:8]
        if cleaned:
            out["meta"] = cleaned
    return out


# Alias plan A1
journal_entry = make_block


def summarize_block(text: str, *, max_len: int = 80) -> str:
    t = _sanitize_summary(text)
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


def finalize_journal(blocks: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Payload `context_journal` attaché à la réponse /ask."""
    cleaned: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in blocks or []:
        if not isinstance(raw, dict):
            continue
        bid = str(raw.get("id") or "").strip() or "unknown"
        if bid in seen and bid != "short_circuit":
            continue
        seen.add(bid)
        cleaned.append(
            make_block(
                bid,
                label=str(raw.get("label") or bid),
                summary=str(raw.get("summary") or raw.get("detail") or ""),
                chars=int(raw.get("chars") or 0),
                meta=raw.get("meta") if isinstance(raw.get("meta"), dict) else None,
            )
        )
    total = sum(int(b.get("chars") or 0) for b in cleaned)
    return {
        "blocks": cleaned,
        "count": len(cleaned),
        "empty": len(cleaned) == 0,
        "total_chars": total,
    }


def empty_journal() -> dict[str, Any]:
    return finalize_journal([])


def attach_context_journal(
    result: Any,
    entries: list[dict[str, Any]] | None,
) -> Any:
    """Attache `context_journal` sur un dict de réponse LLM (best-effort)."""
    if not isinstance(result, dict):
        return result
    existing = result.get("context_journal")
    if isinstance(existing, dict) and (
        existing.get("blocks") or existing.get("count") is not None
    ):
        # Ne pas écraser un journal déjà posé (short-circuit dédié)
        return result
    out = dict(result)
    out["context_journal"] = finalize_journal(entries)
    return out
