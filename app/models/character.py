from sqlalchemy import String, Integer, BigInteger, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
import uuid

from app.database import Base


class Character(Base):
    __tablename__ = "characters"
    
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    
    # Basic info
    name: Mapped[str] = mapped_column(String(50))
    character_class: Mapped[int] = mapped_column(Integer, default=1)  # 0=Mage, 1=Warrior, 2=Archer
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(BigInteger, default=0)
    power: Mapped[int] = mapped_column(Integer, default=100)
    
    # Currency
    gold: Mapped[int] = mapped_column(BigInteger, default=0)
    gems: Mapped[int] = mapped_column(Integer, default=0)
    
    # Stats (stored as JSON for flexibility)
    free_stat_points: Mapped[int] = mapped_column(Integer, default=0)
    stats: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Inventory (stored as JSON)
    inventory: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Equipment slots (stored as JSON)
    equipped: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Potions
    potions: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Skills
    skills: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Progression
    progression: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Shop data
    shop: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="characters")
    
    def __repr__(self) -> str:
        return f"<Character {self.name} (Lv.{self.level})>"
    
    @staticmethod
    def get_default_stats() -> dict:
        """Default stats for a new character."""
        return {
            "strength": 10,
            "agility": 10,
            "intelligence": 10,
            "vitality": 10,
            "luck": 5,
            "max_health": 100,
            "max_mana": 50,
            "physical_damage": 10,
            "magic_damage": 5,
            "defense": 5,
            "magic_resistance": 5,
            "critical_chance": 0.05,
            "critical_damage": 1.5,
            "dodge_chance": 0.02,
            "movement_speed": 100
        }
    
    @staticmethod
    def get_default_inventory() -> dict:
        """Default inventory for a new character."""
        return {
            "items": [],
            "max_slots": 50
        }
    
    @staticmethod
    def get_default_equipped() -> dict:
        """Default equipment slots."""
        return {
            "weapon": None,
            "helmet": None,
            "chest": None,
            "legs": None,
            "gloves": None,
            "boots": None,
            "ring1": None,
            "ring2": None,
            "amulet": None,
            "bracelet1": None,
            "bracelet2": None,
            "wings": None
        }
    
    @staticmethod
    def get_default_potions() -> dict:
        """Default potions for a new character."""
        return {
            "health_potions": 5,
            "mana_potions": 3
        }
    
    @staticmethod
    def get_default_progression() -> dict:
        """Default progression for a new character."""
        return {
            "chapters": {
                "highest_chapter": 1,
                "highest_stage": 1,
                "completed_stages": []
            },
            "dungeons": {
                "unlocked": [],
                "daily_attempts": {}
            }
        }
    
    @staticmethod
    def get_default_skills() -> dict:
        """Default skills for a new character."""
        return {
            "unlocked": [],
            "equipped": [],
            "skill_points": 0
        }
    
    @staticmethod
    def get_default_shop() -> dict:
        """Default shop data."""
        return {
            "daily_refresh_at": None,
            "purchased_today": []
        }

