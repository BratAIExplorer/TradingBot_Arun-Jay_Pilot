"""
Authentication Module for ARUN Trading Bot API
Provides JWT token-based authentication for secure API access
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os
import secrets

# Configuration
SECRET_KEY = os.environ.get("ARUN_JWT_SECRET", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    exp: Optional[datetime] = None


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class AuthConfig:
    """
    Simple auth configuration.
    In production, use database or environment variables.
    """
    # Default admin credentials (CHANGE THESE!)
    DEFAULT_USERNAME = os.environ.get("ARUN_ADMIN_USER", "admin")
    DEFAULT_PASSWORD_HASH = pwd_context.hash(
        os.environ.get("ARUN_ADMIN_PASSWORD", "changeme123")
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate user credentials.
    Returns True if valid, False otherwise.
    """
    if username != AuthConfig.DEFAULT_USERNAME:
        return False
    if not verify_password(password, AuthConfig.DEFAULT_PASSWORD_HASH):
        return False
    return True


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data to encode
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        exp = payload.get("exp")
        
        if username is None:
            return None
            
        return TokenData(username=username, exp=datetime.fromtimestamp(exp))
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Dependency to get current authenticated user from JWT token.
    
    Raises:
        HTTPException: If token is invalid or expired
        
    Returns:
        Username string if authenticated
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    token_data = decode_token(token)
    
    if token_data is None:
        raise credentials_exception
    
    if token_data.exp and token_data.exp < datetime.utcnow():
        raise credentials_exception
    
    return token_data.username


# Optional: Less strict dependency for read-only endpoints
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[str]:
    """
    Optional authentication dependency.
    Returns username if authenticated, None otherwise.
    Does not raise exceptions for unauthenticated requests.
    """
    if credentials is None:
        return None
    
    token_data = decode_token(credentials.credentials)
    if token_data is None:
        return None
    
    return token_data.username
