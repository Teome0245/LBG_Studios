"""Ingestion v1 — lessons / experiences / knowledge text snippets."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .embeddings import embed_text
from .store import ensure_schema, upsert_chunk

logger = logging.getLogger("lbg.rag.ingest")


@dataclass
class IngestItem:
    source_id: str
    source_kind: str
    content: str
    metadata: dict[str, Any]


def _lessons_candidates() -> list[Path]:
    out: list[Path] = []
    env = os.environ.get("LBG_TEAM_LESSONS_PATH", "").strip()
    if env:
        out.append(Path(env))
    here = Path(__file__).resolve()
    # services/rag → services → orchestrator → cortex → knowledge
    out.append(here.parents[3] / "knowledge" / "lessons_learned.json")
    out.append(Path("/var/lib/lbg/knowledge/lessons_learned.json"))
    out.append(Path("/opt/LBG_IA_MMO/knowledge/lessons_learned.json"))
    # dédup
    seen: set[str] = set()
    uniq: list[Path] = []
    for p in out:
        key = str(p)
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    return uniq


def _experiences_path() -> Path | None:
    raw = os.environ.get("LBG_JOBS_MEMORY_PATH", "").strip()
    if raw:
        return Path(raw)
    state = os.environ.get("LBG_JOBS_STATE_PATH", "/var/lib/lbg/jobs/state.json").strip()
    if not state:
        return None
    return Path(state).parent / "experiences.jsonl"


def load_lesson_items() -> list[IngestItem]:
    items: list[IngestItem] = []
    for path in _lessons_candidates():
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        lessons = data.get("lessons") if isinstance(data, dict) else None
        if not isinstance(lessons, list):
            continue
        for lesson in lessons:
            if not isinstance(lesson, dict):
                continue
            lid = str(lesson.get("id") or "").strip()
            pattern = str(lesson.get("pattern") or "").strip()
            if not lid or not pattern:
                continue
            dnr = str(lesson.get("do_not_repeat") or "").strip()
            ctx = str(lesson.get("context") or "").strip()
            role = str(lesson.get("agent_role") or "").strip()
            parts = [pattern]
            if dnr:
                parts.append(f"Ne pas répéter : {dnr}")
            if ctx:
                parts.append(f"Contexte : {ctx}")
            if role:
                parts.append(f"Rôle : {role}")
            items.append(
                IngestItem(
                    source_id=lid,
                    source_kind="lesson",
                    content=" | ".join(parts)[:1200],
                    metadata={
                        "path": str(path),
                        "agent_role": role,
                        "outcome": str(lesson.get("failure_or_success") or ""),
                    },
                )
            )
        if items:
            break
    return items


def load_experience_items(*, limit: int = 200) -> list[IngestItem]:
    path = _experiences_path()
    if path is None or not path.is_file():
        return []
    items: list[IngestItem] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines[-max(1, limit) :]:
        line = line.strip()
        if not line:
            continue
        try:
            note = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(note, dict):
            continue
        eid = str(note.get("id") or "").strip()
        goal = str(note.get("goal") or "").strip()
        if not eid or not goal:
            continue
        outcome = str(note.get("outcome") or "").strip()
        problem = str(note.get("problem") or "").strip()
        resolution = str(note.get("resolution") or "").strip()
        parts = [f"Objectif : {goal}", f"Résultat : {outcome or 'unknown'}"]
        if problem:
            parts.append(f"Problème : {problem}")
        if resolution:
            parts.append(f"Résolution : {resolution}")
        items.append(
            IngestItem(
                source_id=eid,
                source_kind="experience",
                content=" | ".join(parts)[:1200],
                metadata={"path": str(path), "outcome": outcome},
            )
        )
    return items


def load_knowledge_snippets() -> list[IngestItem]:
    """Faits stables knowledge/ — persona + rag_facts.jsonl (pas le dump docs entier)."""
    root = Path(__file__).resolve().parents[3] / "knowledge"
    # Sur .100 backend monté : /app/knowledge
    alt = Path("/app/knowledge")
    if alt.is_dir():
        root = alt
    items: list[IngestItem] = []

    # --- rag_facts.jsonl ---
    facts_path = root / "rag_facts.jsonl"
    if facts_path.is_file():
        try:
            for line in facts_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(row, dict):
                    continue
                fid = str(row.get("id") or "").strip()
                text = str(row.get("text") or "").strip()
                if not fid or not text:
                    continue
                kind = str(row.get("kind") or "knowledge").strip() or "knowledge"
                items.append(
                    IngestItem(
                        source_id=f"fact_{fid}",
                        source_kind="knowledge",
                        content=text[:1200],
                        metadata={"path": str(facts_path), "fact_kind": kind},
                    )
                )
        except OSError:
            pass

    # --- character pack (plusieurs chunks) ---
    pack = root / "character" / "compagnon_v1.json"
    if pack.is_file():
        try:
            data = json.loads(pack.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = None
        if isinstance(data, dict):
            name = str(data.get("display_name") or data.get("name") or "Compagnon").strip()
            personality = data.get("personality") if isinstance(data.get("personality"), dict) else {}
            summary = str(personality.get("summary") or "").strip()
            items.append(
                IngestItem(
                    source_id="character_compagnon_v1",
                    source_kind="knowledge",
                    content=(f"Persona Compagnon « {name} ». {summary}").strip()[:1200],
                    metadata={"path": str(pack)},
                )
            )
            worldview = [str(x).strip() for x in (personality.get("worldview") or []) if str(x).strip()]
            if worldview:
                items.append(
                    IngestItem(
                        source_id="character_worldview",
                        source_kind="knowledge",
                        content=("Worldview Compagnon : " + " | ".join(worldview[:6]))[:1200],
                        metadata={"path": str(pack)},
                    )
                )
            nots = [str(x).strip() for x in (personality.get("not") or []) if str(x).strip()]
            if nots:
                items.append(
                    IngestItem(
                        source_id="character_avoid",
                        source_kind="knowledge",
                        content=("Compagnon à éviter : " + " ; ".join(nots[:6]))[:1200],
                        metadata={"path": str(pack)},
                    )
                )
            bl = [str(x).strip() for x in (data.get("blacklist") or []) if str(x).strip()]
            if bl:
                items.append(
                    IngestItem(
                        source_id="character_blacklist",
                        source_kind="knowledge",
                        content=("Blacklist Compagnon : " + ", ".join(f"« {x} »" for x in bl[:10]))[:1200],
                        metadata={"path": str(pack)},
                    )
                )
            phrases = data.get("catchphrases_seed") if isinstance(data.get("catchphrases_seed"), list) else []
            texts = []
            for p in phrases[:5]:
                if isinstance(p, dict) and p.get("text"):
                    texts.append(str(p["text"]).strip())
            if texts:
                items.append(
                    IngestItem(
                        source_id="character_catchphrases",
                        source_kind="knowledge",
                        content=("Formules signature Compagnon : " + " / ".join(texts))[:1200],
                        metadata={"path": str(pack)},
                    )
                )
    return items


def collect_ingest_items() -> list[IngestItem]:
    return load_lesson_items() + load_experience_items() + load_knowledge_snippets()


async def ingest_items(items: Iterable[IngestItem]) -> dict[str, Any]:
    """Embed + upsert. Retourne compteurs."""
    mode = await ensure_schema()
    ok = 0
    fail = 0
    for item in items:
        try:
            emb = await embed_text(item.content)
            await upsert_chunk(
                source_id=item.source_id,
                source_kind=item.source_kind,
                content=item.content,
                embedding=emb,
                metadata=item.metadata,
            )
            ok += 1
        except Exception as exc:
            fail += 1
            logger.warning(
                "ingest skip %s:%s — %s",
                item.source_kind,
                item.source_id,
                exc,
            )
    return {"ok": ok, "fail": fail, "store_mode": mode}


async def ingest_all() -> dict[str, Any]:
    items = collect_ingest_items()
    stats = await ingest_items(items)
    return {
        "items_seen": len(items),
        "upserted": stats["ok"],
        "failed": stats["fail"],
        "store_mode": stats.get("store_mode"),
        "by_kind": {
            "lesson": sum(1 for i in items if i.source_kind == "lesson"),
            "experience": sum(1 for i in items if i.source_kind == "experience"),
            "knowledge": sum(1 for i in items if i.source_kind == "knowledge"),
        },
    }


def main() -> None:
    """CLI : ``python -m services.rag.ingest`` depuis orchestrator/."""
    import asyncio

    result = asyncio.run(ingest_all())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
