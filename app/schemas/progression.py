from pydantic import BaseModel
from datetime import datetime


class MobConfig(BaseModel):
    """Configuration for a mob in a stage."""
    mob_id: str
    mob_name: str
    mob_type: str  # melee, ranged, magic
    health: int
    damage: int
    defense: int
    magic_resistance: int
    speed: float
    attack_speed: float
    critical_chance: float
    critical_multiplier: float
    dodge_chance: float
    attack_range: float
    behavior_type: str  # aggressive, defensive, patrol
    aggro_range: float
    color: list[float]  # RGB values
    size_scale: float
    xp_reward: int
    gold_reward: int
    drop_chance: float
    special_abilities: list[str] = []


class StageRewards(BaseModel):
    """Rewards for completing a stage."""
    gold: int
    gems: int
    xp: int
    items: list[dict] = []


class StageConfigResponse(BaseModel):
    """Response for stage config (sent before battle)."""
    session_token: str
    expires_at: int  # Unix timestamp
    chapter: int
    stage: int
    stage_name: str
    is_boss: bool
    is_miniboss: bool
    difficulty_multiplier: float
    time_limit_seconds: int
    mobs: list[MobConfig]
    rewards: StageRewards


class ChapterInfo(BaseModel):
    """Information about a single chapter."""
    chapter: int
    name: str
    is_unlocked: bool
    stages_completed: int
    total_stages: int = 10


class ChapterProgressResponse(BaseModel):
    """Response for chapter progress."""
    highest_chapter: int
    highest_stage: int
    completed_stages: list[str]
    chapters: list[ChapterInfo]


class MobKillLog(BaseModel):
    """Log entry for a mob kill."""
    name: str
    level: int
    max_health: int
    timestamp: int  # Unix timestamp in milliseconds


class BattleStats(BaseModel):
    """Statistics from a battle."""
    total_damage_dealt: int
    total_damage_received: int
    mobs_killed: int
    skills_used: int
    potions_used: int
    duration_ms: int


class BattleLog(BaseModel):
    """Complete battle log sent by client."""
    version: int = 1
    battle_start_time: int  # Unix timestamp in milliseconds
    battle_end_time: int  # Unix timestamp in milliseconds
    chapter: int
    stage: int
    player_level: int
    player_power: int
    player_class: int
    stats: BattleStats
    mob_kills: list[MobKillLog]
    checksum: str | None = None  # Optional integrity check


class StageCompleteRequest(BaseModel):
    """Request to complete a stage."""
    session_token: str
    chapter: int
    stage: int
    battle_log: BattleLog


class ProgressionUpdate(BaseModel):
    """Progression update after completing a stage."""
    highest_chapter: int
    highest_stage: int
    completed_stages: list[str]


class RewardsResponse(BaseModel):
    """Rewards given to the player."""
    gold: int
    gems: int
    xp: int
    items: list[dict] = []


class StageCompleteResponse(BaseModel):
    """Response after completing a stage."""
    success: bool
    already_completed: bool = False
    error: str | None = None
    rewards: RewardsResponse | None = None
    progression: ProgressionUpdate | None = None
    level_up: bool = False
    new_level: int | None = None

