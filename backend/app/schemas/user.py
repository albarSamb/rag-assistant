"""User schemas for API requests and responses."""
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response (excluding password)."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data."""
    user_id: str | None = None
