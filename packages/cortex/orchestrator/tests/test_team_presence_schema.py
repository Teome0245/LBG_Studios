"""Validation légère du contrat team.presence.v1 (sans dépendance jsonschema)."""

from __future__ import annotations

import json
from pathlib import Path

SCHEMAS = Path(__file__).resolve().parents[2] / "docs" / "schemas" / "team"
EXAMPLE = SCHEMAS / "examples" / "team.presence.v1.example.json"
PRESENCE = SCHEMAS / "team.presence.v1.schema.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_team_presence_example_matches_contract():
    schema = _load(PRESENCE)
    example = _load(EXAMPLE)
    assert example["schema"] == schema["properties"]["schema"]["const"]
    for key in schema["required"]:
        assert key in example, f"missing required field {key}"
    statuses = set(schema["$defs"]["presence_status"]["enum"])
    zones = set(schema["$defs"]["zone_id"]["enum"])
    assert example["status"] in statuses
    assert example["location"] in zones
    assert example["target_destination"] in zones
    assert len(example["current_action"]) <= schema["properties"]["current_action"]["maxLength"]
