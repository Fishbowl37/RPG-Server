import random
from app.schemas.progression import MobConfig, StageRewards


class StageGenerator:
    """
    Generates stage configurations including mobs and rewards.
    
    This is the SERVER's source of truth for what a stage contains.
    The client displays what we tell it to display.
    """
    
    # Mob templates by type
    MOB_TEMPLATES = {
        "orc_warrior": {
            "mob_name": "Orc Warrior",
            "mob_type": "melee",
            "base_health": 100,
            "base_damage": 15,
            "base_defense": 8,
            "magic_resistance": 3,
            "speed": 90.0,
            "attack_speed": 1.2,
            "critical_chance": 0.08,
            "critical_multiplier": 1.5,
            "dodge_chance": 0.05,
            "attack_range": 50.0,
            "behavior_type": "aggressive",
            "aggro_range": 150.0,
            "color": [0.4, 0.6, 0.3],
            "size_scale": 1.0,
            "special_abilities": ["charge"],
        },
        "goblin_archer": {
            "mob_name": "Goblin Archer",
            "mob_type": "ranged",
            "base_health": 60,
            "base_damage": 20,
            "base_defense": 4,
            "magic_resistance": 2,
            "speed": 110.0,
            "attack_speed": 1.0,
            "critical_chance": 0.12,
            "critical_multiplier": 1.8,
            "dodge_chance": 0.10,
            "attack_range": 200.0,
            "behavior_type": "defensive",
            "aggro_range": 200.0,
            "color": [0.3, 0.5, 0.2],
            "size_scale": 0.7,
            "special_abilities": ["rapid_shot"],
        },
        "dark_mage": {
            "mob_name": "Dark Mage",
            "mob_type": "magic",
            "base_health": 50,
            "base_damage": 30,
            "base_defense": 3,
            "magic_resistance": 15,
            "speed": 70.0,
            "attack_speed": 0.8,
            "critical_chance": 0.10,
            "critical_multiplier": 2.0,
            "dodge_chance": 0.03,
            "attack_range": 250.0,
            "behavior_type": "defensive",
            "aggro_range": 180.0,
            "color": [0.3, 0.1, 0.4],
            "size_scale": 0.9,
            "special_abilities": ["fireball", "teleport"],
        },
        "skeleton": {
            "mob_name": "Skeleton",
            "mob_type": "melee",
            "base_health": 70,
            "base_damage": 12,
            "base_defense": 6,
            "magic_resistance": 10,
            "speed": 85.0,
            "attack_speed": 1.4,
            "critical_chance": 0.05,
            "critical_multiplier": 1.3,
            "dodge_chance": 0.08,
            "attack_range": 45.0,
            "behavior_type": "patrol",
            "aggro_range": 120.0,
            "color": [0.9, 0.9, 0.85],
            "size_scale": 0.95,
            "special_abilities": [],
        },
        "troll": {
            "mob_name": "Troll",
            "mob_type": "melee",
            "base_health": 200,
            "base_damage": 25,
            "base_defense": 15,
            "magic_resistance": 5,
            "speed": 60.0,
            "attack_speed": 0.7,
            "critical_chance": 0.05,
            "critical_multiplier": 1.4,
            "dodge_chance": 0.02,
            "attack_range": 60.0,
            "behavior_type": "aggressive",
            "aggro_range": 100.0,
            "color": [0.5, 0.7, 0.5],
            "size_scale": 1.5,
            "special_abilities": ["regenerate", "ground_slam"],
        },
    }
    
    # Boss templates (stronger variants)
    BOSS_TEMPLATES = {
        "orc_warlord": {
            "mob_name": "Orc Warlord",
            "mob_type": "melee",
            "base_health": 500,
            "base_damage": 40,
            "base_defense": 20,
            "magic_resistance": 10,
            "speed": 80.0,
            "attack_speed": 1.0,
            "critical_chance": 0.15,
            "critical_multiplier": 2.0,
            "dodge_chance": 0.08,
            "attack_range": 70.0,
            "behavior_type": "aggressive",
            "aggro_range": 200.0,
            "color": [0.6, 0.2, 0.2],
            "size_scale": 1.8,
            "special_abilities": ["war_cry", "cleave", "enrage"],
        },
        "lich_king": {
            "mob_name": "Lich King",
            "mob_type": "magic",
            "base_health": 400,
            "base_damage": 60,
            "base_defense": 12,
            "magic_resistance": 30,
            "speed": 50.0,
            "attack_speed": 0.6,
            "critical_chance": 0.20,
            "critical_multiplier": 2.5,
            "dodge_chance": 0.05,
            "attack_range": 300.0,
            "behavior_type": "defensive",
            "aggro_range": 250.0,
            "color": [0.2, 0.1, 0.3],
            "size_scale": 1.6,
            "special_abilities": ["death_bolt", "summon_skeletons", "soul_drain"],
        },
        "dragon": {
            "mob_name": "Ancient Dragon",
            "mob_type": "magic",
            "base_health": 1000,
            "base_damage": 80,
            "base_defense": 25,
            "magic_resistance": 25,
            "speed": 100.0,
            "attack_speed": 0.5,
            "critical_chance": 0.15,
            "critical_multiplier": 2.0,
            "dodge_chance": 0.10,
            "attack_range": 350.0,
            "behavior_type": "aggressive",
            "aggro_range": 300.0,
            "color": [0.8, 0.3, 0.1],
            "size_scale": 3.0,
            "special_abilities": ["fire_breath", "tail_swipe", "fly"],
        },
    }
    
    # Chapter themes determine which mobs appear
    CHAPTER_THEMES = {
        1: ["orc_warrior", "goblin_archer"],
        2: ["orc_warrior", "goblin_archer", "skeleton"],
        3: ["skeleton", "dark_mage"],
        4: ["skeleton", "dark_mage", "troll"],
        5: ["dark_mage", "troll"],
        # Higher chapters mix all types with increased difficulty
    }
    
    @classmethod
    def get_difficulty_multiplier(cls, chapter: int, stage: int) -> float:
        """
        Calculate difficulty multiplier based on chapter and stage.
        """
        # Base difficulty scales with chapter
        base = 1.0 + (chapter - 1) * 0.5
        
        # Stage within chapter adds smaller increments
        stage_bonus = (stage - 1) * 0.1
        
        # Boss stages get extra difficulty
        if stage == 10:  # Final boss
            stage_bonus += 0.5
        elif stage == 5:  # Mini-boss
            stage_bonus += 0.25
        
        return base + stage_bonus
    
    @classmethod
    def get_mob_count(cls, chapter: int, stage: int) -> int:
        """
        Determine how many mobs spawn in a stage.
        """
        base_count = 3 + chapter // 2
        
        if stage == 10:  # Boss stage - fewer but stronger
            return 1
        elif stage == 5:  # Mini-boss
            return 2
        else:
            # Regular stages have more mobs at higher stages
            return min(base_count + stage // 3, 10)
    
    @classmethod
    def generate_mob(
        cls, 
        mob_id: str, 
        template: dict, 
        difficulty: float,
        chapter: int
    ) -> MobConfig:
        """
        Generate a mob with scaled stats.
        """
        # Scale stats by difficulty
        health = int(template["base_health"] * difficulty)
        damage = int(template["base_damage"] * difficulty)
        defense = int(template["base_defense"] * difficulty)
        magic_res = int(template["magic_resistance"] * difficulty)
        
        # XP and gold scale with difficulty
        base_xp = 10 + chapter * 5
        base_gold = 5 + chapter * 3
        
        return MobConfig(
            mob_id=mob_id,
            mob_name=template["mob_name"],
            mob_type=template["mob_type"],
            health=health,
            damage=damage,
            defense=defense,
            magic_resistance=magic_res,
            speed=template["speed"],
            attack_speed=template["attack_speed"],
            critical_chance=template["critical_chance"],
            critical_multiplier=template["critical_multiplier"],
            dodge_chance=template["dodge_chance"],
            attack_range=template["attack_range"],
            behavior_type=template["behavior_type"],
            aggro_range=template["aggro_range"],
            color=template["color"],
            size_scale=template["size_scale"],
            xp_reward=int(base_xp * difficulty),
            gold_reward=int(base_gold * difficulty),
            drop_chance=0.05 + chapter * 0.01,
            special_abilities=template["special_abilities"],
        )
    
    @classmethod
    def generate_stage_mobs(
        cls, 
        chapter: int, 
        stage: int
    ) -> list[MobConfig]:
        """
        Generate all mobs for a stage.
        """
        difficulty = cls.get_difficulty_multiplier(chapter, stage)
        mob_count = cls.get_mob_count(chapter, stage)
        mobs = []
        
        if stage == 10:
            # Final boss
            boss_choices = list(cls.BOSS_TEMPLATES.keys())
            boss_id = boss_choices[(chapter - 1) % len(boss_choices)]
            boss_template = cls.BOSS_TEMPLATES[boss_id]
            mobs.append(cls.generate_mob(boss_id, boss_template, difficulty, chapter))
            
        elif stage == 5:
            # Mini-boss (use boss template but weaker)
            boss_choices = list(cls.BOSS_TEMPLATES.keys())
            boss_id = boss_choices[(chapter - 1) % len(boss_choices)]
            boss_template = cls.BOSS_TEMPLATES[boss_id].copy()
            # Mini-boss is 60% of full boss stats
            boss_template["base_health"] = int(boss_template["base_health"] * 0.6)
            boss_template["base_damage"] = int(boss_template["base_damage"] * 0.6)
            mobs.append(cls.generate_mob(boss_id + "_mini", boss_template, difficulty, chapter))
            
            # Add one regular mob as support
            theme = cls.CHAPTER_THEMES.get(chapter, list(cls.MOB_TEMPLATES.keys()))
            mob_id = random.choice(theme)
            mobs.append(cls.generate_mob(mob_id, cls.MOB_TEMPLATES[mob_id], difficulty, chapter))
            
        else:
            # Regular stage - mix of mobs from chapter theme
            theme = cls.CHAPTER_THEMES.get(chapter, list(cls.MOB_TEMPLATES.keys()))
            
            for _ in range(mob_count):
                mob_id = random.choice(theme)
                template = cls.MOB_TEMPLATES[mob_id]
                mobs.append(cls.generate_mob(mob_id, template, difficulty, chapter))
        
        return mobs
    
    @classmethod
    def generate_stage_rewards(
        cls, 
        chapter: int, 
        stage: int,
        mobs: list[MobConfig]
    ) -> StageRewards:
        """
        Calculate rewards for completing a stage.
        
        Server pre-calculates this - client CANNOT modify rewards.
        """
        difficulty = cls.get_difficulty_multiplier(chapter, stage)
        
        # Base rewards scale with chapter and stage
        base_gold = 100 * chapter + 10 * stage
        base_gems = chapter + (stage // 5)  # Gems are rarer
        base_xp = 50 * chapter + 5 * stage
        
        # Sum mob rewards
        mob_gold = sum(m.gold_reward for m in mobs)
        mob_xp = sum(m.xp_reward for m in mobs)
        
        # Boss/mini-boss bonuses
        if stage == 10:
            multiplier = 3.0
        elif stage == 5:
            multiplier = 2.0
        else:
            multiplier = 1.0
        
        return StageRewards(
            gold=int((base_gold + mob_gold) * multiplier),
            gems=int(base_gems * multiplier),
            xp=int((base_xp + mob_xp) * multiplier),
            items=[]  # Item drops would be generated here
        )
    
    @classmethod
    def get_stage_name(cls, chapter: int, stage: int) -> str:
        """Generate a stage name."""
        if stage == 10:
            return f"Chapter {chapter} - Final Boss"
        elif stage == 5:
            return f"Chapter {chapter}-{stage} (Mini-Boss)"
        else:
            return f"Chapter {chapter}-{stage}"
    
    @classmethod
    def get_time_limit(cls, chapter: int, stage: int) -> int:
        """Get time limit in seconds for a stage."""
        base_time = 180  # 3 minutes base
        
        if stage == 10:
            return base_time + 120  # 5 minutes for boss
        elif stage == 5:
            return base_time + 60   # 4 minutes for mini-boss
        else:
            return base_time + stage * 10  # Slightly more time for later stages

