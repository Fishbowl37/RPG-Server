from pydantic import BaseModel
from datetime import datetime


class UserInfo(BaseModel):
    """Basic user information."""
    id: str
    email: str
    display_name: str | None = None
    avatar_url: str | None = None
    created_at: datetime


class CharacterSummary(BaseModel):
    """Brief character info for user summary."""
    id: str
    name: str
    character_class: int
    level: int
    power: int


class UserSummaryResponse(BaseModel):
    """Response for /user/summary endpoint."""
    user: UserInfo
    characters: list[CharacterSummary]
    max_characters: int = 3

