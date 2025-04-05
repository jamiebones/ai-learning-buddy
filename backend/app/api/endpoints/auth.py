# Standard library imports
from datetime import timedelta, datetime, timezone

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

# Application imports
from app.core import security
from app.core.config import settings
from app.core.db import get_db
from app.models.user import User, RefreshToken
from app.schemas.token import Token, RefreshToken as RefreshTokenSchema, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import get_current_user

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    query = select(User).where(User.email == user_data.email)
    result = await db.execute(query)
    user = result.scalars().first()
    
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    hashed_password = security.get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    # Note: The username field from OAuth form is used for email in our application
    query = select(User).where(User.email == form_data.username)
    result = await db.execute(query)
    user = result.scalars().first()
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = security.create_refresh_token(
        subject=str(user.id), expires_delta=refresh_token_expires
    )
    
    # Store refresh token in database
    expires_at = datetime.now(timezone.utc) + refresh_token_expires
    db_refresh_token = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(db_refresh_token)
    await db.commit()
    
    # Set refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # Convert days to seconds
        expires=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth/refresh",
        secure=settings.ENFORCE_HTTPS,
        samesite="lax"
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    refresh_token: RefreshTokenSchema = None,
    db: AsyncSession = Depends(get_db)
):
    # Get refresh token from request body or cookie
    token_str = None
    if refresh_token and refresh_token.refresh_token:
        token_str = refresh_token.refresh_token
    
    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Find the token in database
        query = select(RefreshToken).where(
            (RefreshToken.token == token_str) & 
            (RefreshToken.revoked == False) &
            (RefreshToken.expires_at > datetime.now(timezone.utc))
        )
        result = await db.execute(query)
        db_token = result.scalars().first()
        
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user ID from token
        user_id = security.decode_refresh_token(token_str)
        
        # Get user
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()
        
        if not user:
            # Revoke the token
            db_token.revoked = True
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Revoke the old token
        db_token.revoked = True
        await db.commit()
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            subject=str(user.id), expires_delta=access_token_expires
        )
        
        # Create new refresh token
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        new_refresh_token = security.create_refresh_token(
            subject=str(user.id), expires_delta=refresh_token_expires
        )
        
        # Store new refresh token in database
        expires_at = datetime.now(timezone.utc) + refresh_token_expires
        new_db_token = RefreshToken(
            token=new_refresh_token,
            user_id=user.id,
            expires_at=expires_at
        )
        db.add(new_db_token)
        await db.commit()
        
        # Set refresh token as HTTP-only cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            expires=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            path="/api/auth/refresh",
            secure=settings.ENFORCE_HTTPS,
            samesite="lax"
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Clear refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        path="/api/auth/refresh"
    )
    
    # Revoke all refresh tokens for the user
    query = select(RefreshToken).where(
        (RefreshToken.user_id == current_user.id) &
        (RefreshToken.revoked == False)
    )
    result = await db.execute(query)
    tokens = result.scalars().all()
    
    for token in tokens:
        token.revoked = True
    
    await db.commit()
    
    return {"detail": "Successfully logged out"} 

