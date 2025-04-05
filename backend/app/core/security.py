from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional, Dict

from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token for the given subject
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "sub": str(subject),
        "type": "access"
    }
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(subject: str, expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {"exp": expire, "sub": subject, "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.REFRESH_TOKEN_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token
    Raises JWTError if invalid
    """
    payload = jwt.decode(
        token, 
        settings.SECRET_KEY, 
        algorithms=["HS256"]
    )
    return payload

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash"""
    return pwd_context.hash(password)

def decode_refresh_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.REFRESH_TOKEN_SECRET, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")
        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("Invalid token payload")
        return user_id
    except jwt.JWTError:
        raise ValueError("Invalid refresh token") 