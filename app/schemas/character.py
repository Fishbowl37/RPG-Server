from pydantic import BaseModel, Field
from datetime import datetime


class CharacterStats(BaseModel):
    """Character stats."""
    strength: int = 10
    agility: int = 10
    intelligence: int = 10
    vitality: int = 10
    luck: int = 5
    max_health: int = 100
    max_mana: int = 50
    physical_damage: int = 10
    magic_damage: int = 5
    defense: int = 5
    magic_resistance: int = 5
    critical_chance: float = 0.05
    critical_damage: float = 1.5
    dodge_chance: float = 0.02
    movement_speed: int = 100


class EquippedItems(BaseModel):
    """Equipped item slots."""
    weapon: str | None = None
    helmet: str | None = None
    chest: str | None = None
    legs: str | None = None
    gloves: str | None = None
    boots: str | None = None
    ring1: str | None = None
    ring2: str | None = None
    amulet: str | None = None
    bracelet1: str | None = None
    bracelet2: str | None = None
    wings: str | None = None


class Inventory(BaseModel):
    """Character inventory."""
    items: list[dict] = []
    max_slots: int = 50


class Potions(BaseModel):
    """Character potions."""
    health_potions: int = 5
    mana_potions: int = 3


class ChapterProgression(BaseModel):
    """Chapter progression data."""
    highest_chapter: int = 1
    highest_stage: int = 1
    completed_stages: list[str] = []


class DungeonProgression(BaseModel):
    """Dungeon progression data."""
    unlocked: list[str] = []
    daily_attempts: dict = {}


class Progression(BaseModel):
    """Full progression data."""
    chapters: ChapterProgression = Field(default_factory=ChapterProgression)
    dungeons: DungeonProgression = Field(default_factory=DungeonProgression)


class Skills(BaseModel):
    """Character skills."""
    unlocked: list[str] = []
    equipped: list[str] = []
    skill_points: int = 0


class Shop(BaseModel):
    """Shop data."""
    daily_refresh_at: datetime | None = None
    purchased_today: list[str] = []


class CharacterCreate(BaseModel):
    """Request to create a new character."""
    name: str = Field(..., min_length=1, max_length=50)
    character_class: int = Field(..., ge=0, le=2)  # 0=Mage, 1=Warrior, 2=Archer


class CharacterListItem(BaseModel):
    """Character in a list (brief info)."""
    id: str
    name: str
    character_class: int
    level: int
    power: int
    
    class Config:
        from_attributes = True


class CharacterResponse(BaseModel):
    """Response after creating a character."""
    id: str
    name: str
    character_class: int
    level: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CharacterFullData(BaseModel):
    """Complete character data for save/load."""
    id: str
    name: str
    character_class: int
    level: int
    xp: int
    power: int
    gold: int
    gems: int
    free_stat_points: int
    stats: CharacterStats
    inventory: Inventory
    equipped: EquippedItems
    potions: Potions
    skills: Skills
    progression: Progression
    shop: Shop
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CharacterSaveRequest(BaseModel):
    """Request to save character data (partial updates allowed)."""
    gold: int | None = None
    gems: int | None = None
    free_stat_points: int | None = None
    stats: dict | None = None
    inventory: dict | None = None
    equipped: dict | None = None
    potions: dict | None = None
    skills: dict | None = None
    shop: dict | None = None

