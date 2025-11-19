"""
§¡åàC!W
- JWT Token åå¡
- ∆»
- CPùV
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


# ========== ∆» ==========
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ========== Pydantic !ã ==========
class Token(BaseModel):
    """Token Õî!ã"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token pn!ã"""
    username: Optional[str] = None


class UserCreate(BaseModel):
    """(7˙!ã"""
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """(7{U!ã"""
    username: str
    password: str


class UserResponse(BaseModel):
    """(7Õî!ã"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool

    class Config:
        from_attributes = True


# ========== ∆ ==========
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """å¡∆"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """»∆"""
    return pwd_context.hash(password)


# ========== JWT Token  ==========
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    ˙ JWT Token

    Args:
        data: ÅÑpn8+ sub: username	
        expires_delta: «ˆÙÔ		

    Returns:
        JWT Token W&2
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
    „ JWT Token

    Args:
        token: JWT Token W&2

    Returns:
        TokenData  None
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return TokenData(username=username)
    except JWTError:
        return None


# ========== (7§¡ ==========
def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    å¡(7Ì¡

    Args:
        db: pnì›
        username: (7
        password: ∆

    Returns:
        (7˘a None
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ========== ùVËe∑÷SM(7 ==========
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Œ Token ∑÷SM(7

    (π
    ```python
    @app.get("/me")
    def read_current_user(current_user: User = Depends(get_current_user)):
        return current_user
    ```
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="‡’å¡Ì¡",
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
    ∑÷SM¿;(7

    (π
    ```python
    @app.get("/me")
    def read_me(current_user: User = Depends(get_current_active_user)):
        return current_user
    ```
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="(7*¿;")
    return current_user


# ========== CP¿Â ==========
def require_role(allowed_roles: list[UserRole]):
    """
    CP¿Â≈phÂÇ

    (π
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
                detail="CP≥"
            )
        return current_user
    return role_checker


# ÎwCPùV
require_admin = require_role([UserRole.ADMIN])
require_user = require_role([UserRole.ADMIN, UserRole.USER])
