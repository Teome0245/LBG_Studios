"""Auth légère hub_runtime — comptes + sessions (hors Core3)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from pathlib import Path
from typing import Any

from tools.hub_runtime.sim import HUMAN_OID


def _state_dir() -> Path:
    env = os.environ.get("LBG_HUB_STATE_DIR", "").strip()
    if env:
        return Path(env)
    local = Path(__file__).resolve().parent / "data"
    remote = Path("/opt/lbg-hub-runtime/data")
    if remote.is_dir():
        return remote
    try:
        remote.mkdir(parents=True, exist_ok=True)
        return remote
    except OSError:
        local.mkdir(parents=True, exist_ok=True)
        return local


def _hash_password(password: str, salt: str) -> str:
    raw = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return raw


class HubAuth:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._accounts: dict[str, dict[str, Any]] = {}
        self._sessions: dict[str, dict[str, Any]] = {}
        self._next_oid = HUMAN_OID
        self._ws_public = os.environ.get(
            "LBG_HUB_WS_PUBLIC", "ws://192.168.0.246:8787/ws"
        )
        self._load()

    def _accounts_path(self) -> Path:
        return _state_dir() / "accounts.json"

    def _load(self) -> None:
        path = self._accounts_path()
        if not path.is_file():
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(raw, dict):
            return
        acc = raw.get("accounts") or {}
        if isinstance(acc, dict):
            self._accounts = {str(k): v for k, v in acc.items() if isinstance(v, dict)}
        self._next_oid = int(raw.get("next_oid", HUMAN_OID))
        # sessions non persistées (redémarrage = re-login) — OK spike

    def _save(self) -> None:
        path = self._accounts_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "accounts": self._accounts,
            "next_oid": self._next_oid,
            "saved_at": int(time.time()),
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)

    def _alloc_oid(self) -> int:
        self._next_oid = max(self._next_oid + 1, HUMAN_OID + 1)
        return self._next_oid

    def register_or_login(self, username: str, password: str) -> dict[str, Any]:
        name = (username or "").strip()
        if not name:
            return {"ok": False, "error": "auth_failed", "message": "username vide"}
        pwd = password or ""
        with self._lock:
            acc = self._accounts.get(name.lower())
            if acc is None:
                salt = secrets.token_hex(8)
                oid = HUMAN_OID if name.lower() == "voyageur" else self._alloc_oid()
                acc = {
                    "username": name,
                    "salt": salt,
                    "password_hash": _hash_password(pwd, salt),
                    "character_id": oid,
                    "display_name": name,
                    "created_at": int(time.time()),
                }
                self._accounts[name.lower()] = acc
                self._save()
            else:
                salt = str(acc.get("salt", ""))
                expect = str(acc.get("password_hash", ""))
                got = _hash_password(pwd, salt)
                # spike : mot de passe vide accepte si compte créé avec vide
                if not hmac.compare_digest(expect, got):
                    return {"ok": False, "error": "auth_failed", "message": "mot de passe invalide"}
            token = secrets.token_urlsafe(24)
            self._sessions[token] = {
                "username": acc["username"],
                "character_id": int(acc["character_id"]),
                "created_at": time.time(),
            }
            return {
                "ok": True,
                "session_token": token,
                "characters": [
                    {
                        "id": int(acc["character_id"]),
                        "name": str(acc.get("display_name", name)),
                        "race": "hub_runtime",
                    }
                ],
                "source": "hub_runtime",
            }

    def guest(self, player_name: str = "Voyageur") -> dict[str, Any]:
        return self.register_or_login(player_name or "Voyageur", "")

    def resolve(self, token: str) -> dict[str, Any] | None:
        if not token:
            return None
        with self._lock:
            # compat spike-local
            if token in {"spike-local", "spike", "dev-mock-token"}:
                return {
                    "username": "Voyageur",
                    "character_id": HUMAN_OID,
                }
            return self._sessions.get(token)

    def select_character(self, token: str, character_id: int) -> dict[str, Any]:
        sess = self.resolve(token)
        if sess is None:
            return {"ok": False, "error": "session_expired", "message": "login requis"}
        cid = int(character_id) or int(sess["character_id"])
        if cid != int(sess["character_id"]):
            return {"ok": False, "error": "auth_failed", "message": "character_id inconnu"}
        return {
            "ok": True,
            "character_id": cid,
            "ws_url": self._ws_public,
            "source": "hub_runtime",
        }

    def enter_zone(self, token: str, zone: str = "scrapaltai") -> dict[str, Any]:
        sess = self.resolve(token)
        if sess is None:
            return {"ok": False, "error": "session_expired", "message": "login requis"}
        return {
            "ok": True,
            "ws_url": self._ws_public,
            "your_character_id": int(sess["character_id"]),
            "zone": zone or "scrapaltai",
            "source": "hub_runtime",
        }


AUTH = HubAuth()
