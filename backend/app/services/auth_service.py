"""Authentication service with JWT and bcrypt."""

from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
from app.schemas.auth import TokenData
from app.utils.errors import AuthenticationError, ValidationError


class AuthService:
    """Authentication service with JWT and bcrypt."""
    
    def __init__(self):
        """Initialize authentication service."""
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            # Convert strings to bytes for bcrypt
            password_bytes = plain_password.encode('utf-8')
            hash_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            # Log error but return False for any verification failure
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        try:
            # Convert password to bytes and hash with bcrypt
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_bytes = bcrypt.hashpw(password_bytes, salt)
            return hashed_bytes.decode('utf-8')
        except Exception as e:
            raise ValidationError(f"Password hashing failed: {str(e)}")
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: int = payload.get("user_id")
            email: str = payload.get("email")
            exp: int = payload.get("exp")
            
            if user_id is None or email is None:
                raise AuthenticationError("Invalid token payload")
            
            return TokenData(user_id=user_id, email=email, exp=exp)
        except JWTError:
            raise AuthenticationError("Could not validate credentials")
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        
        return user
    
    def create_user(self, db: Session, email: str, password: str) -> User:
        """Create a new user."""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValidationError("Email already registered")
        
        # Hash password
        password_hash = self.get_password_hash(password)
        
        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            is_active=True,
            is_admin=False
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()
    
    def is_admin(self, db: Session, user_id: int) -> bool:
        """Check if user is admin."""
        user = self.get_user_by_id(db, user_id)
        return user.is_admin if user else False


# Global auth service instance
auth_service = AuthService()

