"""Pydantic schemas for prediction endpoints."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.utils.validation import validate_time_horizon_months


class QuestionRequest(BaseModel):
    """Schema for prediction question request."""
    profile_id: int
    question: str = Field(..., min_length=1, max_length=500)
    time_horizon_months: Optional[int] = Field(default=12, ge=1, le=120)
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": 1,
                "question": "Will I get a new job soon?",
                "time_horizon_months": 12
            }
        }


class TimeWindow(BaseModel):
    """Schema for time window in predictions."""
    start: str  # YYYY-MM-DD
    end: str    # YYYY-MM-DD
    focus: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "start": "2024-03-01",
                "end": "2024-06-30",
                "focus": "promotion/role-shift",
                "confidence": 0.8
            }
        }


class Evidence(BaseModel):
    """Schema for evidence in predictions."""
    calc_field: str
    value: Any
    interpretation: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "calc_field": "timing.current_md",
                "value": "Moon",
                "interpretation": "Current MD activates career house"
            }
        }


class Source(BaseModel):
    """Schema for sources/citations in predictions."""
    title: str
    url: Optional[str] = None
    note: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Brihat Parashara Hora Shastra - Chapter on Dashas",
                "url": "https://example.com/bphs-dasha",
                "note": "Classical reference supporting timing logic"
            }
        }


class Answer(BaseModel):
    """Schema for prediction answer."""
    summary: str = Field(..., max_length=2000)
    time_windows: List[TimeWindow] = Field(default_factory=list)
    actions: List[str] = Field(..., min_items=2, max_items=4)
    risks: Optional[List[str]] = Field(default=None, max_items=2)
    evidence: List[Evidence] = Field(default_factory=list)
    confidence_topic: float = Field(..., ge=0.0, le=1.0)
    rationale: Optional[str] = Field(default=None, max_length=4000)
    sources: Optional[List[Source]] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": "Your career prospects look promising in the next 6 months...",
                "time_windows": [
                    {
                        "start": "2024-03-01",
                        "end": "2024-06-30",
                        "focus": "promotion/role-shift",
                        "confidence": 0.8
                    }
                ],
                "actions": [
                    "Focus on networking in March-April",
                    "Prepare for interviews in May-June",
                    "Consider upskilling opportunities"
                ],
                "risks": [
                    "Avoid major decisions during Mercury retrograde"
                ],
                "evidence": [
                    {
                        "calc_field": "timing.current_md",
                        "value": "Moon",
                        "interpretation": "Current MD activates career house"
                    }
                ],
                "confidence_topic": 0.75,
                "rationale": "Based on Jupiter transit to 10th from Lagna and strong 10th lord dignity.",
                "sources": [
                    {
                        "title": "Jupiter transit effects on career",
                        "url": "https://example.com/jupiter-career",
                        "note": "General transit principle"
                    }
                ]
            }
        }


class AnswerResponse(BaseModel):
    """Schema for prediction response."""
    prediction_id: int
    topic: str
    answer: Answer
    confidence_overall: float = Field(..., ge=0.0, le=1.0)
    sensitivity_notice: Optional[str] = None
    calc_snapshot_id: int
    llm_model: str
    created_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "prediction_id": 1,
                "topic": "career",
                "answer": {
                    "summary": "Your career prospects look promising...",
                    "time_windows": [],
                    "actions": [],
                    "risks": [],
                    "evidence": [],
                    "confidence_topic": 0.75
                },
                "confidence_overall": 0.72,
                "sensitivity_notice": None,
                "calc_snapshot_id": 1,
                "llm_model": "gpt-4o-mini",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class PredictionHistoryItem(BaseModel):
    """Schema for prediction history item."""
    id: int
    question: str
    topic: str
    answer_summary: str
    confidence_overall: float
    created_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "question": "Will I get a new job soon?",
                "topic": "career",
                "answer_summary": "Your career prospects look promising...",
                "confidence_overall": 0.72,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class PredictionHistoryResponse(BaseModel):
    """Schema for prediction history response."""
    predictions: List[PredictionHistoryItem]
    total: int
    page: int
    per_page: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "predictions": [],
                "total": 0,
                "page": 1,
                "per_page": 20
            }
        }

