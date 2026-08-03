"""Schémas Team — propositions de plan + messages inter-agents (ADR 0019)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from team.models import VALID_PRIORITIES, VALID_ROLES

PlanSource = Literal["heuristic", "llm", "hybrid"]
MessageKind = Literal["consult", "gap", "propose", "ack", "verify_result"]
AutonomyLevel = Literal["L0", "L1", "L2"]

VALID_PLAN_SOURCES: frozenset[str] = frozenset({"heuristic", "llm", "hybrid"})
VALID_MESSAGE_KINDS: frozenset[str] = frozenset(
    {"consult", "gap", "propose", "ack", "verify_result"}
)
VALID_AUTONOMY: frozenset[str] = frozenset({"L0", "L1", "L2"})

# Context keys autorisés sur une proposition de plan (whitelist Vague 1–2).
ALLOWED_PLAN_CONTEXT_KEYS: frozenset[str] = frozenset(
    {
        "subproject",
        "godot_supervisor",
        "godot_mode",
        "godot_track",
        "godot_dev_persona",
        "godot_dev_track",
        "godot_validation",
        "infographiste_ia",
        "m9_track",
        "autoconsult",
        "autoconsult_round",
        "reunification_brief",
        "lbg_sa_plan",
        "core3_build",
        "workflow",
        "player_ia_mode",
        "cursor_cloud_agent",
        "repository",
        "dry_run",
        "trace_id",
        "parent_task_id",
        "owner_agent",
        "capability_hint",
    }
)

MAX_OBJECTIVE_LEN = 800
MAX_RATIONALE_LEN = 400
MAX_AGENT_ID_LEN = 64
MAX_PAYLOAD_KEYS = 32
MAX_PAYLOAD_STR_LEN = 2000


@dataclass
class TeamPlanProposal:
    role: str
    objective: str
    priority: str = "normal"
    approval_required: bool = False
    autonomy: str = "L1"
    context: dict[str, object] = field(default_factory=dict)
    rationale: str = ""
    capability: str = ""
    actor_id: str = "system:team"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class TeamMessage:
    id: str
    from_agent: str
    to_agent: str
    kind: str
    payload: dict[str, object] = field(default_factory=dict)
    task_id: str = ""
    created_ts: float = 0.0
    actor_id: str = "system:team"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class TeamMemoryEntry:
    id: str
    agent_id: str
    kind: str
    summary: str
    tags: list[str] = field(default_factory=list)
    task_id: str = ""
    created_ts: float = 0.0
    meta: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def truncate_text(text: str, limit: int) -> str:
    t = (text or "").strip()
    if len(t) <= limit:
        return t
    return t[: max(0, limit - 1)] + "…"


def sanitize_context(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, object] = {}
    for key, value in raw.items():
        k = str(key)
        if k not in ALLOWED_PLAN_CONTEXT_KEYS:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            out[k] = value
        elif isinstance(value, list) and all(isinstance(x, (str, int, float, bool)) for x in value):
            out[k] = list(value)[:20]
    return out


def sanitize_plan_proposal(raw: dict[str, Any], *, actor_id: str = "system:team") -> TeamPlanProposal:
    """Valide / normalise une proposition ; lève ValueError si hors allowlist."""
    role = str(raw.get("role") or "").strip()
    if role not in VALID_ROLES:
        raise ValueError(f"role invalide: {role}")
    objective = truncate_text(str(raw.get("objective") or ""), MAX_OBJECTIVE_LEN)
    if not objective:
        raise ValueError("objective vide")
    priority = str(raw.get("priority") or "normal").strip()
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"priority invalide: {priority}")
    autonomy = str(raw.get("autonomy") or "L1").strip().upper()
    if autonomy not in VALID_AUTONOMY:
        raise ValueError(f"autonomy invalide: {autonomy}")
    approval_required = bool(raw.get("approval_required") or False)
    if autonomy == "L2":
        approval_required = True
    context = sanitize_context(raw.get("context"))
    rationale = truncate_text(str(raw.get("rationale") or ""), MAX_RATIONALE_LEN)
    capability = truncate_text(str(raw.get("capability") or ""), 80)
    aid = truncate_text(str(raw.get("actor_id") or actor_id), MAX_AGENT_ID_LEN) or actor_id
    return TeamPlanProposal(
        role=role,
        objective=objective,
        priority=priority,
        approval_required=approval_required,
        autonomy=autonomy,
        context=context,
        rationale=rationale,
        capability=capability,
        actor_id=aid,
    )


def sanitize_plan_proposals(
    raw_list: object, *, actor_id: str = "system:team"
) -> tuple[list[TeamPlanProposal], list[str]]:
    """Retourne (proposals valides, erreurs). N’échoue pas en bloc."""
    if not isinstance(raw_list, list):
        return [], ["proposals must be a list"]
    ok: list[TeamPlanProposal] = []
    errors: list[str] = []
    for i, item in enumerate(raw_list[:20]):
        if not isinstance(item, dict):
            errors.append(f"[{i}] not an object")
            continue
        try:
            ok.append(sanitize_plan_proposal(item, actor_id=actor_id))
        except ValueError as e:
            errors.append(f"[{i}] {e}")
    return ok, errors


def sanitize_payload(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, object] = {}
    for i, (key, value) in enumerate(raw.items()):
        if i >= MAX_PAYLOAD_KEYS:
            break
        k = truncate_text(str(key), 64)
        if isinstance(value, str):
            out[k] = truncate_text(value, MAX_PAYLOAD_STR_LEN)
        elif isinstance(value, (int, float, bool)) or value is None:
            out[k] = value
        elif isinstance(value, list):
            clean: list[object] = []
            for x in value[:30]:
                if isinstance(x, str):
                    clean.append(truncate_text(x, 200))
                elif isinstance(x, (int, float, bool)) or x is None:
                    clean.append(x)
            out[k] = clean
        elif isinstance(value, dict):
            nested: dict[str, object] = {}
            for j, (nk, nv) in enumerate(value.items()):
                if j >= 16:
                    break
                if isinstance(nv, (str, int, float, bool)) or nv is None:
                    nested[truncate_text(str(nk), 64)] = (
                        truncate_text(nv, 400) if isinstance(nv, str) else nv
                    )
            out[k] = nested
    return out


def validate_message_fields(
    *,
    from_agent: str,
    to_agent: str,
    kind: str,
) -> tuple[str, str, str]:
    fa = truncate_text(from_agent, MAX_AGENT_ID_LEN)
    ta = truncate_text(to_agent, MAX_AGENT_ID_LEN)
    k = (kind or "").strip().lower()
    if not fa:
        raise ValueError("from_agent vide")
    if not ta:
        raise ValueError("to_agent vide")
    if k not in VALID_MESSAGE_KINDS:
        raise ValueError(f"kind invalide: {kind}")
    return fa, ta, k
