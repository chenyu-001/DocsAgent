"""
Authentication Module
- JWT Token management
- Password hashing
- Permission validation
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.config import settings
from api.db import get_db
from models.user_models import User, UserRole


# ========== Password Hashing ==========
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ========== Pydantic Models ==========
class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None


class UserCreate(BaseModel):
    """User registration model"""
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login model"""
    username: str
    password: str


class UserResponse(BaseModel):
    """User response model"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool

    class Config:
        from_attributes = True


# ========== Password Functions ==========
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


# ========== JWT Token Functions ==========
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT Token

    Args:
        data: Token payload data (must include sub: username)
        expires_delta: Optional expiration time delta

    Returns:
        JWT Token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode JWT Token

    Args:
        token: JWT Token string

    Returns:
        TokenData or None
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return TokenData(username=username)
    except JWTError:
        return None


# ========== User Authentication ==========
def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate user credentials

    Args:
        db: Database session
        username: Username
        password: Password

    Returns:
        User object or None
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ========== Dependency Functions to Get Current User ==========
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from Token

    Example usage:
    ```python
    @app.get("/me")
    def read_current_user(current_user: User = Depends(get_current_user)):
        return current_user
    ```
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = decode_access_token(token)
    if token_data is None or token_data.username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user

    Example usage:
    ```python
    @app.get("/me")
    def read_me(current_user: User = Depends(get_current_active_user)):
        return current_user
    ```
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# ========== Permission Validation ==========
def require_role(allowed_roles: list[UserRole]):
    """
    Permission validation decorator

    Example usage:
    ```python
    @app.get("/admin")
    def admin_only(current_user: User = Depends(require_role([UserRole.ADMIN]))):
        return {"message": "Admin only"}
    ```
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


# Common permission validators
require_admin = require_role([UserRole.ADMIN])
require_user = require_role([UserRole.ADMIN, UserRole.USER])
