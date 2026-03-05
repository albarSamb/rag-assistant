"""Authentication router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated

from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.dependencies import CurrentUser


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Register a new user account.
    
    Args:
        user_data: User registration data (email, password, full_name)
        db: Database session
        
    Returns:
        Created user
        
    Raises:
        ConflictException: If email already exists
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise ConflictException("Email already registered")
    
    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Login with email and password.
    
    Args:
        credentials: Login credentials (email, password)
        db: Database session
        
    Returns:
        JWT access token
        
    Raises:
        UnauthorizedException: If credentials are invalid
    """
    # Get user by email
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise UnauthorizedException("Invalid email or password")
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password")
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser):
    """Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user (from JWT token)
        
    Returns:
        User information
    """
    return current_user
