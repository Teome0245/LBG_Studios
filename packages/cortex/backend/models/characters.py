from __future__ import annotations

import enum

from pydantic import BaseModel, Field


class CreationMode(str, enum.Enum):
    archetype = "archetype"
    empreinte = "empreinte"
    chaos = "chaos"


class ArchetypeId(str, enum.Enum):
    forgeur = "forgeur"
    traqueur = "traqueur"
    soigneur = "soigneur"
    voix = "voix"
    poing = "poing"
    oeil = "oeil"


class ColorCustomization(BaseModel):
    skin: str | None = Field(None, examples=["#8B6914"])
    eyes: str | None = Field(None, examples=["#00CED1"])
    accent: str | None = Field(None, examples=["#FF6B35"])


class Customization(BaseModel):
    name: str = Field(..., min_length=2, max_length=32, examples=["Kael"])
    colors: ColorCustomization = Field(default_factory=ColorCustomization)
    traits: list[str] = Field(default_factory=list, max_length=3)
    corpulence: float = Field(default=0.5, ge=0.0, le=1.0)


class CharacterCreateRequest(BaseModel):
    mode: CreationMode = Field(..., examples=["archetype"])
    archetype: ArchetypeId | None = Field(
        None,
        description="Requis si mode=archetype",
        examples=["traqueur"],
    )
    empreinte_pnj_id: str | None = Field(
        None,
        description="Requis si mode=empreinte",
        examples=["npc:core3_kisreudi"],
    )
    race_id: str | None = Field(
        None,
        description="Optionnel si mode=archetype — race parmi les suggestions de l'archétype",
        examples=["race:fel_rani"],
    )
    customization: Customization
    skip_awakening: bool = Field(default=False)
    ai_brief: str | None = Field(
        None,
        max_length=256,
        description="Brief narratif optionnel (joueur IA)",
        examples=["un traqueur solitaire, méfiant"],
    )
    is_ai: bool = Field(default=False)


class CharacterStats(BaseModel):
    force: int
    agilite: int
    intelligence: int
    hp: int = 100
    endurance: int
    esprit: int


class CharacterOrigin(BaseModel):
    mode: CreationMode
    archetype: ArchetypeId | None = None
    empreinte_pnj_id: str | None = None
    amas_location: str = "champ_des_amas_est"
    ai_brief: str | None = None


class CharacterCreateResponse(BaseModel):
    character_id: str = Field(..., examples=["chr_a7f3e1"])
    name: str
    race: str = Field(..., examples=["race:fel_rani"])
    race_display: str = Field(..., examples=["Fel'Rani"])
    archetype_starter: ArchetypeId
    stats: CharacterStats
    origin: CharacterOrigin
    is_ai: bool = False
    lore_brief: str = Field(..., examples=["L'Amas a pulsé au rythme du vent."])
    noyau_id: str = Field(..., examples=["noyau_a1b2c3d4"])
    particule_seed: str = Field(..., examples=["p7e4f2a9"])
