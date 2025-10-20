"""Pydantic schemas for authentication endpoints."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.utils.validation import validate_email, validate_password


class UserRegister(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72, description="Password must be 8-72 characters long (72-byte limit for security)")
    
    @field_validator('password')
    @classmethod
    def validate_password_field(cls, v: str) -> str:
        """Validate password using custom validation."""
        return validate_password(v)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class TokenData(BaseModel):
    """Schema for token payload data."""
    user_id: int
    email: str
    exp: int

