from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User, Character
from app.schemas.user import UserSummaryResponse, UserInfo, CharacterSummary
from app.auth.jwt import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/user", tags=["User"])
settings = get_settings()


@router.get("/summary", response_model=UserSummaryResponse)
async def get_user_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user profile and character list.
    
    This is the first endpoint called after login to get
    the user's basic info and their characters.
    """
    # Fetch user with characters
    result = await db.execute(
        select(User)
        .options(selectinload(User.characters))
        .where(User.id == current_user.id)
    )
    user = result.scalar_one()
    
    # Build response
    user_info = UserInfo(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        created_at=user.created_at
    )
    
    characters = [
        CharacterSummary(
            id=char.id,
            name=char.name,
            character_class=char.character_class,
            level=char.level,
            power=char.power
        )
        for char in user.characters
    ]
    
    return UserSummaryResponse(
        user=user_info,
        characters=characters,
        max_characters=settings.max_characters_per_user
    )

