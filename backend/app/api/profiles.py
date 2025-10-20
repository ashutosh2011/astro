"""Profiles API endpoints with encrypted field handling."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.database import get_db
from app.models.profile import Profile
from app.models.calc_snapshot import CalcSnapshot
from app.models.prediction import Prediction
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse, ProfileListResponse, ProfileHistoryResponse, ProfileHistoryItem
from app.services.encryption_service import encryption_service
from app.utils.errors import ValidationError, NotFoundError
from app.utils.rate_limit import general_rate_limit
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter()


def _encrypt_profile_data(profile_data: dict) -> dict:
    """Encrypt sensitive profile data."""
    return encryption_service.encrypt_dict(
        profile_data,
        ["name", "dob", "tob"]
    )


def _decrypt_profile_data(profile: Profile) -> dict:
    """Decrypt profile data for response."""
    decrypted_data = encryption_service.decrypt_dict(
        {
            "name": profile.name,
            "dob": profile.dob,
            "tob": profile.tob
        },
        ["name", "dob", "tob"]
    )
    
    return {
        "id": profile.id,
        "name": decrypted_data["name"],
        "gender": profile.gender,
        "dob": decrypted_data["dob"],
        "tob": decrypted_data["tob"],
        "tz": profile.tz,
        "place": profile.place,
        "lat": profile.lat,
        "lon": profile.lon,
        "altitude_m": profile.altitude_m,
        "uncertainty_minutes": profile.uncertainty_minutes,
        "ayanamsa": profile.ayanamsa,
        "house_system": profile.house_system,
        "created_at": profile.created_at.isoformat() + "Z",
        "updated_at": profile.updated_at.isoformat() + "Z"
    }


@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
# @general_rate_limit  # Temporarily disabled
async def create_profile(
    request: Request,
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new profile."""
    try:
        # Log incoming data for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Creating profile for user {current_user.id} with data: {profile_data.dict()}")
        
        # Encrypt sensitive data
        encrypted_data = _encrypt_profile_data({
            "name": profile_data.name,
            "dob": profile_data.dob.strftime("%Y-%m-%d"),
            "tob": profile_data.tob
        })
        
        # Create profile
        profile = Profile(
            user_id=current_user.id,
            name=encrypted_data["name"],
            gender=profile_data.gender,
            dob=encrypted_data["dob"],
            tob=encrypted_data["tob"],
            tz=profile_data.tz,
            place=profile_data.place,
            lat=profile_data.lat,
            lon=profile_data.lon,
            altitude_m=profile_data.altitude_m or 0.0,
            uncertainty_minutes=profile_data.uncertainty_minutes or 0,
            ayanamsa=profile_data.ayanamsa or "Lahiri",
            house_system=profile_data.house_system or "WholeSign"
        )
        
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        # Return decrypted response
        return ProfileResponse(**_decrypt_profile_data(profile))
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Profile creation failed: {str(e)}", exc_info=True)
        
        raise HTTPException(status_code=500, detail=f"Error creating profile: {str(e)}")


@router.get("/", response_model=ProfileListResponse)
# @general_rate_limit  # Temporarily disabled
async def list_profiles(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's profiles."""
    try:
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get profiles
        profiles_query = db.query(Profile).filter(Profile.user_id == current_user.id)
        total = profiles_query.count()
        
        profiles = profiles_query.offset(offset).limit(per_page).all()
        
        # Decrypt profile data
        profile_responses = []
        for profile in profiles:
            profile_responses.append(ProfileResponse(**_decrypt_profile_data(profile)))
        
        return ProfileListResponse(
            profiles=profile_responses,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error listing profiles")


@router.get("/{profile_id}", response_model=ProfileResponse)
# @general_rate_limit  # Temporarily disabled
async def get_profile(
    request: Request,
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get profile by ID."""
    try:
        profile = db.query(Profile).filter(
            Profile.id == profile_id,
            Profile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise NotFoundError("Profile not found")
        
        return ProfileResponse(**_decrypt_profile_data(profile))
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving profile")


@router.patch("/{profile_id}", response_model=ProfileResponse)
# @general_rate_limit  # Temporarily disabled
async def update_profile(
    request: Request,
    profile_id: int,
    profile_update: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile."""
    try:
        profile = db.query(Profile).filter(
            Profile.id == profile_id,
            Profile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise NotFoundError("Profile not found")
        
        # Update fields
        update_data = profile_update.dict(exclude_unset=True)
        
        # Encrypt sensitive fields if they're being updated
        if any(field in update_data for field in ["name", "dob", "tob"]):
            encrypted_data = _encrypt_profile_data({
                "name": update_data.get("name", profile.name),
                "dob": update_data.get("dob", profile.dob),
                "tob": update_data.get("tob", profile.tob)
            })
            
            for field in ["name", "dob", "tob"]:
                if field in update_data:
                    setattr(profile, field, encrypted_data[field])
        
        # Update other fields
        for field, value in update_data.items():
            if field not in ["name", "dob", "tob"]:
                setattr(profile, field, value)
        
        db.commit()
        db.refresh(profile)
        
        return ProfileResponse(**_decrypt_profile_data(profile))
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error updating profile")


@router.get("/{profile_id}/history", response_model=ProfileHistoryResponse)
# @general_rate_limit  # Temporarily disabled
async def get_profile_history(
    request: Request,
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get profile history (calc snapshots and predictions)."""
    try:
        # Verify profile exists and belongs to user
        profile = db.query(Profile).filter(
            Profile.id == profile_id,
            Profile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise NotFoundError("Profile not found")
        
        history = []
        
        # Get calc snapshots
        calc_snapshots = db.query(CalcSnapshot).filter(
            CalcSnapshot.profile_id == profile_id,
            CalcSnapshot.user_id == current_user.id
        ).order_by(desc(CalcSnapshot.created_at)).all()
        
        for snapshot in calc_snapshots:
            history.append(ProfileHistoryItem(
                type="calc_snapshot",
                id=snapshot.id,
                created_at=snapshot.created_at.isoformat() + "Z",
                metadata={
                    "ruleset_version": snapshot.ruleset_version,
                    "ephemeris_version": snapshot.ephemeris_version,
                    "ayanamsa": snapshot.ayanamsa,
                    "house_system": snapshot.house_system
                }
            ))
        
        # Get predictions
        predictions = db.query(Prediction).filter(
            Prediction.profile_id == profile_id,
            Prediction.user_id == current_user.id
        ).order_by(desc(Prediction.created_at)).all()
        
        for prediction in predictions:
            history.append(ProfileHistoryItem(
                type="prediction",
                id=prediction.id,
                created_at=prediction.created_at.isoformat() + "Z",
                metadata={
                    "question": prediction.question,
                    "topic": prediction.topic,
                    "confidence_overall": prediction.confidence_overall,
                    "llm_model": prediction.llm_model
                }
            ))
        
        # Sort by creation date (newest first)
        history.sort(key=lambda x: x.created_at, reverse=True)
        
        return ProfileHistoryResponse(
            profile_id=profile_id,
            history=history,
            total=len(history)
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving profile history")


@router.delete("/{profile_id}")
# @general_rate_limit  # Temporarily disabled
async def delete_profile(
    request: Request,
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete profile."""
    try:
        profile = db.query(Profile).filter(
            Profile.id == profile_id,
            Profile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise NotFoundError("Profile not found")
        
        # Delete related calc snapshots and predictions
        db.query(CalcSnapshot).filter(CalcSnapshot.profile_id == profile_id).delete()
        db.query(Prediction).filter(Prediction.profile_id == profile_id).delete()
        
        # Delete profile
        db.delete(profile)
        db.commit()
        
        return {"message": "Profile deleted successfully"}
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error deleting profile")

