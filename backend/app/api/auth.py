"""Authentication API endpoints."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.schemas.auth import UserRegister, UserLogin, Token
from app.services.auth_service import auth_service
from app.utils.errors import AuthenticationError, ValidationError
from app.utils.rate_limit import general_rate_limit
from app.config import settings

router = APIRouter()
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user."""
    try:
        token = credentials.credentials
        token_data = auth_service.verify_token(token)
        user = auth_service.get_user_by_id(db, user_id=token_data.user_id)
        
        if user is None:
            raise AuthenticationError("User not found")
        
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        
        return user
    except Exception as e:
        raise AuthenticationError("Could not validate credentials")


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
# @general_rate_limit  # Temporarily disabled
async def register(
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    try:
        # Create user
        user = auth_service.create_user(
            db=db,
            email=user_data.email,
            password=user_data.password
        )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = auth_service.create_access_token(
            data={"user_id": user.id, "email": user.email},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Registration failed: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
# @general_rate_limit  # Temporarily disabled
async def login(
    request: Request,
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user and return access token."""
    try:
        # Authenticate user
        user = auth_service.authenticate_user(
            db=db,
            email=user_data.email,
            password=user_data.password
        )
        
        if not user:
            raise AuthenticationError("Invalid email or password")
        
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = auth_service.create_access_token(
            data={"user_id": user.id, "email": user.email},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/logout")
# @general_rate_limit  # Temporarily disabled
async def logout(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Logout user (client should discard token)."""
    # In a stateless JWT system, logout is handled client-side
    # by discarding the token. We could implement token blacklisting
    # here if needed for enhanced security.
    return {"message": "Logged out successfully"}


@router.get("/me")
# @general_rate_limit  # Temporarily disabled
async def get_current_user_info(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Get current user information."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at.isoformat()
    }

