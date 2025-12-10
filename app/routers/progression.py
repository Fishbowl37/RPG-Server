from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
import uuid

from app.database import get_db
from app.models import User, Character, BattleSession
from app.schemas.progression import (
    ChapterProgressResponse,
    ChapterInfo,
    StageConfigResponse,
    StageCompleteRequest,
    StageCompleteResponse,
    RewardsResponse,
    ProgressionUpdate,
)
from app.auth.jwt import get_current_user
from app.config import get_settings
from app.services.stage_generator import StageGenerator
from app.services.battle_validator import BattleValidator
from app.services.rewards import RewardsCalculator

router = APIRouter(prefix="/character", tags=["Progression"])
settings = get_settings()

TOTAL_CHAPTERS = 20
STAGES_PER_CHAPTER = 10


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


def get_completed_stages(character: Character) -> list[str]:
    """Extract completed stages from character progression."""
    prog = character.progression or {}
    chapters = prog.get("chapters", {})
    return chapters.get("completed_stages", [])


def is_stage_unlocked(character: Character, chapter: int, stage: int) -> bool:
    """Check if a stage is unlocked for the character."""
    # Stage 1-1 is always unlocked
    if chapter == 1 and stage == 1:
        return True
    
    completed = get_completed_stages(character)
    
    # To play stage X, you need to have completed stage X-1
    if stage > 1:
        prev_stage = f"{chapter}-{stage - 1}"
        return prev_stage in completed
    else:
        # First stage of a chapter requires last stage of previous chapter
        prev_chapter_last = f"{chapter - 1}-{STAGES_PER_CHAPTER}"
        return prev_chapter_last in completed


@router.get("/{character_id}/progression/chapters", response_model=ChapterProgressResponse)
async def get_chapter_progress(
    character_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get chapter unlock status and progress.
    
    Returns which chapters/stages are unlocked and completed.
    """
    character = await get_character_for_user(character_id, current_user, db)
    
    prog = character.progression or {}
    chapters_data = prog.get("chapters", {})
    
    highest_chapter = chapters_data.get("highest_chapter", 1)
    highest_stage = chapters_data.get("highest_stage", 1)
    completed_stages = chapters_data.get("completed_stages", [])
    
    # Build chapter list
    chapters = []
    for ch in range(1, TOTAL_CHAPTERS + 1):
        # Count completed stages in this chapter
        stages_completed = sum(
            1 for s in completed_stages 
            if s.startswith(f"{ch}-")
        )
        
        # Chapter is unlocked if we've reached it
        is_unlocked = ch <= highest_chapter or (
            ch == highest_chapter + 1 and 
            f"{ch-1}-{STAGES_PER_CHAPTER}" in completed_stages
        )
        
        chapters.append(ChapterInfo(
            chapter=ch,
            name=f"Chapter {ch}",
            is_unlocked=is_unlocked,
            stages_completed=stages_completed,
            total_stages=STAGES_PER_CHAPTER
        ))
    
    return ChapterProgressResponse(
        highest_chapter=highest_chapter,
        highest_stage=highest_stage,
        completed_stages=completed_stages,
        chapters=chapters
    )


@router.get(
    "/{character_id}/progression/chapters/{chapter}/stages/{stage}/config",
    response_model=StageConfigResponse
)
async def get_stage_config(
    character_id: str,
    chapter: int,
    stage: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get stage configuration before battle.
    
    CRITICAL ANTI-CHEAT ENDPOINT:
    - Generates a unique session token
    - Pre-calculates mob stats and rewards
    - Client MUST call this before every battle
    - Session token is required to complete the stage
    """
    # Validate chapter/stage range
    if chapter < 1 or chapter > TOTAL_CHAPTERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid chapter: {chapter}"
        )
    if stage < 1 or stage > STAGES_PER_CHAPTER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stage: {stage}"
        )
    
    character = await get_character_for_user(character_id, current_user, db)
    
    # Check if stage is unlocked
    if not is_stage_unlocked(character, chapter, stage):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Stage not unlocked"
        )
    
    # Generate mob configuration
    mobs = StageGenerator.generate_stage_mobs(chapter, stage)
    
    # Pre-calculate rewards (server decides!)
    rewards = StageGenerator.generate_stage_rewards(chapter, stage, mobs)
    
    # Add item drops to rewards
    rewards.items = RewardsCalculator.generate_stage_item_drops(
        chapter, stage, len(mobs)
    )
    
    # Create session token
    session_token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.battle_session_expiry_seconds
    )
    
    # Store session in database
    battle_session = BattleSession(
        session_token=session_token,
        character_id=character_id,
        chapter=chapter,
        stage=stage,
        mob_config=[m.model_dump() for m in mobs],
        rewards=rewards.model_dump(),
        expires_at=expires_at,
    )
    db.add(battle_session)
    await db.commit()
    
    # Determine stage type
    is_boss = stage == STAGES_PER_CHAPTER
    is_miniboss = stage == 5
    
    return StageConfigResponse(
        session_token=session_token,
        expires_at=int(expires_at.timestamp()),
        chapter=chapter,
        stage=stage,
        stage_name=StageGenerator.get_stage_name(chapter, stage),
        is_boss=is_boss,
        is_miniboss=is_miniboss,
        difficulty_multiplier=StageGenerator.get_difficulty_multiplier(chapter, stage),
        time_limit_seconds=StageGenerator.get_time_limit(chapter, stage),
        mobs=mobs,
        rewards=rewards
    )


@router.post(
    "/{character_id}/progression/chapters/complete",
    response_model=StageCompleteResponse
)
async def complete_stage(
    character_id: str,
    request: StageCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Complete a stage and receive rewards.
    
    CRITICAL ANTI-CHEAT ENDPOINT:
    - Validates session token (one-time use)
    - Validates battle log against expected values
    - Server applies pre-calculated rewards (not client values!)
    - Updates progression
    """
    character = await get_character_for_user(character_id, current_user, db)
    
    # 1. Fetch and validate session
    result = await db.execute(
        select(BattleSession).where(
            BattleSession.session_token == request.session_token,
            BattleSession.character_id == character_id
        )
    )
    session = result.scalar_one_or_none()
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session token"
        )
    
    # 2. Check if already used (prevent replay attacks)
    if session.is_used:
        return StageCompleteResponse(
            success=False,
            already_completed=True,
            error="Session already used"
        )
    
    # 3. Check expiration
    if session.is_expired():
        return StageCompleteResponse(
            success=False,
            error="Session expired"
        )
    
    # 4. Verify chapter/stage match
    if session.chapter != request.chapter or session.stage != request.stage:
        return StageCompleteResponse(
            success=False,
            error="Chapter/stage mismatch"
        )
    
    # 5. Reconstruct expected mobs from session
    from app.schemas.progression import MobConfig
    expected_mobs = [MobConfig(**m) for m in session.mob_config]
    
    # 6. Validate battle log
    is_valid, error = BattleValidator.validate_battle_log(
        battle_log=request.battle_log,
        expected_chapter=session.chapter,
        expected_stage=session.stage,
        expected_mobs=expected_mobs,
        session_created_at=session.created_at
    )
    
    if not is_valid:
        # Log suspicious activity (could flag for review)
        suspicion_score = BattleValidator.calculate_suspicion_score(
            request.battle_log, expected_mobs
        )
        print(f"Battle validation failed for {character_id}: {error} (suspicion: {suspicion_score})")
        
        return StageCompleteResponse(
            success=False,
            error=f"Battle validation failed: {error}"
        )
    
    # 7. Mark session as used
    session.is_used = True
    session.used_at = datetime.now(timezone.utc)
    
    # 8. Apply rewards from SESSION (not from client!)
    rewards_data = session.rewards
    
    # Update currency
    character.gold += rewards_data["gold"]
    character.gems += rewards_data["gems"]
    
    # Apply XP and check for level up
    new_xp, new_level, did_level_up = RewardsCalculator.apply_xp(
        character.xp,
        character.level,
        rewards_data["xp"]
    )
    character.xp = new_xp
    
    if did_level_up:
        character.level = new_level
        # Award stat points on level up
        character.free_stat_points += 5
    
    # Add items to inventory
    inventory = character.inventory or {"items": [], "max_slots": 50}
    for item in rewards_data.get("items", []):
        if len(inventory["items"]) < inventory["max_slots"]:
            inventory["items"].append(item)
    character.inventory = inventory
    
    # 9. Update progression
    stage_key = f"{session.chapter}-{session.stage}"
    progression = character.progression or {"chapters": {"completed_stages": []}}
    chapters_prog = progression.get("chapters", {"completed_stages": []})
    
    if stage_key not in chapters_prog.get("completed_stages", []):
        chapters_prog.setdefault("completed_stages", []).append(stage_key)
    
    # Update highest chapter/stage
    if session.chapter > chapters_prog.get("highest_chapter", 1):
        chapters_prog["highest_chapter"] = session.chapter
        chapters_prog["highest_stage"] = session.stage
    elif session.chapter == chapters_prog.get("highest_chapter", 1):
        if session.stage >= chapters_prog.get("highest_stage", 1):
            chapters_prog["highest_stage"] = session.stage
            # If completed last stage of chapter, advance to next chapter
            if session.stage == STAGES_PER_CHAPTER:
                chapters_prog["highest_chapter"] = session.chapter + 1
                chapters_prog["highest_stage"] = 1
    
    progression["chapters"] = chapters_prog
    character.progression = progression
    
    # Recalculate power
    from app.routers.character import calculate_power
    character.power = calculate_power(character)
    
    # 10. Commit all changes
    await db.commit()
    
    # 11. Build response
    return StageCompleteResponse(
        success=True,
        already_completed=False,
        rewards=RewardsResponse(
            gold=rewards_data["gold"],
            gems=rewards_data["gems"],
            xp=rewards_data["xp"],
            items=rewards_data.get("items", [])
        ),
        progression=ProgressionUpdate(
            highest_chapter=chapters_prog["highest_chapter"],
            highest_stage=chapters_prog["highest_stage"],
            completed_stages=chapters_prog["completed_stages"]
        ),
        level_up=did_level_up,
        new_level=new_level if did_level_up else None
    )

