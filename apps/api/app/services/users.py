from datetime import UTC

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.schemas.auth import CreateUserRequest, UpdateAccountRequest, UserResponse
from apps.api.app.security import hash_password, verify_password
from shared.config import get_settings
from shared.db.models import UserAccount, UserRole


DEFAULT_USERS = (
    ("admin", "admin", UserRole.ADMIN),
    ("viewer", "viewer", UserRole.VIEWER),
)


def normalize_username(username: str) -> str:
    normalized = username.strip().lower()
    if len(normalized) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username must be at least 3 characters")
    return normalized


def to_user_response(user: UserAccount) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        is_system_account=user.is_system_account,
        created_at=user.created_at.astimezone(UTC),
        updated_at=user.updated_at.astimezone(UTC),
    )


def get_user_by_id(db: Session, user_id: int) -> UserAccount | None:
    return db.get(UserAccount, user_id)


def get_user_by_username(db: Session, username: str) -> UserAccount | None:
    return db.scalar(select(UserAccount).where(UserAccount.username == normalize_username(username)))


def authenticate_user(db: Session, username: str, password: str) -> UserAccount:
    user = get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return user


def list_users(db: Session) -> list[UserAccount]:
    return list(db.scalars(select(UserAccount).order_by(UserAccount.username.asc())))


def create_user(db: Session, payload: CreateUserRequest, *, is_system_account: bool = False) -> UserAccount:
    username = normalize_username(payload.username)
    if get_user_by_username(db, username) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    user = UserAccount(
        username=username,
        password_hash=hash_password(payload.password),
        role=payload.role.value,
        is_system_account=is_system_account,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, target_user_id: int, *, acting_user: UserAccount) -> None:
    target = get_user_by_id(db, target_user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.id == acting_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account")

    db.delete(target)
    db.commit()


def update_account(db: Session, user: UserAccount, payload: UpdateAccountRequest) -> UserAccount:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")

    if payload.username:
        next_username = normalize_username(payload.username)
        existing = get_user_by_username(db, next_username)
        if existing is not None and existing.id != user.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
        user.username = next_username

    if payload.new_password:
        user.password_hash = hash_password(payload.new_password)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def ensure_seed_users(db: Session) -> None:
    if not get_settings().auth_seed_default_users:
        return

    for username, password, role in DEFAULT_USERS:
        existing = db.scalar(select(UserAccount).where(UserAccount.username == username))
        if existing is None:
            db.add(
                UserAccount(
                    username=username,
                    password_hash=hash_password(password),
                    role=role.value,
                    is_system_account=True,
                )
            )
            continue

        existing.password_hash = hash_password(password)
        existing.role = role.value
        existing.is_system_account = True
        db.add(existing)

    db.commit()
