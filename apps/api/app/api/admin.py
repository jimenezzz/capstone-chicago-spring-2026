from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from apps.api.app.api.auth import get_current_user, require_admin
from apps.api.app.db.session import get_db
from apps.api.app.schemas.auth import CreateUserRequest, UserResponse
from apps.api.app.services.users import create_user, delete_user, list_users, to_user_response
from shared.db.models import UserAccount

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=list[UserResponse])
def admin_list_users(db: Session = Depends(get_db)) -> list[UserResponse]:
    return [to_user_response(user) for user in list_users(db)]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def admin_create_user(payload: CreateUserRequest, db: Session = Depends(get_db)) -> UserResponse:
    return to_user_response(create_user(db, payload))


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserAccount = Depends(get_current_user),
) -> Response:
    delete_user(db, user_id, acting_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
