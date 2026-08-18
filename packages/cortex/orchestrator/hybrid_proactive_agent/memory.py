from __future__ import annotations

import json
from pathlib import Path
from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    summary: str
    tags: list[str] = Field(default_factory=list)
    payload: dict[str, object] = Field(default_factory=dict)


class LongTermMemoryStore:
    def __init__(self, path: str | Path | None = None, max_entries: int = 500) -> None:
        self.path = Path(path) if path else None
        self.max_entries = max(1, int(max_entries))
        self._entries: list[MemoryEntry] = []
        self._load()

    def _load(self) -> None:
        if not self.path or not self.path.exists():
            return
        try:
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                self._entries.append(MemoryEntry.model_validate_json(line))
        except Exception:
            self._entries = []

    def _persist(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = "\n".join(e.model_dump_json() for e in self._entries[-self.max_entries:]) + "\n"
        self.path.write_text(data, encoding="utf-8")

    def append(self, entry: MemoryEntry) -> None:
        self._entries.append(entry)
        self._entries = self._entries[-self.max_entries:]
        self._persist()

    def recall(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        q = (query or "").strip().lower()
        if not q:
            return self._entries[-limit:][::-1]
        ranked = [e for e in reversed(self._entries) if q in e.summary.lower() or any(q in t.lower() for t in e.tags)]
        return ranked[: max(1, int(limit))]

    def context_hints(self, query: str, limit: int = 3) -> str:
        items = self.recall(query, limit=limit)
        if not items:
            return ""
        return "\n".join(f"- {item.summary}" for item in items)
