"""
JWT-based Authentication Module
Replaces Firebase Auth with self-contained token management
"""
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel


# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Make HTTP bearer optional (no auth errors when header is missing)
security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """JWT Token payload"""
    userId: str
    username: Optional[str] = None
    exp: Optional[datetime] = None


def create_access_token(user_id: str, username: str = None) -> str:
    """
    Create a JWT access token
    
    Args:
        user_id: User identifier
        username: Optional username
        
    Returns:
        JWT token string
    """
    expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "userId": user_id,
        "username": username or user_id,
        "exp": expires,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_token(token: str) -> TokenData:
    """
    Decode and verify JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData object
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("userId")
        
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing userId"
            )
        
        return TokenData(
            userId=user_id,
            username=payload.get("username"),
            exp=datetime.fromtimestamp(payload.get("exp"))
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> TokenData:
    """
    Permissive auth dependency: if token is missing/invalid/expired, fall back to anonymous.
    """
    try:
        if not credentials or not credentials.credentials:
            return TokenData(userId="anon", username="Anonymous")
        return decode_token(credentials.credentials)
    except HTTPException:
        # Fallback to anonymous when token invalid/expired
        return TokenData(userId="anon", username="Anonymous")


def create_demo_token(user_id: str = None) -> str:
    """
    Create a demo token for development/testing
    
    Args:
        user_id: Optional user ID (generates one if not provided)
        
    Returns:
        JWT token string
    """
    if not user_id:
        user_id = f"demo_user_{int(datetime.utcnow().timestamp())}"
    
    return create_access_token(user_id, username=f"Demo User ({user_id[:8]})")


def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[TokenData]:
    """
    Optional authentication - returns None if no token provided
    
    Args:
        credentials: Optional HTTP Authorization credentials
        
    Returns:
        TokenData object or None
    """
    if credentials and credentials.credentials:
        try:
            return decode_token(credentials.credentials)
        except HTTPException:
            return None
    return None

