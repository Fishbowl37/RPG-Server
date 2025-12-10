import random
import uuid
from app.schemas.progression import StageRewards
from app.schemas.items import ItemType, Rarity


class RewardsCalculator:
    """
    Calculates and generates rewards for various game activities.
    
    All reward calculations happen SERVER-SIDE. The client
    never decides what rewards it gets.
    """
    
    # XP required per level (simple formula)
    @staticmethod
    def xp_for_level(level: int) -> int:
        """Calculate XP required to reach a level."""
        return 100 * level * level
    
    @staticmethod
    def calculate_level_from_xp(total_xp: int) -> int:
        """Calculate level from total XP."""
        level = 1
        while RewardsCalculator.xp_for_level(level + 1) <= total_xp:
            level += 1
        return level
    
    @staticmethod
    def apply_xp(
        current_xp: int, 
        current_level: int, 
        xp_gained: int
    ) -> tuple[int, int, bool]:
        """
        Apply XP and calculate level ups.
        
        Returns (new_xp, new_level, did_level_up).
        """
        new_xp = current_xp + xp_gained
        new_level = RewardsCalculator.calculate_level_from_xp(new_xp)
        did_level_up = new_level > current_level
        
        return new_xp, new_level, did_level_up
    
    @staticmethod
    def roll_item_drop(
        chapter: int, 
        stage: int, 
        drop_chance: float
    ) -> dict | None:
        """
        Roll for an item drop.
        
        Returns item dict or None if no drop.
        """
        if random.random() > drop_chance:
            return None
        
        # Determine rarity based on chapter/stage
        rarity_roll = random.random()
        
        # Higher chapters have better drop rates
        rare_threshold = 0.7 - (chapter * 0.02)
        epic_threshold = 0.9 - (chapter * 0.01)
        legendary_threshold = 0.98 - (chapter * 0.005)
        
        if rarity_roll > legendary_threshold:
            rarity = Rarity.LEGENDARY
        elif rarity_roll > epic_threshold:
            rarity = Rarity.EPIC
        elif rarity_roll > rare_threshold:
            rarity = Rarity.RARE
        elif rarity_roll > 0.4:
            rarity = Rarity.UNCOMMON
        else:
            rarity = Rarity.COMMON
        
        # Generate random gear
        slots = ["weapon", "helmet", "chest", "legs", "gloves", "boots", "ring", "amulet"]
        slot = random.choice(slots)
        
        # Base stats scale with chapter and rarity
        base_stat = 5 + chapter * 2 + rarity * 3
        
        item = {
            "item_type": ItemType.GEAR,
            "id": str(uuid.uuid4()),
            "name": RewardsCalculator._generate_item_name(slot, rarity),
            "rarity": rarity,
            "slot": slots.index(slot),
            "atk": base_stat if slot in ["weapon", "ring"] else base_stat // 3,
            "def": base_stat // 2 if slot in ["helmet", "chest", "legs", "gloves", "boots"] else 0,
            "bonus_stats": [],
            "upgrade_level": 0,
            "refine_level": 0,
        }
        
        # Add bonus stats for higher rarity
        if rarity >= Rarity.RARE:
            item["bonus_stats"] = RewardsCalculator._generate_bonus_stats(rarity)
        
        return item
    
    @staticmethod
    def _generate_item_name(slot: str, rarity: int) -> str:
        """Generate a random item name."""
        prefixes = {
            Rarity.COMMON: ["Worn", "Simple", "Basic"],
            Rarity.UNCOMMON: ["Sturdy", "Refined", "Quality"],
            Rarity.RARE: ["Superior", "Exceptional", "Pristine"],
            Rarity.EPIC: ["Heroic", "Valiant", "Glorious"],
            Rarity.LEGENDARY: ["Legendary", "Mythical", "Divine"],
        }
        
        slot_names = {
            "weapon": "Sword",
            "helmet": "Helm",
            "chest": "Chestplate",
            "legs": "Greaves",
            "gloves": "Gauntlets",
            "boots": "Boots",
            "ring": "Ring",
            "amulet": "Amulet",
        }
        
        prefix = random.choice(prefixes.get(rarity, ["Unknown"]))
        base = slot_names.get(slot, "Item")
        
        return f"{prefix} {base}"
    
    @staticmethod
    def _generate_bonus_stats(rarity: int) -> list[dict]:
        """Generate bonus stats based on rarity."""
        stat_types = [
            "strength", "agility", "intelligence", "vitality", "luck",
            "critical_chance", "critical_damage", "dodge_chance"
        ]
        
        num_stats = min(rarity - 1, 4)  # Rare=1, Epic=2, Legendary=3, Mythic=4
        chosen_stats = random.sample(stat_types, num_stats)
        
        bonus_stats = []
        for stat in chosen_stats:
            if stat in ["critical_chance", "dodge_chance"]:
                value = round(random.uniform(0.01, 0.05) * rarity, 3)
            elif stat == "critical_damage":
                value = round(random.uniform(0.1, 0.3) * rarity, 2)
            else:
                value = random.randint(1, 5) * rarity
            
            bonus_stats.append({
                "stat_type": stat,
                "value": value
            })
        
        return bonus_stats
    
    @staticmethod
    def generate_stage_item_drops(
        chapter: int,
        stage: int,
        num_mobs: int
    ) -> list[dict]:
        """
        Generate item drops for completing a stage.
        
        Each mob has a chance to drop an item.
        """
        items = []
        base_drop_chance = 0.05 + chapter * 0.01
        
        # Boss stages have guaranteed drops
        if stage == 10:
            # Guaranteed boss drop
            item = RewardsCalculator.roll_item_drop(chapter, stage, 1.0)
            if item:
                items.append(item)
        
        # Roll for each mob
        for _ in range(num_mobs):
            item = RewardsCalculator.roll_item_drop(chapter, stage, base_drop_chance)
            if item:
                items.append(item)
        
        return items

