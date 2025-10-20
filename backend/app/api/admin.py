"""Admin endpoints for health checks and cache management."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.models.database import get_db, engine
from app.services.cache_service import cache_service
from app.utils.errors import AuthorizationError
from app.utils.rate_limit import general_rate_limit
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter()


def check_admin_permissions(current_user: User = Depends(get_current_user)):
    """Check if user has admin permissions."""
    if not current_user.is_admin:
        raise AuthorizationError("Admin access required")
    return current_user


@router.get("/healthz")
async def health_check():
    """Liveness probe."""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


@router.get("/readyz")
# @general_rate_limit  # Temporarily disabled
async def readiness_check(
    request: Request,
    db: Session = Depends(get_db)
):
    """Readiness probe - check database and Redis connectivity."""
    try:
        # Check database
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    # Check Redis
    redis_status = "healthy" if cache_service.health_check() else "unhealthy"
    
    overall_status = "ready" if db_status == "healthy" and redis_status == "healthy" else "not_ready"
    
    return {
        "status": overall_status,
        "database": db_status,
        "redis": redis_status,
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.delete("/cache/reset/{profile_id}")
# @general_rate_limit  # Temporarily disabled
async def reset_profile_cache(
    request: Request,
    profile_id: int,
    admin_user: User = Depends(check_admin_permissions),
    db: Session = Depends(get_db)
):
    """Reset cache for a specific profile (admin only)."""
    try:
        # Verify profile exists
        from app.models.profile import Profile
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Clear user cache
        cleared_count = cache_service.clear_user_cache(profile.user_id)
        
        return {
            "message": f"Cache cleared for profile {profile_id}",
            "cleared_keys": cleared_count,
            "admin_user": admin_user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")


@router.delete("/cache/reset/all")
# @general_rate_limit  # Temporarily disabled
async def reset_all_cache(
    request: Request,
    admin_user: User = Depends(check_admin_permissions)
):
    """Reset all cache (admin only)."""
    try:
        # This would require implementing a method to clear all cache
        # For now, we'll return a not implemented message
        return {
            "message": "Clear all cache not implemented yet",
            "admin_user": admin_user.email,
            "note": "Use profile-specific cache reset instead"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")


@router.get("/stats")
# @general_rate_limit  # Temporarily disabled
async def get_admin_stats(
    request: Request,
    admin_user: User = Depends(check_admin_permissions),
    db: Session = Depends(get_db)
):
    """Get admin statistics."""
    try:
        from app.models.profile import Profile
        from app.models.calc_snapshot import CalcSnapshot
        from app.models.prediction import Prediction
        
        # Get counts
        total_users = db.query(User).count()
        total_profiles = db.query(Profile).count()
        total_calc_snapshots = db.query(CalcSnapshot).count()
        total_predictions = db.query(Prediction).count()
        
        # Get Redis status
        redis_healthy = cache_service.health_check()
        
        return {
            "total_users": total_users,
            "total_profiles": total_profiles,
            "total_calc_snapshots": total_calc_snapshots,
            "total_predictions": total_predictions,
            "redis_status": "healthy" if redis_healthy else "unhealthy",
            "admin_user": admin_user.email
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

