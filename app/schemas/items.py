from pydantic import BaseModel
from enum import IntEnum


class ItemType(IntEnum):
    GEAR = 0
    CONSUMABLE = 1
    UPGRADE_GEM = 2
    REFINE_GEM = 3
    EVENT_ITEM = 4


class GearSlot(IntEnum):
    WEAPON = 0
    HELMET = 1
    CHEST = 2
    LEGS = 3
    GLOVES = 4
    BOOTS = 5
    RING = 6
    AMULET = 7
    BRACELET = 8
    WINGS = 9


class Rarity(IntEnum):
    COMMON = 0
    UNCOMMON = 1
    RARE = 2
    EPIC = 3
    LEGENDARY = 4
    MYTHIC = 5


class BonusStat(BaseModel):
    """Bonus stat on an item."""
    stat_type: str
    value: float


class Item(BaseModel):
    """Base item schema."""
    item_type: int
    id: str
    name: str
    rarity: int = 0
    
    class Config:
        from_attributes = True


class GearItem(Item):
    """Gear/equipment item."""
    item_type: int = ItemType.GEAR
    slot: int
    atk: int = 0
    def_: int = 0  # 'def' is reserved in Python
    bonus_stats: list[BonusStat] = []
    upgrade_level: int = 0
    refine_level: int = 0
    
    class Config:
        from_attributes = True
        populate_by_name = True
        # Map 'def_' to 'def' in JSON
        json_schema_extra = {
            "properties": {
                "def": {"type": "integer"}
            }
        }


class ConsumableItem(Item):
    """Consumable item."""
    item_type: int = ItemType.CONSUMABLE
    consumable_type: str
    effect_value: int
    stack_size: int = 1


class UpgradeGem(Item):
    """Upgrade gem for enhancing gear."""
    item_type: int = ItemType.UPGRADE_GEM
    gem_tier: int
    stack_size: int = 1


class RefineGem(Item):
    """Refine gem for refining gear."""
    item_type: int = ItemType.REFINE_GEM
    gem_tier: int
    stack_size: int = 1


class EventItem(Item):
    """Event-specific item."""
    item_type: int = ItemType.EVENT_ITEM
    event_id: str

