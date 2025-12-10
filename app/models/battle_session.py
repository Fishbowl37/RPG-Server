from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
import uuid

from app.database import Base


class BattleSession(Base):
    """
    Battle sessions for anti-cheat validation.
    Each session is created when a player requests stage config,
    and consumed when they complete the stage.
    """
    __tablename__ = "battle_sessions"
    
    session_token: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    character_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("characters.id", ondelete="CASCADE"),
        index=True
    )
    
    # Stage info
    chapter: Mapped[int] = mapped_column(Integer)
    stage: Mapped[int] = mapped_column(Integer)
    
    # Server-generated config (what the client was told to expect)
    mob_config: Mapped[dict] = mapped_column(JSON)
    
    # Pre-calculated rewards (server decides, not client!)
    rewards: Mapped[dict] = mapped_column(JSON)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    # Completion tracking
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        default=None
    )
    
    def __repr__(self) -> str:
        return f"<BattleSession {self.session_token[:8]}... Ch{self.chapter}-{self.stage}>"
    
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if the session is still valid (not used and not expired)."""
        return not self.is_used and not self.is_expired()

