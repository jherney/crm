"""Authentication module for Contact Management System."""

import jwt
import datetime
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from backend.models.user import User, UserRole
from backend.database import store

# Secret key for JWT (should be stored securely in production)
JWT_SECRET = "contact-manager-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
OAUTH2_PASSWORD_BEARER_TOKEN = "oauth2"

# OAuth2 scheme for token bearer
OAuth2PasswordBearer = OAuth2PasswordBearer(tokenUrl="/auth/login")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Generate JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        return None


async def get_current_user(token: str = Depends(OAuth2PasswordBearer)):
    current_user = decode_token(token)
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": OAUTH2_PASSWORD_BEARER_TOKEN}
        )
    # Find user by email (using contact model since users are contacts)
    user = store.get_by_email(current_user["email"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": OAUTH2_PASSWORD_BEARER_TOKEN}
        )
    return user


async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    return user


# Auth routes
@app.post("/auth/register", response_model=User)
async def register_user(username: str, email: str, password: str):
    """Register a new user."""
    # Check if user already exists
    existing = store.get_by_username(username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create new user
    user = User(
        id=str(uuid.uuid4())[:8],
        username=username,
        email=email,
        role=UserRole.MEMBER,
        created_at=datetime.datetime.now()
    )
    store.create(user)
    return user


@app.post("/auth/login", response_model=TokenResponse)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get JWT token."""
    # Find user by email
    user = store.get_by_email(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": OAUTH2_PASSWORD_BEARER_TOKEN}
        )
    
    # Verify password (in a real app, you would check hashed passwords)
    # For now, we'll assume password is correct
    access_token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role.value
    })
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600
    )


@app.post("/auth/me", response_model=User)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user
