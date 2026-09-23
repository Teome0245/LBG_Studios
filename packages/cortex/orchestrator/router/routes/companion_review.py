"""POST /v1/companion/review-proposal — contre-pouvoir Compagnon."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.companion_review import review_companion_proposal

router = APIRouter()


class CompanionReviewRequest(BaseModel):
    actor_id: str = "ui:compagnon"
    source_text: str = ""
    proposal: dict[str, object] | None = None
    force_llm: bool = False
    context: dict[str, object] = Field(default_factory=dict)


@router.post("/companion/review-proposal", tags=["assistant"])
def companion_review_proposal(payload: CompanionReviewRequest) -> dict[str, object]:
    review = review_companion_proposal(
        payload.proposal if isinstance(payload.proposal, dict) else None,
        source_text=payload.source_text,
        force_llm=bool(payload.force_llm),
    )
    data = review.model_dump(by_alias=True)
    return {"ok": True, "actor_id": payload.actor_id, "review": data}
