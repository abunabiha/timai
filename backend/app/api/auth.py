from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    SetupAdminRequest,
    SetupStatusResponse,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/setup-status", response_model=SetupStatusResponse)
async def get_setup_status(db: Annotated[AsyncSession, Depends(get_db)]) -> SetupStatusResponse:
    """Check if the system has been initialized with at least one Admin account."""
    result = await db.execute(select(func.count(User.id)).where(User.role == "admin"))
    admin_count = result.scalar() or 0
    return SetupStatusResponse(is_setup=admin_count > 0, admin_count=admin_count)


@router.post("/setup-admin", response_model=TokenResponse)
async def setup_admin(
    payload: SetupAdminRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """First-run wizard: initialize the first Admin account. Fails if admin already exists."""
    result = await db.execute(select(func.count(User.id)).where(User.role == "admin"))
    admin_count = result.scalar() or 0
    if admin_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System is already initialized with an Admin account",
        )

    # Check if email is already taken
    existing_user = await db.execute(select(User).where(User.email == payload.email.lower()))
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already in use",
        )

    admin_user = User(
        name=payload.name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role="admin",
        is_active=True,
    )
    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)

    token = create_access_token(subject=admin_user.id, role=admin_user.role)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(admin_user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Authenticate user with email and password."""
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    token = create_access_token(subject=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    """Return currently authenticated user information."""
    return UserResponse.model_validate(current_user)
