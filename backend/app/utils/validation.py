"""Validation utilities for the Astro MVP Backend."""

import re
from datetime import datetime, date
from typing import Optional, Tuple
import pytz
from app.config import settings
from app.utils.errors import (
    InvalidTimezoneError,
    BirthDateOutOfRangeError,
    MissingLatLonError,
    ValidationError
)


def validate_timezone(timezone: str) -> str:
    """Validate IANA timezone string."""
    try:
        pytz.timezone(timezone)
        return timezone
    except pytz.exceptions.UnknownTimeZoneError:
        raise InvalidTimezoneError(timezone)


def validate_latitude(lat: float) -> float:
    """Validate latitude is within valid range."""
    if not isinstance(lat, (int, float)):
        raise ValidationError("Latitude must be a number")
    
    if not -90 <= lat <= 90:
        raise ValidationError(
            "Latitude must be between -90 and 90 degrees",
            details={"latitude": lat, "min": -90, "max": 90}
        )
    
    return float(lat)


def validate_longitude(lon: float) -> float:
    """Validate longitude is within valid range."""
    if not isinstance(lon, (int, float)):
        raise ValidationError("Longitude must be a number")
    
    if not -180 <= lon <= 180:
        raise ValidationError(
            "Longitude must be between -180 and 180 degrees",
            details={"longitude": lon, "min": -180, "max": 180}
        )
    
    return float(lon)


def validate_lat_lon(lat: Optional[float], lon: Optional[float]) -> Tuple[float, float]:
    """Validate that both latitude and longitude are provided."""
    if lat is None or lon is None:
        raise MissingLatLonError()
    
    return validate_latitude(lat), validate_longitude(lon)


def validate_birth_date(dob: date) -> date:
    """Validate birth date is within allowed range."""
    year = dob.year
    
    if not settings.min_birth_year <= year <= settings.max_birth_year:
        raise BirthDateOutOfRangeError(year, settings.min_birth_year, settings.max_birth_year)
    
    return dob


def validate_birth_time(tob: str) -> str:
    """Validate birth time format (HH:MM[:SS])."""
    # Allow formats: HH:MM or HH:MM:SS
    time_pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$'
    
    if not re.match(time_pattern, tob):
        raise ValidationError(
            "Birth time must be in format HH:MM or HH:MM:SS",
            details={"time_format": "HH:MM[:SS]", "provided": tob}
        )
    
    return tob


def validate_uncertainty_minutes(uncertainty: Optional[int]) -> int:
    """Validate uncertainty in minutes."""
    if uncertainty is None:
        return 0
    
    if not isinstance(uncertainty, int):
        raise ValidationError("Uncertainty must be an integer")
    
    if uncertainty < 0 or uncertainty > settings.max_uncertainty_minutes:
        raise ValidationError(
            f"Uncertainty must be between 0 and {settings.max_uncertainty_minutes} minutes",
            details={"uncertainty": uncertainty, "max": settings.max_uncertainty_minutes}
        )
    
    return uncertainty


def validate_altitude(altitude: Optional[float]) -> float:
    """Validate altitude in meters."""
    if altitude is None:
        return 0.0
    
    if not isinstance(altitude, (int, float)):
        raise ValidationError("Altitude must be a number")
    
    # Reasonable altitude range: -500m to 10000m
    if not -500 <= altitude <= 10000:
        raise ValidationError(
            "Altitude must be between -500 and 10000 meters",
            details={"altitude": altitude, "min": -500, "max": 10000}
        )
    
    return float(altitude)


def validate_ayanamsa(ayanamsa: Optional[str]) -> str:
    """Validate ayanamsa type."""
    if ayanamsa is None:
        return settings.ayanamsa_default
    
    valid_ayanamsas = ["Lahiri", "Raman", "KP", "Fagan-Bradley", "Yukteshwar"]
    
    if ayanamsa not in valid_ayanamsas:
        raise ValidationError(
            f"Ayanamsa must be one of: {', '.join(valid_ayanamsas)}",
            details={"ayanamsa": ayanamsa, "valid_options": valid_ayanamsas}
        )
    
    return ayanamsa


def validate_house_system(house_system: Optional[str]) -> str:
    """Validate house system."""
    if house_system is None:
        return settings.house_system_default
    
    valid_systems = ["WholeSign", "Placidus", "Koch", "Equal"]
    
    if house_system not in valid_systems:
        raise ValidationError(
            f"House system must be one of: {', '.join(valid_systems)}",
            details={"house_system": house_system, "valid_options": valid_systems}
        )
    
    return house_system


def validate_gender(gender: str) -> str:
    """Validate gender field."""
    valid_genders = ["male", "female", "other"]
    
    if gender.lower() not in valid_genders:
        raise ValidationError(
            f"Gender must be one of: {', '.join(valid_genders)}",
            details={"gender": gender, "valid_options": valid_genders}
        )
    
    return gender.lower()


def validate_place_name(place: str) -> str:
    """Validate place name."""
    if not isinstance(place, str):
        raise ValidationError("Place name must be a string")
    
    place = place.strip()
    
    if not place:
        raise ValidationError("Place name cannot be empty")
    
    if len(place) > 100:
        raise ValidationError(
            "Place name must be 100 characters or less",
            details={"place": place, "max_length": 100}
        )
    
    return place


def validate_name(name: str) -> str:
    """Validate person name."""
    if not isinstance(name, str):
        raise ValidationError("Name must be a string")
    
    name = name.strip()
    
    if not name:
        raise ValidationError("Name cannot be empty")
    
    if len(name) > 50:
        raise ValidationError(
            "Name must be 50 characters or less",
            details={"name": name, "max_length": 50}
        )
    
    return name


def validate_email(email: str) -> str:
    """Validate email format."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise ValidationError(
            "Invalid email format",
            details={"email": email}
        )
    
    return email.lower()


def validate_password(password: str) -> str:
    """Validate password strength and reject passwords longer than bcrypt's 72-byte limit."""
    if len(password) < 8:
        raise ValidationError(
            "Password must be at least 8 characters long",
            details={"min_length": 8}
        )
    
    # bcrypt has a 72-byte limit - reject passwords that exceed this
    password_bytes = len(password.encode('utf-8'))
    if password_bytes > 72:
        raise ValidationError(
            f"Password is too long ({password_bytes} bytes). Maximum allowed is 72 bytes for security reasons. Please use a shorter password.",
            details={"max_bytes": 72, "actual_bytes": password_bytes}
        )
    
    # Check for at least one letter and one number
    if not re.search(r'[A-Za-z]', password):
        raise ValidationError(
            "Password must contain at least one letter",
            details={"requirement": "at_least_one_letter"}
        )
    
    if not re.search(r'\d', password):
        raise ValidationError(
            "Password must contain at least one number",
            details={"requirement": "at_least_one_number"}
        )
    
    return password


def validate_time_horizon_months(months: Optional[int]) -> int:
    """Validate time horizon for predictions."""
    if months is None:
        return 12
    
    if not isinstance(months, int):
        raise ValidationError("Time horizon must be an integer")
    
    if not 1 <= months <= 120:
        raise ValidationError(
            "Time horizon must be between 1 and 120 months (10 years)",
            details={"months": months, "min": 1, "max": 120}
        )
    
    return months

