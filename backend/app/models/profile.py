"""Profile model with encrypted fields."""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.database import Base


class Profile(Base):
    """Profile model with encrypted personal data."""
    
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Encrypted fields (will be encrypted at application level)
    name = Column(String(500), nullable=False)  # Encrypted name
    dob = Column(String(500), nullable=False)    # Encrypted date
    tob = Column(String(500), nullable=False)    # Encrypted time
    
    # Plain fields
    gender = Column(String(20), nullable=False)
    tz = Column(String(100), nullable=False)
    place = Column(String(255), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    altitude_m = Column(Float, default=0.0)
    uncertainty_minutes = Column(Integer, default=0)
    ayanamsa = Column(String(50), default="Lahiri")
    house_system = Column(String(50), default="WholeSign")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Profile(id={self.id}, user_id={self.user_id}, place={self.place})>"

