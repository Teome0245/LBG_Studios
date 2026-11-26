"""Lecteur Thunderbird en lecture seule (index SQLite Gloda global-messages-db.sqlite).

Copie la base vers un fichier temporaire avant lecture pour ne jamais verrouiller
Thunderbird lorsqu'il est ouvert sur le poste Windows (.10).
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
from typing import Any
from urllib.parse import unquote


def find_thunderbird_gloda_dbs() -> list[Path]:
    """Localise les bases global-messages-db.sqlite dans les profils Thunderbird."""
    candidates: list[Path] = []
    appdata = os.environ.get("APPDATA", "").strip()
    if appdata:
        candidates.append(Path(appdata) / "Thunderbird" / "Profiles")
    home = Path.home()
    candidates.extend([
        home / "AppData" / "Roaming" / "Thunderbird" / "Profiles",
        home / ".thunderbird",
    ])
    found: list[Path] = []
    for root in candidates:
        if not root.is_dir():
            continue
        for db in root.glob("*/global-messages-db.sqlite"):
            if db.is_file():
                found.append(db)
    # Plus récente en premier
    found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return found


def _parse_folder_uri(uri: str) -> tuple[str, str]:
    """Extrait (compte, dossier) depuis une URI Thunderbird imap://user@host/INBOX."""
    raw = unquote(uri or "")
    if "://" not in raw:
        return "", raw
    rest = raw.split("://", 1)[1]
    parts = rest.split("/", 1)
    account = parts[0]
    folder = parts[1] if len(parts) > 1 else ""
    return account, folder


def read_thunderbird_recent(limit: int = 15, account_filter: str = "") -> dict[str, Any]:
    """Retourne les `limit` derniers messages indexés par Thunderbird (lecture seule)."""
    dbs = find_thunderbird_gloda_dbs()
    if not dbs:
        return {"ok": False, "error": "Profil Thunderbird (global-messages-db.sqlite) introuvable", "messages": []}

    db_path = dbs[0]
    limit = max(1, min(int(limit), 50))
    filt = (account_filter or "").strip().lower()

    with tempfile.TemporaryDirectory(prefix="lbg_tb_") as tmpdir:
        tmp_db = Path(tmpdir) / "gloda.sqlite"
        try:
            shutil.copy2(db_path, tmp_db)
            for suffix in ("-wal", "-shm"):
                side = Path(str(db_path) + suffix)
                if side.is_file():
                    shutil.copy2(side, Path(str(tmp_db) + suffix))
        except Exception as exc:
            return {"ok": False, "error": f"Copie temporaire impossible: {exc}", "messages": []}

        try:
            conn = sqlite3.connect(f"file:{tmp_db}?mode=ro", uri=True, timeout=5.0)
            cur = conn.cursor()
            query = """
                SELECT m.date, t.c3author, t.c1subject, f.folderURI
                FROM messages m
                JOIN messagesText_content t ON m.id = t.docid
                LEFT JOIN folderLocations f ON m.folderID = f.id
                WHERE m.deleted = 0
                ORDER BY m.date DESC
                LIMIT ?
            """
            rows = cur.execute(query, (limit * 3 if filt else limit,)).fetchall()
            conn.close()
        except Exception as exc:
            return {"ok": False, "error": f"Lecture SQLite Gloda impossible: {exc}", "messages": []}

    messages: list[dict[str, Any]] = []
    for ts_us, author, subject, folder_uri in rows:
        account, folder = _parse_folder_uri(str(folder_uri or ""))
        if filt and filt not in account.lower() and filt not in str(folder_uri or "").lower():
            continue
        date_str = ""
        if isinstance(ts_us, (int, float)) and ts_us > 0:
            try:
                dt = datetime.fromtimestamp(ts_us / 1_000_000.0, tz=timezone.utc).astimezone()
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                date_str = str(ts_us)
        messages.append({
            "date": date_str,
            "account": account,
            "folder": folder,
            "from": str(author or "").strip(),
            "subject": str(subject or "(Sans objet)").strip(),
        })
        if len(messages) >= limit:
            break

    return {
        "ok": True,
        "profile": db_path.parent.name,
        "count": len(messages),
        "messages": messages,
    }
