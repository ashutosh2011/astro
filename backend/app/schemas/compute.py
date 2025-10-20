"""Pydantic schemas for compute endpoints."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.profile import ProfileCreate


class ComputeRequest(BaseModel):
    """Schema for compute request."""
    profile_id: Optional[int] = None
    # Inline birth data (alternative to profile_id)
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    gender: Optional[str] = None
    dob: Optional[str] = None  # YYYY-MM-DD format
    tob: Optional[str] = Field(None, pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$')
    tz: Optional[str] = None
    place: Optional[str] = Field(None, min_length=1, max_length=100)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    altitude_m: Optional[float] = Field(None, ge=-500, le=10000)
    uncertainty_minutes: Optional[int] = Field(None, ge=0, le=10)
    ayanamsa: Optional[str] = Field(default="Lahiri")
    house_system: Optional[str] = Field(default="WholeSign")
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": 1
            }
        }


class ComputeResponse(BaseModel):
    """Schema for compute response."""
    calc_snapshot_id: int
    input_hash: str
    ruleset_version: str
    ephemeris_version: str
    ayanamsa: str
    house_system: str
    calc_timestamp: str
    cached: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "calc_snapshot_id": 1,
                "input_hash": "a1b2c3d4e5f6...",
                "ruleset_version": "1.0.0",
                "ephemeris_version": "sepl_18",
                "ayanamsa": "Lahiri",
                "house_system": "WholeSign",
                "calc_timestamp": "2024-01-01T00:00:00Z",
                "cached": False
            }
        }


class CalcSnapshotData(BaseModel):
    """Schema for calc snapshot data structure."""
    meta: Dict[str, Any]
    panchanga: Dict[str, Any]
    d1: Dict[str, Any]
    dignities: Dict[str, Any]
    aspects: Dict[str, Any]
    dasha: Dict[str, Any]
    transits: Dict[str, Any]
    d9: Dict[str, Any]
    sav: Dict[str, Any]
    yogas: Dict[str, Any]
    bhava_bala: Dict[str, Any]
    sensitivity: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "meta": {
                    "ayanamsa": "Lahiri",
                    "house_system": "WholeSign",
                    "timezone": "America/New_York",
                    "dst_used": True,
                    "ephemeris": "SwissEph",
                    "calc_timestamp": "2024-01-01T00:00:00Z",
                    "ruleset_version": "1.0.0"
                },
                "panchanga": {
                    "weekday": "Tuesday",
                    "tithi": "Shukla Paksha 5",
                    "nakshatra": "Rohini",
                    "pada": 2,
                    "yoga": "Siddhi",
                    "karana": "Bava"
                },
                "d1": {
                    "ascendant": {
                        "sign": "Leo",
                        "degree": 15.5,
                        "nakshatra": "Magha",
                        "pada": 1
                    },
                    "planets": [],
                    "houses": []
                },
                "dignities": {},
                "aspects": {},
                "dasha": {
                    "current_md": "Moon",
                    "current_ad": "Mars",
                    "next_12m_ads": []
                },
                "transits": {
                    "saturn_house_from_lagna": 7,
                    "jupiter_house_from_lagna": 10,
                    "rahu_ketu_axis_from_lagna": [2, 8],
                    "sade_sati_phase": "none"
                },
                "d9": {
                    "asc_sign": "Sagittarius",
                    "planet_signs": {},
                    "d9_better": {}
                },
                "sav": [28, 31, 34, 29, 32, 30, 33, 31, 29, 34, 32, 30],
                "yogas": [],
                "bhava_bala": [0.72, 0.54, 0.68, 0.61, 0.75, 0.58, 0.69, 0.63, 0.71, 0.66, 0.73, 0.59],
                "sensitivity": {
                    "lagna_flips": False,
                    "moon_sign_flips": False,
                    "d9_asc_flips": False,
                    "dasha_boundary_risky": False
                }
            }
        }

