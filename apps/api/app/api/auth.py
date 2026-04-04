from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from apps.api.app.db.session import get_db
from apps.api.app.schemas.auth import LoginRequest, LoginResponse, UpdateAccountRequest, UserResponse
from apps.api.app.security import create_access_token, decode_access_token
from apps.api.app.services.users import authenticate_user, get_user_by_id, to_user_response, update_account
from shared.config import get_settings
from shared.db.models import UserAccount

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserAccount:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_viewer(user: UserAccount = Depends(get_current_user)) -> UserAccount:
    return user


def require_admin(user: UserAccount = Depends(get_current_user)) -> UserAccount:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = authenticate_user(db, payload.username, payload.password)
    token, expires_at = create_access_token(user_id=user.id, username=user.username, role=user.role)
    return LoginResponse(
        access_token=token,
        expires_in_seconds=get_settings().auth_token_ttl_minutes * 60,
        expires_at=expires_at,
        user=to_user_response(user),
    )


@router.get("/me", response_model=UserResponse)
def me(user: UserAccount = Depends(require_viewer)) -> UserResponse:
    return to_user_response(user)


@router.patch("/me", response_model=UserResponse)
def patch_me(
    payload: UpdateAccountRequest,
    db: Session = Depends(get_db),
    user: UserAccount = Depends(require_viewer),
) -> UserResponse:
    updated = update_account(db, user, payload)
    return to_user_response(updated)
