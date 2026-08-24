from fastapi import APIRouter, Header, HTTPException

from models.characters import CharacterCreateRequest, CharacterCreateResponse
from services.character_creation import CharacterCreationError, create_character

router = APIRouter()


@router.post("", response_model=CharacterCreateResponse, status_code=201)
async def create_character_route(
    payload: CharacterCreateRequest,
    x_account_id: str = Header(default="default", alias="X-Account-Id"),
) -> CharacterCreateResponse:
    try:
        return create_character(payload, account_id=x_account_id)
    except CharacterCreationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
