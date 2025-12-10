from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import User, Character
from app.schemas.character import (
    CharacterCreate,
    CharacterResponse,
    CharacterFullData,
    CharacterSaveRequest,
    CharacterStats,
    Inventory,
    EquippedItems,
    Potions,
    Skills,
    Progression,
    ChapterProgression,
    DungeonProgression,
    Shop,
)
from app.auth.jwt import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/character", tags=["Character"])
settings = get_settings()


async def get_character_for_user(
    character_id: str,
    user: User,
    db: AsyncSession
) -> Character:
    """Helper to get a character and verify ownership."""
    result = await db.execute(
        select(Character).where(
            Character.id == character_id,
            Character.user_id == user.id
        )
    )
    character = result.scalar_one_or_none()
    
    if character is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    
    return character


@router.post("", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    request: CharacterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new character.
    
    Users can have a maximum of 3 characters.
    """
    # Check character limit
    result = await db.execute(
        select(func.count(Character.id)).where(Character.user_id == current_user.id)
    )
    char_count = result.scalar()
    
    if char_count >= settings.max_characters_per_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum of {settings.max_characters_per_user} characters allowed"
        )
    
    # Check for duplicate name
    result = await db.execute(
        select(Character).where(
            Character.user_id == current_user.id,
            Character.name == request.name
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a character with this name"
        )
    
    # Create character with defaults
    character = Character(
        user_id=current_user.id,
        name=request.name,
        character_class=request.character_class,
        level=1,
        xp=0,
        power=100,
        gold=100,  # Starting gold
        gems=10,   # Starting gems
        free_stat_points=0,
        stats=Character.get_default_stats(),
        inventory=Character.get_default_inventory(),
        equipped=Character.get_default_equipped(),
        potions=Character.get_default_potions(),
        skills=Character.get_default_skills(),
        progression=Character.get_default_progression(),
        shop=Character.get_default_shop(),
    )
    
    db.add(character)
    await db.commit()
    await db.refresh(character)
    
    return CharacterResponse(
        id=character.id,
        name=character.name,
        character_class=character.character_class,
        level=character.level,
        created_at=character.created_at
    )


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    character_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a character.
    
    This is permanent and cannot be undone.
    """
    character = await get_character_for_user(character_id, current_user, db)
    
    await db.delete(character)
    await db.commit()
    
    return None


@router.get("/{character_id}", response_model=CharacterFullData)
async def get_character(
    character_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Full Load - Get complete character data.
    
    Returns all character data including inventory, stats, progression, etc.
    Called when selecting a character to play.
    """
    character = await get_character_for_user(character_id, current_user, db)
    
    # Convert JSON fields to proper schema objects
    stats = CharacterStats(**character.stats) if character.stats else CharacterStats()
    inventory = Inventory(**character.inventory) if character.inventory else Inventory()
    equipped = EquippedItems(**character.equipped) if character.equipped else EquippedItems()
    potions = Potions(**character.potions) if character.potions else Potions()
    skills = Skills(**character.skills) if character.skills else Skills()
    shop = Shop(**character.shop) if character.shop else Shop()
    
    # Handle progression specially
    prog_data = character.progression or {}
    chapters_data = prog_data.get("chapters", {})
    dungeons_data = prog_data.get("dungeons", {})
    
    progression = Progression(
        chapters=ChapterProgression(**chapters_data) if chapters_data else ChapterProgression(),
        dungeons=DungeonProgression(**dungeons_data) if dungeons_data else DungeonProgression()
    )
    
    return CharacterFullData(
        id=character.id,
        name=character.name,
        character_class=character.character_class,
        level=character.level,
        xp=character.xp,
        power=character.power,
        gold=character.gold,
        gems=character.gems,
        free_stat_points=character.free_stat_points,
        stats=stats,
        inventory=inventory,
        equipped=equipped,
        potions=potions,
        skills=skills,
        progression=progression,
        shop=shop,
        created_at=character.created_at,
        updated_at=character.updated_at
    )


@router.put("/{character_id}", response_model=CharacterFullData)
async def save_character(
    character_id: str,
    request: CharacterSaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Full Save - Save complete character data.
    
    Allows partial updates - only provided fields will be updated.
    
    NOTE: For sensitive fields like gold/gems/xp, consider whether
    clients should be allowed to set them directly. In a strict
    anti-cheat model, these should only be modified by the server
    through gameplay endpoints (like stage completion).
    """
    character = await get_character_for_user(character_id, current_user, db)
    
    # Update only provided fields
    # NOTE: In production, you may want to restrict which fields
    # clients can modify directly (e.g., not gold/gems)
    
    if request.gold is not None:
        character.gold = request.gold
    if request.gems is not None:
        character.gems = request.gems
    if request.free_stat_points is not None:
        character.free_stat_points = request.free_stat_points
    if request.stats is not None:
        character.stats = request.stats
    if request.inventory is not None:
        character.inventory = request.inventory
    if request.equipped is not None:
        character.equipped = request.equipped
    if request.potions is not None:
        character.potions = request.potions
    if request.skills is not None:
        character.skills = request.skills
    if request.shop is not None:
        character.shop = request.shop
    
    # Recalculate power based on stats and equipment
    # This is a simplified calculation - adjust based on your game design
    character.power = calculate_power(character)
    
    await db.commit()
    await db.refresh(character)
    
    # Return full character data
    return await get_character(character_id, current_user, db)


def calculate_power(character: Character) -> int:
    """
    Calculate character power rating.
    
    This is a server-side calculation to prevent manipulation.
    Adjust the formula based on your game design.
    """
    stats = character.stats or {}
    
    # Base power from level
    power = character.level * 10
    
    # Add from stats
    power += stats.get("strength", 0) * 2
    power += stats.get("agility", 0) * 2
    power += stats.get("intelligence", 0) * 2
    power += stats.get("vitality", 0) * 2
    power += stats.get("physical_damage", 0) * 3
    power += stats.get("magic_damage", 0) * 3
    power += stats.get("defense", 0) * 2
    power += stats.get("magic_resistance", 0) * 2
    
    # Add from equipment (simplified - you'd iterate equipped items)
    # In a full implementation, you'd look up each equipped item and add its stats
    
    return max(100, power)  # Minimum power of 100

