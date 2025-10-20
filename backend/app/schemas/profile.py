"""Pydantic schemas for profile endpoints."""

from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field
from app.utils.validation import (
    validate_name, validate_gender, validate_birth_date, validate_birth_time,
    validate_timezone, validate_place_name, validate_latitude, validate_longitude,
    validate_altitude, validate_uncertainty_minutes, validate_ayanamsa, validate_house_system
)


class ProfileCreate(BaseModel):
    """Schema for creating a new profile."""
    name: str = Field(..., min_length=1, max_length=50)
    gender: str
    dob: date
    tob: str = Field(..., pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$')
    tz: str
    place: str = Field(..., min_length=1, max_length=100)
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    altitude_m: Optional[float] = Field(default=0.0, ge=-500, le=10000)
    uncertainty_minutes: Optional[int] = Field(default=0, ge=0, le=10)
    ayanamsa: Optional[str] = Field(default="Lahiri")
    house_system: Optional[str] = Field(default="WholeSign")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "gender": "male",
                "dob": "1990-05-15",
                "tob": "14:30",
                "tz": "America/New_York",
                "place": "New York, NY",
                "lat": 40.7128,
                "lon": -74.0060,
                "altitude_m": 10,
                "uncertainty_minutes": 5,
                "ayanamsa": "Lahiri",
                "house_system": "WholeSign"
            }
        }


class ProfileUpdate(BaseModel):
    """Schema for updating a profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    gender: Optional[str] = None
    dob: Optional[date] = None
    tob: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$')
    tz: Optional[str] = None
    place: Optional[str] = Field(None, min_length=1, max_length=100)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    altitude_m: Optional[float] = Field(None, ge=-500, le=10000)
    uncertainty_minutes: Optional[int] = Field(None, ge=0, le=10)
    ayanamsa: Optional[str] = None
    house_system: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Smith",
                "uncertainty_minutes": 10
            }
        }


class ProfileResponse(BaseModel):
    """Schema for profile response."""
    id: int
    name: str
    gender: str
    dob: date
    tob: str
    tz: str
    place: str
    lat: float
    lon: float
    altitude_m: float
    uncertainty_minutes: int
    ayanamsa: str
    house_system: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "John Doe",
                "gender": "male",
                "dob": "1990-05-15",
                "tob": "14:30",
                "tz": "America/New_York",
                "place": "New York, NY",
                "lat": 40.7128,
                "lon": -74.0060,
                "altitude_m": 10,
                "uncertainty_minutes": 5,
                "ayanamsa": "Lahiri",
                "house_system": "WholeSign",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class ProfileListResponse(BaseModel):
    """Schema for profile list response."""
    profiles: List[ProfileResponse]
    total: int
    page: int
    per_page: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "profiles": [],
                "total": 0,
                "page": 1,
                "per_page": 20
            }
        }


class ProfileHistoryItem(BaseModel):
    """Schema for profile history item."""
    type: str  # "calc_snapshot" or "prediction"
    id: int
    created_at: str
    metadata: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "calc_snapshot",
                "id": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "metadata": {
                    "ruleset_version": "1.0.0",
                    "ephemeris_version": "sepl_18"
                }
            }
        }


class ProfileHistoryResponse(BaseModel):
    """Schema for profile history response."""
    profile_id: int
    history: List[ProfileHistoryItem]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": 1,
                "history": [],
                "total": 0
            }
        }

