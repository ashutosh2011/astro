"""CalcSnapshot model for storing calculation results."""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.models.database import Base


class CalcSnapshot(Base):
    """CalcSnapshot model for storing calculation results."""
    
    __tablename__ = "calc_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=True, index=True)
    
    # Input hash for idempotency
    input_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Calculation metadata
    ayanamsa = Column(String(50), nullable=False)
    house_system = Column(String(50), nullable=False)
    ephemeris_version = Column(String(50), nullable=False)
    ruleset_version = Column(String(50), nullable=False)
    
    # Compressed JSON payload
    payload_json = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<CalcSnapshot(id={self.id}, profile_id={self.profile_id}, input_hash={self.input_hash[:8]}...)>"

