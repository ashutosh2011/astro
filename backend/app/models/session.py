"""Session model for tracking user sessions."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.database import Base


class Session(Base):
    """Session model for tracking user sessions."""
    
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=True, index=True)
    
    # Session state
    last_calc_snapshot_id = Column(Integer, ForeignKey("calc_snapshots.id"), nullable=True)
    last_prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True)
    onboarding_step = Column(String(50), default="profile_creation")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, step={self.onboarding_step})>"

