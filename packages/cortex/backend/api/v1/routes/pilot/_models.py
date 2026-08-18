"""Modèles Pydantic partagés des routes Pilot."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentDialogueInvokeBody(BaseModel):
    """Corps pour `POST agent-dialogue /invoke` (même forme que l'agent HTTP dialogue)."""

    actor_id: str
    text: str
    context: dict[str, object] = Field(default_factory=dict)


class ActionProposalBody(BaseModel):
    """Corps pour `POST orchestrator /v1/action-proposal`."""

    actor_id: str
    text: str = Field(..., min_length=1)
    context: dict[str, object] = Field(default_factory=dict)


class AssistantSessionExportBody(BaseModel):
    """Corps pour export borné de résumé session (validation serveur, sans persistance)."""

    notes: str | None = None
    history: list[dict[str, object]] | None = None
    session_summary: dict[str, object] | None = None
    mmo_bridge: dict[str, object] | None = None


class AidRequest(BaseModel):
    npc_id: str
    hunger_delta: float = 0.0
    thirst_delta: float = 0.0
    fatigue_delta: float = 0.0
    reputation_delta: int = 0


class JobCreateBody(BaseModel):
    """Corps pour `POST orchestrator /v1/jobs` (moteur de jobs autonome)."""

    actor_id: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
    context: dict[str, object] = Field(default_factory=dict)
    approval_token: str | None = None
    auto_start: bool = True
    model: str | None = None
    planner: str | None = None


class JobApproveBody(BaseModel):
    token: str = Field(..., min_length=1)


class TeamCreateBody(BaseModel):
    role: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
    actor_id: str = "pilot:team"
    priority: str = "normal"
    approval_required: bool | None = None
    context: dict[str, object] = Field(default_factory=dict)
    approval_token: str | None = None


class TeamPlanBody(BaseModel):
    objective: str = Field(..., min_length=1)
    actor_id: str = "pilot:team"
    use_llm: bool | None = None
    include_memory: bool | None = None


class TeamApproveBody(BaseModel):
    token: str = Field(..., min_length=1)


class TeamRunBody(BaseModel):
    approval_token: str | None = None


class TeamMessageBody(BaseModel):
    from_agent: str = Field(..., min_length=1)
    to_agent: str = Field(..., min_length=1)
    kind: str = Field(..., min_length=1)
    payload: dict[str, object] = Field(default_factory=dict)
    task_id: str = ""
    actor_id: str = "pilot:team"


class TeamMemoryBody(BaseModel):
    agent_id: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    kind: str = "learning"
    tags: list[str] = Field(default_factory=list)
    task_id: str = ""
    meta: dict[str, object] = Field(default_factory=dict)
