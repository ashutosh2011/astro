"""Compute endpoint for calculation requests."""

import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.calc_snapshot import CalcSnapshot
from app.models.profile import Profile
from app.schemas.compute import ComputeRequest, ComputeResponse
from app.services.calc_engine.orchestrator import calc_orchestrator
from app.services.cache_service import cache_service
from app.services.encryption_service import encryption_service
from app.utils.errors import CalculationError, NotFoundError, ValidationError
from app.utils.rate_limit import compute_rate_limit
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter()


def _datetime_to_julian(dt: datetime) -> float:
    """Convert datetime to Julian day number."""
    from app.services.calc_engine.ephemeris import ephemeris_service
    return ephemeris_service._datetime_to_julian(dt)


def _calculate_input_hash(birth_data: Dict, calc_config: Dict) -> str:
    """Calculate input hash for idempotency."""
    # Create hash input from birth data and config
    hash_input = {
        "birth_data": birth_data,
        "calc_config": calc_config,
        "ruleset_version": calc_config.get("ruleset_version", "1.0.0")
    }
    
    # Convert to JSON string and hash
    json_str = json.dumps(hash_input, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode()).hexdigest()


def _prepare_birth_data_from_profile(profile: Profile) -> Dict:
    """Prepare birth data from profile."""
    # Decrypt sensitive fields
    decrypted_data = encryption_service.decrypt_dict(
        {
            "name": profile.name,
            "dob": profile.dob,
            "tob": profile.tob
        },
        ["name", "dob", "tob"]
    )
    
    # Parse date and time
    from datetime import datetime
    dob = datetime.strptime(decrypted_data["dob"], "%Y-%m-%d").date()
    tob_parts = decrypted_data["tob"].split(":")
    hour = int(tob_parts[0])
    minute = int(tob_parts[1])
    second = int(tob_parts[2]) if len(tob_parts) > 2 else 0
    
    # Create birth datetime
    birth_datetime = datetime.combine(dob, datetime.min.time().replace(hour=hour, minute=minute, second=second))
    
    # Convert to Julian day
    birth_jd = _datetime_to_julian(birth_datetime)
    
    # Get current time for transits
    current_jd = _datetime_to_julian(datetime.utcnow())
    
    return {
        "jd": birth_jd,
        "current_jd": current_jd,
        "lat": profile.lat,
        "lon": profile.lon,
        "altitude_m": profile.altitude_m,
        "timezone": profile.tz,
        "ayanamsa": profile.ayanamsa,
        "house_system": profile.house_system,
        "uncertainty_minutes": profile.uncertainty_minutes
    }


def _prepare_birth_data_from_request(request: ComputeRequest) -> Dict:
    """Prepare birth data from compute request."""
    from datetime import datetime
    
    # Parse date and time
    dob = datetime.strptime(request.dob, "%Y-%m-%d").date()
    tob_parts = request.tob.split(":")
    hour = int(tob_parts[0])
    minute = int(tob_parts[1])
    second = int(tob_parts[2]) if len(tob_parts) > 2 else 0
    
    # Create birth datetime
    birth_datetime = datetime.combine(dob, datetime.min.time().replace(hour=hour, minute=minute, second=second))
    
    # Convert to Julian day
    birth_jd = _datetime_to_julian(birth_datetime)
    
    # Get current time for transits
    current_jd = _datetime_to_julian(datetime.utcnow())
    
    return {
        "jd": birth_jd,
        "current_jd": current_jd,
        "lat": request.lat,
        "lon": request.lon,
        "altitude_m": request.altitude_m or 0.0,
        "timezone": request.tz,
        "ayanamsa": request.ayanamsa or "Lahiri",
        "house_system": request.house_system or "WholeSign",
        "uncertainty_minutes": request.uncertainty_minutes or 0
    }


@router.post("/", response_model=ComputeResponse)
async def compute(
    http_request: Request,
    request: ComputeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compute astrological calculations."""
    try:
        # Prepare birth data
        if request.profile_id:
            # Get profile from database
            profile = db.query(Profile).filter(
                Profile.id == request.profile_id,
                Profile.user_id == current_user.id
            ).first()
            
            if not profile:
                raise NotFoundError("Profile not found")
            
            birth_data = _prepare_birth_data_from_profile(profile)
            profile_id = profile.id
            
        else:
            # Use inline birth data
            if not all([request.name, request.dob, request.tob, request.tz, 
                       request.lat is not None, request.lon is not None]):
                raise ValidationError("All birth data fields are required for inline calculation")
            
            birth_data = _prepare_birth_data_from_request(request)
            profile_id = None
        
        # Calculate input hash for idempotency
        calc_config = {
            "ayanamsa": birth_data["ayanamsa"],
            "house_system": birth_data["house_system"],
            "ruleset_version": "1.0.0",
            "ephemeris_version": "sepl_18"
        }
        
        input_hash = _calculate_input_hash(birth_data, calc_config)
        
        # Check cache first
        cached_result = cache_service.get_calc_snapshot(input_hash)
        if cached_result:
            # Check if we have this in database
            existing_snapshot = db.query(CalcSnapshot).filter(
                CalcSnapshot.input_hash == input_hash,
                CalcSnapshot.user_id == current_user.id
            ).first()
            
            if existing_snapshot:
                return ComputeResponse(
                    calc_snapshot_id=existing_snapshot.id,
                    input_hash=input_hash,
                    ruleset_version=existing_snapshot.ruleset_version,
                    ephemeris_version=existing_snapshot.ephemeris_version,
                    ayanamsa=existing_snapshot.ayanamsa,
                    house_system=existing_snapshot.house_system,
                    calc_timestamp=existing_snapshot.created_at.isoformat() + "Z",
                    cached=True
                )
        
        # Run calculation
        calc_snapshot_data = calc_orchestrator.run_full_calculation(birth_data)
        
        # Compress data
        compressed_data = calc_orchestrator.compress_calc_snapshot(calc_snapshot_data)
        
        # Encode as base64 for database storage
        import base64
        encoded_data = base64.b64encode(compressed_data).decode('ascii')
        
        # Store in database
        calc_snapshot = CalcSnapshot(
            user_id=current_user.id,
            profile_id=profile_id,
            input_hash=input_hash,
            ayanamsa=birth_data["ayanamsa"],
            house_system=birth_data["house_system"],
            ephemeris_version="sepl_18",
            ruleset_version="1.0.0",
            payload_json=encoded_data  # Store as base64 encoded string
        )
        
        db.add(calc_snapshot)
        db.commit()
        db.refresh(calc_snapshot)
        
        # Store in cache
        cache_service.set_calc_snapshot(input_hash, calc_snapshot_data)
        
        return ComputeResponse(
            calc_snapshot_id=calc_snapshot.id,
            input_hash=input_hash,
            ruleset_version=calc_snapshot.ruleset_version,
            ephemeris_version=calc_snapshot.ephemeris_version,
            ayanamsa=calc_snapshot.ayanamsa,
            house_system=calc_snapshot.house_system,
            calc_timestamp=calc_snapshot.created_at.isoformat() + "Z",
            cached=False
        )
        
    except (CalculationError, ValidationError, NotFoundError) as e:
        raise HTTPException(
            status_code=400 if isinstance(e, (ValidationError, NotFoundError)) else 503,
            detail=e.message
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in compute endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during calculation"
        )


@router.get("/{calc_snapshot_id}")
async def get_calc_snapshot(
    calc_snapshot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get calculation snapshot by ID."""
    try:
        calc_snapshot = db.query(CalcSnapshot).filter(
            CalcSnapshot.id == calc_snapshot_id,
            CalcSnapshot.user_id == current_user.id
        ).first()
        
        if not calc_snapshot:
            raise NotFoundError("Calculation snapshot not found")
        
        # Decompress and return data
        import base64
        compressed_data = base64.b64decode(calc_snapshot.payload_json.encode('ascii'))
        calc_data = calc_orchestrator.decompress_calc_snapshot(compressed_data)
        
        return {
            "id": calc_snapshot.id,
            "input_hash": calc_snapshot.input_hash,
            "ayanamsa": calc_snapshot.ayanamsa,
            "house_system": calc_snapshot.house_system,
            "ephemeris_version": calc_snapshot.ephemeris_version,
            "ruleset_version": calc_snapshot.ruleset_version,
            "created_at": calc_snapshot.created_at.isoformat() + "Z",
            "data": calc_data
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving calculation snapshot")

