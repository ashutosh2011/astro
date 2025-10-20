"""Prediction model for storing LLM predictions."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.sql import func
from app.models.database import Base


class Prediction(Base):
    """Prediction model for storing LLM predictions."""
    
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    calc_snapshot_id = Column(Integer, ForeignKey("calc_snapshots.id"), nullable=False, index=True)
    
    # Question and classification
    question = Column(Text, nullable=False)
    topic = Column(String(50), nullable=False)
    
    # LLM metadata
    llm_model = Column(String(100), nullable=False)
    llm_params_json = Column(Text, nullable=False)  # Temperature, seed, etc.
    
    # Results
    result_json = Column(Text, nullable=False)
    confidence_overall = Column(Float, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Prediction(id={self.id}, profile_id={self.profile_id}, topic={self.topic})>"

